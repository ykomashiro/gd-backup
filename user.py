from __future__ import print_function

import os.path
import pickle
import socket
import time
import socks
from apiclient import discovery, errors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools
from core.function import *
from core.common import *
socks.set_default_proxy(socks.HTTP, addr='127.0.0.1', port=7890)  # 设置socks代理
socket.socket = socks.socksocket  # 把代理应用到socket

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.appdata",
    "https://www.googleapis.com/auth/drive.photos.readonly",
    "https://www.googleapis.com/auth/drive.metadata",
    "https://www.googleapis.com/auth/drive.metadata.readonly"

]
path = r"account/user/credentials.json"


def get_service():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('account/token.pickle'):
        with open('account/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('account/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    return service



src_id = "1dD3pmsSosMQEj-ioj1dQ_WF_slF7f5tR"
dst_id = "1fA6gDyodM4yjWIbpQwqc-jsoigqSto2U"


print("获取账号信息")
service = get_service()
res = None


print("start to save")
#SaveTo(service, folder_id, dst_id)

src_info = Get(service, src_id)
print("原始文件夹信息")
print(src_info)
Global.Parallelism[src_info.parent] = dst_id
Global.SearchFolderQueue.put(src_info)
print("遍历所有文件")
ListAll(service, src_info)


while (Global.CreateFolderQueue.qsize() > 0):
    cur_info = Global.CreateFolderQueue.get()
    print(cur_info)
    res_uid = CreateFolder(service, cur_info, Global.Parallelism[cur_info.parent])
    Global.Parallelism[cur_info.uid] = res_uid

while (Global.CreateFileQueue.qsize() > 0):
    cur_info = Global.CreateFileQueue.get()
    print(cur_info)
    Copy(service, cur_info.uid, Global.Parallelism[cur_info.parent])

print(Global.Parallelism)












print(res)
print("-" * 20)
print("SearchFolderQueue\n","####")
while (Global.SearchFolderQueue.qsize() > 0):
    print(Global.SearchFolderQueue.get())
    time.sleep(0.5)
    print("-" * 20)
print("CreateFolderQueue\n","####")
while (Global.CreateFolderQueue.qsize() > 0):
    print(Global.CreateFolderQueue.get())
    time.sleep(0.5)
    print("-" * 20)
print("CreateFileQueue\n","####")

while (Global.CreateFileQueue.qsize() > 0):
    print(Global.CreateFileQueue.get())
    time.sleep(0.5)
    print("-" * 20)
