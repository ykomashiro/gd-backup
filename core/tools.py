def get_all_children(search_folder_information: dict, original_uid: str):
    """get_all_children 从一系列文件夹中寻找他们的父子关系

    Args:
        search_folder_information (dict): 文件夹列表

        original_uid (str) 顶级父文件夹id

    Returns:
        [type]: 以父文件夹uid为键, 子文件夹uid列表为值的字典
    """
    parent2children = dict([(key, []) for key in search_folder_information.keys()])
    parent2children[original_uid] = []
    for key in search_folder_information.keys():
        child = key
        parent = search_folder_information[child].parent
        parent2children[parent].append(child)
    print(parent2children)
    return parent2children
