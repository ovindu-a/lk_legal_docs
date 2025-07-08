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

    def git_add(self, files):
        cmds = [
            f"cd {self.dir_git}",
            f"git add {files}",
        ]
        Git.run_cmds(cmds)
        return self

    def git_commit(self, message):
        cmds = [
            f"cd {self.dir_git}",
            f"git diff --cached --quiet || git commit -m '{message}'",
        ]
        Git.run_cmds(cmds)
        return self

    def git_pull(self):
        cmds = [
            f"cd {self.dir_git}",
            "git pull --rebase origin main",
        ]
        Git.run_cmds(cmds)
        return self
