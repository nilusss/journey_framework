import sys
import json
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import journey.lib.serialization as se
import pymel.core as pm
import maya.cmds as mc
import maya.mel as mel
if sys.version_info.major >= 3:
    from importlib import reload
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(guides)
reload(bwsc)
reload(se)


class SetupTabUI(QtWidgets.QWidget):

    FILE_FILTER = "Maya (*.ma;*.mb;*.fbx;*.FBX);;Maya ASCII (*.ma);;Maya Binary (*.mb);; Fbx (*.fbx;*.FBX)"
    selected_filter = "Maya (*.ma;*.mb;*.fbx;*.FBX)"

    def __init__(self, parent):
        super(SetupTabUI, self).__init__(parent)
        self.parent_inst = parent

        # create ui elements
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.get_optionvars()
        self.set_import_and_rig_btn_state()

    def create_widgets(self):
        """Create controls for the window"""

        # set prefix input field and corresponding label
        self.char_name_le = QtWidgets.QLineEdit(self.get_character_name())
        self.char_name_label = QtWidgets.QLabel()
        self.char_name_label.setText("Character Name")
        self.char_name_label.setBuddy(self.char_name_le)

        # set prefix input field and corresponding label
        # model filepath
        self.filepath_le = QtWidgets.QLineEdit()
        self.filepath_btn = QtWidgets.QPushButton()
        self.import_model_btn = QtWidgets.QPushButton("Import model")
        self.filepath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.filepath_btn.setToolTip("Select Model File")
        self.filepath_label = QtWidgets.QLabel()
        self.filepath_label.setText("Model File (*.ma, *.mb, *.fbx)")
        self.filepath_label.setBuddy(self.filepath_le)

        # builder filepath
        self.filepath_builder_le = QtWidgets.QLineEdit()
        self.filepath_builder_btn = QtWidgets.QPushButton()
        self.import_builder_btn = QtWidgets.QPushButton("Import guides")
        self.filepath_builder_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.filepath_builder_btn.setToolTip("Select Guides File")
        self.filepath_builder_label = QtWidgets.QLabel()
        self.filepath_builder_label.setText("Guides File (*.json)")
        self.filepath_builder_label.setBuddy(self.filepath_le)

        # builder filepath
        self.filepath_skin_le = QtWidgets.QLineEdit()
        self.filepath_skin_btn = QtWidgets.QPushButton()
        self.filepath_skin_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.filepath_skin_btn.setToolTip("Select Skin Weights Directory")
        self.filepath_skin_label = QtWidgets.QLabel()
        self.filepath_skin_label.setText("Skin Weights (directory)")
        self.filepath_skin_label.setBuddy(self.filepath_skin_le)

        self.import_and_rig_btn = QtWidgets.QPushButton('Import Everything and Rig!')

    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        # create filepath layout for browsing model file
        filepath_layout = QtWidgets.QHBoxLayout()
        filepath_layout.addWidget(self.filepath_le)
        filepath_layout.addWidget(self.filepath_btn)
        import_model_layout = QtWidgets.QHBoxLayout()
        import_model_layout.addWidget(self.import_model_btn)

        # create filepath layout for browsing builder file
        filepath_builder_layout = QtWidgets.QHBoxLayout()
        filepath_builder_layout.addWidget(self.filepath_builder_le)
        filepath_builder_layout.addWidget(self.filepath_builder_btn)
        import_builder_layout = QtWidgets.QHBoxLayout()
        import_builder_layout.addWidget(self.import_builder_btn)

        # create filepath layout for browsing builder file
        filepath_skin_layout = QtWidgets.QHBoxLayout()
        filepath_skin_layout.addWidget(self.filepath_skin_le)
        filepath_skin_layout.addWidget(self.filepath_skin_btn)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 10, 5, 5)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.char_name_label)
        main_layout.addWidget(self.char_name_le)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.filepath_label)
        main_layout.addLayout(filepath_layout)
        main_layout.addLayout(import_model_layout)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.filepath_builder_label)
        main_layout.addLayout(filepath_builder_layout)
        main_layout.addLayout(import_builder_layout)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.filepath_skin_label)
        main_layout.addLayout(filepath_skin_layout)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.import_and_rig_btn)

        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        self.filepath_btn.clicked.connect(self.config_browse)
        self.filepath_builder_btn.clicked.connect(self.builder_browse)
        self.filepath_skin_btn.clicked.connect(self.skin_weights_browse)
        #self.save_btn.clicked.connect(self.config_save)
        self.char_name_le.textChanged.connect(self.set_character_name)
        self.import_model_btn.clicked.connect(self.on_import_model)
        self.import_builder_btn.clicked.connect(self.on_import_builder)
        self.import_and_rig_btn.clicked.connect(self.full_import_rig)

        # optionvar setters
        self.char_name_le.editingFinished.connect(self.set_optionvars)
        self.filepath_le.editingFinished.connect(self.set_optionvars)
        self.filepath_builder_le.editingFinished.connect(self.set_optionvars)
        self.filepath_skin_le.editingFinished.connect(self.set_optionvars)

    def get_optionvars(self):
        """used to get line edit fields that have been assigned to option vars"""
        if pm.optionVar(exists='Journey_char_name'):
            self.char_name_le.setText(pm.optionVar(q='Journey_char_name'))

        if pm.optionVar(exists='Journey_model_file'):
            self.filepath_le.setText(pm.optionVar(q='Journey_model_file'))

        if pm.optionVar(exists='Journey_builder_file'):
            self.filepath_builder_le.setText(pm.optionVar(q='Journey_builder_file'))

        if pm.optionVar(exists='Journey_skin_weights_dir'):
            self.filepath_skin_le.setText(pm.optionVar(q='Journey_skin_weights_dir'))

    def set_optionvars(self):
        pm.optionVar(sv=('Journey_char_name', self.char_name_le.text()))
        pm.optionVar(sv=('Journey_model_file', self.filepath_le.text()))
        pm.optionVar(sv=('Journey_builder_file', self.filepath_builder_le.text()))
        pm.optionVar(sv=('Journey_skin_weights_dir', self.filepath_skin_le.text()))

        self.set_import_and_rig_btn_state()

    def set_import_and_rig_btn_state(self):
        if self.char_name_le.text() and self.filepath_le.text() and self.filepath_builder_le.text() and self.filepath_skin_le.text():
            self.import_and_rig_btn.setEnabled(True)
        else:
            self.import_and_rig_btn.setEnabled(False)

    ###############
    # SLOTS START #
    ###############
    def full_import_rig(self):
        if self.char_name_le.text() and self.filepath_le.text() and self.filepath_builder_le.text() and self.filepath_skin_le.text():
            print('heeee')
            self.on_import_builder()
            self.parent_inst.guides_tab.on_rig_guides(skip_dialog=True)
        else:
            pm.warning('Some fields are empty!')

    def config_browse(self):
        model_filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "",
                                                                          self.FILE_FILTER, self.selected_filter)
        if model_filepath:
            self.filepath_le.setText(model_filepath)
            self.set_optionvars()
    
    def builder_browse(self):
        filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "",
                                                                          ("JSON (*.json)"))
        if filepath:
            self.filepath_builder_le.setText(filepath)
            self.set_optionvars()

    def skin_weights_browse(self):
        filepath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Skin Weights Dir", "",
                                                                               QtWidgets.QFileDialog.ShowDirsOnly)
        if filepath:
            self.filepath_skin_le.setText(filepath)
            self.set_optionvars()

    def config_save(self):
        self.set_character_name()

    def get_character_name(self):
        return self.parent_inst.character_name

    def set_character_name(self):
        self.parent_inst.character_name = self.char_name_le.text()
        try:
            self.parent_inst.set_ui_title()
        except:
            pass

    def on_import_model(self):
        grp_exists = pm.ls("*_TEMP_grp")
        if not grp_exists:
            model_file = self.filepath_le.text()
            file_type = model_file.split('.')[-1]
            if model_file:
                pm.undoInfo(openChunk=True, chunkName="importmodel")
                if 'fbx' in file_type:
                    before = pm.ls(assemblies=True)
                    mel.eval('FBXImport -f "{}";'.format(model_file))
                    after = pm.ls(assemblies=True)
                    model_node = set(after).difference(before).pop()
                    group_node = pm.createNode('transform', n=self.get_character_name() + '_TEMP_grp')
                    pm.parent(model_node, group_node)
                else:
                    group_name = self.get_character_name() + '_TEMP_grp'
                    model_node = pm.importFile(model_file, i=True, groupReference=True, groupName=group_name, returnNewNodes=True,)
                    group_node = pm.PyNode(group_name)
                    group_node.attr('overrideEnabled').set(1)
                    group_node.attr('overrideDisplayType').set(2)
                pm.select(None)
                pm.undoInfo(closeChunk=True, chunkName="importmodel")
            else:
                pm.warning("No model file available!")

        else:
            pm.warning("Model already in scene!")

    def on_import_builder(self):
        filepath = self.filepath_builder_le.text()
        if pm.ls('*_base'):
            pm.error("Modules already exists in the scene. Please clean up your scene before importing new guides!")
        elif filepath:
            pm.undoInfo(openChunk=True, chunkName="importbuilder")
            print( filepath)
            with open(filepath, 'r') as json_file:
                jdata = json.load(json_file)
                for data in jdata:
                    try:
                        obj = se.deserialize_guide(data)
                    except:
                        pm.confirmDialog(title='File Error!', message='Loaded file is not a valid preset file',
                                         button=['Ok'], defaultButton='Ok')
                        break
                    obj.draw()
                    guide_list_item = QtWidgets.QListWidgetItem()
                    guide_list_item.setData(QtCore.Qt.UserRole, obj)
                    guide_list_item.setText(obj.prefix)
                    self.parent_inst.guides_tab.list_wdg.addItem(guide_list_item)
            pm.undoInfo(closeChunk=True, chunkName="importbuilder")

        else:
            pm.warning("No builder file!")



    #############
    # SLOTS END #
    #############
