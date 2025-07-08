import os

from utils import Log

log = Log("Git")


class Git:
    def __init__(self, dir_git):
        self.dir_git = dir_git

    @staticmethod
    def run_cmds(cmds):
        for cmd in cmds:
            log.debug(f"🖥️: {cmd}")
            os.system(cmd)

    def clone(self, repo_url):
        if os.path.exists(self.dir_git):
            raise FileExistsError(f"Directory {self.dir_git} already exists.")
        cmds = [
            f"git clone {repo_url} {self.dir_git}",
            f"cd {self.dir_git}",
        ]
        Git.run_cmds(cmds)

    def add(self, files):
        cmds = [
            f"cd {self.dir_git}",
            f"git add {files}",
        ]
        Git.run_cmds(cmds)
        return self

    def commit(self, message):
        cmds = [
            f"cd {self.dir_git}",
            f"git diff --cached --quiet || git commit -m '{message}'",
        ]
        Git.run_cmds(cmds)
        return self

    def pull(self):
        cmds = [
            f"cd {self.dir_git}",
            "git pull --rebase origin main",
        ]
        Git.run_cmds(cmds)
        return self

    def push(self):
        cmds = [
            f"cd {self.dir_git}",
            "git push origin main",
        ]
        Git.run_cmds(cmds)
        return self
