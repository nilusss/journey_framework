# from journey.vendor.Qt import QtWidgets, QtGui, QtCore
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance
import journey.lib.guides as guides
import maya.OpenMayaUI as mui
import pymel.core as pm
import maya.cmds as mc
import traceback
from functools import partial
# import sip
reload(guides)
"""
TODO: make dialog a dockable window
"""



def get_maya_window():
    """
    Return maya main window as a python object
    """
    ptr = mui.MQtUtil.mainWindow()  # ptr = pointer
    return wrapInstance(long(ptr), QtWidgets.QWidget)


def all_members(a_class):
    try:
        # Try getting all relevant classes in method-resolution order
        mro = list(a_class.__mro__)
    except AttributeError:
        # If a class has no _ _mro_ _, then it's a classic class
        def getmro(a_class, recurse):
            mro = [a_class]
            for base in a_class.__bases__: mro.extend(recurse(base, recurse))
            return mro
        mro = getmro(a_class, getmro)
    mro.reverse()
    members = {}
    for someClass in mro: members.update(vars(someClass))
    return members


class BuilderUI(QtWidgets.QDialog):
    def __init__(self, parent):

        super(BuilderUI, self).__init__(parent)

        self.parent_inst = parent

        # define empty variables
        self.draw_classes = {}  # fetch all draw classes in guides modules
        self.buttons = []  # list of all buttons created

        self.setWindowTitle("JOURNEY Builder")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Delete window when it's closed to free resources

        self.create_controls()
        self.create_layout()
        self.create_connections()
        # set line edit prefix text
        self.change_selection()

    def create_controls(self):
        """Create controls for the window"""
        # get all draw classes from guides module to make corresponding buttons
        self.draw_classes = dict([(name, cls) for name, cls in guides.__dict__.items()
                                  if isinstance(cls, type) and "Draw" in name])
        self.draw_classes.pop('DrawMaster')


        # draw button
        self.draw_btn = QtWidgets.QPushButton("Draw module")

        # create guide position radio buttons
        self.radiobutton_01 = QtWidgets.QRadioButton("Left")
        self.radiobutton_01.side = "l_"

        self.radiobutton_02 = QtWidgets.QRadioButton("Center")
        self.radiobutton_02.side = "c_"

        self.radiobutton_03 = QtWidgets.QRadioButton("Right")
        self.radiobutton_03.side = "r_"

        # set prefix input field and corresponding label
        self.line_edit = QtWidgets.QLineEdit("prefix")
        self.prefix_label = QtWidgets.QLabel()
        self.prefix_label.setText("Prefix")
        self.prefix_label.setBuddy(self.line_edit)

        # create list widget to select module to be used
        self.list_wdg = QtWidgets.QListWidget()
        self.list_wdg.addItems(self.draw_classes.keys())
        self.list_wdg.setCurrentRow(0)
        self.list_wdg.setMaximumHeight(300)

        self.settings_label = QtWidgets.QLabel("Settings for: ")
        self.amount_label = QtWidgets.QLabel("Joint Amount: ")
        self.amount_le = QtWidgets.QLineEdit("4")


        self.class_for_amount = []
        for cls in self.draw_classes:
            # create "create" button for each module
            btn = QtWidgets.QPushButton("Create " + str(cls).replace("Draw", "") + " Guides")
            self.buttons.append(btn)

            # get variables for setting panel ## amount
            exec('gds = guides.{}'.format(cls))
            get_members = all_members(gds)
            for membr in get_members.keys():
                if 'amount' in membr:
                    self.class_for_amount.append(cls.replace('Draw', ''))


        print self.class_for_amount

    def create_layout(self):
        """Layout all the controls in corresponding layout"""
        self.settings_frame = QtWidgets.QFrame()
        settings_layout = QtWidgets.QGridLayout()
        settings_layout.addWidget(self.settings_label, 0, 0)
        self.settings_frame.setLayout(settings_layout)

        self.amount_frame = QtWidgets.QFrame()
        amount_layout = QtWidgets.QGridLayout()
        amount_layout.addWidget(self.amount_label, 1, 0)
        amount_layout.addWidget(self.amount_le, 1, 1)
        self.amount_frame.setLayout(amount_layout)


        """Settings panel done"""

        """Layout all the controls in corresponding layout"""
        radio_layout = QtWidgets.QHBoxLayout()
        radio_layout.setContentsMargins(5, 5, 5, 5)
        radio_layout.addWidget(self.radiobutton_01)
        radio_layout.addWidget(self.radiobutton_02)
        radio_layout.addWidget(self.radiobutton_03)

        # create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        main_layout.addWidget(QtWidgets.QLabel('Position:'))
        main_layout.addLayout(radio_layout)
        main_layout.addSpacing(10)

        main_layout.addWidget(self.prefix_label)
        main_layout.addWidget(self.line_edit)
        main_layout.addSpacing(10)
        main_layout.addWidget(QtWidgets.QLabel('Modules:'))
        main_layout.addWidget(self.list_wdg)
        main_layout.addWidget(self.settings_frame)
        main_layout.addWidget(self.amount_frame)
        self.settings_frame.hide()
        main_layout.addWidget(self.draw_btn)

        # for btn in self.buttons:
        #     main_layout.addWidget(btn)
        main_layout.setSpacing(5)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_connections(self):
        """Create signals and slots for buttons"""
        self.list_wdg.itemSelectionChanged.connect(self.on_list_change_prefix)
        self.draw_btn.clicked.connect(self.on_draw_pressed)

    def draw_guide(self, guide_type, prefix):
        try:
            mc.undoInfo(openChunk=True, chunkName="drawguide")
            if not pm.ls('Master___*'):
                if guide_type not in 'DrawMaster':
                    master = guides.DrawMaster(prefix='c_root').draw()
                    try:
                        print "IN"
                        guide_list_item = QtWidgets.QListWidgetItem()
                        guide_list_item.setData(QtCore.Qt.UserRole, master)
                        guide_list_item.setText('c_root')
                        self.parent_inst.list_wdg.addItem(guide_list_item)
                    except Exception as e:
                        print str(e)
                    master.radius_ctrl.attr('ty').set(3)
                    pm.select(master.controllers[0])
            a = prefix

            if self.has_amount:
                print 'ass'
                try:
                    amount = int(self.amount_le.text())
                    exec('guide_am = guides.{0}(prefix=\'{1}\', amount={2}).draw()'.format(guide_type,
                                                                                               prefix,
                                                                                               amount))
                    return guide_am
                except Exception as e:
                    raise e
            else:
                print "bingonb"
            exec('guide = guides.{}(prefix=\'{}\').draw()'.format(guide_type, prefix))
            return guide
        except Exception as e:
            raise e
        finally:
            pass
            mc.undoInfo(closeChunk=True, chunkName="drawguide")

    ###############
    # SLOTS START #
    ###############

    def change_selection(self):
        prefix = self.list_wdg.currentItem().text().replace('Draw', '')
        self.line_edit.setText(prefix.lower())
        check_string = ['Spine', 'Master', 'Neck']
        if any(s in self.list_wdg.currentItem().text() for s in check_string):
            self.radiobutton_01.setChecked(False)
            self.radiobutton_02.setChecked(True)
            self.radiobutton_03.setChecked(False)
        else:
            self.radiobutton_01.setChecked(True)
            self.radiobutton_02.setChecked(False)
            self.radiobutton_03.setChecked(False)

        self.settings_frame.show()
        self.settings_label.setText('Settings for: ' + str(prefix))

        if any(x in prefix for x in self.class_for_amount):
            self.has_amount = True
            self.amount_frame.show()
        else:
            self.amount_frame.hide()
            self.has_amount = False


    def on_list_change_prefix(self):
        self.change_selection()

    def on_draw_pressed(self):
        side_value = ''
        for radio in [self.radiobutton_01, self.radiobutton_02, self.radiobutton_03]:
            if radio.isChecked():
                side_value = radio.side

        guide = self.list_wdg.currentItem().text()
        prefix = self.line_edit.text()
        returned_guide = self.draw_guide(guide, side_value + prefix)
        try:
            print "IN"
            guide_list_item = QtWidgets.QListWidgetItem()
            guide_list_item.setData(QtCore.Qt.UserRole, returned_guide)
            guide_list_item.setText(side_value + prefix)
            self.parent_inst.list_wdg.addItem(guide_list_item)
        except Exception as e:
            print str(e)

    #############
    # SLOTS END #
    #############

def show(parent=get_maya_window()):
    try:
        d.close()
    except:
        pass

    d = BuilderUI(parent=parent)
    d.show()
    return d