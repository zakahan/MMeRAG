import logging

def mmelogger():
    # 创建logger实例
    logger = logging.getLogger('mme_rag_logger')
    logger.setLevel(logging.DEBUG)  # 设置日志级别为DEBUG

    # 创建handler，用于写入日志文件
    file_handler = logging.FileHandler('mme_rag_logger.log')
    file_handler.setLevel(logging.DEBUG)

    # 创建handler，用于输出到控制台
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)

    # 定义handler的输出格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    # console_handler.setFormatter(formatter)

    # 添加handler到logger实例
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)

    return logger


logger = mmelogger()
