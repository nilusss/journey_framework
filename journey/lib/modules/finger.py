"""
module containing finger setup.
used for: Metacarpal (Fingers), Metatarsal (Toes)

NOTE: inherit set_base and set_prefix from Module class
NOTE: when attaching finger joints, only use the base joint of the finger and attach meta ctrl in the right order

TODO: loop through every finger give a proxy controls controller with fk ik switch to put on every fk and ik
controller for that specific finger """
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


class Finger(lo.Module):
    def __init__(self,
                 driven,
                 meta_ctrls=[],
                 splay=True,
                 splay_up_pos='',
                 incl_last_child=False,
                 parent='',
                 prefix='new',
                 scale=1.0,
                 base_rig=None
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        if self.driven:
            self.driven = tools.list_check(self.driven)
        self.meta_ctrls = meta_ctrls
        self.splay = splay
        self.splay_up_pos = splay_up_pos
        self.incl_last_child = incl_last_child
        self.parent = parent
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

    def create(self, *args):
        # create module from parent class
        super(Finger, self).create_structure()

        self.meta_f_ctrls_offset = []
        self.meta_f_ctrls = []
        for i, driven in enumerate(self.driven):
            print driven
            prefix = tools.split_at(driven, '_', 2)
            letter = tools.int_to_letter(i).capitalize()

            # create buffer node
            buffer = pm.createNode('transform', n=prefix + '_buffer_grp')
            buffer_offset = pm.createNode('transform', n=prefix + '_buffer_offset_grp')
            pm.parent(buffer, buffer_offset)
            pm.parent(buffer_offset, self.controls_grp)
            pm.delete(pm.parentConstraint(driven, buffer_offset))
            # pm.makeIdentity(buffer, apply=True)
            # DeleteHistory()

            meta_ctrl = ctrl.Control(prefix=prefix,
                                     scale=self.scale,
                                     trans_to=driven,
                                     rot_to=driven,
                                     parent=buffer,
                                     shape='circle')
            meta_ctrl.create()
            meta_ctrl.set_constraint(driven)

            self.meta_f_ctrls_offset.append(meta_ctrl.get_offset())
            self.meta_f_ctrls.append(meta_ctrl.get_ctrl())

            if self.meta_ctrls:
                pass
                tools.matrix_constraint(self.meta_ctrls[i], buffer_offset)

            child_joints = pm.listRelatives(driven, children=True, ad=True, type='joint')
            child_joints.reverse()
            print child_joints
            if self.incl_last_child is False:
                del(child_joints[-1])

            f_ctrls = []
            for i, joint in enumerate(child_joints):
                prefix = tools.split_at(joint, '_', 2)
                finger_fk = ctrl.Control(prefix=prefix,
                                         scale=self.scale,
                                         trans_to=joint,
                                         rot_to=joint,
                                         shape='circle')
                finger_fk.create()
                finger_fk.set_constraint(joint)
                f_ctrls.append(finger_fk)
                if joint == child_joints[0]:
                    tools.matrix_constraint(meta_ctrl.get_ctrl(), finger_fk.get_offset())
                if i > 0:
                    tools.matrix_constraint(f_ctrls[i-1].get_ctrl(), f_ctrls[i].get_offset())
                pm.parent(finger_fk.get_offset(), self.controls_grp)
        if self.splay:
            splay_mid_ctrl = ctrl.Control(prefix=self.prefix + 'SplayMidA',
                                          scale=self.scale * 0.2,
                                          trans_to=self.splay_up_pos,
                                          rot_to=self.splay_up_pos,
                                          parent=self.controls_grp,
                                          shape='diamond')
            splay_mid_ctrl.create()

            splay_ctrl = ctrl.Control(prefix=self.prefix + 'SplayA',
                                      scale=self.scale * 0.2,
                                      trans_to=self.splay_up_pos,
                                      rot_to=self.splay_up_pos,
                                      parent=self.controls_grp,
                                      shape='diamond')
            splay_ctrl.create()

            # try:
            #     pm.parent(self.splay_up_pos, self.parts_grp)
            # except:
            #     pass

            # splay mid and splay end controller0
            pm.delete(pm.parentConstraint(self.driven[0], self.driven[-1], splay_mid_ctrl.get_offset(), st=['y']))
            pm.delete(pm.parentConstraint(self.driven[-1], splay_ctrl.get_offset(), st=['y']))

            pm.addAttr(splay_mid_ctrl.get_ctrl(), shortName='splaymid', longName='SplayMid', nn='SPLAY Mid',
                       at="enum", keyable=False, en="=======")
            pm.addAttr(splay_ctrl.get_ctrl(), shortName='splay', longName='Splay', nn='SPLAY',
                       at="enum", keyable=False, en="=======")

            tools.setup_splay(splay_mid_ctrl.get_ctrl(), splay_ctrl.get_ctrl(), self.driven,
                              meta_ctrls_offset=self.meta_f_ctrls_offset, prefix=self.prefix, scale=self.scale)

        if self.parent:
            if pm.objExists(self.parent):
                finger_ss = space.SpaceSwitcherLogic(self.parent, self.controls_grp, split=False)
                finger_ss.setup_switcher()
                finger_ss.set_space(self.parent)
