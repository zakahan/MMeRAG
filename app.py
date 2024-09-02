import sys
sys.path.append("/mnt/c/MyScripts/Indie/MMeRAG")
import argparse
from fastapi import FastAPI
import uvicorn

from config.server_config import VERSION, back_host, back_port
from apis.utils import BaseResponse
from apis.crud_apis import list_kb, list_kb_details, create_kb, add_docs, delete_kb
from apis.crud_apis import rename_kb, drop_all_kb, delete_docs, list_sub_db, upload_file_api
from apis.core_apis import chat_qa, bm25_search, vector_search, naive_rag_qa, advanced_rag_qa, query_decompose_rag_qa


def mount_app_routes(app: FastAPI):
    # ----------------------------------------
    # 知识库交互 --------------------------------
    app.post('/mme/upload_file',
             summary='直接加载文档到raw'
             )(upload_file_api)
    app.get('/mme/list_kb',
            summary='知识库列表展示',
            )(list_kb)

    app.get('/mme/list_kb_details',
             summary='知识库信息细节展示'
             )(list_kb_details)

    app.get('/mme/list_sub_db',
            summary='某个知识库内容展示',
    )(list_sub_db)

    app.post('/mme/create_kb',
             summary='创建新的知识库',
             )(create_kb)

    app.post('/mme/delete_kb',
             summary='删除知识库',
            )(delete_kb)

    app.post('/mme/rename_kb',
             summary='重命名知识库',
             )(rename_kb)

    app.post('/mme/drop_all_kb',
             summary='清空所有知识库',
             )(drop_all_kb)

    # --------------------------------------
    # 文档交互 ------------------------------
    app.post('/mme/add_docs',
             summary='向知识库添加文档',
             )(add_docs)

    app.post('/mme/delete_docs',
             summary='从知识库中删除文档',
             )(delete_docs)

    # ---------------------------------
    # 问答
    app.post('/mme/chat_qa',
             summary='常规问答'
             )(chat_qa)

    # ------------------------------------
    # 搜索 -------------------------------
    app.post('/mme/vector_search',
             summary='使用向量检索知识库内容'
             )(vector_search)

    app.post('/mme/bm25_search',
             summary='使用bm25进行检索',
            )(bm25_search)

    app.post('/mme/naive_rag_qa',
             summary='简单rag检索',
             )(naive_rag_qa)

    app.post('/mme/advanced_rag_qa',
             summary='高级rag检索',
             )(advanced_rag_qa)

    app.post('/mme/query_decompose_rag_qa',
             summary='问题驱动rag检索',
             )(query_decompose_rag_qa)


    pass


app = FastAPI(
    title="MMeRAG",
    version=VERSION
)
mount_app_routes(app)


def run_api(host, port, reload=False):
    uvicorn.run(
        app="app:app",
        host=host,
        port=port,
        reload=reload
    )

if __name__ == '__main__':
    parser =argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=back_host, help="host")
    parser.add_argument("--port", type=int, default=back_port, help="port")
    args = parser.parse_args()

    run_api(args.host, args.port)



