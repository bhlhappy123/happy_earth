import os  # 导入os模块，用于与操作系统交互
import random
import faiss
from tqdm import tqdm  # 导入tqdm模块，用于显示进度条
from langchain_community.vectorstores import FAISS  # 导入FAISS模块，用于向量存储
from langchain_community.document_loaders import BSHTMLLoader  # 导入BSHTMLLoader模块，用于加载HTML文档
from erniebot_agent.extensions.langchain.embeddings import ErnieEmbeddings  # 导入ErnieEmbeddings模块，用于生成嵌入
from sklearn.metrics.pairwise import cosine_similarity  # 导入cosine_similarity函数，用于计算余弦相似度
from langchain.text_splitter import RecursiveCharacterTextSplitter  # 导入RecursiveCharacterTextSplitter模块，用于文本分割
import os
from langchain_community.document_loaders import UnstructuredHTMLLoader
"""
这个程序主要用于构建和搜索FAISS向量数据库，用于快速文本检索。具体功能如下：

加载和创建向量库：从本地文件夹加载HTML文件，创建或加载FAISS向量库。
文本嵌入和分割：使用ErnieEmbeddings生成文本嵌入，并使用RecursiveCharacterTextSplitter进行文本分割。
相似性搜索：提供一个查询字符串，通过余弦相似度计算，返回与查询最相关的文档内容和相似度得分。
"""

# 定义FaissSearch类
class FaissSearch:
    def __init__(self, embeddings: ErnieEmbeddings, chunk_size: int = 256, chunk_overlap: int = 32):
        self.db = None
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = None
        self.embeddings = embeddings
        self.index = None

    def initialize_empty_db(self):
        if self.embeddings is None:
            raise ValueError("Embeddings object must be initialized before initializing Faiss index.")
        self.index = faiss.IndexFlatL2(self.embeddings.get_embedding_dimension())

    # 加载向量库
    def load_db(self, faiss_name: str):
        self.db = FAISS.load_local(faiss_name, self.embeddings, allow_dangerous_deserialization=True)

    # 读取本地文件创建信息
    def create_db(self, html_folder_path: str, faiss_name: str):
        # 读取文件列表
        files_path = self._get_files(html_folder_path)
        # 获取文本分类器duquwenjian
        if self.splitter is None:
            self._create_splitter()
        # 按html文件切割文档
        docs = []
        for html_file in tqdm(files_path):
            documents = UnstructuredHTMLLoader(html_file).load()
            docs += self.splitter.split_documents(documents)
        # 构建向量库
        db_struct_vectory = FAISS.from_documents(docs, self.embeddings)
        db_struct_vectory.save_local(faiss_name)
        self.db = db_struct_vectory

    # 向量查询的方法
    def search(self, query: str, top_k: int = 10, **kwargs):
        # 定义一个搜索方法，接受一个查询字符串 'query' 和一个整数 'top_k'，默认为 10
        docs = self.db.similarity_search(query, top_k)
        # 调用数据库的 similarity_search 方法来获取与查询最相关的文档
        para_result = self.embeddings.embed_documents([i.page_content for i in docs])
        # 对获取的文档内容进行嵌入（embedding），以便进行相似性比较
        query_result = self.embeddings.embed_query(query)
        # 对查询字符串也进行嵌入
        similarities = cosine_similarity([query_result], para_result).reshape((-1,))
        # 计算查询嵌入和文档嵌入之间的余弦相似度
        retrieval_results = []
        for index, doc in enumerate(docs):
            retrieval_results.append(
                {"content": doc.page_content, "score": similarities[index], "title": doc.metadata["source"]}
            )
        # 遍历每个文档，将内容、相似度得分和来源标题作为字典添加到结果列表中
        return retrieval_results  # 返回包含搜索结果的列表

    def initialize_empty_db(self):
        self.index = faiss.IndexFlatL2(self.embeddings.dimension)

    def merge_db(self, db_path):
        if not os.path.exists(db_path):
            print(f"Database path {db_path} does not exist.")
            return
        new_index = faiss.read_index(db_path)
        if self.index is None or self.index.ntotal == 0:
            self.index = new_index
        else:
            self.index.merge_from(new_index)

    def add_embeddings(self, embeddings):
        self.index.add(embeddings)

    # 获取文件列表
    def _get_files(self, folder_path: str):
        # 读取文件夹中的所有文件和目录名称
        files_and_dirs = os.listdir(folder_path)
        # 初始化结果
        files_path = []
        # 获取文件的完整路径
        for f in files_and_dirs:
            if '.xhtml' in f:
                files_path.append(os.path.join(folder_path, f))
        return files_path

    # 创建文本分类器
    def _create_splitter(self):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)


if __name__ == '__main__':
    from dotenv import find_dotenv, load_dotenv  # 导入find_dotenv和load_dotenv，用于加载环境变量

    _ = load_dotenv(find_dotenv())  # 加载环境变量文件（.env）
    enrine_key = os.environ["access_token"]  # 从环境变量中读取access_token
    # 创建embedding
    embeddings = ErnieEmbeddings(aistudio_access_token=enrine_key, chunk_size=16)
    faiss_search = FaissSearch(embeddings)
    # 创建向量库（首次加载时需要）
    # faiss_search.create_db('/home/datasets/contest/shiwan/OEBPS/Text', 'faiss_index_tianwen')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/shiwan/animal/OEBPS/Text', 'faiss_index_animal')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/shiwan/ocean/OEBPS/Text', 'D:/python/pythonProject/ernie-edu-master/faiss_index_ocean')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/shiwan/aviation/OEBPS/Text', 'D:/python/pythonProject/ernie-edu-master/faiss_index_aviation')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/shiwan/plant/OEBPS/Text',
    #                         'D:/python/pythonProject/ernie-edu-master/faiss_index_plant')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/shiwan/life/OEBPS/Text',
    #                        'D:/python/pythonProject/ernie-edu-master/faiss_index_life')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/shiwan/paleontology/OEBPS/Text',
    #                         'D:/python/pythonProject/ernie-edu-master/faiss_index_paleontology')
    # faiss_search.create_db('D:/python/pythonProject/ernie-edu-master/htmlData',
    #                          'D:/python/pythonProject/ernie-edu-master/all_index')
    # 加载向量库
    # faiss_search.load_db('/home/aistudio/ernie-edu/faiss_index')
    # results = faiss_search.search('发现天王星的过程是什么？')
    # for res in results:
    #     print(res['content'], res['score'])
