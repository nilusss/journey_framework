import maya.cmds as mc
from pymel import mayautils

PORT = '7001'


def load():
    """Fake loading of the Journey Framework
    TODO: initialize an installation of the framework on startup
    """
    print("userSetup Start -----------------------")

    try:
        if not mc.commandPort(':' + PORT, query=True):
            mc.commandPort(name=':' + PORT)
        print("Port Open: " + PORT)
    except RuntimeError as e:
        print("Unable to open port: " + PORT)
        print(e)

    print("\n###############################")
    print("#Journey Framework initialized#")
    print("###############################\n")


if not mc.about(batch=True):
    mayautils.executeDeferred(load)


