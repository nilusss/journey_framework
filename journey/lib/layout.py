"""
module for making top rig structure and rig module structure

TODO: update imports for cleaner look
"""
import os
import pymel.core as pm
import journey.lib.utils.tools as tools
from journey.env import JF_VERSION, JF_AUTHOR, JF_NAME
import journey.lib.control as ctrl
import journey.lib.serialization as se
reload(ctrl)
reload(tools)
reload(se)
import journey.lib.serialization as se


class Base:
    """class for building top rig structure
    TODO: automatically look for object in scene created with class - see if it's an instance
    """

    def __init__(self,
                 char_name='new',
                 scene_obj_type='rig',
                 scale=1.0,
                 global_ctrl_scale=20):
        """

        Args:
            char_name (str): name for the base rig grp
            scene_obj_type (str): object type for the base structure. Usually 'rig'
            scale (float, int): initial scale of the rig
            global_ctrl_scale (float, int): initial scale of the master and offset controller
        """
        self.char_name = char_name
        self.scene_obj_type = scene_obj_type
        self.scale = scale
        self.global_ctrl_scale = global_ctrl_scale

    def create(self, *args):
        """Create method for base class
        """
        # create initial rig structure groups
        self.top_grp = pm.group(name=self.char_name + '_rig_grp', em=1)
        self.rig_grp = pm.group(name='rig_grp', em=1, p=self.top_grp)
        self.model_grp = pm.group(name='model_grp', em=1, p=self.top_grp)

        # lock top group channels
        tools.lock_channels(obj=self.top_grp, channels=['t', 'r', 's', 'v'])

        # make model_grp content non-selectable
        pm.setAttr(self.model_grp + '.overrideEnabled', 1)
        pm.setAttr(self.model_grp + '.overrideDisplayType', 2)

        char_name_attr = 'CHARACTER_NAME'
        scene_obj_type_attr = 'SCENE_OBJECT_TYPE'

        for attr_name, attr in zip([char_name_attr, scene_obj_type_attr, 'VERSION'],
                                   [self.char_name, self.scene_obj_type, JF_VERSION]):
            pm.addAttr(self.top_grp, shortName=attr_name, longName=attr_name,
                       at="enum", enumName=attr, keyable=False)
            pm.setAttr(self.top_grp + '.' + attr_name, edit=True, channelBox=True)

        # make global control and offset control
        self.global_ctrl = ctrl.Control(prefix='master',
                                        scale=self.scale * self.global_ctrl_scale,
                                        parent=self.rig_grp,
                                        shape='master',
                                        channels=['v'])
        self.global_ctrl.create()

        self.offset_ctrl = ctrl.Control(prefix='offset',
                                        scale=self.scale * self.global_ctrl_scale * 0.7,
                                        parent=self.rig_grp,
                                        shape='offset',
                                        channels=['s', 'v'])
        self.offset_ctrl.create()

        tools.matrix_constraint(self.global_ctrl.get_ctrl(), self.offset_ctrl.get_offset())

        for axis in ['y', 'z']:
            pm.connectAttr(self.global_ctrl.get_ctrl() + '.sx', self.global_ctrl.get_ctrl() + '.s' + axis)
            pm.setAttr(self.global_ctrl.get_ctrl() + '.s' + axis, keyable=0)

        self.joints_grp = pm.group(n='joints_grp', em=1, p=self.rig_grp)
        # mc.hide(self.jointsGrp)
        self.modules_grp = pm.group(n='modules_grp', em=1, p=self.rig_grp)

        #tools.matrix_constraint(self.offset_ctrl.ctrl_object, self.joints_grp, mo=True)
        tools.matrix_constraint(self.offset_ctrl.ctrl_object, self.modules_grp, mo=True)

        self.extra_grp = pm.group(n='extra_grp', em=1, p=self.rig_grp)
        pm.setAttr(self.extra_grp + '.it', 0, lock=1)


class Module(se.Serialize):
    """
    class for building rig module structure
    """

    all_names_list = []
    all_instances_list = []

    def __init__(self,
                 prefix='new',
                 base_rig=None
                 ):
        super(Module, self).__init__()

        self.prefix = prefix
        self.base_rig = base_rig

    def create_structure(self, *args):
        get_duplicate = pm.ls(self.prefix + '_*')
        if pm.objExists(self.prefix + '_module_grp'):
            pm.error("Module already exists with prefix: " + self.prefix)
        # create initial rig structure groups
        self.top_grp = pm.group(name=self.prefix + '_module_grp', em=1)
        self.controls_grp = pm.group(name=self.prefix + '_controls_grp', em=1, p=self.top_grp)
        self.joints_grp = pm.group(name=self.prefix + '_joints_grp', em=1, p=self.top_grp)
        self.parts_grp = pm.group(name=self.prefix + '_parts_grp', em=1, p=self.top_grp)
        self.static_grp = pm.group(name=self.prefix + '_static_grp', em=1, p=self.top_grp)
        # self.info_grp = pm.group(name=prefix + '_info_grp', em=1, p=self.topGrp)
        self.joints_offset_grp = pm.createNode('transform', n=self.prefix + 'joints_offset_grp')
        pm.parent(self.joints_offset_grp, self.joints_grp)

        # hide module groups and make static group
        pm.hide(self.parts_grp, self.static_grp, self.joints_grp)
        pm.setAttr(self.static_grp + '.it', 0, l=1)

        self.body_attach_grp = pm.group(n=self.prefix + '_bodyAttach_grp', em=1, p=self.parts_grp)
        self.base_attach_grp = pm.group(n=self.prefix + '_baseAttach_grp', em=1, p=self.parts_grp)

        # parent module
        self.set_base(self.base_rig)
        if self.base_rig:
            pm.parent(self.top_grp, self.base_rig.modules_grp)

    def set_base(self, base_rig):
        self.base_rig = base_rig
        if self.base_rig:
            pm.parent(self.top_grp, self.base_rig.modules_grp)

    def set_prefix(self, new_prefix):
        sel = pm.ls(self.prefix + '*')

        for s in sel:
            pm.rename(s, s.replace(self.prefix, new_prefix))

        self.prefix = new_prefix

    def get_instance(self):
        return self

    def get_all_module_names(self):
        self.all_names_list.append(self.prefix)
        return self.all_names_list

    def get_all_module_instances(self):
        self.all_instances_list.append(self)
        return self.all_instances_list
