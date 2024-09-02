import os
import sqlite3
from pydantic import BaseModel, Field
from config.mme_rag_config import KB_BASE_PATH, KB_CONTENT_PATH
from typing import List, Dict, Tuple, Set, Union
import glob

class CollectionItem(BaseModel):
    collection_name: str
    file_number: int = Field(0, description='文档数量')


class FileItem(BaseModel):
    source_id: str
    file_name: str = Field(default='大耳朵图图之牛爷爷去哪了.mp4', description='文件名称')
    chunk_number: int = Field(default=0, description='切片数量')
    file_path: str = Field(default=r'/你找不着它在哪', description='文件路径')
    input_time: str = Field(default=r'1970-01-01', description='输入的时间')
    pass


# #### collection表
# | collection_name | file_number |
# | --------------  | ----------  |
# | test_kb1        |   25        |
#
# #### collection的子表
#
# | source_id | file_name | chunk_number | file_path | input_time |
# | -------   | --------- | ---------    | --------  | ---------  |
# | x6f8e45   | idol      | 25           | /home/xxx |  2024-08-08 |


class SQLiteBase:
    def __init__(self):
        self.content_dir = KB_CONTENT_PATH
        self.base_dir = KB_BASE_PATH
        self.collection_db_path = os.path.join(self.base_dir, 'collections.db')
        self.init_collections_db()

    def name2path(self, sub_collection_name: str) -> str:
        return os.path.join(self.content_dir, sub_collection_name + '.db')

    def sub_db_exist(self, collection_name):
        collection_path = self.name2path(collection_name)
        if not os.path.exists(collection_path):
            raise Exception(f'sql_db.sub_db_exist(collection_name): 数据库{collection_name}不存在。')

    def get_sub_conn(self, collection_name: str):
        collection_path = self.name2path(collection_name)
        # if not os.path.exists(collection_path):
        #     raise Exception(f'数据库{collection_name}不存在。')
        conn = sqlite3.connect(collection_path)
        yield conn

    def get_collections_conn(self):
        conn = sqlite3.connect(self.collection_db_path)
        yield conn

    def init_collections_db(self):
        """
            初始化collections表
        """
        conn = next(self.get_collections_conn())
        c = conn.cursor()
        try:
            c.execute('''
                CREATE TABLE IF NOT EXISTS collections (
                collection_name TEXT PRIMARY KEY,
                file_number INT NOT NULL
                )
                ''')
            conn.commit()
            c.close()
            conn.close()
            return True, ''
        except Exception as e:
            c.close()
            conn.close()
            return False, str(e)
            pass

    def create_sub_db(self, collection_name:str) -> Tuple[bool, str]:
        conn = next(self.get_sub_conn(collection_name))
        c = conn.cursor()
        try:
            c.execute(
                f'''
                    CREATE TABLE {collection_name} (
                        source_id TEXT PRIMARY KEY,
                        file_name TEXT NOT NULL,
                        chunk_number INTEGER NOT NULL,
                        file_path TEXT NOT NULL,
                        input_time TEXT NOT NULL
                    )
                    '''
            )
            conn.commit()
            c.close()
            conn.close()
            return True, ''
        except Exception as e:
            c.close()
            conn.close()
            return False, str(e)

    def show_collections_details(self) -> Dict[str, str]:
        """
            展示collections表，查询操作
        """
        # 连接到数据库
        conn = next(self.get_collections_conn())
        c = conn.cursor()
        # 查询并展示所有数据
        c.execute(f'SELECT * FROM {"collections"}')     # 防止pycharm报错误提示
        # 获取所有结果
        rows = c.fetchall()
        counts_dict = {}
        for row in rows:
            counts_dict[row[0]] = row[1]
        c.close()
        conn.close()
        return counts_dict

    def show_sub_details(self, collection_name: str) -> Dict[str, FileItem]:
        """
            展示sub db表，查询操作
        """

        conn = next(self.get_sub_conn(collection_name))
        c = conn.cursor()
        c.execute(f'SELECT * FROM {collection_name}')
        rows = c.fetchall()
        collection_dict = {}
        for row in rows:
            collection_dict[row[0]] = FileItem(
                source_id = row[0],
                file_name = row[1],
                chunk_number = row[2],
                file_path = row[3],
                input_time = row[4]
            )
        c.close()
        conn.close()
        return collection_dict


    def add_collection_item(self, item: CollectionItem) -> Tuple[bool, str]:
        "在collection表中添加新的数据"
        conn = next(self.get_collections_conn())
        c = conn.cursor()
        try:
            insert_sql = f"""
            INSERT INTO {'collections'} (collection_name, file_number)
            VALUES (?, ?)
            """
            c.execute(insert_sql, (item.collection_name, item.file_number))
            conn.commit()
            c.close()
            conn.close()
            return True, ''
        except Exception as e:
            c.close()
            conn.close()
            return False, str(e)

    def add_sub_item(self, collection_name, new_item: FileItem) -> Tuple[bool, str]:
        "在sub表中添加新的数据 "
        conn = next(self.get_sub_conn(collection_name))
        c = conn.cursor()
        try:
            insert_sql = f'''
            INSERT INTO {collection_name} 
            (source_id, file_name, chunk_number, file_path, input_time)
            VALUES (?, ?, ?, ?, ?)
            '''
            c.execute(
                insert_sql,
                (new_item.source_id, new_item.file_name, new_item.chunk_number,
                 new_item.file_path, new_item.input_time)
            )
            conn.commit()
            c.close()
            conn.close()

            return True, ''

        except Exception as e:
            c.close()
            conn.close()
            return False, f"sqlbase.add_sub_item:{str(e)}"

    def delete_collection_db(self, item: CollectionItem) -> Tuple[bool, str]:
        "删除collections表中的一个表项,也就是去除一个sub表"
        conn = next(self.get_collections_conn())
        c = conn.cursor()
        try:
            c.execute(
                f'DELETE FROM {"collections"} WHERE collection_name=?',
                (item.collection_name,)
            )
            conn.commit()
            c.close()
            conn.close()
            return True, ''
        except Exception as e:
            c.close()
            conn.close()
            return False, str(e)

    def delete_sub_db_item(self, collection_name :str, item: FileItem) -> Tuple[bool, str]:
        "删除子表的表项"
        conn = next(self.get_sub_conn(collection_name))
        c = conn.cursor()
        try:
            c.execute(
                f"DELETE FROM {collection_name} WHERE source_id=?",
                (item.source_id,)
            )
            conn.commit()
            c.close()
            conn.close()
            return True, ''
        except Exception as e:
            c.close()
            conn.close()
            return False, str(e)

    def drop_sub_db(self, collection_name: str) -> None:
        sub_db_path = self.name2path(collection_name)
        if os.path.exists(sub_db_path):
            os.remove(sub_db_path)
        else:
            raise Exception(f'数据库文件删除错误，db文件{collection_name}不存在。')

    def drop_all_db(self):

        if os.path.exists(self.collection_db_path):
            os.remove(self.collection_db_path)
        else:
            raise Exception('collection.db不存在，尚未初始化。')

        sub_list = glob.glob(os.path.join(self.content_dir, '*.db'))
        for sub_db in sub_list:
            os.remove(sub_db)

        # 先删除所有，然后重新初始化
        self.init_collections_db()

    def update_collections_db(self, old_item: CollectionItem ,new_item : CollectionItem) -> Tuple[bool, str]:
        "更新collections的表项"
        conn = next(self.get_collections_conn())
        c = conn.cursor()
        try:
            update_sql = f"""
            UPDATE {'collections'}
            SET file_number = ?
            WHERE collection_name = ?
            """
            c.execute(
                update_sql,
                (new_item.file_number, old_item.collection_name)
            )
            conn.commit()
            c.close()
            conn.close()
            return True , ''
        except Exception as e:
            c.close()
            conn.close()
            return False, str(e)

    def update_collections_up_one(self, item: CollectionItem, delta: int=1):
        "更新collections的某个表项，让其file_number + or -= 1"
        conn = next(self.get_collections_conn())
        c = conn.cursor()
        try:
            update_sql = f"""
                    UPDATE {"collections"}
                    SET file_number = file_number + ?
                    WHERE collection_name = ?
                    """
            c.execute(
                update_sql,
                (delta, item.collection_name,)
            )
            conn.commit()
            c.close()
            conn.close()
            return True, ''
        except Exception as e:
            c.close()
            conn.close()
            return False, f"sqlbase.update_collections_up_one:{str(e)}"

    def update_sub_db(self,
                      collection_name: str,
                      item: FileItem
    ) -> Tuple[bool, str]:
        "更新sub的表项, 其实这个没用，因为根本不会改变"
        conn = next(self.get_sub_conn(collection_name))
        c = conn.cursor()
        try:
            update_sql = f"""
            UPDATE {collection_name}
            SET file_name = ?,
                chunk_number = ?,
                file_path = ?,
                input_time = ?
            WHERE source_id = ?
            """
            c.execute(
                update_sql,
                (
                    item.file_name,
                    item.chunk_number,
                    item.file_path,
                    item.input_time,
                    item.source_id
                )
            )
            conn.commit()
            c.close()
            conn.close()
            return True, ''

        except Exception as e:
            c.close()
            conn.close()
            return False, 'sql_db.update_sub_db' + str(e)

if __name__ == "__main__":
    sqlitbase = SQLiteBase()
    print(sqlitbase.show_collections_details())