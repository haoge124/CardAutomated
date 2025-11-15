"""
日志工具模块
提供统一的日志记录功能，支持控制台和文件输出
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
import colorlog


class Logger:
    """日志管理器类"""

    _instances = {}  # 存储不同名称的logger实例

    def __init__(self,
                 name: str = "CardSortingRobot",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 console_output: bool = True,
                 file_output: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件路径
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件数量
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # 避免重复添加handler
        if self.logger.handlers:
            return

        # 日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # 控制台输出（带颜色）
        if console_output:
            console_handler = colorlog.StreamHandler()
            console_handler.setLevel(getattr(logging, level.upper()))

            color_format = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt=date_format,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_format)
            self.logger.addHandler(console_handler)

        # 文件输出
        if file_output and log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, level.upper()))

            file_format = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls,
                   name: str = "CardSortingRobot",
                   **kwargs) -> 'Logger':
        """
        获取日志记录器实例（单例模式）

        Args:
            name: 日志记录器名称
            **kwargs: 其他初始化参数

        Returns:
            Logger实例
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
        return cls._instances[name]

    def debug(self, message: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """记录异常信息"""
        self.logger.exception(message, *args, **kwargs)


def setup_logger_from_config(config: dict) -> Logger:
    """
    从配置字典创建日志记录器

    Args:
        config: 包含日志配置的字典

    Returns:
        配置好的Logger实例
    """
    log_config = config.get('logging', {})

    return Logger.get_logger(
        name="CardSortingRobot",
        level=log_config.get('level', 'INFO'),
        log_file=log_config.get('log_file'),
        console_output=log_config.get('console_output', True),
        file_output=log_config.get('file_output', True),
        max_file_size=log_config.get('max_file_size', 10 * 1024 * 1024),
        backup_count=log_config.get('backup_count', 5)
    )


if __name__ == "__main__":
    # 测试代码
    logger = Logger.get_logger(
        name="TestLogger",
        level="DEBUG",
        log_file="test.log"
    )

    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")

    try:
        1 / 0
    except Exception as e:
        logger.exception("捕获到异常")
