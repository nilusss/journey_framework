"""
module containing meta setup.
used for: Metacarpal (Fingers), Metatarsal (Toes)

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
reload(lo)
reload(space)
import journey.lib.layout as lo


class Meta(lo.Module):
    def __init__(self,
                 driven,
                 splay_up_pos='',
                 parent='',
                 prefix='new',
                 scale=1.0,
                 base_rig=None
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        self.splay_up_pos = splay_up_pos
        self.parent = parent
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

    def create(self, *args):
        # create module from parent class
        super(Meta, self).create_structure()

        splay_mid_ctrl = ctrl.Control(prefix=self.prefix + 'SplayMidA',
                                      scale=self.scale * 1.2,
                                      trans_to=self.splay_up_pos,
                                      rot_to=self.splay_up_pos,
                                      parent=self.controls_grp,
                                      shape='diamond')

        splay_mid_ctrl.create()

        splay_ctrl = ctrl.Control(prefix=self.prefix + 'SplayA',
                                  scale=self.scale * 1.2,
                                  trans_to=self.splay_up_pos,
                                  rot_to=self.splay_up_pos,
                                  parent=self.controls_grp,
                                  shape='diamond')

        splay_ctrl.create()

        try:
            pm.parent(self.splay_up_pos, self.parts_grp)
        except:
            pass

        # splay mid and splay end controllers
        pm.delete(pm.parentConstraint(self.driven[0], self.driven[-1], splay_mid_ctrl.get_offset(), st=['x', 'y']))
        pm.delete(pm.parentConstraint(self.driven[-1], splay_ctrl.get_offset(), st=['x', 'y']))

        #splay_mid_ctrl.freeze_transforms()
        #splay_ctrl.freeze_transforms()

        pm.addAttr(splay_mid_ctrl.get_ctrl(), shortName='splaymid', longName='SplayMid', nn='SPLAY Mid',
                   at="enum", keyable=False, en="=======")
        pm.addAttr(splay_ctrl.get_ctrl(), shortName='splay', longName='Splay', nn='SPLAY',
                   at="enum", keyable=False, en="=======")

        self.meta_ctrls_offset = []
        self.meta_ctrls = []
        for i, driven in enumerate(self.driven):
            prefix = tools.split_at(driven, '_', 2)
            letter = tools.int_to_letter(i).capitalize()
            buffer = pm.createNode('transform', n=prefix + '_buffer_grp')
            buffer_offset = pm.createNode('transform', n=prefix + '_buffer_offset_grp')
            pm.parent(buffer, buffer_offset)
            pm.parent(buffer_offset, self.controls_grp)
            pm.delete(pm.parentConstraint(driven, buffer_offset))
            meta_ctrl = ctrl.Control(prefix=self.prefix + letter,
                                     scale=self.scale,
                                     trans_to=driven,
                                     rot_to=driven,
                                     parent=buffer,
                                     shape='circle')
            meta_ctrl.create()
            meta_ctrl.freeze_transforms()
            meta_ctrl.set_constraint(driven)
            #pm.parent(meta_ctrl.get_offset(), self.controls_grp)

            self.meta_ctrls_offset.append(meta_ctrl.get_offset())
            self.meta_ctrls.append(meta_ctrl.get_ctrl())

        tools.setup_splay(splay_mid_ctrl.get_ctrl(), splay_ctrl.get_ctrl(), self.driven,
                          meta_ctrls_offset=self.meta_ctrls_offset, prefix=self.prefix, scale=self.scale)

        if self.parent:
            if pm.objExists(self.parent):
                meta_ss = space.SpaceSwitcherLogic(self.parent, self.controls_grp, split=False, base_rig=self.base_rig)
                meta_ss.setup_switcher()
                meta_ss.set_space(self.parent)

