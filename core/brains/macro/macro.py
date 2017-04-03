from core.logging.logger import Logger
from blessings import Terminal
from os import path, listdir
from json import loads
from datetime import datetime
import os.path


class MacroError(Exception):
    def __init__(self, message):
        self.logger = Logger()
        self.message = message
        self.logger.log("Error", "Macro : {}".format(self.message))


class Macro(object):
    def __init__(self, apk):
        self.logger = Logger()
        self.t = Terminal()

    def macro_generator(self):

        """
        := macro
        """
        # Locals
        directory_items = None
        macro_path = "".join([path.dirname(path.realpath(__file__)), "/../../../files/"])
        selection = None
        apk_path = None
        json = None

        try:
            print("\n")
            directory_items = listdir(macro_path)
            for i, item in enumerate(directory_items):
                print(self.t.cyan("\t--> [{}] {}"
                                  .format(i, item)))
            print("\n")
            selection = raw_input(self.t.yellow("[{}] Select config : ".format(datetime.now())))
            try:
                index = int(selection)
            except ValueError:
                index = -1
            print("\n")
            if selection:
                for i, item in enumerate(directory_items):
                    if selection == item or i == index:
                        selection = item
                        break
                with open("".join([macro_path, "/", selection]), "rb") as config:
                    # Load the config as JSON
                    # Being parsing the config for operations
                    json = loads(config.read())
                    if json:
                        for k, v in json.items():
                            if k == "apk":
                                if v:
                                    apk_path = str(v)
                                    # Call operate() with the path to apk
                                    self.do_operate("apk {}".format(apk_path))
                                    return
                                else:
                                    CommandError("macro : Path to APK not found in {}".format(selection))

                            else:
                                CommandError("macro : Error loading {} as JSON".format(selection))
        except Exception as e:
            MacroError("macro : {}".format(e))
