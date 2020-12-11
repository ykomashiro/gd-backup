from __future__ import print_function

import argparse
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

from core.common import *
from core.function import *
from core.sa import *
from core.task import *
from core.config import SCOPES

socks.set_default_proxy(socks.HTTP, addr='127.0.0.1', port=7890)  # 设置socks代理
socket.socket = socks.socksocket  # 把代理应用到socket


def get_args():
    parser = argparse.ArgumentParser(
        description='google drive tools',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m',
                        '--mission',
                        metavar='M',
                        type=str,
                        default="get",
                        help='what you want to do',
                        dest='mission')
    parser.add_argument('-s',
                        '--src',
                        metavar='S',
                        type=str,
                        default=None,
                        help='source file or folder',
                        dest='src')
    parser.add_argument('-d',
                        '--dst',
                        metavar='D',
                        type=str,
                        default=None,
                        help='destination folder',
                        dest='dst')
    parser.add_argument('-n',
                        '--num_worker',
                        metavar='N',
                        type=int,
                        default=1,
                        help='Number of worker/thread',
                        dest='num_worker')
    parser.add_argument('-u',
                        '--user_account',
                        metavar='U',
                        type=bool,
                        default=False,
                        help='Is use user account, not use service account?',
                        dest='user_account')

    return parser.parse_args()


if __name__ == "__main__":
    process_bar()
    args = get_args()
    src_folder_id = args.src
    dst_folder_id = args.dst
    service = None
    args.mission = "saveto"
    service = GetService(
        "account/sa/19c3ada8792dafc0d0928673c35ff27b07a59b46.json")
    temp_folder_id = "18ftr9eVbX1ncYx6jxgPrlv6Wpp33SMrw"
    temp_folder_id2 = "1eSUI4GXs0Jr9UAP4mZQG7VWQDv-i8EWB"
    src_folder_id = temp_folder_id
    dst_folder_id = temp_folder_id2

    print("*current mission:", args.mission)
    if args.mission == "show":
        result = Get(service, src_folder_id)
        ListAll(service, result)
        #show_all()
        statistics_file_information()
        save_cache()
    if args.mission == "get":
        result = Get(service, src_folder_id)
        print(result)

    if args.mission == "saveto":
        #SaveTo(service, src_folder_id, dst_folder_id)
        SAManage.read_sa_files(r"account/sa")
        AsynSaveTo(src_folder_id, dst_folder_id, 5)
