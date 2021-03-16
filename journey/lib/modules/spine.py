"""
module containing foot setup.
create a three chain setup

NOTE: inherit set_base and set_prefix from Module class

TODO: parent stuff to correct module group
"""
import pymel.core as pm
import maya.OpenMaya as om
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.utils.kinematics as kine
import journey.lib.space_switcher as space
import journey.lib.layout as lo
reload(ctrl)
reload(tools)
reload(kine)
reload(lo)
reload(space)
import journey.lib.layout as lo


class Spine(lo.Module):
    def __init__(self,
                 driven,
                 stretch=True,
                 com=True,
                 prefix='new',
                 scale=1.0,
                 base_rig=None
                 ):
        self.CLASS_NAME = self.__class__.__name__
        self.driven = driven
        self.stretch = stretch
        self.com = com
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

    def create(self):
        # create module from parent class
        super(Spine, self).create_structure()

        self.offset_joint = pm.listRelatives(self.driven[0], parent=True)
        if self.offset_joint:
            pm.delete(pm.parentConstraint(self.offset_joint, self.joints_offset_grp, mo=0))

        spline = kine.Spline(self.driven, rot_to=False, preserve_vol=False, prefix=self.prefix,
                             scale=self.scale, rig_module=self.get_instance())
        spline.create()
        spline.end_bind_ctrl.set_shape_scale(scale=[1, 0.7, 1])
        spline.start_bind_ctrl.set_shape_scale(scale=[1.1, 0.7, 1.1])
        spline.twist()

        if self.stretch:
            spline.stretch()

        fk_spine = ctrl.Control(prefix=self.prefix + 'FK',
                                scale=self.scale * 0.9,
                                shape='circleY')
        fk_spine.create()
        pm.delete(pm.parentConstraint(spline.end_bind_ctrl.get_ctrl(), spline.start_bind_ctrl.get_ctrl(),
                                      fk_spine.get_offset()))

        tools.matrix_constraint(fk_spine.get_ctrl(), spline.end_bind_ctrl.get_offset())

        if self.com:
            com = ctrl.Control(prefix=self.prefix + 'COM',
                               trans_to=self.driven[0],
                               scale=self.scale * 1.2,
                               shape='diamondY')
            com.create()
            com.movable_pivot()
            com.set_constraint(fk_spine.get_offset())
            com.set_constraint(spline.start_bind_ctrl.get_offset())

            pm.parent(com.get_offset(), self.controls_grp)

