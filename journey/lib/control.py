"""
module for making curve controls
"""

import pymel.core as pm
import journey.lib.utils.shapes as shapes
import journey.lib.utils.tools as tools
from journey.lib.utils.tools import lock_channels, colors
import journey.lib.utils.color as color

reload(tools)
reload(shapes)


class Control:
    control_list = []

    def __init__(self,
                 prefix='new',
                 scale=1.0,
                 trans_to='',
                 rot_to='',
                 rot_shape=True,
                 parent='',
                 shape='circle',
                 channels=['s', 'v']):
        """Short text

        Desc

        Args:
            prefix (str): name for the controller
            scale (float, int): initial scale of the controller
            trans_to (str): object to translate the controller to
            rot_to (str): object to rotate the controller to
            rot_shape (bool): whether the controller shape should match the top transform node translation
            parent (str): object to parent the controller under
            shape (str): visual shape to give the controller. Usable names can be found under journey.lib.utils.shapes
        """
        Control.control_list.append(self)

        self.ctrl_object = None
        self.ctrl_offset = None
        self.prefix = prefix
        self.scale = scale
        self.trans_to = trans_to
        self.rot_to = rot_to
        self.rot_shape = rot_shape
        self.parent = parent
        self.shape = shape
        self.channels = channels

    def set_shape(self, shape):
        # exec("return_shape = shapes.{0}({1}, {2})".format(self.shape, self.scale, self.prefix + '_ctrl'))
        exec("return_shape = shapes.{0}(self.scale, self.prefix + '_ctrl')".format(self.shape))
        self.ctrl_object = return_shape

        return self.ctrl_object

    def get_shape(self):
        pass

    def set_parent(self):
        pass

    def set_color(self, ctrl_color=''):
        ctrl_color = ctrl_color.upper()
        [pm.setAttr(s + '.ove', 1) for s in self.ctrl_object.getShapes()]

        if self.prefix.startswith('l_'):
            [pm.setAttr(s + '.ovc', color.BLUE) for s in self.ctrl_object.getShapes()]
        elif self.prefix.startswith('r_'):
            [pm.setAttr(s + '.ovc', color.RED) for s in self.ctrl_object.getShapes()]
        else:
            [pm.setAttr(s + '.ovc', color.YELLOW) for s in self.ctrl_object.getShapes()]

        if ctrl_color:
            exec('clr_key = color.{0}'.format(ctrl_color))
            [pm.setAttr(s + '.ovc', clr_key) for s in self.ctrl_object.getShapes()]

    def set_channels(self, channels):
        attr = lock_channels(self.ctrl_object, channels)
        return attr

    def set_translation(self, *args):
        # translate control
        if pm.objExists(self.trans_to):
            pm.delete(pm.pointConstraint(self.trans_to, self.ctrl_offset))

    def set_rotation(self, *args):
        # rotate control
        if pm.objExists(self.rot_to):
            if not self.rot_shape:
                ctrl_shapes = self.ctrl_object.getShapes()
                loc = pm.spaceLocator()
                for shape in ctrl_shapes:
                    pm.parent(shape, loc, relative=1, shape=1)
                pm.delete(pm.orientConstraint(self.rot_to, self.ctrl_offset))
                pm.parent(loc, self.rot_to)
                pm.setAttr(loc + ".tx", 0)
                pm.setAttr(loc + ".ty", 0)
                pm.setAttr(loc + ".tz", 0)
                pm.makeIdentity(loc, apply=True, r=True, t=True)
                for shape in ctrl_shapes:
                    pm.parent(shape, self.ctrl_object[0], relative=1, shape=1)
                pm.delete(loc)
            else:
                pm.delete(pm.orientConstraint(self.rot_to, self.ctrl_offset))

    def create(self):
        # set controller shape
        self.set_shape(self.shape)

        # set offset group for controller and re-parent
        self.ctrl_offset = pm.group(n=self.prefix + '_offset_grp', em=1)
        pm.parent(self.ctrl_object, self.ctrl_offset)

        # parent offset group to parent if set
        if pm.objExists(self.parent):
            pm.parent(self.ctrl_offset, self.parent)

        self.set_color()
        self.set_translation()
        self.set_rotation()

        self.set_channels(self.channels)

    def get_ctrl(self, *args):
        return self.ctrl_object

    def get_offset(self, *args):
        return self.ctrl_offset
