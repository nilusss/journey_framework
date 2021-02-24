"""
module containing limp setup.
create a three chain setup

NOTE: inherit set_base and set_prefix from Module class
"""
import pymel.core as pm
import maya.OpenMaya as om
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.utils.kinematics as kine
import journey.lib.layout as lo
# reload(ctrl)
# reload(tools)
# reload(kine)
# reload(lo)
import journey.lib.layout as lo


class Limb(lo.Module):
    def __init__(self,
                 driven=[],
                 stretch=True,
                 joint_radius=0.4,
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):

        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        self.stretch = stretch
        self.joint_radius = joint_radius
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

        # init empty public variables

        # init Module class
        super(Limb, self).__init__(self.prefix, self.base_rig)
        print("init limb")

    def create(self, *args):
        # create module from parent class
        super(Limb, self).create_structure()

        offset_joint = pm.listRelatives(self.driven[0], parent=True)
        pm.delete(pm.parentConstraint(offset_joint, self.joints_offset_grp, mo=0))

        ik_joints = tools.joint_duplicate(self.driven, 'IK', offset_grp=self.joints_offset_grp)
        fk_joints = tools.joint_duplicate(self.driven, 'FK', offset_grp=self.joints_offset_grp)

        arm_ik = kine.IK(ik_joints, prefix=self.prefix, scale=self.scale, rig_module=self.get_instance())
        arm_ik.create()
        arm_ik.pole_vector()
        arm_fk = kine.FK(fk_joints, prefix=self.prefix, scale=self.scale, rig_module=self.get_instance())
        arm_fk.create()

        # setup stretch if argument is True
        if self.stretch:
            arm_ik.stretch()

        blend_ctrl = ctrl.Control(prefix=self.prefix + 'IKFKBlend', trans_to=self.driven[-1],
                                  scale=self.scale, parent=self.controls_grp, shape='cog')
        blend_ctrl.create()
        blend_ctrl.get_offset().attr('rx').set(90)

        # get vector between lower and end joint. move blend controller with that offset
        lower_pos = pm.xform(self.driven[-2], q=True, ws=True, t=True)
        end_pos = pm.xform(self.driven[-1], q=True, ws=True, t=True)

        lower_joint_vec = om.MVector(lower_pos[0], lower_pos[1], lower_pos[2])
        end_joint_vec = om.MVector(end_pos[0], end_pos[1], end_pos[2])

        get_offset = (end_joint_vec - lower_joint_vec).length()

        #_pos = get_offset.normal() * get_offset.length() + end_joint_vec

        # TODO: position the blend controller using vector position instead of pm.move
        pm.move(blend_ctrl.get_offset(), get_offset, 0, get_offset, r=True)
        #pm.move(blend_ctrl.get_offset(), _pos[0], _pos[1], _pos[2])

        tools.joint_constraint(fk_joints, self.driven, blender=blend_ctrl.get_ctrl(), driver2=ik_joints)
