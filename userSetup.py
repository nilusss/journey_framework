import maya.cmds as mc
from pymel import mayautils

PORT = '7001'
MATRIX_PLUGIN = "matrixNodes.mll"


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

    # load matrix nodes plugin
    if not mc.pluginInfo(MATRIX_PLUGIN, query=True, loaded=True):
        mc.loadPlugin(MATRIX_PLUGIN)


if not mc.about(batch=True):
    mayautils.executeDeferred(load)


