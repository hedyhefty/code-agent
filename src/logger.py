"""
日志配置模块 - 类似 Java @Slf4j 的功能

由于 rich.live 占用了标准输出（STDOUT），将调试信息和运行日志重定向到文件是最佳实践。
"""

import logging
import os
from datetime import datetime


def setup_logging():
    """
    配置全局日志系统
    
    注意：这里不添加 StreamHandler，避免日志冲刷到控制台破坏 Live 界面
    """
    # 确保 logs 目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成日志文件名，例如 logs/agent_20240314.log
    log_file = os.path.join(log_dir, f"agent_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 全局配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            # 使用 FileHandler 将日志写入文件，编码设为 utf-8 避免中文乱码
            logging.FileHandler(log_file, encoding='utf-8'),
            # 注意：这里不要添加 logging.StreamHandler()，
            # 否则日志会再次冲刷到控制台破坏 Live 界面
        ]
    )
    
    # 设置更详细的日志级别
    logging.getLogger("CodeAgent").setLevel(logging.DEBUG)
    # 设置 src 模块的日志级别
    logging.getLogger("src").setLevel(logging.DEBUG)
    
    logger = logging.getLogger("CodeAgent")
    logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    return logger


# 获取全局 logger（类似 Java 的静态 log 变量）
logger = logging.getLogger("CodeAgent")


def get_logger(name: str):
    """
    获取指定名称的 logger
    
    用法：
        logger = get_logger(__name__)
        logger.info("消息")
    """
    return logging.getLogger(name)