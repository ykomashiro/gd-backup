import logging
import logging.config
import os
import threading

import yaml


def synchronized(func):
    func.__lock__ = threading.Lock()

    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func


class LogSingleton(object):
    instance = None

    def __init__(self):
        LogSingleton.setup_logging()
        self.logger = logging.getLogger("logger")

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)

    @staticmethod
    def setup_logging(default_path="data/log.yaml",
                      default_level=logging.INFO,
                      env_key="LOG_CFG"):
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
                logging.config.dictConfig(config)

    @synchronized
    def __new__(cls, *args, **kwargs):
        """
        :type kwargs: object
        """
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance


class RuntimeException(Exception):
    def __init__(self,
                 code=-1,
                 message="unknown error",
                 description="unknown error"):
        self.code_ = code
        self.message_ = message
        self.description_ = description
        self.__write_log()

    def __repr__(self):
        text = f">>{self.code_} >>{self.message_} >>{self.description_}"
        return text

    def __str__(self):
        text = f">>{self.code_} >>{self.message_} >>{self.description_}"
        return text

    def __write_log(self):
        text = f">>{self.code_} >>{self.message_} >>{self.description_}"
        logger = LogSingleton()
        logger.error(text)


if __name__ == "__main__":
    try:
        raise RuntimeException()
    except RuntimeException as e:
        print(e)