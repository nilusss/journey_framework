"""
Base workspace control module
"""

from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance, getCppPointer
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import pymel.core as pm
import traceback
from functools import partial
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
from maya.OpenMayaUI import MQtUtil


class BaseWorkspaceControl(object):
    def __init__(self, name):
        self.name = name
        self.widget = None

    def create(self, label, widget, ui_script=None):
        pm.workspaceControl(self.name, label=label)

        if ui_script:
            pm.workspaceControl(self.name, e=True, uiScript=ui_script)

        self.add_widget_to_layout(widget)
        self.set_visible(True)

    def restore(self, widget):
        self.add_widget_to_layout(widget)

    def add_widget_to_layout(self, widget):
        if widget:
            self.widget = widget
            self.widget.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)

            ws_control_ptr = long(mui.MQtUtil.findControl(self.name))
            widget_ptr = long(getCppPointer(self.widget)[0])

            mui.MQtUtil.addWidgetToMayaLayout(widget_ptr, ws_control_ptr)

    def exists(self):
        return pm.workspaceControl(self.name, q=True, exists=True)

    def is_visible(self):
        return pm.workspaceControl(self.name, q=True, visible=True)

    def set_visible(self, visible):
        if visible:
            pm.workspaceControl(self.name, e=True, restore=True)
        else:
            pm.workspaceControl(self.name, e=True, visible=False)

    def set_label(self, label):
        pm.workspaceControl(self.name, e=True, label=label)

    def is_floating(self):
        return pm.workspaceControl(self.name, q=True, floating=True)

    def is_collapsed(self):
        return pm.workspaceControl(self.name, q=True, collapse=True)
