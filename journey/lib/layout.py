import pymel.core as pm
"""
module for making top rig structure and rig module structure
"""
import os
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
from journey.env import JF_VERSION, JF_AUTHOR, JF_NAME
reload(ctrl)
reload(tools)

scene_obj_type = 'rig'


class Base:
    """
    class for building top rig structure
    """

    def __init__(self,
                 char_name='new',
                 scale=1.0,
                 global_ctrl_scale=20):

        # create initial rig structure groups
        self.top_grp = pm.group(name=char_name + '_rig_grp', em=1)
        self.rig_grp = pm.group(name='rig_grp', em=1, p=self.top_grp)
        self.model_grp = pm.group(name='model_grp', em=1, p=self.top_grp)
        self.info_grp = pm.group(name='info_grp', em=1, p=self.top_grp)
        pm.addAttr(self.info_grp, shortName='version', longName='VERSION',
                   at="enum", enumName=JF_VERSION, keyable=False)
        pm.setAttr(self.info_grp + '.version', edit=True, channelBox=True)

        # lock info group channels
        tools.lock_channels(obj=self.info_grp, channels=['t', 'r', 's', 'v'])

        # make modelGrp content non-selectable
        pm.setAttr(self.model_grp + '.overrideEnabled', 1)
        pm.setAttr(self.model_grp + '.overrideDisplayType', 2)

        char_name_attr = 'characterName'
        scene_obj_type_attr = 'sceneObjectType'

        for at in [char_name_attr, scene_obj_type_attr]:
            pm.addAttr(self.top_grp, ln=at, dt='string')

        pm.setAttr(self.top_grp + '.' + char_name_attr, char_name,
                   type='string', lock=1)
        pm.setAttr(self.top_grp + '.' + scene_obj_type_attr, scene_obj_type,
                   type='string', lock=1)

        # make global control and offset control
        self.global_ctrl = ctrl.Control(prefix='master',
                                        scale=scale * global_ctrl_scale,
                                        parent=self.rig_grp,
                                        shape='master',
                                        lock_channels=['v'])
        self.global_ctrl.create()

        self.offset_ctrl = ctrl.Control(prefix='offset',
                                        scale=scale * global_ctrl_scale - 2,
                                        parent=self.rig_grp,
                                        shape='offset',
                                        lock_channels=['s', 'v'])
        self.offset_ctrl.create()

        tools.matrix_constraint(self.global_ctrl.get_ctrl(), self.offset_ctrl.get_offset())

        for axis in ['y', 'z']:
            pm.connectAttr(self.global_ctrl.get_ctrl() + '.sx', self.global_ctrl.get_ctrl() + '.s' + axis)
            pm.setAttr(self.global_ctrl.get_ctrl() + '.s' + axis, keyable=0)

        self.joints_grp = pm.group(n='joints_grp', em=1, p=self.rig_grp)
        # mc.hide(self.jointsGrp)
        self.modules_grp = pm.group(n='modules_grp', em=1, p=self.rig_grp)

        tools.matrix_constraint(self.offset_ctrl.ctrl_object, self.joints_grp, mo=True)
        tools.matrix_constraint(self.offset_ctrl.ctrl_object, self.modules_grp, mo=True)

        self.extraNodesGrp = pm.group(n='extra_grp', em=1, p=self.rig_grp)
        pm.setAttr(self.extraNodesGrp + '.it', 0, lock=1)


class Module:
    """
    class for building rig module structure
    """

    def __init__(self,
                 prefix='new',
                 base_rig=None
                 ):

        # create initial rig structure groups
        self.topGrp = pm.group(name=prefix + '_module_grp', em=1)

        self.controls_grp = pm.group(name=prefix + '_controls_grp', em=1, p=self.topGrp)
        self.joints_grp = pm.group(name=prefix + '_joints_grp', em=1, p=self.topGrp)
        self.parts_grp = pm.group(name=prefix + '_parts_grp', em=1, p=self.topGrp)
        self.static_grp = pm.group(name=prefix + '_static_grp', em=1, p=self.topGrp)
        self.info_grp = pm.group(name=prefix + '_info_grp', em=1, p=self.topGrp)

        #
        pm.hide(self.parts_grp, self.static_grp, self.joints_grp, self.info_grp)
        pm.setAttr(self.static_grp + '.it', 0, l=1)

        # parent module

        if base_rig:
            pm.parent(self.topGrp, base_rig.modules_grp)

