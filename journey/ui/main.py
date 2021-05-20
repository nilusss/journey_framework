from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import webbrowser
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import journey.ui.setup_tab as setup_tab
import journey.ui.guides_tab as guides_tab
import journey.ui.skinning_tab as skinning_tab
import journey.presets as presets
import journey.lib.serialization as se
import pymel.core as pm
import maya.cmds as mc
import json
import os
import sys
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil
reload(guides)
reload(se)
reload(bwsc)
reload(setup_tab)
reload(guides_tab)
reload(skinning_tab)

# load plugins
pm.loadPlugin('quatNodes', qt=True)
pm.loadPlugin('matrixNodes', qt=True)


def get_maya_window():
    """
    Return maya main window as a python object
    """
    ptr = mui.MQtUtil.mainWindow()  # ptr = pointer
    return wrapInstance(long(ptr), QtWidgets.QWidget)


def restore(settings):
    finfo = QtCore.QFileInfo(settings.fileName())
    if finfo.exists() and finfo.isFile():
        for w in QtWidgets.qApp.allWidgets():
            mo = w.metaObject()
            if w.objectName() and not w.objectName().startswith("qt_"):
                settings.beginGroup(w.objectName())
                for i in range( mo.propertyCount(), mo.propertyOffset()-1, -1):
                    prop = mo.property(i)
                    if prop.isWritable():
                        name = prop.name()
                        val = settings.value(name, w.property(name))
                        if str(val).isdigit():
                            val = int(val)
                        w.setProperty(name, val)
                settings.endGroup()


def save(settings):
    for w in QtWidgets.qApp.allWidgets():
        mo = w.metaObject()
        if w.objectName() and not w.objectName().startswith("qt_"):
            settings.beginGroup(w.objectName())
            for i in range(mo.propertyCount()):
                prop = mo.property(i)
                name = prop.name()
                if prop.isWritable():
                    settings.setValue(name, w.property(name))
            settings.endGroup()


class JourneyMainUI(QtWidgets.QWidget, se.Serialize):

    LOAD_PRESET_FILTERS = "JSON (*.json)"
    selected_load_preset_filter = "JSON (*.json)"

    UI_NAME = "JourneyMainUI"
    UI_TITLE = "JOURNEY"

    character_name = 'new'
    ui_instance = None

    @classmethod
    def display(cls):
        if cls.ui_instance:
            cls.ui_instance.show_ws_control()
        else:
            cls.ui_instance = cls()

    @classmethod
    def get_ws_control_name(cls):
        return "{}WorkspaceControl".format(cls.__name__)

    @classmethod
    def get_ui_script(cls):
        module_name = cls.__module__
        if module_name == "__main__":
            module_name = cls.module_name_override

        ui_script = "import journey.ui.main as maui\nreload(maui)\nmaui.JourneyMainUI.display()"

        # ui_script = "from {0} import {1}\n{1}.display()".format(module_name, cls.__name__)
        return ui_script

    def __init__(self):
        super(JourneyMainUI, self).__init__()

        self.setObjectName(self.__class__.UI_NAME)

        self.setMinimumSize(200, 100)
        self.loaded_file = ''

        # self.setWindowFlags(QtCore.Qt.Tool)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Delete window when it's closed to free resources

        # create ui elements
        self.create_menu()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_ws_control()
        #self.temp_load_preset()  # TODO: REMOVE THIS LINE AND FUNCTION WHEN DONE TESTING

    def create_menu(self):
        # Create a menubar
        self.main_menu = QtWidgets.QMenuBar(self)

        # File menu section
        self.file_menu = self.main_menu.addMenu("File")
        self.new_m = QtWidgets.QAction('New Preset', self)
        self.load_preset_m = QtWidgets.QAction('Load Preset...', self)
        self.save_m = QtWidgets.QAction('Save Preset', self)
        self.save_as_m = QtWidgets.QAction('Save As...', self)
        self.restore_window_m = QtWidgets.QAction("Restore Window...", self)

        self.file_menu.addAction(self.new_m)
        self.file_menu.addAction(self.load_preset_m)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.save_m)
        self.file_menu.addAction(self.save_as_m)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.restore_window_m)

        # Edit menu section
        self.edit_menu = self.main_menu.addMenu("Edit")
        self.space_switch_m = QtWidgets.QAction('Space Switcher...', self)

        self.edit_menu.addAction(self.space_switch_m)

        # Help menu section
        self.help_menu_m = self.main_menu.addMenu("Help")
        self.about_m = QtWidgets.QAction('About...', self)
        self.author_m = QtWidgets.QAction('Author...', self)
        self.help_m = QtWidgets.QAction('Help...', self)

        self.help_menu_m.addAction(self.about_m)
        self.help_menu_m.addAction(self.author_m)
        self.help_menu_m.addSeparator()
        self.help_menu_m.addAction(self.help_m)

    def create_widgets(self):
        """Create controls for the window"""
        self.loaded_file_label = QtWidgets.QLabel('File: ' + self.loaded_file,
                                                  wordWrap=True,
                                                  alignment=QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        # create tab widget
        self.tab_widget = QtWidgets.QTabWidget()

        self.config_tab = setup_tab.SetupTabUI(self)
        self.guides_tab = guides_tab.GuidesTabUI(self)
        self.skinning_tab = skinning_tab.SkinningTabUI(self)

        self.tab_widget.addTab(self.config_tab, "Config")
        self.tab_widget.addTab(self.guides_tab, "Guides")
        self.tab_widget.addTab(self.skinning_tab, "Skinning")

        # get widget tab instances and reassign to variables
        self.config_tab = self.tab_widget.widget(0)
        self.guides_tab = self.tab_widget.widget(1)
        self.skinning_tab = self.tab_widget.widget(2)

        self.warning_label = QtWidgets.QLabel("ATT: Guides created when this window is closed will not be registered. "
                                              "Having guides in your scene when opening "
                                              "the editor will also not be registered",
                                              wordWrap=True,
                                              alignment=QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)


        #self.setWindowTitle("tab demo")
        # self.tab_widget.addTab("Config")
        # self.tab_widget.addTab("Guides")

    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        # create menu layout
        menu_layout = QtWidgets.QGridLayout()
        menu_layout.addWidget(self.main_menu, 0, 0)
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        menu_layout.addWidget(line)

        # loaded file layout
        lf_layout = QtWidgets.QGridLayout()
        lf_layout.setContentsMargins(2, 2, 2, 2)
        lf_layout.addWidget(self.loaded_file_label)

        # warning layout
        warning_layout = QtWidgets.QGridLayout()
        warning_layout.setContentsMargins(2, 2, 2, 2)
        #warning_layout.addWidget(self.warning_label)

        # tab layout
        tab_layout = QtWidgets.QHBoxLayout()
        tab_layout.setContentsMargins(2, 2, 2, 2)
        tab_layout.addWidget(self.tab_widget)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        main_layout.addLayout(menu_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(lf_layout)
        main_layout.addLayout(tab_layout)

        main_layout.addSpacing(10)
        main_layout.addLayout(warning_layout)

        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        # menu signals
        self.load_preset_m.triggered.connect(self.menu_load_preset)
        self.new_m.triggered.connect(self.menu_new)
        self.save_m.triggered.connect(self.menu_save)
        self.save_as_m.triggered.connect(self.menu_save_as)
        self.restore_window_m.triggered.connect(self.menu_restore_window)
        self.about_m.triggered.connect(self.menu_about)
        self.author_m.triggered.connect(self.menu_author)
        self.help_m.triggered.connect(self.menu_help)

    def create_ws_control(self):
        self.ws_control_inst = bwsc.BaseWorkspaceControl(self.get_ws_control_name())
        if self.ws_control_inst.exists():
            self.ws_control_inst.restore(self)
        else:
            self.ws_control_inst.create(self.UI_TITLE, self, ui_script=self.get_ui_script())

    def show_ws_control(self):
        self.ws_control_inst.set_visible(True)

    def showEvent(self, e):
        self.set_ui_title()

    def set_ui_title(self):
        self.config_tab.char_name_le.setText(self.character_name)
        if self.ws_control_inst.is_floating():
            self.ws_control_inst.set_label(self.character_name + " - " + self.UI_TITLE)
        else:
            self.ws_control_inst.set_label(self.UI_TITLE)

    ###############
    # SLOTS START #
    ###############
    def clear_ui(self):
        self.set_loaded_file(None)
        self.config_tab.char_name_le.setText('')
        self.config_tab.filepath_le.setText('')
        self.config_tab.filepath_builder_le.setText('')
        self.config_tab.filepath_skin_le.setText('')
        self.guides_tab.list_wdg.clear()
        self.config_tab.set_optionvars()
        pm.select(None)

    def menu_new(self):
        confirm = pm.confirmDialog(title='Confirm', message='Are you sure?', button=['Yes', 'No'],
                                   defaultButton='Yes', cancelButton='No', dismissString='No')
        if confirm == 'Yes':
            self.clear_ui()

    def get_json_values(self):
        json_value = {
            "char_name": self.config_tab.char_name_le.text(),
            "model_file": self.config_tab.filepath_le.text(),
            "builder_file": self.config_tab.filepath_builder_le.text(),
            "skin_weights_dir": self.config_tab.filepath_skin_le.text(),
        }
        print json_value
        return json_value

    def save_dialog(self, json_value):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save Guides",
                                                         "",
                                                         "JSON (*.json)",
                                                         "JSON (*.json)")
        if filename[0]:
            with open(filename[0], 'w') as json_file:
                json.dump(json_value, json_file)
                # save(self.settings)
                # print self.settings
            self.set_loaded_file(filename[0])

    def menu_save(self):
        json_value = self.get_json_values()
        if self.loaded_file:
            with open(self.loaded_file, 'w') as json_file:
                json.dump(json_value, json_file)
        else:
            self.save_dialog(json_value)

    def menu_save_as(self):
        json_value = self.get_json_values()
        self.save_dialog(json_value)

    def set_loaded_file(self, file):
        def set_file(file):
            self.loaded_file = file
            self.loaded_file_name = file.split('/')[-1]
            self.loaded_file_label.setText('File: ' + self.loaded_file)
        if file:
            set_file(file)
        else:
            set_file('')

    def menu_load_preset(self):
        os.path.dirname(presets.__file__)
        filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File",
                                                                          "",
                                                                          self.LOAD_PRESET_FILTERS,
                                                                          self.selected_load_preset_filter)
        self.load_preset(filepath)


    def temp_load_preset(self):
        """TODO: REMOVE FUNCTION LATER. ONLY USED FOR LOADING A PRESET WHEN SHOWING UI"""
        filepath = 'C:/Users/nilas/Documents/maya/2019/modules/journey_framework/journey/presets/bingbong.json'
        self.load_preset(filepath)
        
    
    def load_preset(self, filepath):
        if filepath:
            with open(filepath, 'r') as json_file:
                jdata = json.load(json_file)
                try:
                    self.guides_tab.check_if_guides_exists()
                    self.config_tab.char_name_le.setText(jdata['char_name'])
                    self.character_name = jdata['char_name']
                    try:
                        self.config_tab.filepath_le.setText(jdata['model_file'])
                    except:
                        pass
                    try:
                        self.config_tab.filepath_builder_le.setText(jdata['builder_file'])
                    except:
                        pass
                    try:
                        self.config_tab.filepath_skin_le.setText(jdata['skin_weights_dir'])
                    except:
                        pass
                    self.set_loaded_file(filepath)
                except:
                    pm.confirmDialog(title='File Error!', message='Loaded file is not a valid preset file',
                                     button=['Ok'], defaultButton='Ok')

    def menu_restore_window(self):
        confirm = pm.confirmDialog(title='Confirm', message='Are you sure?', button=['Yes', 'No'],
                                   defaultButton='Yes', cancelButton='No', dismissString='No')
        if confirm == 'Yes':
            d = show()

    def menu_about(self):
        url = 'https://github.com/nilusss/journey_framework#readme'
        webbrowser.open(url, new=0, autoraise=True)

    def menu_author(self):
        url = 'https://github.com/nilusss'
        webbrowser.open(url, new=0, autoraise=True)

    def menu_help(self):
        url = 'https://github.com/nilusss/journey_framework/wiki'
        webbrowser.open(url, new=0, autoraise=True)

    #############
    # SLOTS END #
    #############


def show():
    try:
        d.setParent(None)
        d.deleteLater()
    except:
        pass
    ws_control_name = JourneyMainUI.get_ws_control_name()
    if pm.window(ws_control_name, exists=True):
        pm.deleteUI(ws_control_name)

    d = JourneyMainUI()
    return d
