import sys
import json
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import maya.OpenMayaUI as mui
import journey.ui.builder as builder_ui
import journey.lib.guides as guides
if sys.version_info.major >= 3:
    from importlib import reload

import fnmatch
import pymel.core as pm
import maya.cmds as mc
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(builder_ui)
reload(guides)


class GuidesTabUI(QtWidgets.QWidget):
    """TODO: ADD ABILITY TO DELETE THE LOADED PRESET. THIS WILL DELETE THE PRESET FROM DISC, BUT SHOULD KEEP CURRENT VALUES
     TODO: ADD A LINE SHOWING WHAT FILE HAS BEEN LOADED. AT THE TOP OF THE WINDOW"""

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
        self.get_guides()

    def create_widgets(self):
        """Create controls for the window"""
        
        self.open_builder_btn = QtWidgets.QPushButton("Open Builder")

        # create list widget to select module to be used
        self.list_wdg = QtWidgets.QListWidget()
        self.list_wdg.setCurrentRow(0)
        self.list_wdg.setMaximumHeight(300)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.save_guides_btn = QtWidgets.QPushButton("Save Guides")

        self.settings_label = QtWidgets.QLabel()
        self.dropdown_mirror_label = QtWidgets.QLabel("Mirror:")
        self.dropdown_mirror_menu = QtWidgets.QComboBox()
        self.dropdown_mirror_menu.addItems(['off', 'on'])
        self.dropdown_ant_label = QtWidgets.QLabel("Display Annotation:")
        self.dropdown_ant_menu = QtWidgets.QComboBox()
        self.dropdown_ant_menu.addItems(['off', 'on'])
        self.settings_delete_btn = QtWidgets.QPushButton('Delete guide')

        self.rig_guides_btn = QtWidgets.QPushButton('Rig Guides')


    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        self.settings_frame = QtWidgets.QFrame()
        settings_layout = QtWidgets.QGridLayout()
        settings_layout.addWidget(self.settings_label, 0, 0)
        settings_layout.addWidget(self.dropdown_mirror_label, 1, 0)
        settings_layout.addWidget(self.dropdown_mirror_menu, 1, 1)
        settings_layout.addWidget(self.dropdown_ant_label, 2, 0)
        settings_layout.addWidget(self.dropdown_ant_menu, 2, 1)
        settings_layout.addWidget(self.settings_delete_btn, 3, 0)
        self.settings_frame.setLayout(settings_layout)

        refresh_layout = QtWidgets.QGridLayout()
        refresh_layout.addWidget(self.refresh_btn, 0, 0)
        refresh_layout.addWidget(self.save_guides_btn, 0, 1)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 10, 5, 5)

        main_layout.addWidget(self.open_builder_btn)
        main_layout.addSpacing(10)

        main_layout.addWidget(self.list_wdg)
        main_layout.addSpacing(10)
        main_layout.addLayout(refresh_layout)

        main_layout.addSpacing(10)
        main_layout.addWidget(self.settings_frame)
        self.settings_frame.hide()

        main_layout.setSpacing(10)
        main_layout.addWidget(self.rig_guides_btn)

        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        self.open_builder_btn.clicked.connect(self.open_builder)
        self.save_guides_btn.clicked.connect(self.save_guides)
        self.list_wdg.currentItemChanged.connect(self.on_change_item_selection)
        self.settings_delete_btn.clicked.connect(self.on_delete_guide)
        self.dropdown_mirror_menu.activated.connect(self.on_change_mirror)
        self.dropdown_ant_menu.activated.connect(self.on_change_ant)
        self.rig_guides_btn.clicked.connect(self.on_rig_guides)
        self.refresh_btn.clicked.connect(self.check_if_guides_exists)

    def get_mirror_state(self):
        return self.selected_guide_inst.base_ctrl.getAttr('mirror_enable')

    def get_ant_state(self):
        return self.selected_guide_inst.base_ctrl.getAttr('display_annotation')

    ###############
    # SLOTS START #
    ###############

    def on_rig_guides(self, skip_dialog=False):
        if pm.ls('Master___*'):
            if skip_dialog:
                confirm = 'Yes'
            else:
                confirm = pm.confirmDialog(title='Rig Guides', message='Rigging the guides will delete all guides '
                                                                       'in the scene.\n'
                                                                       'Do you want to continue? ',
                                           button=['Yes', 'No'], defaultButton='Yes',
                                           cancelButton='No', dismissString='No')
            if confirm == 'Yes':
                pm.undoInfo(openChunk=True)
                import journey.lib.builder as builder
                reload(builder)
                model_path = self.parent_inst.config_tab.filepath_le.text()
                skin_weights_dir = self.parent_inst.config_tab.filepath_skin_le.text()
                char_name = self.parent_inst.character_name
                if not model_path:
                    model_grp = pm.ls('*_TEMP_grp')
                l = builder.Builder(char_name=char_name, model_path=model_path, weights_path=skin_weights_dir).build()
                items = []
                for x in range(self.list_wdg.count()):
                    items.append(self.list_wdg.item(x))
                for item in items:
                    item_obj = item
                    object_row = self.list_wdg.row(item)
                    if item_obj:
                        item_obj = item_obj.data(QtCore.Qt.UserRole)
                        try:
                            item_obj.delete_guide()
                        except:
                            pass
                sel = pm.ls("*HIDOFFSET_GRP")
                try:
                    pm.delete(sel)
                except:
                    pass
                try:
                    pm.delete("MIRROR_GRP")
                except:
                    pass

                self.check_if_guides_exists()
                self.settings_frame.hide()
                pm.undoInfo(closeChunk=True)
                del l
        else:
            pm.warning("No guides in scene!")

    def on_change_mirror(self):
        state = self.dropdown_mirror_menu.currentIndex()
        if state:
            if self.selected_guide_inst:
                mc.undoInfo(openChunk=True, chunkName=self.selected_guide_inst.name + "_mirrorOn")
                self.selected_guide_inst.set_mirror(True)
                mc.undoInfo(closeChunk=True, chunkName=self.selected_guide_inst.name + "_mirrorOn")
        else:
            try:
                if self.selected_guide_inst:
                    mc.undoInfo(openChunk=True, chunkName=self.selected_guide_inst.name + "_mirrorOff")
                    self.selected_guide_inst.set_mirror(False)
                    mc.undoInfo(closeChunk=True, chunkName=self.selected_guide_inst.name + "_mirrorOff")
            except Exception as e:
                pm.warning('Cant mirror!' + str(e))

    def on_change_ant(self):
        state = self.dropdown_ant_menu.currentIndex()
        if state:
            if self.selected_guide_inst:
                mc.undoInfo(openChunk=True, chunkName=self.selected_guide_inst.name + "_antOn")
                self.selected_guide_inst.base_ctrl.attr('display_annotation').set(1)
                mc.undoInfo(closeChunk=True, chunkName=self.selected_guide_inst.name + "_antOn")
        else:
            if self.selected_guide_inst:
                mc.undoInfo(openChunk=True, chunkName=self.selected_guide_inst.name + "_antOff")
                self.selected_guide_inst.base_ctrl.attr('display_annotation').set(0)
                mc.undoInfo(closeChunk=True, chunkName=self.selected_guide_inst.name + "_antOff")

    def on_change_selection_in_viewport(self):
        # print( "from viewport")
        sel_list = pm.ls(sl=True)
        if sel_list:
            for item in sel_list:
                if pm.objExists(item):
                    if sys.version_info.major >= 3:
                        for list_index in range(self.list_wdg.count()):
                            print (list_index)
                            # get guide object stored in the QtListWidgetItem
                            if self.list_wdg.item(list_index).data(QtCore.Qt.UserRole).base_ctrl == item:
                                self.list_wdg.setCurrentItem(self.list_wdg.item(list_index))
                                self.selected_guide_inst = self.list_wdg.currentItem().data(QtCore.Qt.UserRole)
                                self.change_settings_panel()
                    else:
                        for list_index in xrange(self.list_wdg.count()):
                            # get guide object stored in the QtListWidgetItem
                            if self.list_wdg.item(list_index).data(QtCore.Qt.UserRole).base_ctrl == item:
                                self.list_wdg.setCurrentItem(self.list_wdg.item(list_index))
                                self.selected_guide_inst = self.list_wdg.currentItem().data(QtCore.Qt.UserRole)
                                self.change_settings_panel()
        else:
            self.list_wdg.clearSelection()
            self.selected_guide_inst = ''
            pm.select(clear=True)
            self.settings_frame.hide()

    def on_change_item_selection(self):
        # print( "from UI")
        get_sel = ''
        sel = pm.ls(sl=True)
        if not sel:
            pass
            #self.check_if_guides_exists()
        try:
            get_sel = self.list_wdg.currentItem().data(QtCore.Qt.UserRole).base_ctrl
            # print( get_sel)
        except:
            pass
        if pm.objExists(get_sel):
            # print( "got object")
            pm.select(get_sel)
            self.selected_guide_inst = self.list_wdg.currentItem().data(QtCore.Qt.UserRole)
            self.change_settings_panel()
        # else:
            # self.check_if_guides_exists()
            # print( "cant find")
            # pm.select(clear=True)
            # selected_list = self.list_wdg.selectionModel().selectedIndexes()
            # for index in selected_list:
            #     self.list_wdg.model().removeRow(index.row())
            # self.selected_guide_inst = ''

    def check_if_guides_exists(self):
        # print( "## CHECK IF GUIDES EXISTS ##")
        items = []
        for x in range(self.list_wdg.count()):
            items.append(self.list_wdg.item(x))
        for item in items:
            item_obj = item
            object_row = self.list_wdg.row(item)
            if item_obj:
                item_obj = item_obj.data(QtCore.Qt.UserRole).base_ctrl
            else:
                self.list_wdg.takeItem(object_row)
            if not item_obj:
                item_obj = ''
            if not pm.objExists(item_obj):
                # print( "OBJECT DOESNT EXIST")
                self.list_wdg.takeItem(object_row)
            #self.list_wdg.takeItem(index)
        #self.get_guides()

        # print( "## DONE ##")

    def on_delete_guide(self):
        if self.selected_guide_inst:
            self.selected_guide_inst.delete_guide()
            # print( "SELECTED INST " + str(self.selected_guide_inst))
            object_row = self.list_wdg.row(self.list_wdg.currentItem())
            del self.selected_guide_inst
            self.list_wdg.takeItem(object_row)


    def open_builder(self):
        #builder.BuilderUI(self)
        build_ui = builder_ui.show(self)

    def save_guides(self):
        guide_dict_list = []

        if self.list_wdg.count():
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save Guides",
                                                             "",
                                                             "JSON (*.json)",
                                                             "JSON (*.json)")
            # print( filename[0])
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
                                        get_parent = pm.listRelatives(c.name(), parent=True)[0]
                                        # print( get_parent)
                                        if "MIRROR" not in get_parent.name():
                                            modules.append(c)
                                            # print( modules)
                    for i, module in enumerate(modules):
                        custom_name = pm.PyNode(module).getAttr('custom_name')
                        # print( custom_name)
                        item_obj = ''
                        try:
                            item_obj = self.list_wdg.findItems(custom_name, QtCore.Qt.MatchExactly)[0].data(QtCore.Qt.UserRole)
                            # print( item_obj)
                        except:
                            pass
                        try:
                            if pm.objExists(item_obj.base_ctrl):
                                obj_to_dict = item_obj.serialize()
                                # print( obj_to_dict)
                                guide_dict_list.append(obj_to_dict)
                        except:
                            raise

                    #json_write = json.dumps(guide_dict_list, )
                    json.dump(guide_dict_list, json_file)
                    #jdata = json.load(json_file)
                    # print( 'writing to json')
        else:
            pm.warning('No guides in scene to save!')

    def change_settings_panel(self):
        if 'root' not in self.list_wdg.currentItem().text():
            self.settings_frame.show()
        else:
            self.settings_frame.hide()
        try:
            self.settings_label.setText('Settings for: ' + self.list_wdg.currentItem().text())
            self.selected_guide_inst = self.list_wdg.currentItem().data(QtCore.Qt.UserRole)
            if self.get_mirror_state():
                mir_index = self.dropdown_mirror_menu.findText("on", QtCore.Qt.MatchFixedString)
                # print( "mirror is on")

            else:
                # print( "mirror is off")
                mir_index = self.dropdown_mirror_menu.findText("off", QtCore.Qt.MatchFixedString)
            try:
                if mir_index >= 0:
                    self.dropdown_mirror_menu.setCurrentIndex(mir_index)
            except:
                pass
            if self.get_ant_state():
                ant_index = self.dropdown_ant_menu.findText("on", QtCore.Qt.MatchFixedString)
                # print( "ant is on")

            else:
                print("ant is off")
                ant_index = self.dropdown_ant_menu.findText("off", QtCore.Qt.MatchFixedString)
            try:
                if ant_index >= 0:
                    self.dropdown_ant_menu.setCurrentIndex(ant_index)
            except:
                pass
        except:
            pass

    #############
    # SLOTS END #
    #############

    def get_guides(self):
        guide_objects = guides.get_guides_in_scene()

        for obj in guide_objects:
            try:
                print("IN")
                guide_list_item = QtWidgets.QListWidgetItem()
                guide_list_item.setData(QtCore.Qt.UserRole, obj)
                guide_list_item.setText(obj.prefix)
                self.list_wdg.addItem(guide_list_item)
            except Exception as e:
                print(str(e))
