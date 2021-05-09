import json
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import journey.lib.serialization as se
import pymel.core as pm
import maya.cmds as mc
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(guides)
reload(bwsc)
reload(se)


class SetupTabUI(QtWidgets.QWidget):

    FILE_FILTER = "Maya (*.ma;*.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);; Fbx (*.fbx;*.FBX)"
    selected_filter = "Maya (*.ma, *.mb)"

    def __init__(self, parent):
        super(SetupTabUI, self).__init__(parent)
        self.parent_inst = parent

        # create ui elements
        self.create_widgets()
        self.create_layout()
        self.create_connections()


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
        self.import_model_btn = QtWidgets.QPushButton("Import as template")
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
        self.filepath_builder_btn.setToolTip("Select Builder File")
        self.filepath_builder_label = QtWidgets.QLabel()
        self.filepath_builder_label.setText("Builder File (*.json)")
        self.filepath_builder_label.setBuddy(self.filepath_le)

        # builder filepath
        self.filepath_skin_le = QtWidgets.QLineEdit()
        self.filepath_skin_btn = QtWidgets.QPushButton()
        self.filepath_skin_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.filepath_skin_btn.setToolTip("Select Skin Weights Directory")
        self.filepath_skin_label = QtWidgets.QLabel()
        self.filepath_skin_label.setText("Skin Weights (directory)")
        self.filepath_skin_label.setBuddy(self.filepath_skin_le)

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
        #main_layout.addWidget(self.save_btn)

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

    def get_optionvars(self):
        """used to get line edit fields that have been assigned to option vars"""
        pass

    ###############
    # SLOTS START #
    ###############
    def simple_print(self):
        print "yuuh"

    def config_browse(self):
        model_filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "",
                                                                          self.FILE_FILTER, self.selected_filter)
        if model_filepath:
            self.filepath_le.setText(model_filepath)
    
    def builder_browse(self):
        filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "",
                                                                          ("JSON (*.json)"))
        if filepath:
            self.filepath_builder_le.setText(filepath)

    def skin_weights_browse(self):
        filepath, selected_filter = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Skin Weights Dir", "",
                                                                               QtWidgets.QFileDialog.ShowDirsOnly)
        if filepath:
            self.filepath_skin_le.setText(filepath)

    def config_save(self):
        self.set_character_name()

    def get_character_name(self):
        return self.parent_inst.character_name

    def set_character_name(self):
        self.parent_inst.character_name = self.char_name_le.text()
        self.parent_inst.set_ui_title()

    def on_import_model(self):
        model_file = self.filepath_le.text()
        if model_file:
            before = pm.ls(assemblies=True)
            pm.importFile(model_file, namespace=self.get_character_name() + '')
            after = pm.ls(assemblies=True)
            # Using the before and after variable
            # to determine the model node
            model_node = set(after).difference(before).pop()
            node = pm.createNode('transform', n=self.get_character_name() + '_temp_grp')
            pm.parent(model_node, node)

        else:
            pm.warning("No model file available")

    def on_import_builder(self):
        filepath = self.filepath_builder_le.text()
        if pm.ls('*_base'):
            pm.error("Modules already exists in the scene. Please clean up your scene before importing new guides!")
        elif filepath:
            print filepath
            with open(filepath, 'r') as json_file:
                jdata = json.load(json_file)
                for data in jdata:
                    obj = se.deserialize_guide(data)
                    obj.draw()
                    guide_list_item = QtWidgets.QListWidgetItem()
                    guide_list_item.setData(QtCore.Qt.UserRole, obj)
                    guide_list_item.setText(obj.prefix)
                    self.parent_inst.guides_tab.list_wdg.addItem(guide_list_item)
        else:
            pm.warning("No builder file!")



    #############
    # SLOTS END #
    #############
