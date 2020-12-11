from __future__ import print_function

import json
import os.path
import pickle
import queue
import socket
import sys
import threading
import time
import uuid
from threading import Thread

import socks  # pip install PySocks
from apiclient import errors
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.error import *

socks.set_default_proxy(socks.HTTP, addr='127.0.0.1', port=7890)  # 设置socks代理
socket.socket = socks.socksocket  # 把代理应用到socket


def get_service(path: str, scopes: list, must_update=False):
    """get_service basic usage of the Drive v3 API.
    用于个人账号的授权

    Args:
        path (str): 授权文件路径
        scopes (list): 权限范围
        must_update (bool, optional): 强制更新缓存token文件, 需重新登录授权. Defaults to False.

    Returns:
        [type]: 服务账号
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('account/token.pickle') and (not must_update):
        with open('account/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and (
                not must_update):
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(path, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('account/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    return service


def GetService(sa_path: str):
    """GetService 服务账号授权

    Args:
        sa_path (str): service account 配置文件路径

    Returns:
        [type]: [description]
    """
    credentials = service_account.Credentials.from_service_account_file(
        sa_path)
    service = build('drive',
                    'v3',
                    credentials=credentials,
                    cache_discovery=False)
    return service


class FileInfo:
    """ Google Drive文件或文件夹相关信息
    """
    def __init__(self, info: dict, mission="kuon", from_json=False):
        self.uid = None  # 文件或文件夹id, 具有唯一性
        self.md5Checksum = None  # 文件md5信息, 注意, 文件夹不具有此属性
        self.name = None  # 文件或文件夹名称
        self.size = None  # 文件大小, 文件夹不统计, 标记为-1
        self.parent = None  # 父级文件夹, 有多个时选择第一个
        self.parents = None  # 父级文件夹列表, 通常只有一个
        self.mimeType = None  # 文件类型, 文件夹通常为folder
        self.is_folder = False  # 是否为文件夹类型
        self.mission = mission  #

        if from_json:
            self.from_json(info)
        else:
            self.Get(info)

    def Get(self, info: dict):
        """Get 将从Google API返回的信息转化为程序通用格式

        Args:
            info (dict): google drive api调用返回的文件或文件夹信息
        """
        self.uid = info["id"]
        self.name = info["name"]
        if "md5Checksum" in info:
            self.md5Checksum = info["md5Checksum"]
        if "size" not in info:
            # 单位为byte
            info["size"] = "-1"
        self.size = info["size"]
        if "parents" not in info:
            # 正常情况下无法获取分享的顶级文件夹的父文件夹
            # 但因数据记录的需要, 将文件夹的id反转作为父文件夹
            info["parents"] = [info["id"][::-1]]
        self.parents = info["parents"]
        self.parent = self.parents[0]
        self.mimeType = info["mimeType"]
        if "folder" in info["mimeType"]:
            self.is_folder = True

    def to_json(self):
        """to_json 将文件信息转成json格式方便进行存储

        Returns:
            dict: 字典形式的文件信息
        """
        info = {}
        info["uid"] = self.uid
        info["md5Checksum"] = self.md5Checksum
        info["name"] = self.name
        info["size"] = self.size
        info["parent"] = self.parent
        info["parents"] = self.parents
        info["mission"] = self.mission
        info["mimeType"] = self.mimeType
        info["is_folder"] = self.is_folder

        return info

    def from_json(self, info: dict):
        """from_json 从json信息中导入文件信息

        Args:
            info (dict): 文件信息(json)
        """
        self.uid = info["uid"]
        self.name = info["name"]
        self.size = info["size"]
        self.parent = info["parent"]
        self.parents = info["parents"]
        self.mission = info["mission"]
        self.mimeType = info["mimeType"]
        self.is_folder = info["is_folder"]
        self.md5Checksum = info["md5Checksum"]

    def __repr__(self):
        string = "\nid: {0}\nmd5: {1}\nname: {2}\nparents: {3}\nis folder: {4}\n".format(
            self.uid, self.md5Checksum, self.name, str(self.parents),
            str(self.is_folder))
        return string

    def __eq__(self, value):
        # 先判断文件类型
        if (self.is_folder ^ value.is_folder):
            return False  # 如果文件类型不一致, 返回False
        # 文件的判断
        if (self.md5Checksum):
            return self.md5Checksum == self.md5Checksum
        # 文件夹的判断
        else:
            return self.name == value.name


class Global:
    # 任务信息
    isExit = False  # 是否退出程序
    user_only = False  # 是否使用个人账号
    current_mission = None  # 当前任务
    is_use_process_bar = False

    # 遍历文件夹
    SearchFolderQueue = queue.Queue()
    # 存放遍历得到的文件和文件夹信息
    INFO = {}
    # 存放遍历得到的文件夹信息
    SearchInformation = {}
    # 创建文件夹
    CreateFolderQueue = queue.Queue()
    # 创建文件
    CreateFileQueue = queue.Queue()
    # 原始文件夹id与复制文件夹id的对应关系
    Parallelism = dict()
    # 任务队列
    Mission = list()

    # sa文件信息
    SAFiles = []
    SAInfos = {}

    # 并行任务状态信息, 全局任务锁
    TaskLock = threading.Lock()
    add_info_lock = threading.Lock()
    add_folder_info_lock = threading.Lock()
    TaskStatus = []

    # 最大报错累积量
    CumErrorNum = 20

    # 程序运行过程中产生的信息
    Message = queue.Queue()

    logger = LogSingleton()

    @staticmethod
    def add_create_folder(file_info: FileInfo):
        """add_create_folder 往待创建文件夹队列中放入文件夹信息

        Args:
            file_info (FileInfo): 文件夹信息
        """
        Global.CreateFolderQueue.put(file_info)

    @staticmethod
    def add_create_file(file_info: FileInfo):
        """add_create_file 往待创建文件队列中放入文件信息

        Args:
            file_info (FileInfo): 文件信息, 非文件夹
        """
        Global.CreateFileQueue.put(file_info)

    @staticmethod
    def add_search_folder(file_info: FileInfo):
        """add_search_folder 往待遍历文件夹队列中放入文件夹信息

        Args:
            file_info (FileInfo): 文件夹信息
        """
        Global.SearchFolderQueue.put(file_info)

    @staticmethod
    def add_folder_information(file_info: FileInfo):
        """add_folder_information 将经过遍历查询的文件夹放进一字典中, 以文件信息uid作为键, 文件信息作为值.

        Args:
            file_info (FileInfo): 文件信息
        """
        Global.add_folder_info_lock.acquire()
        Global.SearchInformation[file_info.uid] = file_info
        Global.add_folder_info_lock.release()

    @staticmethod
    def add_info(uid: str, files: list):
        Global.add_info_lock.acquire()
        Global.INFO[uid] = files
        Global.add_info_lock.release()


class Mission:
    """ 任务调度
    """
    def __init__(self, src, dst=None):
        self.types = {0: "list", 1: "save"}


def save_cache():
    """save_cache 保存程序缓存数据
    """
    search_folder_json = {}
    create_folder_json = {}
    create_file_json = {}
    uids = []
    while (Global.SearchFolderQueue.qsize() > 0):
        cur_info = Global.SearchFolderQueue.get()
        search_folder_json[cur_info.uid] = cur_info.to_json()

    while (Global.CreateFolderQueue.qsize() > 0):
        cur_info = Global.CreateFolderQueue.get()
        uids.append(cur_info.uid)
        uids.append(cur_info.parent)
        create_folder_json[cur_info.uid] = cur_info.to_json()

    while (Global.CreateFileQueue.qsize() > 0):
        cur_info = Global.CreateFileQueue.get()
        uids.append(cur_info.uid)
        uids.append(cur_info.parent)
        create_file_json[cur_info.uid] = cur_info.to_json()

    with open("data/search_folder.json", "w") as fp:
        json.dump(search_folder_json, fp)

    with open("data/create_folder.json", "w") as fp:
        json.dump(create_folder_json, fp)

    with open("data/create_file.json", "w") as fp:
        json.dump(create_file_json, fp)

    # with open("data/folder_info.json", "w") as fp:
    #     json.dump(Global.SearchInformation, fp)

    # 已经完成创建或复制的文件或文件夹的键需要删除
    all_keys = set(Global.Parallelism.keys())
    exist_keys = set(uids)
    used_keys = all_keys - exist_keys
    for key in used_keys:
        Global.Parallelism.pop(key)

    with open("data/Parallelism.json", "w") as fp:
        json.dump(Global.Parallelism, fp)


def load_cache():
    """load_cache 从本地缓存中导入数据
    """
    with open("data/search_folder.json", "r") as fp:
        search_folder_json = json.load(fp)

    with open("data/create_folder.json", "r") as fp:
        create_folder_json = json.load(fp)

    with open("data/search_folder.json", "r") as fp:
        create_file_json = json.load(fp)

    with open("data/Parallelism.json", "r") as fp:
        Global.Parallelism = json.load(fp)

    # with open("data/folder_info.json", "r") as fp:
    #     Global.SearchInformation = json.load(fp)

    for item in search_folder_json:
        cur_info = FileInfo(item, from_json=True)
        Global.SearchFolderQueue.put(cur_info)

    for item in create_folder_json:
        cur_info = FileInfo(item, from_json=True)
        Global.CreateFolderQueue.put(cur_info)

    for item in create_file_json:
        cur_info = FileInfo(item, from_json=True)
        Global.CreateFileQueue.put(cur_info)


def show_all():
    print("-" * 20)
    print("SearchFolderQueue\n", "####" * 10)
    for cur_info in list(Global.SearchFolderQueue.queue):
        print(cur_info)
        time.sleep(0.1)
        print("-" * 20)

    print("\nCreateFolderQueue\n", "####" * 10)
    for cur_info in list(Global.CreateFolderQueue.queue):
        print(cur_info)
        time.sleep(0.1)
        print("-" * 20)

    print("\nCreateFileQueue\n", "####" * 10)
    for cur_info in list(Global.CreateFileQueue.queue):
        print(cur_info)
        time.sleep(0.1)
        print("-" * 20)


def statistics_file_information():
    print("\n统计信息:")
    print(">>> 待遍历文件夹数量: {0}".format(Global.SearchFolderQueue.qsize()))

    print(">>> 待创建文件夹数量: {0}".format(len(Global.SearchInformation)))

    print(">>> 待拷贝文件数量: {0}".format(Global.CreateFileQueue.qsize()))
    max_size = 0
    md5_list = []
    for cur_info in list(Global.CreateFileQueue.queue):
        max_size += int(cur_info.size)
        md5_list.append(cur_info.md5Checksum)

    print("  >>> 总文件大小: {0}mb".format(round(max_size / 1024 / 1024, 2)))
    print("  >>> 重复文件数量: {0}".format(len(md5_list) - len(set(md5_list))))


def process_bar():
    """process_bar 在控制台展示相关信息
    """
    def task():
        if (Global.is_use_process_bar):
            return
        print("process bar start...")
        Global.is_use_process_bar = True
        while (not Global.isExit):
            file_num = Global.CreateFileQueue.qsize()
            ignore = file_num == 0
            if not ignore:
                print("待创建的文件: {0}".format(file_num))
            time.sleep(6)
        Global.is_use_process_bar = False

    t = Thread(target=task, daemon=True)
    t.start()
