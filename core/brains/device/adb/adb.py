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
        self.logger = Logger()
        self.adb = ADBPaths.adb_bin(base_path)
        self.serial = " "

    def cmd(self, *args, **kwargs):
        """
        Command wrapper for adb
        
        Args:
            param1:
            param2:
        Returns:
            return1:
        """
        # Locals
        cmdline = None
        shell = None
        p = None
        wait = kwargs.get("wait", True)
        
        if len(args) == 1 and isinstance(args[0], basestring):
            cmdline = " ".join([self.adb, self.serial, args[0]])
            shell=True
        else:
            if isinstance(args[0], list) or isinstance(args[0], tuple):
                args = args[0]
            cmdline = [self.adb] + list(args)
            if self.serial:
                cmdline.insert(1, self.serial)
            shell=False
        try:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE, shell=shell)
            if wait:
                stdout,stderr = p.communicate()
                if p.returncode:
                    self.logger.log("critical", stderr)
                    return
                return (stdout, stderr)
            else:
                return ("", "")
        except Exception as e:
            raise e

    def get_devices(self):
        """
        adb devices -l
        """
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
        """
        adb push
        """
        self.cmd("push %s %s" % (local, remote))

    def pull(self, remote, local):
        """
        adb pull
        """
        self.cmd("pull %s %s" % (remote, local))

    def install(self, pkg, options):
        """
        adb install
        """
        pass

    def console(self):
        """
        adb shell
        """
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
        """
        Initialize the Frida agent
        
        Args:
            None
        Returns:
            None
        """
        # Locals
        stdout = None
        stderr = None
        
        try:
            self.logger.log("info", "Checking for if Frida Agent is running ...")
            if self.is_frida_running():
                # Frida is already initialized, return
                self.logger.log("info", "Frida is running (!)")
                return
            # Frida has not been initialized, check to see if the agent is on the target device
            self.logger.log("critical", "Frida is not running (!)")
            self.logger.log("info", "Checking for the frida-server binary")
            stdout,stderr = self.su("ls %s" % self.frida_dev_path)
            # If the Frida agent is not on the device, attempt to push it
            if "No such file or directory" in stdout:
                self.logger.log("critical", "Frida-server is not on the device (!)")
                self.logger.log("info", "Copying frida-server to device")
                # Push frida-server
                self.adb.push(self.frida_bin, self.frida_dev_path)
                # Set up the permissions
                self.su("chmod 755 %s" % self.frida_dev_path)
                self.logger.log("info", "Verifying copy ...")
                stdout,stderr = self.su("ls {}".format(self.frida_dev_path))
                # Handle if we could not push the agent to the target device
                if "No such file or directory" in stdout:
                    self.logger.log("critical", "Could not copy frida-server to device (!)")
                    return
            self.logger.log("info", "Attempting to launch the Frida agent ...")
            stdout,stderr = self.su("%s &" % self.frida_dev_path, wait=False)
            # This may need to be adjusted
            time.sleep(1)
            self.logger.log("info", "Checking for if Frida Agent is running ...")
            # If the Frida agent is running, return
            if self.is_frida_running():
                self.logger.log("info", "Frida is running (!)")
                return
            self.logger.log("critical", "Frida is not running (!)")
            return
        except Exception as e:
            raise e

    def kill_frida(self):
        """
        Kill the Frida agent if it is running
        
        Args:
            None
        Returns:
            None
        """
        pids = self.get_pids("frida-server")
        if pids:
            self.kill_proc(pids[0][0])

    def remove_frida(self):
        """
        Wrapper for killing and deleting the Frida agent
        
        Args:
            None
        Returns:
            None
        """
        if self.is_frida_running():
            self.logger.log("info", "Killing Frida agent (!)")
            self.kill_frida()
            time.sleep(.5)
        if self.is_frida_running():
            self.logger.log("critical", "Frida agent still running (!)")
        self.logger.log("info", "Deleting the frida-server binary (!)")
        self.su("rm -f %s" % self.frida_dev_path)
        stdout,stderr = self.su("ls %s" % self.frida_dev_path)
        if not "No such file or directory" in stdout:
            self.logger.log("critical", "Frida agent unable to be removed (!)")


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
