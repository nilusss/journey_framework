import json
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import journey.lib.serialization as se
import pymel.core as pm
try:
    import journey.lib.utils.deform as deform
except:
    confirm = pm.confirmDialog(title='ngSkinTools not on PC', message='ngSkinTools was not found!\n'
                                                                      'Skin saving and skin loading'
                                                                      'will therefore not work.\n'
                                                                      'Using those buttons will result in an error',
                               button=['OK'],
                               defaultButton='OK')
import journey.lib.utils.tools as tools
import maya.cmds as mc
import maya.mel as mel
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(guides)
reload(bwsc)
reload(se)
reload(deform)
reload(tools)


class SkinningTabUI(QtWidgets.QWidget):
    FILE_FILTER = "Maya (*.ma;*.mb;*.fbx;*.FBX);;Maya ASCII (*.ma);;Maya Binary (*.mb);; Fbx (*.fbx;*.FBX)"
    selected_filter = "Maya (*.ma;*.mb;*.fbx;*.FBX)"

    def __init__(self, parent):
        super(SkinningTabUI, self).__init__(parent)
        self.parent_inst = parent

        # create ui elements
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create controls for the window"""

        self.prep_btn = QtWidgets.QPushButton('Prep For Skinning')
        self.show_all_btn = QtWidgets.QPushButton('Show All')
        self.hide_joints_btn = QtWidgets.QPushButton('Hide Joints')
        self.save_btn = QtWidgets.QPushButton('Save Skinning')

    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        btn_layout = QtWidgets.QVBoxLayout()
        btn_layout.addWidget(self.prep_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.show_all_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.hide_joints_btn)
        btn_layout.addSpacing(30)
        btn_layout.addWidget(self.save_btn)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 10, 5, 5)

        main_layout.addSpacing(10)
        main_layout.addLayout(btn_layout)

        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        self.prep_btn.clicked.connect(self.on_prep)
        self.show_all_btn.clicked.connect(self.on_show_all)
        self.hide_joints_btn.clicked.connect(self.on_hide_joints)
        self.save_btn.clicked.connect(self.on_save)

    ###############
    # SLOTS START #
    ###############
    def on_prep(self):
        get_rig_grp = pm.ls("*_rig_grp", assemblies=True)
        if get_rig_grp:
            children = pm.ls("rig_grp")[0].getChildren()
            for child in children:
                if "joints" not in child.name():
                    child.attr('v').set(0)
                else:
                    child.attr('v').set(1)
            pm.PyNode('model_grp').attr('overrideEnabled').set(0)
            pm.PyNode('model_grp').attr('overrideDisplayType').set(2)

        else:
            pm.warning("No rig in scene!")

    def on_show_all(self):
        get_rig_grp = pm.ls("*_rig_grp", assemblies=True)
        if get_rig_grp:
            children = pm.ls("rig_grp")[0].getChildren()
            for child in children:
                if "joints" not in child.name():
                    child.attr('v').set(1)
                else:
                    child.attr('v').set(1)
            pm.PyNode('model_grp').attr('overrideEnabled').set(1)
            pm.PyNode('model_grp').attr('overrideDisplayType').set(2)
        else:
            pm.warning("No rig in scene!")

    def on_hide_joints(self):
        if pm.ls("joints_grp"):
            pm.ls("joints_grp")[0].attr('v').set(0)
        else:
            pm.warning("No rig in scene!")

    def on_save(self):
        if pm.ls('c_root_result_jnt'):
            pm.parent('c_root_result_jnt', w=True)
        try:
            geo_list = tools.get_geo('model_grp')
        except:
            geo_list = ''
        if geo_list:
            filepath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Skin Weights Dir", "",
                                                                  QtWidgets.QFileDialog.ShowDirsOnly)
            if filepath:
                print filepath
                deform.save_weights(filepath, geo_list)
            if pm.ls('c_root_result_jnt'):
                pm.parent('c_root_result_jnt', 'joints_grp')
        else:
            pm.warning("No model or rig found!")

    #############
    # SLOTS END #
    #############
