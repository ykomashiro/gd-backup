import abc
from abc import ABC, abstractmethod


class Action(ABC):
    def __init__(self, src: str, dst: str, is_my_parent=True):
        self.__type_list = ["create_folder", "copy_file_to"]
        self.type = None
        self.src = src
        self.dst = dst
        self.is_my_parent = is_my_parent

    def get_type(self):
        return self.type
