from subprocess import Popen, PIPE
from core.logging.logger import Logger
import os


class ADBPaths(object):
    @staticmethod
    def adb_bin(base_dir):
        return os.path.join(base_dir, "bin", "adb")


class ADB(object):
    def __init__(self, base_path):
        self.logger = Logger()
        self.adb = ADBPaths.adb_bin(base_path)
        self.serial = ""

    def cmd(self, *args, **kwargs):
        """
        Run an adb command
        """
        wait = kwargs.get("wait", True)
        if len(args) == 1 and isinstance(args[0], basestring):
            cmdline = " ".join([self.adb, self.serial, args[0]])
            shell = True
        else:
            if isinstance(args[0], list) or isinstance(args[0], tuple):
                args = args[0]
            cmdline = [self.adb] + list(args)
            if self.serial:
                cmdline.insert(1, self.serial)
            shell = False
        try:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE, shell=shell)
            if wait:
                stdout, stderr = p.communicate()
                if p.returncode:
                    self.logger.log("critical", stderr)
                    raise OSError(stderr)
                return (stdout, stderr)
            else:
                return ("", "")
        except Exception as e:
            raise e

    def get_devices(self):
        """
        """
        raw = self.cmd("devices -l")[0].split("\n")
        raw.pop(), raw.pop(), raw.pop(0)
        return [(item.split(' ')[0], item) for item in raw]

    def set_serial(self, serial):
        """
        """
        if not serial:
            self.serial = ""
        else:
            self.serial = "-s " + serial

    def get_serial(self):
        """
        """
        return self.serial[2:]

    def push(self, local, remote):
        """
        """
        self.cmd("push %s %s" % (local, remote))

    def pull(self, remote, local):
        """
        """
        self.cmd("pull %s %s" % (remote, local))

    def install(self, pkg, options):
        pass

    def console(self):
        pass
