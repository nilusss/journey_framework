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
                 prefix='new',
                 scale=1.0,
                 base_rig=None
                 ):
        self.CLASS_NAME = self.__class__.__name__

        # self.bank_inside = bank_inside
        # self.bank_outside = bank_outside
        self.driven = driven
        self.splay_up_pos = splay_up_pos
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

    def create(self, *args):
        # create module from parent class
        super(Meta, self).create_structure()

        splay_mid_ctrl = ctrl.Control(prefix=self.prefix + 'SplayMidA',
                                      scale=self.scale,
                                      trans_to=self.splay_up_pos,
                                      shape='diamond')

        splay_mid_ctrl.create()

        splay_ctrl = ctrl.Control(prefix=self.prefix + 'SplayA',
                                  scale=self.scale,
                                  trans_to=self.splay_up_pos,
                                  shape='diamond')

        splay_ctrl.create()

        # splay mid and splay end controllers
        pm.delete(pm.parentConstraint(self.driven[0], self.driven[-1], splay_mid_ctrl.get_offset(), st=['x']))
        pm.delete(pm.parentConstraint(self.driven[-1], splay_ctrl.get_offset(), st=['x']))

        splay_mid_ctrl.freeze_transforms()
        splay_ctrl.freeze_transforms()

        pm.addAttr(splay_mid_ctrl.get_ctrl(), shortName='splaymid', longName='SplayMid', nn='SPLAY Mid',
                   at="enum", keyable=False, en="=======")
        pm.addAttr(splay_ctrl.get_ctrl(), shortName='splay', longName='Splay', nn='SPLAY',
                   at="enum", keyable=False, en="=======")

        tools.setup_splay(splay_mid_ctrl.get_ctrl(), splay_ctrl.get_ctrl(), self.driven,
                          prefix=self.prefix, scale=self.scale)
