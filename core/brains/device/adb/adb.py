from subprocess import Popen, PIPE
import os
import time
from core.logging.logger import Logger

class ADBPaths(object):
    @staticmethod
    def adb_bin(base_dir):
        return os.path.join(base_dir, "bin", "adb")

    @staticmethod
    def frida_bin(base_dir):
        return os.path.join(base_dir, "bin", "frida-server")

    @staticmethod
    def frida_dev_path():
        return "/data/local/tmp/frida-server"


class ADB(object):
    def __init__(self, base_path):
        self.adb = ADBPaths.adb_bin(base_path)
        self.serial = ''

    def cmd(self, *args, **kwargs):
        """
        Run an adb command
        """
        wait = kwargs.get("wait", True)
        if len(args) == 1 and isinstance(args[0], basestring):
            cmdline = " ".join([self.adb, self.serial, args[0]])
            shell=True
        else:
            if isinstance(args[0], list) or isinstance(args[0], tuple):
                # Single iterable arg, make into a list object
                args = args[0]
            # add the adb executable to the front of the args
            cmdline = [self.adb] + list(args)
            if self.serial:
                cmdline.insert(1, self.serial)
            shell=False
        try:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE, shell=shell)
            if wait:
                stdout,stderr = p.communicate()
                if p.returncode:
                    Logger.log("critical", stderr)
                    raise OSError(stderr)
                return (stdout, stderr)
            else:
                return ("", "")
        except Exception as e:
            raise e

    def get_devices(self):
        raw = self.cmd("devices -l")[0].split("\n")
        raw.pop(), raw.pop(), raw.pop(0)
        return [(item.split(" ")[0], item) for item in raw]

    def set_serial(self, serial):
        if not serial:
            self.serial = " "
        else:
            self.serial = "-s " + serial

    def get_serial(self):
        return self.serial[2:]

    def push(self, local, remote):
        self.cmd("push %s %s" % (local, remote))

    def pull(self, remote, local):
        self.cmd("pull %s %s" % (remote, local))

    def install(self, pkg, options):
        pass

    def console(self):
        pass


class Device(object):
    def __init__(self, dev_id, project_dir):
        self.serial,self.desc = dev_id
        self.adb = ADB(project_dir)
        self.adb.set_serial(self.serial)
        self.frida_bin = ADBPaths.frida_bin(project_dir)
        self.frida_dev_path = ADBPaths.frida_dev_path()

    def __str__(self):
        return "Device : {}".format(self.desc)

    def shell(self, cmd, **kwargs):
        return self.adb.cmd("shell " + cmd, **kwargs)

    def su(self, cmd, **kwargs):
        return self.shell("su -c '%s'" % cmd, **kwargs)

    def get_pids(self, name):
        stdout,x = self.shell("ps -x")
        pids = []
        for line in stdout.split("\n"):
            if name in line:
                pid = filter(lambda x: x, line.split(" "))[1]
                pids.append((pid, line))
        return pids

    def kill_proc(self, pid):
        stdout,x = self.su("kill -9 {}".format(pid))

    def is_frida_running(self):
        pids = self.get_pids("frida-server")
        if pids:
            return True
        else:
            return False

    def init_frida(self):
        Logger.log("info", "Checking for if Frida Agent is running ...")
        if self.is_frida_running():
            Logger.log("info", "Frida is running (!)")
            return

        Logger.log("critical", "Frida is not running (!)")
        Logger.log("info", "Checking for the frida-server binary")
        stdout,stderr = self.su("ls %s" % self.frida_dev_path)
        if "No such file or directory" in stdout:
            Logger.log("critical", "Frida-server is not on the device (!)")
            Logger.log("info", "Copying frida-server to device")
            self.adb.push(self.frida_bin, self.frida_dev_path)
            self.su("chmod 755 %s" % self.frida_dev_path)

            # Verify it made it
            Logger.log("info", "Verifying copy ...")
            stdout,stderr = self.su("ls %s" % self.frida_dev_path)
            if "No such file or directory" in stdout:
                Logger.log("critical", "Could not copy frida-server to phone (!)")
                raise Exception

        Logger.log("info", "Attempting to launch the Frida Agent ...")
        stdout,stderr = self.su("%s &" % self.frida_dev_path, wait=False)
        time.sleep(1)

        Logger.log("info", "Checking for if Frida Agent is running ...")
        if self.is_frida_running():
            Logger.log("info", "Frida is running (!)")
            return

        Logger.log("critical", "Frida is not running (!)")
        raise Exception

    def kill_frida(self):
        pids = self.get_pids("frida-server")
        if pids:
            self.kill_proc(pids[0][0])

    def remove_frida(self):
        if self.is_frida_running():
            Logger.log("info", "Killing Frida Agent (!)")
            self.kill_frida()
            time.sleep(.5)

        if self.is_frida_running():
            Logger.log("critical", "Frida Agent still running (!)")

        Logger.log("info", "Deleting the frida-server binary (!)")
        self.su("rm -f %s" % self.frida_dev_path)
        stdout,stderr = self.su("ls %s" % self.frida_dev_path)
        if not "No such file or directory" in stdout:
            Logger.log("critical", "Frida-server unable to be removed (!)")


def enumerate_devices(project_dir):
    adb = ADB(project_dir)
    return adb.get_devices()

if __name__ == "__main__":
    PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
    devices = enumerate_devices(PROJECT_DIR)
    device = devices[0]
    device = Device(device, PROJECT_DIR)
    device.init_frida()
    device.remove_frida()
