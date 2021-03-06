from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import journey.ui.base_ws_control as bwsc
import journey.ui.setup_tab as setup_tab
import journey.ui.guides_tab as guides_tab
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
"""
TODO: make dialog a dockable window
"""


def value_is_valid(val):
    if isinstance(val, QtGui.QPixmap):
        return not val.isNull()
    return True


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

        # self.setWindowFlags(QtCore.Qt.Tool)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Delete window when it's closed to free resources

        # create ui elements
        self.create_menu()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_ws_control()

        # self.settings = QtCore.QSettings("JourneyFramework", "JourneyFramework")
        # print(self.settings.fileName())
        # restore(self.settings)

    def create_menu(self):
        # Create a menubar
        self.main_menu = QtWidgets.QMenuBar(self)

        # File menu section
        self.file_menu = self.main_menu.addMenu("File")
        self.new_m = QtWidgets.QAction('New Preset', self)
        self.load_preset_m = QtWidgets.QAction('Load Preset...', self)
        self.save_m = QtWidgets.QAction('Save', self)
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
        self.about_m = QtWidgets.QAction('About', self)
        self.author_m = QtWidgets.QAction('Author', self)
        self.help_m = QtWidgets.QAction('Help...', self)

        self.help_menu_m.addAction(self.about_m)
        self.help_menu_m.addAction(self.author_m)
        self.help_menu_m.addSeparator()
        self.help_menu_m.addAction(self.help_m)

    def create_widgets(self):
        """Create controls for the window"""
        # create tab widget
        self.tab_widget = QtWidgets.QTabWidget()

        self.config_tab = setup_tab.SetupTabUI(self)
        self.guides_tab = guides_tab.GuidesTabUI(self)

        self.tab_widget.addTab(self.config_tab, "Config")
        self.tab_widget.addTab(self.guides_tab, "Guides")

        # get widget tab instances and reassign to variables
        self.config_tab = self.tab_widget.widget(0)
        self.guides_tab = self.tab_widget.widget(1)


        self.setWindowTitle("tab demo")
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

        # tab layout
        tab_layout = QtWidgets.QHBoxLayout()
        tab_layout.setContentsMargins(2, 2, 2, 2)
        tab_layout.addWidget(self.tab_widget)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        main_layout.addLayout(menu_layout)
        main_layout.addLayout(tab_layout)


        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        # menu signals
        self.load_preset_m.triggered.connect(self.menu_load_preset)
        self.new_m.triggered.connect(self.menu_new)
        self.save_m.triggered.connect(self.menu_save)
        self.restore_window_m.triggered.connect(self.menu_restore_window)


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

    # def closeEvent(self, event):
    #     save(self.settings)
    #     super().closeEvent(event)

    def set_ui_title(self):
        self.config_tab.char_name_le.setText(self.character_name)
        if self.ws_control_inst.is_floating():
            self.ws_control_inst.set_label(self.character_name + " - " + self.UI_TITLE)
        else:
            self.ws_control_inst.set_label(self.UI_TITLE)

    ###############
    # SLOTS START #
    ###############
    def simple_print(self):
        print "yuuh"

    def menu_new(self):
        confirm = pm.confirmDialog(title='Confirm', message='Are you sure?', button=['Yes', 'No'],
                                   defaultButton='Yes', cancelButton='No', dismissString='No')
        if confirm == 'Yes':

            result = pm.promptDialog(
                title='Character Name',
                message='Enter Name:',
                button=['OK'],
                defaultButton='OK')

            if result == 'OK':
                name = pm.promptDialog(query=True, text=True)
                #self.ws_control_inst.restore(self)
                if name:
                    self.character_name = name
                else:
                    pm.warning("No value entered!")

                self.set_ui_title()

    def menu_save(self):
        json_value = {
            "char_name": self.config_tab.char_name_le.text(),
            "model_file": self.config_tab.filepath_le.text(),
        }
        print json_value    
        p = os.path.dirname(presets.__file__)
        print p
        with open(p + "\{}.json".format(self.config_tab.get_character_name()), 'w') as json_file:
            json.dump(json_value, json_file)
        # save(self.settings)
        # print self.settings


    def menu_load_preset(self):
        filepath, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", os.path.dirname(presets.__file__),
                                                                          self.LOAD_PRESET_FILTERS,
                                                                          self.selected_load_preset_filter)
        if filepath:
            print filepath
            with open(filepath, 'r') as json_file:
                jdata = json.load(json_file)
                self.config_tab.char_name_le.setText(jdata['char_name'])
                self.config_tab.filepath_le.setText(jdata['model_file'])
                self.config_tab.filepath_le.setText(jdata['model_file'])

    
    def menu_restore_window(self):
        confirm = pm.confirmDialog(title='Confirm', message='Are you sure?', button=['Yes', 'No'],
                                   defaultButton='Yes', cancelButton='No', dismissString='No')
        if confirm == 'Yes':
            try:
                self.setParent(None)
                self.deleteLater()
            except:
                pass
            ws_control_name = self.get_ws_control_name()
            if pm.window(ws_control_name, exists=True):
                pm.deleteUI(ws_control_name)
            
            d = show()

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
    #d.show()
    return d
