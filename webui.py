import os
import streamlit as st
from streamlit_option_menu import option_menu
import web.response2back as r2b
from web.custom_modal import VideoModal, AddModal, Modal
from config.server_config import back_url
from config.mme_rag_config import CHAT_API_KEY

st.set_page_config(
    page_title="MMeRAG",
    layout="wide",
)
# 问答有关的状态组
if 'source_file' not in st.session_state:       # list
    st.session_state.source_files = None    #
if 'show_video' not in st.session_state:        # list
    st.session_state.show_video = None    # 不行，这个还是得多个，整成一个列表，肯定得在每个下拉列表里面展示，不然太长怎么
if 'ref_ans' not in st.session_state:
    st.session_state.ref_ans = []

if 'show_details' not in st.session_state:
    st.session_state.show_details = False

# 状态组
if 'tab1' not in st.session_state:
    st.session_state['tab1'] = True
if 'tab2' not in st.session_state:
    st.session_state['tab2'] = False
if 'tab3' not in st.session_state:
    st.session_state['tab3'] = False
if 'tab4' not in st.session_state:
    st.session_state['tab3'] = False

if 'first_load' not in st.session_state:
    st.session_state.first_load = None
if 'error_reason' not in st.session_state:
    st.session_state.error_reason = None
if 'collection_name' not in st.session_state:
    st.session_state.collection_name = None
# 初始化 session state
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'add_ok' not in st.session_state:
    st.session_state.add_ok = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
# 初始化 session_state 变量
if 'top_k' not in st.session_state:
    st.session_state.top_k = 10  # 设置默认值

if 'num_candidates' not in st.session_state:
    st.session_state.num_candidates = 5  # 设置默认值

if 'is_rewritten' not in st.session_state:
    st.session_state.is_rewritten = True  # 设置默认值

if 'is_rerank' not in st.session_state:
    st.session_state.is_rerank = True  # 设置默认值

if 'search_method' not in st.session_state:
    st.session_state.search_method = 'search_by_vector'  # 设置默认值
if 'search_index' not in st.session_state:
    st.session_state.search_index = 0
if 'llm_ans' not in st.session_state:
    st.session_state.llm_ans = None
if 'model_index' not in st.session_state:
    st.session_state.model_index = 0
if 'model_llm' not in st.session_state:
    st.session_state.model_llm = 'glm-4-flash'
if 'user_api_key' not in st.session_state:
    st.session_state.user_api_key = CHAT_API_KEY        # 默认


menu1 = '知识库处理'
menu2 = '知识库问答'
menu3 = '知识库问答'
# import streamlit.delta_generator.DeltaGenerator'
# st.sidebar.title("MMeRAG")
with st.sidebar:
    menu = option_menu("MMeRAG", [menu1, menu2],
                       icons=['database', "chat-square-text"],
                       menu_icon="wrench-adjustable", default_index=0)
    user_api_key = st.text_input('Enter your API-KEY:', type='password', value=st.session_state.user_api_key)

    # st.sidebar.write(user_api_key)

    selected_model = st.sidebar.selectbox('Choose a model', ['glm-4-flash', 'glm-4-plus', 'glm-4-long'],
                                          key='selected_model', index=st.session_state.model_index)
    if selected_model == 'glm-4-flash':
        st.session_state.model_index = 0
        st.session_state.model_llm = 'glm-4-flash'
    elif selected_model == 'glm-4-plus':
        st.session_state.model_index = 1
        st.session_state.model_llm = 'glm-4-plus'
    else:
        st.session_state.model_index = 2
        st.session_state.model_llm = 'glm-4-long'

    search_method = st.sidebar.selectbox('Choose a search_method', ['search_by_vector', 'search_by_bm25'],
                                          key='selected_search_method', index=st.session_state.search_index)

    if search_method == 'search_by_vector':
        st.session_state.search_index = 0
        st.session_state.search_method = 'search_by_vector'
    else:
        st.session_state.search_index = 1
        st.session_state.search_method = 'search_by_bm25'
    st.write(f"{st.session_state.search_method}, index: {st.session_state.search_index}")


    st.sidebar.write('top_k: chunk number for searching.')
    top_k = st.sidebar.slider('top_k', min_value=1, max_value=20, value=st.session_state.top_k, step=1)
    # 问题重生成
    is_rewritten = st.sidebar.checkbox('is_rewritten: advance rag only', value=st.session_state.is_rewritten)
    # 重排序
    is_rerank = st.sidebar.checkbox('is_rerank: advance rag & qd rag.', value=st.session_state.is_rerank)

    # st.sidebar.write(str(is_rerank))
    # 获取值
    st.session_state.user_api_key = user_api_key
    st.session_state.top_k = int(top_k)
    st.session_state.is_rerank = bool(is_rerank)
    st.session_state.is_rewritten = bool(is_rewritten)

def main():
    global chat_info
    col1, col2 = st.columns([1, 4])
    if menu == menu2:
        chat_info = st.chat_input()

    with col1:
        # 左侧二号侧边栏
        st.subheader("知识库列表")
        # 新建知识库
        with st.form("create"):
            st.text('请输入知识库名称')
            sub_col1, sub_col2 = st.columns([2, 1])

            with sub_col1:
                user_input = st.text_input('请输入知识库名称', label_visibility='collapsed')
                # 这里对应create

            with sub_col2:
                submit_button = st.form_submit_button("新建")
        # 更新 session state
        if submit_button:
            r2b.create_process(back_url, user_input)

        # 接下来是互斥的button
        # 使用容器来更好地控制布局
        r2b.show_collections_process(back_url)
        pass

    with col2:
        if menu == menu1:
            # 知识库处理的内容
            # 创建一个文件上传器，允许用户上传文件
            uploaded_file = st.file_uploader("请选择一个音视频上传", type=['mp3', 'mp4', 'avi', 'wav'])
            if uploaded_file is not None and st.session_state.uploaded_file != uploaded_file:
                # 上传文件操作
                file_bytes = uploaded_file.getvalue()
                file_name = uploaded_file.name
                files = {'file': (file_name, file_bytes)}
                # 更新状态
                st.session_state.uploaded_file = uploaded_file

                is_ok, reason = r2b.upload_file_process(
                    collection_name=st.session_state.collection_name, files=files)
                if is_ok:
                    st.session_state.add_ok = True
                else:
                    st.session_state.add_ok = False
                    st.session_state.error_reason = reason
            if st.session_state.collection_name is None:
                pass
            else:
                r2b.show_details_process(back_url, collection_name=st.session_state.collection_name)

            pass
        if menu == menu2:
            # 大模型问答的内容
            # tab_pure_qa, tab_na_rag, tab_ad_rag, tab_qd_rag = st.tabs([
            #     '一般问答', '普通RAG', '高级RAG', '问题重构RAG'
            # ])
            # 创建一行按钮
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                tab1 = st.button('常规问答', use_container_width=True, on_click=lambda: r2b.set_active('tab1'))
                if tab1 and not st.session_state['tab1']:
                    r2b.set_active('tab1')
            with col2:
                tab2 = st.button('普通RAG', use_container_width=True, on_click=lambda: r2b.set_active('tab2'))
                if tab2 and not st.session_state['tab2']:
                    r2b.set_active('tab2')
            with col3:
                tab3 = st.button('高级RAG', use_container_width=True, on_click=lambda: r2b.set_active('tab3'))
                if tab3 and not st.session_state['tab3']:
                    r2b.set_active('tab3')
            with col4:
                tab3 = st.button('问题重构RAG', use_container_width=True, on_click=lambda: r2b.set_active('tab4'))
                if tab3 and not st.session_state['tab4']:
                    r2b.set_active('tab4')


            # 根据激活状态显示不同的内容
            if st.session_state['tab1']:
                r2b.st_chat_qa(info=chat_info)
            elif st.session_state['tab2']:
                r2b.st_naive_rag_qa(info=chat_info)
            elif st.session_state['tab3']:
                r2b.st_advanced_rag_qa(info=chat_info)
            else:
                r2b.st_qd_rag_qa(info=chat_info)

        # -----------------------
        # 各种弹窗
        if st.session_state.video_path is not None:
            video_modal = VideoModal(title="video", key="modal_key", max_width=600)
            with video_modal.container():
                st.video(st.session_state.video_path, format="video/mp4")
                # 定义一个确定按钮，注意key值为指定的session_state，on_click调用回调函数改session_state的值
                if st.button("确定", key="confirm", ):
                    st.session_state.video_path = None
                    st.rerun()

        if st.session_state.add_ok is not None and st.session_state.add_ok:
            add_modal = AddModal(title="success", key="modal_key", max_width=800, )
            with add_modal.container():
                st.markdown('''文件上传成功！''')
                # 定义一个确定按钮，注意key值为指定的session_state，on_click调用回调函数改session_state的值
                if st.button("确定", key="confirm"):
                    st.session_state.add_ok = None
                    st.rerun()
        if st.session_state.add_ok is not None and not st.session_state.add_ok:
            add_modal = AddModal(title="failed", key="modal_key", max_width=800, )
            with add_modal.container():
                st.markdown(f'''文件上传失败！错误信息{st.session_state.error_reason}''')
                # 定义一个确定按钮，注意key值为指定的session_state，on_click调用回调函数改session_state的值
                if st.button("确定", key="confirm"):
                    st.session_state.add_ok = None
                    st.rerun()



if __name__ == '__main__':
    main()
