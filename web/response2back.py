import uuid
import json
import requests
from typing import Dict, List, Any, Union
import streamlit as st
from streamlit_modal import Modal
from web import sub_assembly as st_sub
from config.server_config import back_url
# 新建知识库响应
def create_process(base_address: str, collection_name: str):
    if collection_name is None:
        return

    response = requests.post(
        url=f'http://{base_address}/mme/create_kb',
        json=collection_name,
        headers={'Content-Type': 'application/json'}
    )
    result = response.json()

    if result['code'] == 200:
        success_modal = Modal(title="success", key="modal_key", max_width=400)
        with success_modal.container():
            st.markdown(f"""
                                     知识库{collection_name}创建成功
                                     """)

            st.button("确定", key="confirm", )
    else:
        error_modal = Modal(title="error", key="modal_key", max_width=400)
        with error_modal.container():
            st.markdown(f"""
                             知识库{collection_name}已存在，请选择其他名称
                             """)  # 这里的t[1]为用例名称
            # 定义一个确定按钮，注意key值为指定的session_state，on_click调用回调函数改session_state的值
            st.button("确定", key="confirm", )


# 展示知识库列表
def show_collections_process(base_address: str):
    print(f'http://{base_address}/mme/list_kb')
    response = requests.get(
        url=f'http://{base_address}/mme/list_kb',
    )
    result = response.json()
    if result['code'] == 200:
        collection_list = result['data']['collection_list']
        for i, collection_name in enumerate(collection_list):
            if st.session_state.first_load is None and i == 0:
                st.session_state.collection_name = collection_name      # 初始化的时候默认一下
                st.session_state.first_load = 'is_load'
            with st.container():
                # 展示知识库清单
                if st.button(collection_name, key=collection_name, use_container_width=True):
                    st.session_state.collection_name = collection_name


# 展示具体某个知识库的页面信息（右侧）
def show_details_process(base_address: str, collection_name: str):

    response = requests.get(
        url=f'http://{base_address}/mme/list_sub_db',
        json=collection_name,
        headers={'Content-Type': 'application/json'}
    )
    result = response.json()
    if result['code'] == 200:
        # 开始展示
        data_dic_list = response.json()['data']['data']
        items = []
        for i in range(0, len(data_dic_list)):
            x = {
                'title': data_dic_list[i]['file_name'],
                'details': f'''
                source_id: {data_dic_list[i]['source_id']}\n
                chunk_number: {data_dic_list[i]['chunk_number']}\n
                input_time: {data_dic_list[i]['input_time']}
                '''
            }
            items.append(x)
            pass

        # 遍历列表，为每个项目创建一个可展开的详情
        for i, item in enumerate(items):
            with st.expander(item["title"]):
                sub_col1, sub_col2 = st.columns([9, 1])
                with sub_col1:
                    st.write(item["details"])
                    # video修改一下，改成点开才显示的  done
                    # st.video(data_dic_list[i]['file_path'], format="video/mp4")
                with sub_col2:
                    video_source_id = data_dic_list[i]['source_id']
                    if st.button('🎦', key=f'video_{video_source_id}'):
                        st.session_state.video_path = data_dic_list[i]['file_path']

                    if st.button('🗑️', key=f'delete_{video_source_id}'):
                        # 执行删除操作，
                        delete_docs_process(
                            base_address=base_address,
                            collection_name=collection_name,
                            source_id=video_source_id
                        )
                        pass
            pass

    pass


# 删除这个文件
def delete_docs_process(
    base_address: str,
    collection_name: str,
    source_id: str
):

    data = {
        'collection_name' : collection_name,
        'source_id' : source_id
    }
    response = requests.post(
        url=f'http://{base_address}/mme/delete_docs',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    if response.json()['code'] == 200:
        st.session_state.collection_name = collection_name
        st.rerun()

    pass


# 上传
def upload_file_process(
    collection_name: str,
    files: Dict[str, Any],
    base_address: str=back_url
):
    data = {
        'collection_name': collection_name,
    }
    response = requests.post(
        url=f'http://{base_address}/mme/add_docs',
        files=files,
        data=data
    )
    if response.json()['code'] == 200:
        return True, ''
    else:
        return False, response.json()['data']['exception']


def st_chat_qa(info: Union[str, None]):

    if info == None:
        with st.container():
            # st.title("💬 MMeRAG 问答模块")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG 问答模块  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write('你好，你是谁')
            st.chat_message("assistant").write(
                '你好，请输入你的问题'
            )
            pass
    else:
        # 这个只允许执行一次
        st.session_state.llm_ans = chat_qa(query=info)
        with st.container():
            # st.title("💬 MMeRAG 问答模块")
            st.markdown(f"<h3 style='font-size: 30px;'>💬 MMeRAG 问答模块  当前知识库{st.session_state.collection_name}</h3>", unsafe_allow_html=True)
            st.chat_message('user').write(info)
            st.chat_message("assistant").write(
                st.session_state.llm_ans
            )
            pass
    pass

def chat_qa(query: str, base_address: str=back_url):
    data = {
        'query': query,
        'api_key' : st.session_state.user_api_key,
        'model_id' : st.session_state.model_llm,

    }
    response = requests.post(
        url=f'http://{base_address}/mme/chat_qa',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'},

    )
    if response.status_code == 200:
        return response.json()['data']['llm_ans']
    else:
        # return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息：{response.json()['data']['exception']}"
        return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息{response.json()}"


def st_naive_rag_qa(info: Union[str, None]):
    if info == None:
        with st.container():
            # st.title("💬 MMeRAG Naive")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG Naive  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write('你好，你是谁')
            st.chat_message("assistant").write(
                '你好，我是接入了naive rag方法的知识库问答大模型，请你提出你的问题，我会尽力回答。'
            )
            pass
    else:
        # 这个只允许执行一次
        llm_ans, ref_ans = naive_rag_qa(query=info)
        st.session_state.llm_ans, st.session_state.res_ans = llm_ans, ref_ans       # st.ss.ref_ans这个赋值没用，不知道为什么，很离谱，我也不动了也不管了

        with st.container():
            # st.title("💬 MMeRAG Naive")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG Naive  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write(info)
            st.chat_message("assistant").write(
                st.session_state.llm_ans
            )
            st.session_state.show_video_list = [False for _ in range(0, len(st.session_state.res_ans))]
            # st.button('具体内容', key='show_dialog', on_click=st_sub.show_details, kwargs={'info': info})
            st.button('具体内容', key='show_dialog', on_click=st_sub.show_details, kwargs={'info': info, 'ref_ans': ref_ans})
            pass
    pass

def details_up():
    st.session_state.show_details = True

def naive_rag_qa(query: str,base_address: str=back_url):
    data = {
        'query': query,
        'collection_name': st.session_state.collection_name,
        'top_k': st.session_state.top_k,
        'api_key': st.session_state.user_api_key,
        'model_id': st.session_state.model_llm,
    }
    response = requests.post(
        url=f'http://{base_address}/mme/naive_rag_qa',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 200:
        return response.json()['data']['llm_ans'], response.json()['data']['ref_ans']
    else:
        # return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息：{response.json()['data']['exception']}"
        return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息{response.json()}"



def st_advanced_rag_qa(info: Union[str, None]):
    if info == None:
        with st.container():
            # st.title("💬 MMeRAG Advanced")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG Advanced  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write('你好，你是谁')
            st.chat_message("assistant").write(
                '你好，我是接入了Advanced RAG方法的知识库问答大模型，请你提出你的问题，我会尽力回答。'
            )

            pass
    else:
        # 这个只允许执行一次
        llm_ans, ref_ans = advanced_rag_qa(query=info)
        st.session_state.llm_ans, st.session_state.ref_ans = llm_ans, ref_ans
        with st.container():
            # st.title("💬 MMeRAG Advanced")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG Advanced  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write(info)
            st.chat_message("assistant").write(
                st.session_state.llm_ans
            )
            st.session_state.show_video_list = [False for _ in range(0, len(ref_ans))]
            st.button('具体内容', key='show_dialog', on_click=st_sub.show_details, kwargs={'info': info, 'ref_ans': ref_ans})

            pass
    pass

def advanced_rag_qa(query: str, base_address: str=back_url):
    data = {
        'query': query,
        'collection_name': st.session_state.collection_name,
        'top_k': st.session_state.top_k,
        'num_candidates': st.session_state.num_candidates,
        'is_rewritten': st.session_state.is_rewritten,
        'is_rerank': st.session_state.is_rerank,
        'search_method': st.session_state.search_method,
        'api_key': st.session_state.user_api_key,
        'model_id': st.session_state.model_llm,
    }
    response = requests.post(
        url=f'http://{base_address}/mme/advanced_rag_qa',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 200:
        return response.json()['data']['llm_ans'], response.json()['data']['ref_ans']
    else:
        # return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息：{response.json()['data']['exception']}"
        return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息{response.json()}"


def st_qd_rag_qa(info: Union[str, None]):
    if info == None:
        with st.container():
            # st.title("💬 MMeRAG QD")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG QD  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write('你好，你是谁')
            st.chat_message("assistant").write(
                '你好，我是接入了问题重构RAG方法的知识库问答大模型，请你提出你的问题，我会尽力回答。'
            )
            pass
    else:
        # 这个只允许执行一次
        llm_ans, ref_ans = qd_rag_qa(query=info)
        st.session_state.llm_ans, st.session_state.ref_ans = llm_ans, ref_ans
        with st.container():
            # st.title("💬 MMeRAG QD")
            st.markdown(
                f"<h3 style='font-size: 30px;'>💬 MMeRAG QD  当前知识库{st.session_state.collection_name}</h3>",
                unsafe_allow_html=True)
            st.chat_message('user').write(info)
            st.chat_message("assistant").write(
                st.session_state.llm_ans
            )
            st.session_state.show_video_list = [False for _ in range(0, len(ref_ans))]
            st.button('具体内容', key='show_dialog', on_click=st_sub.show_details, kwargs={'info': info, 'ref_ans': ref_ans})

            pass
    pass

def qd_rag_qa(query: str,base_address: str=back_url):
    data = {
        'query': query,
        'collection_name': st.session_state.collection_name,
        'top_k': st.session_state.top_k,
        'num_candidates': st.session_state.num_candidates,
        'is_rerank': st.session_state.is_rerank,
        'search_method': st.session_state.search_method,
        'api_key': st.session_state.user_api_key,
        'model_id': st.session_state.model_llm,
    }
    response = requests.post(
        url=f'http://{base_address}/mme/query_decompose_rag_qa',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code == 200:
        return response.json()['data']['llm_ans'], response.json()['data']['ref_ans']
    else:
        # return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息：{response.json()['data']['exception']}"
        return f"错误：请检查您的API_KEY等信息，查看是否出现问题\n错误信息{response.json()}"



def set_active(tab):
    # 设置点击的按钮为激活状态，其余为非激活状态
    for key in ['tab1', 'tab2', 'tab3', 'tab4']:
        if key == tab:
            st.session_state[key] = True
        else:
            st.session_state[key] = False