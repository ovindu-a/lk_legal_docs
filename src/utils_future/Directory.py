import os
from functools import cached_property


class Directory:
    def __init__(self, dir_path):
        self.dir_path = dir_path

    @cached_property
    def size(self) -> int:
        if not os.path.exists(self.dir_path):
            return 0
        total_size = 0
        for dir_path, _, file_names in os.walk(self.dir_path):
            for file_name in file_names:
                file_path = os.path.join(dir_path, file_name)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size
