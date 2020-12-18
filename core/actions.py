from core.base import Action


class CopyFileAction(Action):
    def __init__(self, src: str, dst: str):
        super(CopyFileAction, self).__init__(src, dst)


class CopyFolderAction(Action):
    def __init__(self, src: str, dst: str):
        super(CopyFolderAction, self).__init__(src, dst)


class TraverseFolderAction(Action):
    def __init__(self, src: str, dst: str):
        super(TraverseFolderAction, self).__init__(src, dst)
