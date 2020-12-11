from core.function import *
from core.sa import *
from core.tools import *
import threading
import time


def AsynListAll(worker=1):
    """ListAll 获取指定文件夹下的所有子文件夹以及相关文件

    Args:
        service ([type]): 服务账号信息
    """
    assert worker > 0, "工作线程必须大于0"
    status_with_exit = [False] * worker
    lock = threading.Lock()

    def task(index):
        sa_info = SAManage.request()
        service = sa_info.service
        while (not all(status_with_exit)):
            while ((Global.SearchFolderQueue.qsize() > 0)
                   and (not Global.isExit)):
                current_folder = Global.SearchFolderQueue.get()
                lock.acquire()
                status_with_exit[index] = False
                lock.release()

                files = []
                try:
                    files = ListCurrent(service, current_folder)
                    Global.add_folder_information(current_folder)
                except Exception as e:
                    Global.logger.error(str(e))
                    Global.SearchFolderQueue.put(current_folder)
                    sa_info.cum_error += 1
                    SAManage.recycle(sa_info)
                    sa_info = SAManage.request()
                    service = sa_info.service
                    continue
                for sub_file_info in files:
                    sub_file_info = FileInfo(sub_file_info)
                    sub_file_info.parent = current_folder.uid
                    if (sub_file_info.is_folder):
                        # 添加文件夹
                        Global.SearchFolderQueue.put(sub_file_info)
                    else:
                        # 添加文件
                        Global.CreateFileQueue.put(sub_file_info)

            status_with_exit[index] = True
            time.sleep(1)
        SAManage.recycle(sa_info)

    threads = []
    for i in range(worker):
        t = threading.Thread(target=task, args=(i, ))
        t.start()  # 启动线程，即让线程开始执行
        threads.append(t)

    for t in threads:
        t.join()


def AsynSaveTo(src: str, dst: str, worker=1, is_first=True):
    assert worker > 0, "工作线程必须大于0"
    status_with_exit = [False] * worker
    lock = threading.Lock()

    if (is_first):
        # sa_info = SAManage.request()
        # service = sa_info.service
        # src_info = AddFirst(service, src, dst)
        # SAManage.recycle(sa_info)
        src_info = None
        with SAManage.request() as sa_info:
            service = sa_info.service
            src_info = AddFirst(service, src, dst)
    AsynListAll(worker=worker)
    Global.add_create_folder(src_info)  # 将目标顶级文件夹放入待创建文件夹队列
    parent2children = get_all_children(Global.SearchInformation,
                                       src_info.parent)

    if (Global.isExit):
        return

    def task_1(index):
        """task_1 创建文件夹

        Args:
            index ([type]): 线程标志
        """
        sa_info = SAManage.request()
        service = sa_info.service
        while (not all(status_with_exit)):
            while ((Global.CreateFolderQueue.qsize() > 0)
                   and (not Global.isExit)):
                cur_info = Global.CreateFolderQueue.get()

                lock.acquire()
                status_with_exit[index] = False
                lock.release()
                try:
                    res_uid = CreateFolder(service, cur_info,
                                           Global.Parallelism[cur_info.parent])
                    Global.Parallelism[cur_info.uid] = res_uid
                    # 将current folder 的子文件夹加入到待创建文件夹队列中
                    for uid in parent2children[cur_info.uid]:
                        if uid == cur_info.uid:
                            continue
                        Global.add_create_folder(Global.SearchInformation[uid])

                except Exception as e:
                    print("{0} 触发错误, 无法创建文件夹: {1}".format(sa_info.uid, str(e)))
                    Global.logger.error(str(e))
                    Global.CreateFolderQueue.put(cur_info)
                    sa_info.cum_error += 1
                    SAManage.recycle(sa_info)
                    sa_info = SAManage.request()
                    service = sa_info.service




            status_with_exit[index] = True
            time.sleep(1)
        SAManage.recycle(sa_info)

    def task_2(index):
        """task_2 拷贝文件

        Args:
            index ([type]): 线程标识
        """
        sa_info = SAManage.request()
        service = sa_info.service
        while (not all(status_with_exit)):
            while ((Global.CreateFileQueue.qsize() > 0)
                   and (not Global.isExit)):
                cur_info = Global.CreateFileQueue.get()
                #print(cur_info.name)

                lock.acquire()
                status_with_exit[index] = False
                lock.release()
                try:
                    string = "thread: {0}\tcopy file {1}".format(index, cur_info.name)
                    Global.logger.info(string)
                    Copy(service, cur_info.uid,
                         Global.Parallelism[cur_info.parent])
                except Exception as e:
                    print("{0} 触发错误, 无法拷贝文件".format(sa_info.uid))
                    Global.logger.error(str(e))
                    Global.CreateFileQueue.put(cur_info)
                    sa_info.cum_error += 1
                    SAManage.recycle(sa_info)
                    sa_info = SAManage.request()
                    service = sa_info.service

            status_with_exit[index] = True
            time.sleep(1)
        SAManage.recycle(sa_info)

    threads = []
    for i in range(worker):
        t = threading.Thread(target=task_1, args=(i, ))
        t.start()  # 启动线程，即让线程开始执行
        threads.append(t)

    for t in threads:
        t.join()

    status_with_exit = [False] * worker
    threads = []
    for i in range(worker):
        t = threading.Thread(target=task_2, args=(i, ))
        t.start()  # 启动线程，即让线程开始执行
        threads.append(t)

    for t in threads:
        t.join()
