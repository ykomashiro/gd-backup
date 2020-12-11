from core.common import GetService
from random import choice
from random import shuffle
import time
from glob import glob
import os
from core.error import RuntimeException
from core.common import Global
from threading import Lock


class SAInfo(object):
    def __init__(self, path, user_only=False):
        # 创建id信息
        self.uid = None
        # 文件路径
        self.path = path
        # 是否申请token
        self.service = None
        # 总使用量(byte)// 750 GB
        self.usage = 805306368000
        # 当前剩余量
        self.remaining = self.usage
        # 过期时长(s)
        self.expire = 7200
        # 创建时间戳
        self.timestamp = time.time()
        # 是否使用中
        self.is_using = False
        # 是否已被废弃
        self.is_abandoned = False
        # 累积报错数量
        self.cum_error = 0

        self.CreateService()
        self.Init()

    def CreateService(self, user_only=False):
        if (not os.path.exists(self.path)):
            raise RuntimeException()
        self.service = GetService(self.path)
        self.expire = 7200
        self.timestamp = time.time()

    def UpdateToken(self):
        self.CreateService()

    def Init(self):
        self.uid = os.path.basename(self.path)

    def __close(self):
        if self.cum_error > Global.CumErrorNum:
            self.is_abandoned = True
        elif (self.remaining < 2000):
            self.is_abandoned = True
        self.is_using = False

        Global.TaskLock.acquire()
        Global.SAInfos[self.uid] = self
        Global.TaskLock.release()

    def close(self):
        self.__close()

    def to_json(self):
        pass

    def from_json(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__close()
        if exc_type is not None:
            raise RuntimeException()


class SAManage(object):
    @staticmethod
    def read_sa_files(folder: str):
        """read_sa_files 读取service account配置文件

        Args:
            folder ([type]): [description]

        Raises:
            RuntimeException: [description]
        """
        if (not os.path.exists(folder)):
            raise RuntimeException(102, "{0} 文件夹不存在".format(folder), "service account存放文件夹错误")
        Global.SAFiles = glob(os.path.join(folder, "*.json"))
        shuffle(Global.SAFiles)

    @staticmethod
    def request(random=True):
        """request 申请service account信息

        Args:
            random (bool, optional): 是否随机选取. Defaults to False.

        Raises:
            RuntimeException: [description]

        Returns:
            [type]: sa信息
        """
        Global.TaskLock.acquire()
        # 从全局sa信息中筛选出未被使用且未被废弃的sa信息
        sas = [
            sa for sa in Global.SAInfos.values()
            if (not (sa.is_using | sa.is_abandoned))
        ]
        sa = None
        if (len(sas) == 0):
            if (len(Global.SAFiles) == 0):
                Global.TaskLock.release()
                raise RuntimeException(101, "", "service account耗尽")
            else:
                path = Global.SAFiles.pop()
                sa = SAInfo(path)
                sa.is_using = True
                Global.SAInfos[sa.uid] = sa
        else:
            # TODO: 注意将Global.SAInfos中的信息同步修改
            sa = sas[0]
            if random:
                sa = choice(sas)
            sa.is_using = True
            Global.SAInfos[sa.uid] = sa
        Global.TaskLock.release()
        return sa

    @staticmethod
    def recycle(sa: SAInfo):
        """recycle 回收service account

        Args:
            sa (SAInfo): sa信息
        """
        sa.close()