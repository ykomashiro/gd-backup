from core.common import FileInfo, Global
from core.error import *
from core.tools import *
import time
import json


def Copy(service, src: str, dst: str):
    """Copy 将目标文件src 复制到目标文件夹dst 

    Args:
        service ([type]): 账号权限信息
        src (str): 需复制文件id
        dst (str): 目标文件夹id

    Returns:
        [type]: 复制后的文件信息
    """
    results = None
    body = {"parents": [dst]}
    results = service.files().copy(body=body,
                                   fileId=src,
                                   supportsAllDrives=True,
                                   fields="parents, id, name").execute()
    return results


def Move(service, src: str, dst: str):
    pass


def Delete(service, src: str):
    pass


def Get(service, src: str):
    results = service.files().get(
        fileId=src,
        supportsAllDrives=True,
        fields="kind, parents, id, name, mimeType, size, md5Checksum").execute(
        )
    return FileInfo(results)


def ListAll(service, src: FileInfo):
    """ListAll 获取指定文件夹下的所有子文件夹以及相关文件

    Args:
        service ([type]): 服务账号信息
    """
    Global.SearchFolderQueue.put(src)
    while (Global.SearchFolderQueue.qsize() > 0):
        current_folder = Global.SearchFolderQueue.get()
        files = ListCurrent(service, current_folder)
        Global.add_folder_information(current_folder)
        for sub_file_info in files:
            sub_file_info = FileInfo(sub_file_info)
            sub_file_info.parent = current_folder.uid
            if (sub_file_info.is_folder):
                # 添加文件夹
                Global.add_search_folder(sub_file_info)
            else:
                # 添加文件
                Global.add_create_file(sub_file_info)


def ListCurrent(service, src: FileInfo):
    """ListCurrent 遍历当前文件夹

    Args:
        service ([type]): 服务账号信息
        src (FileInfo): 需遍历的文件夹信息
    Returns:
        files (list) 遍历当前文件夹得到的文件及文件夹信息列表
    """
    files = []
    # 遍历首页
    results = service.files().list(
        #    driveId=drive_id,
        corpora="allDrives",
        includeItemsFromAllDrives=True,
        q="'{0}' in parents".format(src.uid),
        supportsAllDrives=True,
        fields=
        "nextPageToken, files(id, name, parents, kind, mimeType, size, md5Checksum)",
    ).execute()
    files += results["files"]

    # 对下一页进行遍历
    while ("pageToken" in results):
        print("next page")
        results = service.files().list(
            corpora="allDrives",
            includeItemsFromAllDrives=True,
            q="'{0}' in parents".format(src.uid),
            supportsAllDrives=True,
            fields=
            "nextPageToken, files(id, name, parents, kind, mimeType, size, md5Checksum)",
            pageToken=results["pageToken"],
        ).execute()
        files += results["files"]
    Global.add_info(src.uid, files)

    return files


def CreateFolder(service, src: FileInfo, dst_parent):
    """CreateFolder 在文件夹dst_parent下创建子文件夹src

    Args:
        service ([type]): 服务账号信息
        src (FileInfo): 源文件信息
        dst_parent ([type]): 待建立的父级文件夹

    Returns:
        [str]: 新建文件夹id
    """
    body = {
        'name': src.name,
        'kind': "drive#folder",
        'mimeType': "application/vnd.google-apps.folder",
        'parents': [dst_parent]
    }
    result = service.files().create(body=body,
                                    supportsAllDrives=True).execute()
    return result["id"]


def AddFirst(service, src, parent):
    info = Get(service, src)
    Global.SearchFolderQueue.put(info)
    Global.Parallelism[info.parent] = parent
    return info


def SaveTo(service, src: str, dst: str):
    """SaveTo 将文件夹src转存至dst

    Args:
        service ([type]): [description]
        src (str): [description]
        dst (str): [description]
    """
    src_info = Get(service, src)
    print(src_info)  # 打印原始文件夹信息

    Global.Parallelism[src_info.parent] = dst
    # Global.SearchFolderQueue.put(src_info)  # 将目标顶级文件夹放入待遍历文件夹队列
    ListAll(service, src_info)  # 遍历所有文件
    Global.add_create_folder(src_info)  # 将目标顶级文件夹放入待创建文件夹队列
    parent2children = get_all_children(Global.SearchInformation,
                                       src_info.parent)

    while (Global.CreateFolderQueue.qsize() > 0):
        cur_info = Global.CreateFolderQueue.get()
        res_uid = CreateFolder(service, cur_info,
                               Global.Parallelism[cur_info.parent])
        Global.Parallelism[cur_info.uid] = res_uid
        # 将current folder 的子文件夹加入到待创建文件夹队列中
        for uid in parent2children[cur_info.uid]:
            if uid == cur_info.uid:
                continue
            Global.add_create_folder(Global.SearchInformation[uid])

    while (Global.CreateFileQueue.qsize() > 0):
        cur_info = Global.CreateFileQueue.get()
        time_start = time.time()
        Copy(service, cur_info.uid, Global.Parallelism[cur_info.parent])
        time_end = time.time()
        print('time cost', time_end - time_start, 's')
