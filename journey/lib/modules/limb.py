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
import journey.lib.space_switcher as space
import journey.lib.layout as lo
reload(ctrl)
reload(tools)
reload(kine)
reload(space)
# reload(lo)
# import journey.lib.layout as lo


class Limb(lo.Module):
    def __init__(self,
                 driven,
                 spaces=[],
                 parent_joint='',
                 stretch=True,
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 do_spaces_in_limb=True
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        self.spaces = spaces
        if spaces:
            self.spaces = tools.list_check(spaces)
        self.parent_joint = parent_joint
        self.stretch = stretch
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

        # init empty public variables
        self.offset_joint = ''
        self.ik_joints = []
        self.fk_joints = []
        self.blend_ctrl = ''
        self.arm_ik = ''
        self.arm_fk = ''
        self.do_spaces_in_limb = do_spaces_in_limb

    def create(self, *args):
        # create module from parent class
        try:
            super(Limb, self).create_structure()
        except TypeError, e:
            print "Failure initialising Retrieval --> self: %r"
            raise e

        self.offset_joint = pm.listRelatives(self.driven[0], parent=True)
        if self.offset_joint:
            pm.delete(pm.parentConstraint(self.offset_joint, self.joints_offset_grp, mo=0))

        self.ik_joints = tools.joint_duplicate(self.driven, 'IK', offset_grp=self.joints_offset_grp)
        self.fk_joints = tools.joint_duplicate(self.driven, 'FK', offset_grp=self.joints_offset_grp)

        self.arm_ik = kine.IK(self.ik_joints, prefix=self.prefix, scale=self.scale, rig_module=self.get_instance())
        self.arm_ik.create()
        self.arm_ik.pole_vector()
        self.arm_fk = kine.FK(self.fk_joints, prefix=self.prefix, scale=self.scale, rig_module=self.get_instance())
        self.arm_fk.create()

        # setup stretch if argument is True
        if self.stretch:
            self.arm_ik.stretch()

        self.blend_ctrl = ctrl.Control(prefix=self.prefix + 'IKFKBlend', trans_to=self.driven[-1],
                                       scale=self.scale, parent=self.controls_grp, shape='cog')
        self.blend_ctrl.create()
        self.blend_ctrl.get_offset().attr('rx').set(90)

        # get vector between lower and end joint. move blend controller with that offset
        lower_pos = pm.xform(self.driven[-2], q=True, ws=True, t=True)
        end_pos = pm.xform(self.driven[-1], q=True, ws=True, t=True)

        lower_joint_vec = om.MVector(lower_pos[0], lower_pos[1], lower_pos[2])
        end_joint_vec = om.MVector(end_pos[0], end_pos[1], end_pos[2])

        get_offset = (end_joint_vec - lower_joint_vec).length()

        # TODO: position the blend controller using vector position instead of pm.move
        if self.prefix.startswith('l_'):
            pm.move(self.blend_ctrl.get_offset(), get_offset, 0, -get_offset, r=True)
        elif self.prefix.startswith('r_'):
            pm.move(self.blend_ctrl.get_offset(), -get_offset, 0, -get_offset, r=True)

        # setup blending between joint chains and driven. blend_ctrl gets .blend attr added in function
        if self.blend_ctrl:
            for driver1, driven, driver2 in zip(self.fk_joints, self.driven, self.ik_joints):
                tools.matrix_blend(driver1, driven, blender=self.blend_ctrl.get_ctrl(), driver2=driver2, channels=['t', 'r'])

        # setup blend ctrl to hide the kinematic that isn't in use
        reverse = pm.createNode('reverse', n=self.prefix + 'rev_vis')
        pm.connectAttr(self.blend_ctrl.get_ctrl() + '.blend', reverse + '.inputX')

        for driven in self.arm_fk.fk_dict.values():
            pm.connectAttr(reverse + '.outputX', driven.get_offset() + '.v')

        pm.connectAttr(self.blend_ctrl.get_ctrl() + '.blend', self.arm_ik.ik_ctrl.get_offset() + '.v')
        pm.connectAttr(self.blend_ctrl.get_ctrl() + '.blend', self.arm_ik.pv_ctrl.get_offset() + '.v')
        pm.connectAttr(self.blend_ctrl.get_ctrl() + '.blend', self.arm_ik.crv_offset + '.v')

        self.blend_ctrl.get_ctrl().attr('blend').set(1)
        # print self.arm_fk.fk_dict.values()[0].get_offset()
        if self.do_spaces_in_limb:
            if self.parent_joint:
                if self.stretch:
                    tools.matrix_constraint(self.parent_joint, self.arm_ik.upper_null, mo=True)
                tools.matrix_constraint(self.parent_joint, self.ik_joints[0], mo=True)
                tools.matrix_constraint(self.parent_joint, self.arm_fk.fk_dict.values()[0].get_offset(), mo=True)
            if self.spaces:
                ss_pole = space.SpaceSwitcherLogic(self.arm_ik.ik_ctrl.get_ctrl(), self.arm_ik.pv_ctrl.get_ctrl(),
                                                   base_rig=self.base_rig)
                ss_pole.setup_switcher()

                ss_ik = space.SpaceSwitcherLogic(self.spaces, self.arm_ik.ik_ctrl.get_ctrl(),
                                                 base_rig=self.base_rig)
                ss_ik.setup_switcher()

                # ss_fk = space.SpaceSwitcherLogic(self.spaces, self.arm_fk.fk_dict.values()[0].get_ctrl(),
                #                                  base_rig=self.base_rig)
                # ss_fk.setup_switcher()
        return self
