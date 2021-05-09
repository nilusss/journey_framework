import json
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import maya.OpenMayaUI as mui
import journey.ui.builder as builder
import fnmatch
import pymel.core as pm
import maya.cmds as mc
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(builder)


class GuidesTabUI(QtWidgets.QWidget):

    FILE_FILTER = "Maya (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);; All Files(*.*)"

    selected_filter = "Maya (*.ma *.mb)"

    def __init__(self, parent):
        self.sel_change_job_id = 0

        super(GuidesTabUI, self).__init__(parent)

        #self.setObjectName(self.__class__.UI_NAME)

        self.parent_inst = parent

        self.sel_change_job_id = pm.scriptJob(event=("SelectionChanged", self.on_change_selection_in_viewport),
                                              parent=self.parent_inst.__class__.UI_NAME, replacePrevious=True,
                                              killWithScene=True, compressUndo=True, force=True)

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
        self.save_guides_btn = QtWidgets.QPushButton("Save Guides")

        self.settings_label = QtWidgets.QLabel()
        self.settings_delete_btn = QtWidgets.QPushButton('Delete')


    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        self.settings_frame = QtWidgets.QFrame()
        settings_layout = QtWidgets.QHBoxLayout()
        settings_layout.addWidget(self.settings_label)
        self.settings_frame.setLayout(settings_layout)
        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 10, 5, 5)

        main_layout.addWidget(self.open_builder_btn)
        main_layout.addSpacing(10)

        main_layout.addWidget(self.list_wdg)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.save_guides_btn)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.settings_frame)
        self.settings_frame.hide()

        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        self.open_builder_btn.clicked.connect(self.open_builder)
        self.save_guides_btn.clicked.connect(self.save_guides)
        self.list_wdg.itemSelectionChanged.connect(self.on_change_item_selection)

    ###############
    # SLOTS START #
    ###############
    def simple_print(self):
        print "yuuh"

    def on_change_selection_in_viewport(self):
        sel_list = pm.ls(sl=True)
        if sel_list:
            for item in sel_list:
                if pm.objExists(item):
                    for list_index in xrange(self.list_wdg.count()):
                        # get guide object stored in the QtListWidgetItem
                        if self.list_wdg.item(list_index).data(QtCore.Qt.UserRole).base_ctrl == item:
                            self.list_wdg.setCurrentItem(self.list_wdg.item(list_index))
        else:
            self.list_wdg.clearSelection()
            pm.select(clear=True)
            self.settings_frame.hide()

    def on_change_item_selection(self):
        self.change_settings_panel()
        get_sel = self.list_wdg.currentItem().data(QtCore.Qt.UserRole).base_ctrl
        viewport_sel = pm.ls(sl=True)
        if pm.objExists(get_sel):
            pm.select(get_sel)
        else:
            pm.select(clear=True)

    def open_builder(self):
        #builder.BuilderUI(self)
        builder_ui = builder.show(self)

    def save_guides(self):
        guide_dict_list = []

        if self.list_wdg.count():
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save Guides",
                                                             "",
                                                             "JSON (*.json)",
                                                             "JSON (*.json)")
            print filename[0]
            if filename[0]:
                with open(filename[0], 'w') as json_file:
                    get_modules = pm.ls(assemblies=True)
                    # get correct module hierarchy
                    modules = []

                    for dag in get_modules:
                        if '_base' in dag.name():
                            modules.append(dag)
                            for c in pm.listRelatives(dag, ad=True, type='transform')[::-1]:
                                match = fnmatch.fnmatch(c.name(), '*_base')
                                if match:
                                    if 'HIDDEN' not in c.name():
                                        modules.append(c)
                    for i, module in enumerate(modules):
                        item_obj = self.list_wdg.item(i).data(QtCore.Qt.UserRole)
                        if item_obj.base_ctrl == module:
                            obj_to_dict = item_obj.serialize()
                            guide_dict_list.append(obj_to_dict)

                    #json_write = json.dumps(guide_dict_list, )
                    json.dump(guide_dict_list, json_file)
                    #jdata = json.load(json_file)
                    print 'writing to json'
        else:
            pm.warning('No guides in scene to save!')

    def change_settings_panel(self):
        self.settings_frame.show()
        try:
            self.settings_label.setText('Settings for: ' + self.list_wdg.currentItem().text())
        except:
            pass






    #############
    # SLOTS END #
    #############
