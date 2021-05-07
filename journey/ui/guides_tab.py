from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import journey.ui.builder as builder
import pymel.core as pm
import maya.cmds as mc
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(guides)
reload(bwsc)
reload(builder)


class GuidesTabUI(QtWidgets.QWidget):

    FILE_FILTER = "Maya (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);; All Files(*.*)"

    selected_filter = "Maya (*.ma *.mb)"

    def __init__(self, parent):

        super(GuidesTabUI, self).__init__(parent)

        self.parent_inst = parent

        # create ui elements
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create controls for the window"""
        
        self.open_builder_btn = QtWidgets.QPushButton("Open Builder")

        # create list widget to select module to be used
        self.list_wdg = QtWidgets.QListWidget()
        self.list_wdg.setCurrentRow(0)
        self.list_wdg.setMaximumHeight(300)

    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 10, 5, 5)

        main_layout.addWidget(self.open_builder_btn)
        main_layout.addWidget(self.list_wdg)

        main_layout.addSpacing(10)
        #main_layout.addWidget(self.save_btn)

        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        self.open_builder_btn.clicked.connect(self.open_builder)
        
    ###############
    # SLOTS START #
    ###############
    def simple_print(self):
        print "yuuh"

    def open_builder(self):
        #builder.BuilderUI(self)
        builder.show(self)



    #############
    # SLOTS END #
    #############
