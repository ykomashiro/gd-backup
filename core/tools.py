import queue

from core.actions import *
from core.common import FileInfo


def get_all_children(search_folder_information: dict, original_uid: str):
    """get_all_children 从一系列文件夹中寻找他们的父子关系

    Args:
        search_folder_information (dict): 文件夹列表

        original_uid (str) 顶级父文件夹id

    Returns:
        [type]: 以父文件夹uid为键, 子文件夹uid列表为值的字典
    """
    parent2children = dict([(key, [])
                            for key in search_folder_information.keys()])
    parent2children[original_uid] = []
    for key in search_folder_information.keys():
        child = key
        parent = search_folder_information[child].parent
        parent2children[parent].append(child)
    print(parent2children)
    return parent2children


def compare_folder(src: str, dst: str, src_folder: list, dst_folder: list):
    folder_queue = queue.Queue()
    files_queue = queue.Queue()
    


def compare_with_two_folder(src_folder: list, dst_folder: list):
    folder_actions = []
    files_actions = []
    src_sub_folder = []
    src_sub_files = []
    dst_sub_folder = []
    dst_sub_files = []
    for item in src_folder:
        file_info = FileInfo(item)
        if file_info.is_folder:
            src_sub_folder.append(file_info)
        else:
            src_sub_files.append(file_info)

    for item in dst_folder:
        file_info = FileInfo(item)
        if file_info.is_folder:
            dst_sub_folder.append(file_info)
        else:
            dst_sub_files.append(file_info)

    for item in src_sub_folder:
        if item not in dst_sub_folder:
            folder_actions.append(item)

    for item in src_sub_files:
        if item not in dst_sub_files:
            files_actions.append(item)

    return folder_actions, files_actions
