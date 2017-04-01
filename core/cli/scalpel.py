from cmd2 import Cmd as ScalpelCmd
from core.logging.logger import Logger
from functools import wraps
from blessings import Terminal
from datetime import datetime
import readline
# DO NOT REMOVE
# Fix for cmd2 that enables command auto-complete
readline.parse_and_bind("bind ^I rl_complete")


class ScalpelError(Exception):
    def __init__(self, message):
        self.logger = Logger()
        self.message = message
        self.logger.log("critical", "Surgical : {}".format(self.message))


class ScalpelCmdArgumentException(Exception):
    def __init__(self, cmdargs=None, doc=""):
        self.t = Terminal()
        if not cmdargs:
            cmdargs = None
        self.cmdargs = cmdargs
        self.doc = doc

    def __str__(self):
        msg = [self.doc]
        if self.cmdargs:
            msg.insert(0, "\n\t{0} : {1} (!)".format("Command not found",
                                                     self.cmdargs))
        return "\n\n".join(msg)


def cmd_arguments(expected_args):
    def decorator(func):
        func._expected_args = expected_args
        @wraps(func)
        def wrapper(self, *args):
            if args[0].split(" ")[0] not in expected_args:
                raise ScalpelCmdArgumentException(cmdargs=args[0].split(" ")[0],doc=func.func_doc)
            return func(self, *args)
        return wrapper
    return decorator


class Run(ScalpelCmd):
    def __init__(self, vm, vmx):
        ScalpelCmd.__init__(self)
        self.logger = Logger()
        self.t = Terminal()
