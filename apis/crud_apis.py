import datetime
import os
import shutil
import uuid
import warnings

from fastapi import Body, Depends, UploadFile, File
# -------------------
from database.sqlite_base import SQLiteBase, CollectionItem, FileItem
from loader.mme_loader import MMeLoader
from rag.elastic_vector import ElasticVector
from apis.utils import depends_resource, upload_file, validate_kb_name, BaseResponse, human_readable_size_bytes

warnings.filterwarnings("ignore")

# 设置日志
from config.mme_rag_logger import logger


# 1) 上传原始文件到raw文档
async def upload_file_api(
        file: UploadFile = File(...),
        base_raw_path: str = Depends(depends_resource.get_raw_path)
) -> tuple[str, str]:
    file_location = os.path.join(base_raw_path, os.path.basename(file.filename))
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    # response code修改为正常的BaseResponse
    return os.path.basename(file.filename), file_location


# ---------------------
# 知识库操作 -----------
# 2) 展示知识库列表
def list_kb(
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
) -> BaseResponse:
    """
        展示所有知识库
    """
    collection_set = elastic_vector.show_set()
    logger.info(f"list_kb: {collection_set}")
    return BaseResponse(
        code=200,
        msg='展示所有collection',
        data={
            'collection_list': list(collection_set)
        }
    )


# 3) 展示各知识库的细节信息
def list_kb_details(
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base),
        legibility: bool = Body(default=True, description='是否让size_of_byte更易理解')
) -> BaseResponse:
    result = []
    try:
        collection_set = elastic_vector.show_set()
        # 在sql中查找collection
        col_dict = sql_db.show_collections_details()
        for collection_name in collection_set:
            count, size = elastic_vector.show_detail(collection_name)
            result.append(
                {
                    'collection_name': collection_name,
                    'file_count': col_dict[collection_name],
                    'chunk_count': count,
                    'size_of_byte': str(size) if not legibility else human_readable_size_bytes(size),
                }
            )
        return BaseResponse(
            code=200,
            msg='信息列表如下',
            data={
                'data': result
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg='出现了意外情况',
            data={
                'except': str(e)
            }
        )


# 4) 展示具体collection
def list_sub_db(
        collection_name: str = Body(..., description='知识库id'),
        sql_db: SQLiteBase = Depends(depends_resource.get_base)
) -> BaseResponse:
    # 查询一下是否存在这个表
    if not validate_kb_name(collection_name):
        return BaseResponse(
            code=400,
            msg='不要搞路径攻击',
            data={
                'msg': '孩子，这不有趣。'
            }
        )
    try:
        sql_db.sub_db_exist(collection_name)  # 查看是否存在这个db文件
        details = sql_db.show_sub_details(collection_name=collection_name)
        details_list = [dict(value) for key, value in details.items()]
        return BaseResponse(
            code=200,
            msg='查询成功',
            data={
                'data': details_list
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg='出现了意外的错误',
            data={
                'exception': str(e)
            }
        )


# 5) 创建知识库
def create_kb(
        collection_name: str = Body(..., description='知识库id'),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base),
        raw_path: str = Depends(depends_resource.get_raw_path)
) -> BaseResponse:
    """
        创建知识库，包括ES向量库中添加以及SQLite中记录，两个部分
    """
    if not validate_kb_name(collection_name):
        return BaseResponse(
            code=400,
            msg='好玩么？',
            data={
                'msg': '孩子，这不有趣。'
            }
        )
    try:
        # 创建知识库
        # ES添加
        elastic_vector.create(collection_name=collection_name)
        # 在SQLite 1) 在collections.db中创建 2) 新建一个db
        sql_db.create_sub_db(collection_name)
        sql_db.add_collection_item(
            item=CollectionItem(collection_name=collection_name, file_number=0)
        )
        # 在raw里创建一个路径
        os.makedirs(os.path.join(raw_path, collection_name), exist_ok=True)
        logger.info(f'ceate_kb: 创建知识库成功，知识库id {collection_name}。')
        return BaseResponse(
            code=200,
            msg='创建成功',
            data={
                'msg': f'成功创建知识库，知识库id为{collection_name}'
            }
        )

    except Exception as e:
        return BaseResponse(
            code=422,
            msg='创建失败',
            data={
                'exception': str(e)
            }
        )


# 6) 删除知识库
def delete_kb(
        collection_name: str = Body(..., description='知识库名称'),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base),
        raw_path: str = Depends(depends_resource.get_raw_path)
) -> BaseResponse:
    """
        删除知识库
    """
    try:
        col = elastic_vector.drop_collection(collection_name)
        # 1. 删除这个sql数据库表，在collection中删除
        sts, msg = sql_db.delete_collection_db(
            item=CollectionItem(
                collection_name=collection_name
            ))
        if not sts:
            raise Exception(msg)
        sql_db.drop_sub_db(collection_name)

        # 删除原始文件
        dir_path = os.path.join(raw_path, collection_name)
        # 删除dir_path这个文件夹，以及里面的所有文件
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        else:
            raise Exception(f'路径{dir_path}不存在')

        return BaseResponse(
            code=200,
            msg='知识库删除成功',
            data={
                'data': f'已清除知识库 {col}'
            }
        )
    except Exception as e:
        return BaseResponse(
            code=404,
            msg='知识库删除失败',
            data={
                'exception': str(e)
            }
        )


# 7) 清空所有知识库
def drop_all_kb(
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base),
        raw_path: str = Depends(depends_resource.get_raw_path)
) -> BaseResponse:
    try:
        res = elastic_vector.drop_all_collection()
        # 对collections表做清空
        # 删除所有sub collection
        sql_db.drop_all_db()

        # 清空raw_path 文件夹下的所有文件（该文件夹不删除）
        # 删除目录下的所有文件和子目录
        for root, dirs, files in os.walk(raw_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        return BaseResponse(
            code=200,
            msg='已清除所有知识库',
            data={
                'data': res
            }
        )
    except Exception as e:
        return BaseResponse(
            code=404,
            msg='知识库清理失败',
            data={
                'exception': str(e)
            }
        )


# 8) 重命名知识库
def rename_kb(
        source_collection_name: str = Body(..., description='原知识库名称'),
        dest_collection_name: str = Body(..., description='新知识库名称'),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base)
) -> BaseResponse:
    # 两步操作，复制知识库，删除原来的知识库
    try:
        elastic_vector.create(dest_collection_name)
        elastic_vector.copy(source_collection_name, dest_collection_name)
        elastic_vector.drop_collection(source_collection_name)

        # todo: 这个的sql还没做,而且反正前端也还没实现，所有我就不做了先，先别用

        return BaseResponse(
            code=200,
            msg='知识库重命名成功',
            data={}
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg=f'重命名过程出错',
            data={
                "exception": str(e),
            }
        )


# ----------------------------------------------------
# 文档类操作--------------------------------------------

# ----------------------------------------------------
# 文档类操作--------------------------------------------
# 9) 向知识库添加文档
def add_docs(
        collection_name: str = Body(..., description='知识库名称'),
        file: UploadFile = File(..., description='上传的文件，类型为音视频'),
        mme_loader: MMeLoader = Depends(depends_resource.get_loader),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base),
        raw_path: str = Depends(depends_resource.get_raw_path)
) -> BaseResponse:
    """
    向知识库中添加文档：
    该方法所在处理链条的逻辑位置是这样的：
    先用 upload_file上传文件 -> 文件存储到本地raw路径 -> 在调用add_docs加载文件
    这样的优点是
    """
    # 检查这个collection是否存在
    if not elastic_vector.collection_exist(collection_name):
        return BaseResponse(
            code=422,
            msg=f'当前名称为{collection_name}的知识库不存在，请先创建。',
            data={}
        )
    try:
        # 开始执行上传处理
        file_name, file_location = upload_file(raw_path, collection_name, file)
        # 检查raw_path这个文件夹中是否有文件名为file_name的文件
        if not os.path.exists(file_location):
            return BaseResponse(
                code=422,
                msg=f'上传过程存在问题，当前路径为{raw_path}的文件夹中不存在名为{file_name}的文件，请检查。',
                data={}
            )
        # -------------------------------------------------
        # 解析，然后存储
        # source_id应该没在chunk里添加，load函数里应该指定一下source id
        source_id = str(uuid.uuid4())
        chunks, embeds = mme_loader.load(file_location, source_id=source_id)
        doc_ids = elastic_vector.add_chunks(
            collection_name=collection_name,
            chunks=chunks,
            embeddings=embeds
        )

        # 先更新表项，说明某个collection中的file_count + 1
        sts, msg = sql_db.update_collections_up_one(
            item=CollectionItem(
                collection_name=collection_name
            ),
            delta=1
        )
        if not sts:
            raise Exception(msg)
        # 然后再对sub表中添加表项
        sts, msg = sql_db.add_sub_item(
            collection_name=collection_name,
            new_item=FileItem(
                source_id=source_id,
                file_name=file_name,
                chunk_number=len(chunks),
                file_path=file_location,
                input_time=datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"),
            )
        )
        if not sts:
            raise Exception(msg)

        return BaseResponse(
            code=200,
            msg=f'成功添加了 {len(doc_ids)} 条数据',
            data={
                'doc_ids': doc_ids
            }
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg=f'添加过程中出现了意外的错误',
            data={
                'exception': str(e)
            }
        )


# 10) 按source删chunk
def delete_docs(
        collection_name: str = Body(..., description='知识库名称'),
        source_id: str = Body(..., description='待删除文档编号'),
        elastic_vector: ElasticVector = Depends(depends_resource.get_vector),
        sql_db: SQLiteBase = Depends(depends_resource.get_base)
) -> BaseResponse:
    # 检查这个collection是否存在
    if not elastic_vector.collection_exist(collection_name):
        return BaseResponse(
            code=422,
            msg=f'当前名称为{collection_name}的知识库不存在，请先创建。',
            data={}
        )
    try:
        # fixme 有点bug 删除不存在的source_id也会正常响应，可以从sql方面考虑，暂时先不改了
        # 根据source删除 sub里面的具体项目
        elastic_vector.delete_by_source(collection_name, source_id)
        # 删除sub数据库中的某个表项
        sts, msg = sql_db.delete_sub_db_item(
            collection_name=collection_name,
            item=FileItem(
                source_id=source_id
            )
        )
        if not sts:
            raise Exception(msg)
        # 这次得减一了
        sts, msg = sql_db.update_collections_up_one(
            item=CollectionItem(
                collection_name=collection_name,
            ),
            delta=-1
        )
        if not sts:
            raise Exception(msg)

        return BaseResponse(
            code=200,
            msg=f'知识库{collection_name}中，编号为{source_id}的文档块已删除',
            data={}
        )
    except Exception as e:
        return BaseResponse(
            code=500,
            msg=f'删除过程中出现了意外的错误',
            data={
                'exception': str(e)
            }
        )
    pass
