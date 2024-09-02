import uuid
import streamlit as st
from typing import Union, List
import os


@st.dialog("来源信息", width='large')
def show_details(info: str, ref_ans: List):
    # print(ref_ans)
    details_list = ref_ans  # 必须要走这一关，不能直接操作session_state,我也不知道为什么，别改
    l = len(details_list)
    llm_ans = st.session_state.llm_ans
    html_content = f"""
        <h1 style="color: #336699;">你的提问</h1>
        <p style="font-size: 18px; color: #666666;">
            {info}<br>
        </p>
        <h1 style="color: #336699;">回答</h1>
        <p style="font-size: 18px; color: #666666;">
            {llm_ans}<br></p>

    """
    st.markdown(html_content, unsafe_allow_html=True)
    html_content2 = f"""
        <h1 style="color: #336699;">参考资料</h1>
    """
    st.markdown(html_content2, unsafe_allow_html=True)
    for i, chunk_dict in enumerate(details_list):
        video_name = os.path.basename(chunk_dict['source_path']).split('.')[0]
        video_name, video_ext = os.path.splitext(video_name)

        # 添加下拉列表
        with st.expander(f"| {i}/{l} | {video_name} |"):
            sub_col1, sub_col2 = st.columns([9, 1])
            with sub_col1:
                st.write(
                    # str(chunk_dict),
                    f"""
                    内容： {chunk_dict['text']}\n
                    文件名： {video_name}\n
                    视频时间点： {float(chunk_dict['time'])//1000} 秒\n
                    
                    """
                )
            with sub_col2:
                if st.button('展开', key=f'open_video_{i}'):  # , on_click=show_it, kwargs={'i': i}):
                    st.session_state.show_video_list[i] = True
                if st.button('取消', key=f'close_video_{i}'):  # , on_click=close_it, kwargs={'i': i})
                    st.session_state.show_video_list[i] = False
            if st.session_state.show_video_list[i]:
                st.video(chunk_dict['source_path'], format="video/mp4",
                        start_time= float(chunk_dict['time'])//1000 - 1 if float(chunk_dict['time'])//1000 - 1  > 0 else 0
                         )  # 因为视频的话有时候对不准（他会选择帧末尾），所以就提前一秒


def show_it(i: int):
    st.session_state.show_video_list[i] = True

def close_it(i: int):
    st.session_state.show_video_list[i] = False