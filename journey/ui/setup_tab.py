from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import pymel.core as pm
import maya.cmds as mc
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(guides)
reload(bwsc)


class SetupTabUI(QtWidgets.QWidget):

    FILE_FILTER = "Maya (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);; All Files(*.*)"

    selected_filter = "Maya (*.ma *.mb)"

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
        self.line_edit = QtWidgets.QLineEdit(self.get_character_name())
        self.prefix_label = QtWidgets.QLabel()
        self.prefix_label.setText("Character Name")
        self.prefix_label.setBuddy(self.line_edit)

        # set prefix input field and corresponding label
        self.filepath_le = QtWidgets.QLineEdit()
        self.filepath_btn = QtWidgets.QPushButton()
        self.filepath_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.filepath_btn.setToolTip("Select Model File")
        self.filepath_label = QtWidgets.QLabel()
        self.filepath_label.setText("Model File")
        self.filepath_label.setBuddy(self.filepath_le)

        self.save_btn = QtWidgets.QPushButton("Save")

    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        # create filepath layout for browsing model file
        filepath_layout = QtWidgets.QHBoxLayout()
        filepath_layout.addWidget(self.filepath_le)
        filepath_layout.addWidget(self.filepath_btn)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 10, 5, 5)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.prefix_label)
        main_layout.addWidget(self.line_edit)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.filepath_label)
        main_layout.addLayout(filepath_layout)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.save_btn)

        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        self.filepath_btn.clicked.connect(self.config_browse)
        self.save_btn.clicked.connect(self.config_save)



    ###############
    # SLOTS START #
    ###############
    def simple_print(self):
        print "yuuh"

    def config_browse(self):
        filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", "",
                                                                          self.FILE_FILTER, self.selected_filter)
        if filepath:
            self.filepath_le.setText(filepath)
        print("TODO: BROWSE DIALOG")

    def config_save(self):
        self.set_character_name()

    def get_character_name(self):
        return self.parent_inst.character_name

    def set_character_name(self):
        self.parent_inst.character_name = self.line_edit.text()
        self.parent_inst.set_ui_title()


    #############
    # SLOTS END #
    #############
