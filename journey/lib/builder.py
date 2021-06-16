"""
module containing different guide setups.
TODO: take parent module scale into account when scaling child modules
TODO: Scaling guide joints causes the builder to crash - currently disabled guide joint scaling
"""
import re
import os
import fnmatch
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.shapes as shapes
import journey.lib.utils.tools as tools
import journey.lib.utils.deform as deform
import journey.lib.layout as lo
import maya.mel as mel
from maya.cmds import DeleteHistory
#import journey.lib.modules as mdls

#from journey.lib.modules import arm, eye, eyebrow, eyelid, finger, foot, limb, lips, meta, neck, spine

import journey.lib.modules.limb as limb
import journey.lib.modules.arm as arm
import journey.lib.modules.eye as eye
import journey.lib.modules.eyebrow as eyebrow
import journey.lib.modules.eyelid as eyelid
import journey.lib.modules.finger as finger
import journey.lib.modules.foot as foot
import journey.lib.modules.lips as lips
import journey.lib.modules.meta as meta
import journey.lib.modules.neck as neck
import journey.lib.modules.spine as spine
reload(ctrl)
reload(tools)
reload(lo)
reload(limb)
reload(arm)
reload(eye)
reload(eyebrow)
reload(eyelid)
reload(finger)
reload(foot)
reload(lips)
reload(meta)
reload(neck)
reload(spine)
import journey.lib.layout as lo
import journey.lib.modules.limb as limb
import journey.lib.modules.arm as arm
import journey.lib.modules.eye as eye
import journey.lib.modules.eyebrow as eyebrow
import journey.lib.modules.eyelid as eyelid
import journey.lib.modules.finger as finger
import journey.lib.modules.foot as foot
import journey.lib.modules.lips as lips
import journey.lib.modules.meta as meta
import journey.lib.modules.neck as neck
import journey.lib.modules.spine as spine


class Builder():
    def __init__(self,
                 char_name='johnDoe',
                 model_path='',
                 build_path='',
                 weights_path=''):

        self.char_name = char_name
        self.model_path = model_path
        self.build_path = build_path
        self.weights_path = weights_path
        self.root_jnt = 'c_root_result_jnt'

    def build(self):

        if self.build_path:
            pm.importFile(self.build_path)
            pm.parent(self.root_jnt, self.base_rig.joints_grp)

        for s in pm.ls('*_base'):
            tools.unlock_channels(s, ['v'])
            pm.hide(s)
        global_scale = self.get_global_scale()

        # Create base rig)
        self.base_rig = lo.Base(char_name=self.char_name,
                                global_ctrl_scale=global_scale)
        self.base_rig.create()
        model_in_scene = pm.ls('*_TEMP_grp')
        model_node = ''
        if self.model_path:
            if model_in_scene:
                pm.delete(model_in_scene[0])
            file_type = self.model_path.split('.')[-1]
            if 'fbx' in file_type:
                before = pm.ls(assemblies=True)
                mel.eval('FBXImport -f "{}";'.format(self.model_path))
                after = pm.ls(assemblies=True)
                model_node = set(after).difference(before).pop()
                pm.parent(model_node, self.base_rig.model_grp)
            else:
                pm.delete(self.base_rig.model_grp)
                model_node = pm.importFile(self.model_path, i=True, groupReference=True,
                                           groupName='model_grp',
                                           returnNewNodes=True)
                self.base_rig.model_grp = 'model_grp'
                pm.parent(self.base_rig.model_grp, self.base_rig.top_grp)
            pm.select(None)
        elif model_in_scene:
            children = pm.PyNode(model_in_scene).getChildren()
            pm.parent(children, self.base_rig.model_grp)
            model_node = children

        # get module joints and append to new list
        get_modules = pm.ls('*_base', type='transform')

        reparent_to = []
        for module in get_modules:
            self.single_joints = []
            self.single_joints2 = []
            if 'HIDDEN' not in module.name():
                p_joint = self.get_parent_joint(module)
                print 'PARENT JOINT: ' + str(p_joint)

                # split module_joints by '.' usually only used by meta and finger modules
                get_module_joints = module.getAttr('module_joints').split('.')
                get_module_joints = [x for x in get_module_joints if x]
                print "MODULE JOINTS WITH . : " + str(get_module_joints)
                if len(get_module_joints) > 1:
                    pm.PyNode(module).attr('module_joints').set('')
                    for chain in get_module_joints:
                        print chain
                        # split by # to get continuing chain if it excists
                        chain = chain.split('#')
                        print chain

                        chain = tools.joint_duplicate(chain, '_result', self.base_rig.joints_grp)
                        # pm.makeIdentity(chain[0], apply=True)
                        n_chain = []

                        for i, j in enumerate(chain):
                            nice_name = j.split('___')[-1]
                            j = pm.rename(j, nice_name)
                            j.attr('overrideEnabled').set(0)
                            j.attr('overrideDisplayType').set(0)
                            n_chain.append(j)
                            if i == 0:
                                self.single_joints.append(j)
                                try:
                                    pm.addAttr(module, longName='single_joints', dataType='string')
                                except:
                                    pass
                                value = module.getAttr('single_joints')
                                if value:
                                    module.attr('single_joints').set(value + '#' + j)
                                else:
                                    module.attr('single_joints').set(j)
                            elif i == 1:
                                self.single_joints2.append(j)
                                try:
                                    pm.addAttr(module, longName='single_joints2', dataType='string')
                                except:
                                    pass
                                value = module.getAttr('single_joints2')
                                if value:
                                    module.attr('single_joints2').set(value + '#' + j)
                                else:
                                    module.attr('single_joints2').set(j)
                            pm.select(None)

                        print n_chain
                        get_transform = n_chain[0].getParent()
                        get_transform_parent = get_transform.getParent()
                        print get_transform_parent
                        if 'transform' in get_transform.name():
                            print get_transform.name()
                            pm.makeIdentity(get_transform, s=True, apply=True)
                            pm.parent(n_chain[0], get_transform_parent)
                        pm.makeIdentity(n_chain[0], r=True, apply=True)
                        pm.delete(pm.ls('transform*'))

                        if p_joint:
                            reparent_to.append(n_chain[0] + '-' + p_joint)

                        for i, j in enumerate(n_chain):
                            value = pm.PyNode(module).getAttr('module_joints')
                            if i == 0:
                                pm.PyNode(module).attr('module_joints').set(value + '.' + j)
                            elif value:
                                pm.PyNode(module).attr('module_joints').set(value + '#' + j)
                            else:
                                pm.PyNode(module).attr('module_joints').set(j)
                else:
                    get_module_joints = module.getAttr('module_joints').split('#')
                    chain = tools.joint_duplicate(get_module_joints, '_result', self.base_rig.joints_grp)
                    pm.makeIdentity(chain[0], r=True, apply=True)
                    n_chain = []

                    for i, j in enumerate(chain):
                        nice_name = j.split('___')[-1]
                        j = pm.rename(j, nice_name)
                        j.attr('overrideEnabled').set(0)
                        j.attr('overrideDisplayType').set(0)
                        n_chain.append(j)
                        pm.select(None)
                    print n_chain
                    get_transform = n_chain[0].getParent()
                    print 'TRANSFORM IS: ' + get_transform
                    get_transform_parent = get_transform.getParent()
                    print get_transform_parent
                    if 'transform' in get_transform.name():
                        print 'FOUND TRANSFORM'
                        print get_transform.name()
                        pm.makeIdentity(get_transform, s=True, apply=True)
                        pm.parent(n_chain[0], get_transform_parent)
                    pm.makeIdentity(n_chain[0], r=True, apply=True)
                    pm.delete(pm.ls('transform*'))

                    if p_joint:
                        reparent_to.append(n_chain[0] + '-' + p_joint)

                    pm.PyNode(module).attr('module_joints').set('')

                    for j in n_chain:
                        value = pm.PyNode(module).getAttr('module_joints')
                        if value:
                            pm.PyNode(module).attr('module_joints').set(value + '#' + j.replace('jnt1', 'jnt'))
                        else:
                            pm.PyNode(module).attr('module_joints').set(j.replace('jnt1', 'jnt'))
                    if '1' in chain[0].name():
                        try:
                            pm.delete(chain[0].name())
                        except:
                            pass
                    if module.getAttr('mirror_enable'):
                        pm.mirrorJoint(n_chain[0], mirrorYZ=True, mirrorBehavior=True, searchReplace=('l_', 'r_'))

        try:
            for p in reparent_to:
                pm.parent(p.split('-')[0].replace('jnt1', 'jnt'), p.split('-')[1])
                pm.makeIdentity(p.split('-')[0].replace('jnt1', 'jnt'), r=True, a=True)
                DeleteHistory()
            pm.delete(pm.ls('transform*'))
        except:
            pass
        pm.select(None)
        # constrain root joint to offset controller
        tools.matrix_constraint(self.base_rig.offset_ctrl.get_ctrl(), 'c_root_result_jnt', mo=True)

        # import skin weights
        if model_node and self.weights_path:
            if os.listdir(self.weights_path):
                if pm.ls('c_root_result_jnt'):
                    pm.parent('c_root_result_jnt', w=True)
                geo = tools.get_geo(self.base_rig.model_grp)
                joints = tools.get_joints('c_root_result_jnt')

                deform.load_weights(self.weights_path, geo, joints)
                if pm.ls('c_root_result_jnt'):
                    pm.parent('c_root_result_jnt', 'joints_grp')
                pm.polyNormalPerVertex(geo, unFreezeNormal=True)
            else:
                pm.warning('No skin weight files in directory!')
                print("No files found in the directory.")

        # build modules from joints and guides:
        get_modules = pm.ls(assemblies=True)
        # get correct module hierarchy
        modules = []

        for dag in get_modules:
            if '_base' in dag.name():
                modules.append(dag)
                for c in pm.listRelatives(dag, ad=True, type='transform')[::-1]:
                    match = fnmatch.fnmatch(c.name(), '*_base')
                    if match:
                        if 'HIDDEN' not in c.name():
                            modules.append(c)
        for module in modules:
            joints = module.getAttr('module_joints').split('#')
            spaces = module.getAttr('space_switches')

            # get correct scaling from base_ctrl and parents
            scale = pm.PyNode(module.getAttr('radius_ctrl')).getAttr('ty')
            base_scale = module.getAttr('sx')
            sel = module.getAllParents()
            scale_val = 1
            for s in sel:
                scale_val *= s.getAttr('sx')

            scale_val *= base_scale
            scale *= scale_val

            if spaces:
                spaces = spaces.split('#')
            else:
                joint = pm.listRelatives(joints[0].replace('.', ''), parent=True, type='joint')
                if joint:
                    spaces = joint
            try:
                parent_joint = pm.listRelatives(joints[0].replace('.', ''), parent=True, type='joint')[0]
            except:
                parent_joint = None

            prefix = module.getAttr('custom_name')
            get_module = module.split('___')[0]
            parent_module = module.getAllParents()
            parent_module = [match for match in parent_module if "_base" in match.name()]
            pm_name = ''
            if parent_module:
                parent_module = parent_module[0]
                pm_name = parent_module.name()

            if get_module == 'Arm':

                arm_rig = arm.Arm(driven=joints[1::],
                                   clavicle=joints[0],
                                   spaces=spaces,
                                   parent_joint=parent_joint,
                                   stretch=True,
                                   prefix=prefix,
                                   scale=scale,
                                   base_rig=self.base_rig)
                #arm_rig.__class__ = arm.Arm
                arm_rig.create()

            if get_module == 'Eye':
                eye_rig = eye.Eye(eye_center=joints[0],
                                   eye_end=joints[1],
                                   look_at=joints[2],
                                   spaces=spaces,
                                   parent_joint=parent_joint,
                                   prefix=prefix,
                                   scale=scale,
                                   base_rig=self.base_rig)
                eye_rig.create()
            if get_module == 'Eyebrow':
                pass
            if get_module == 'Eyelid':
                pass
            if get_module == 'Finger':
                finger_joints = module.getAttr('module_joints').split('#')[0]
                if finger_joints:
                    finger_rig = finger.Finger(driven=finger_joints,
                                               splay=False,
                                               incl_last_child=False,
                                               parent=parent_joint,
                                               prefix=prefix,
                                               scale=scale,
                                               base_rig=self.base_rig)
                    finger_rig.create()
            if get_module == 'Foot':
                toe_loc = module.getAttr('toe_loc')
                heel_loc = module.getAttr('heel_loc')
                """CHECK FOR LIMB MODULE. IF LIMB MODULE IS PARENT SKIP CREATION OF FOOT
                MODULE AND WAIT FOR LIMB PARENT MODULE TO BE CREATED"""
                if 'Limb' in pm_name:
                    print 'found parent module'
                    foot_rig = foot.Foot(limb_rig.ik_joints[-1],
                                          joints[0],
                                          joints[1],
                                          toe_loc,
                                          heel_loc,
                                          foot_ctrl=limb_rig.arm_ik.ik_ctrl.get_ctrl(),
                                          blend_ctrl=limb_rig.blend_ctrl.get_ctrl(),
                                          attach_joint=limb_rig.driven[-1],
                                          ik_hdl_offset=limb_rig.arm_ik.ik_hdl_grp,
                                          leg_ik_end=limb_rig.ik_joints[-1],
                                          leg_fk_end=limb_rig.fk_joints[-1],
                                          prefix=prefix,
                                          scale=scale,
                                          base_rig=self.base_rig)
                    foot_rig.create()
                else:
                    foot_rig = foot.Foot(joints[0],
                                          joints[1],
                                          joints[2],
                                          toe_loc,
                                          heel_loc,
                                          prefix=prefix,
                                          scale=scale,
                                          base_rig=self.base_rig)
                    foot_rig.create()

            if get_module == 'Limb':
                limb_rig = limb.Limb(driven=joints,
                                      spaces=spaces,
                                      parent_joint=parent_joint,
                                      stretch=True,
                                      prefix=prefix,
                                      scale=scale,
                                      base_rig=self.base_rig,
                                      do_spaces_in_limb=True)
                limb_rig.__class__ = limb.Limb
                limb_rig.create()
                """WHEN CREATING LIMB CHECK IF FOOT MODULE IS CHILD OF CURRENT MODULE THEN GET IK AND FK CONTROLLERS"""
            if get_module == 'Lips':
                pass
            if get_module == 'Meta' and "l_" not in module:
                splay_up_pos = module.getAttr('splay_up_pos')  # define correct splay up position using locator
                single_joints = module.getAttr('single_joints').split('#')
                meta_rig = meta.Meta(driven=single_joints,
                                      splay_up_pos=splay_up_pos,
                                      parent=parent_joint,
                                      prefix=prefix,
                                      scale=scale,
                                      base_rig=self.base_rig)
                meta_rig.create()
                # check if meta joints have fingers attached.
                if module.getAttr('finger_joints'):
                    #splay_up_pos = ''  # define correct splay up position using locator
                    #finger_joints = module.getAttr('finger_joints').split('#')
                    prefix = prefix.replace('meta', 'metaFinger')
                    single_joints2 = module.getAttr('single_joints2').split('#')
                    meta_fingers_rig = finger.Finger(driven=single_joints2,
                                                      meta_ctrls=meta_rig.meta_ctrls,
                                                      splay=True,
                                                      splay_up_pos=splay_up_pos,
                                                      incl_last_child=False,
                                                      parent=parent_joint,
                                                      prefix=prefix,
                                                      scale=scale,
                                                      base_rig=self.base_rig)
                    meta_fingers_rig.create()
            if get_module == 'Neck':
                neck_rig = neck.Neck(driven=joints,
                                      spaces=spaces,
                                      stretch=True,
                                      prefix=prefix,
                                      scale=scale,
                                      base_rig=self.base_rig)
                neck_rig.create()
            if get_module == 'Spine':
                spine_rig = spine.Spine(driven=joints,
                                         stretch=True,
                                         com=True,
                                         prefix=prefix,
                                         scale=scale,
                                         base_rig=self.base_rig)
                spine_rig.create()

        pm.select(None)
        return self

    @staticmethod
    def get_parent_joint(base_ctrl):
        parent = base_ctrl.getAllParents()
        if parent:
            for p in parent:
                print p
                if '_guide' in p.name():
                    parent = p
                    break
        joint = pm.listRelatives(parent, children=True, type='joint')
        if joint:
            joint = joint[0]
            if "result_jnt" in joint:
                last_string = "result_jnt"
            else:
                last_string = '_jnt'
            joint = joint.replace(last_string, '_result_jnt').split('___')[-1]
            pm.PyNode(base_ctrl).attr('parent_joint').set(joint)
        return joint

    @staticmethod
    def get_global_scale():
        global_scale = pm.ls('Master___*_base')
        if len(global_scale) > 1:
            raise Exception('Too many Master modules in scene. Build file should only have one')
        elif len(global_scale) == 1:
            pm.hide(global_scale[0])
            scale = global_scale[0].getAttr('sx')

            radius = pm.ls('Master___*_radius_ctrl')[0]
            global_scale = radius.getAttr('ty')

            global_scale *= scale

        else:
            global_scale = 35
        return global_scale

    @staticmethod
    def update_ss_name(base_ctrl):
        """Update space switch name"""

