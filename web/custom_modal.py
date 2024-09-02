import streamlit as st
from streamlit_modal import Modal


class VideoModal(Modal):
    def close(self, rerun_condition=True):
        # super
        if st.session_state.video_path is not None:
            st.session_state.video_path = None
        super().close(rerun_condition)


class AddModal(Modal):
    def close(self, rerun_condition=True):
        # super
        if st.session_state.add_ok is not None:
            st.session_state.add_ok = None
        super().close(rerun_condition)


# class DetailModal(Modal):
#     def close(self, rerun_condition=True):
#         # super
#         if st.session_state.add_ok is not None:
#             st.session_state.add_ok = None
#         super().close(rerun_condition)