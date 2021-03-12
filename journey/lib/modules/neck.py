"""
module containing finger setup.
used for: Metacarpal (Fingers), Metatarsal (Toes)

NOTE: inherit set_base and set_prefix from Module class
NOTE: when attaching finger joints, only use the base joint of the finger and attach meta ctrl in the right order

TODO: loop through every finger give a proxy controls controller with fk ik switch \
TODO: \to put on every fk and ik controller for that specific finger
"""
import pymel.core as pm
import maya.OpenMaya as om
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.utils.kinematics as kine
import journey.lib.space_switcher as space
import journey.lib.layout as lo
from maya.cmds import DeleteHistory
reload(ctrl)
reload(tools)
reload(kine)
reload(lo)
reload(space)
import journey.lib.layout as lo


class Neck(lo.Module):
    def __init__(self,
                 driven,
                 stretch=True,
                 prefix='new',
                 scale=1.0,
                 base_rig=None
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        self.stretch = stretch
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

    def create(self, *args):
        # create module from parent class
        super(Neck, self).create_structure()

        self.offset_joint = pm.listRelatives(self.driven[0], parent=True)
        if self.offset_joint:
            pm.delete(pm.parentConstraint(self.offset_joint, self.joints_offset_grp, mo=0))

        spline = kine.Spline(self.driven, rot_to=True, rot_shape=False, preserve_vol=False, prefix=self.prefix,
                             scale=self.scale, rig_module=self.get_instance())
        spline.create()
        # spline.end_bind_ctrl.set_shape_scale(scale=[1, 0.7, 1])
        # spline.start_bind_ctrl.set_shape_scale(scale=[1.1, 0.7, 1.1])
        spline.twist()
        pm.select(None)
        spline.end_bind_ctrl.set_shape('cube')

        if self.stretch:
            spline.stretch()

        head_ss = space.SpaceSwitcherLogic(spline.start_bind_ctrl.get_ctrl(), spline.end_bind_ctrl.get_ctrl(),
                                           split=True)
        head_ss.setup_switcher()
        head_ss.set_space(spline.start_bind_ctrl.get_ctrl())
