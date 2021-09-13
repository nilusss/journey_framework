"""
install module to automatically install the journey toolset to maya and create shelf and shelf button
"""

import os
import pymel.core as pm
import maya.mel as mel

from shutil import copy


def onMayaDroppedPythonFile(*args):
    file_path = os.path.dirname(os.path.abspath(__file__))

    for s_file in os.listdir(file_path):
        if 'journey.mod' in s_file:
            copy(file_path + '\\' + s_file, file_path.replace('\\journey_framework', ''))

    mel.eval('global string $gShelfTopLevel;')
    shelf_top_level = mel.eval('$tmp=$gShelfTopLevel;')
    # get top shelf names
    get_shelf = pm.tabLayout(shelf_top_level, query=True, selectTab=True)

    pm.setParent(get_shelf)
    pm.shelfButton(command="import sys\n\n"
                           "if sys.version_info.major >= 3:\n"
                           "    from importlib import reload\n"
                           "import pymel.core as pm\n"
                           "try:\n"
                           "    import journey.ui.main as maui\n"
                           "    print(\"LOADING UI...\")\n"
                           "    reload(maui)\n"
                           "    ui = maui.show()\n"
                           "except:\n"
                           "    pm.warning('Can not load module. Please restart Maya')\n",
                   annotation="Journey Framework",
                   label="JF",
                   image=file_path + "/journey/icons/icon.png",
                   image1=file_path + "/journey/icons/icon.png",
                   sourceType="python")
