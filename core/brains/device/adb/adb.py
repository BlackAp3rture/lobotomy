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
        self.serial = ""

    def cmd(self, *args, **kwargs):
        """
        Command wrapper for adb
        
        Args:
          param1: *args
          param2: **kwargs
        Returns:
          returns: Command result
        """
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
                    Logger.log("critical", stderr)
                    raise OSError(stderr)
                return (stdout, stderr)
            else:
                return ("", "")
        except Exception as e:
            raise e
