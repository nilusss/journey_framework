"""
module containing different guide setups.
NOTE: CONTROLLERS MADE WITH ctrl.Control needs 'channels=['v']'
TODO: MIRROR WITHOUT THE NEED TO HAVE A PARENT MODULE TO ATTACH TO
"""
import re
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.shapes as shapes
import journey.lib.utils.tools as tools
import journey.lib.serialization as se
from maya.cmds import DeleteHistory

reload(ctrl)
reload(tools)


class Guides(object):
    def __init__(self, prefix=''):
        self.name = ''
        self.prefix = ''
        self.offset = [0, 0, 0]
        self.module_name = ''
        self.driven_joints = []
        self.controllers = []
        self.parent = ''
        self.space_switches = ''
        self.guess_up = 1

    def create(self):
        if pm.ls(self.name + '*'):
            pm.error("Module already exists with prefix: " + self.name)
        self.sel_parent = pm.ls(sl=True, type='transform')
        if len(self.sel_parent) > 1:
            print('Only select one object as parent. Selected objects are: ' + str(self.sel_parent))
            print('Parenting module to world')
            self.sel_parent = None
        elif len(self.sel_parent) == 1:
            self.sel_parent = self.sel_parent[0]

        pm.select(None)
        self.base_guide()

        # add attributes to be read when rigging module
        bool_attr_list = ['guide_base', 'mirror_enable', 'display_annotation']
        for bool_attr in bool_attr_list:
            pm.addAttr(self.base_ctrl, longName=bool_attr, attributeType='bool')
            self.base_ctrl.attr(bool_attr).set(1)
            pm.setAttr(self.base_ctrl + '.' + bool_attr, edit=True, channelBox=True)

        string_attr_list = ['module_namespace', 'custom_name', 'mirror_axis', 'mirror_name', 'parent_module',
                            'parent_joint', 'space_switches', 'hook_node', 'module_info', 'guide_info', 'rig_type',
                            'module_joints', 'radius_ctrl']
        for string_attr in string_attr_list:
            pm.addAttr(self.base_ctrl, longName=string_attr, dataType='string')

        pm.setAttr(self.base_ctrl + ".mirror_axis", "off", type='string')
        pm.setAttr(self.base_ctrl + ".mirror_name", 'left --> right', type='string')
        pm.setAttr(self.base_ctrl + ".hook_node", "_Grp", type='string')
        self.base_ctrl.attr('module_namespace').set(self.module_name)
        self.base_ctrl.attr('custom_name').set(self.prefix)
        self.base_ctrl.attr('parent_module').set(str(self.parent))
        self.base_ctrl.attr('space_switches').set(self.space_switches)
        self.base_ctrl.attr('radius_ctrl').set(self.radius_ctrl)

        float_attr_list = ['shapeSize']
        for float_attr in float_attr_list:
            pm.addAttr(self.base_ctrl, longName=float_attr, attributeType='float')

        self.base_ctrl.attr('shapeSize').set(1)

        # create annotation to this module:
        self.annotation = pm.annotate(self.base_ctrl, tx=self.base_ctrl, point=(-1, 2, 0))
        self.annotation = pm.listRelatives(self.annotation, parent=True)[0]
        self.annotation = pm.rename(self.annotation, self.base_ctrl + "_Ant")
        pm.parent(self.annotation, self.base_ctrl)
        pm.setAttr(self.annotation + '.text', self.name.split('__')[0] + '_' + self.prefix,
                   type='string')
        self.annotation.attr('template').set(1)

        self.center_loc_ctrl, self.loc_offset, self.center_joint = self.cv_joint_loc(self.name)

        self.controllers.append(self.center_loc_ctrl)

        pm.parent(self.loc_offset, self.base_ctrl)
        self.driven_joints.append(self.center_joint)
        return self

    def delete_guide(self):
        """used for deleting module and mirror module"""

    def base_guide(self, r=1, up_axis='ty'):
        attr_up = '.' + up_axis
        # create base guide controllers and configure them
        self.base_ctrl, base_ctrl_hist = pm.circle(n=self.name + '_base', ch=True, o=True,
                                                   nr=(0, 0, 1), d=3, s=8, radius=r)
        self.radius_ctrl, radius_ctrl_hist = pm.circle(n=self.name + '_radius_ctrl', ch=True, o=True,
                                                       nr=(1, 0, 0), d=3, s=8, radius=r / 4.0)
        tools.lock_channels(self.base_ctrl, channels=['v'])
        tools.rename_shape([self.base_ctrl, self.radius_ctrl])
        pm.setAttr(self.radius_ctrl + attr_up, 1)
        pm.parent(self.radius_ctrl, self.base_ctrl, relative=True)
        pm.transformLimits(self.radius_ctrl, tx=(0.01, 1), etx=(True, False))
        tools.lock_channels(self.radius_ctrl, channels=['t', 'r', 's', 'v'], t_axis=['x', 'z'])

        # connect radius_ctrl to base_ctrl radius
        pm.connectAttr(self.radius_ctrl + attr_up, base_ctrl_hist + '.radius', force=True)
        # automate scale of radius_ctrl shape
        rc_md = pm.createNode('multiplyDivide', n=self.radius_ctrl + '_md')
        pm.connectAttr(self.radius_ctrl + attr_up, rc_md + '.input1X', force=True)
        rc_md.attr('input2X').set(0.15)
        pm.connectAttr(rc_md + '.outputX', radius_ctrl_hist + '.radius', force=True)
        self.parts = pm.createNode('transform', n=self.name + '_parts_grp')
        self.joints_grp = pm.createNode('transform', n=self.name + '_joints_grp')
        pm.parent(self.parts, self.joints_grp, self.base_ctrl)

    def guide_to_joints(self):
        result_joints = []
        for i, joint in enumerate(self.driven_joints):
            nice_name = joint.replace('_jnt', '_result_jnt').replace(self.module_name + '___', '')
            n_joint = pm.duplicate(joint, name=nice_name, po=True)[0]
            pm.parent(n_joint, w=True)
            n_joint.attr('overrideEnabled').set(0)
            n_joint.attr('overrideDisplayType').set(0)
            pm.select(None)
            result_joints.append(n_joint.name())
            if i > 0:
                pm.parent(result_joints[i], result_joints[i - 1])

    def get_parent_module(self):
        self.parent_module = self.base_ctrl.getAllParents()
        self.parent_module = [match for match in self.parent_module if "_base" in match.name()]
        if self.parent_module:
            self.base_ctrl.attr('parent_module').set(self.parent_module[0])
            return self.parent_module[0]

    def get_parent_joint(self):
        parent = pm.listRelatives(self.base_ctrl, parent=True)
        joint = pm.listRelatives(parent, children=True, type='joint')
        self.base_ctrl.attr('parent_joint').set(joint)
        return joint

    def get_parent(self):
        return self.base_ctrl.getParent()

    def get_module_joints(self):
        for j in self.driven_joints:
            value = self.base_ctrl.getAttr('module_joints')
            if value:
                self.base_ctrl.attr('module_joints').set(value + '#' + j)
            else:
                self.base_ctrl.attr('module_joints').set(j)

    def add_space_switches(self, spaces=[]):
        spaces = tools.list_check(spaces)
        for s in spaces:
            joint = pm.listRelatives(s, children=True, type='joint')[0]
            if joint:
                if "result_jnt" in joint:
                    last_string = "result_jnt"
                else:
                    last_string = '_jnt'
                joint = joint.split('___')[-1].replace(last_string, '_result_jnt')
                value = self.base_ctrl.getAttr('space_switches')
                if value:
                    self.base_ctrl.attr('space_switches').set(value + '#' + joint)
                else:
                    self.base_ctrl.attr('space_switches').set(joint)

    def clear_space_switches(self):
        pm.PyNode(self.base_ctrl).attr('space_switches').set('')

    def toggle_local_axis(self):
        for j in self.controllers:
            pm.select(j)
            pm.toggle(localAxis=True)
            pm.select(None)

    def do_parent(self):
        if self.parent:
            pm.parent(self.base_ctrl, self.parent)
            pm.select(None)
        elif self.sel_parent:
            pm.parent(self.base_ctrl, self.sel_parent)
            pm.select(None)

    def do_parent_line(self):
        if self.parent:
            self.p_line = tools.create_line(self.parent, self.controllers[0], 'parent_' + self.controllers[0])
            pm.parent(self.p_line[0], self.parts, r=True)
            return self.p_line
        elif self.sel_parent:
            self.p_line = tools.create_line(self.sel_parent, self.controllers[0], 'parent_' + self.controllers[0])
            pm.parent(self.p_line[0], self.parts, r=True)
            return self.p_line

    def base_one_scale(self):
        self.base_ctrl.attr('sx').set(1)
        self.base_ctrl.attr('sy').set(1)
        self.base_ctrl.attr('sz').set(1)

    def mirror(self):
        """TODO: give the possibility to mirror on any axis. ATM only mirror from X to -X"""
        mirror_grp = pm.ls("MIRROR_GRP")
        if not mirror_grp:
            mirror_grp = pm.createNode('transform', n="MIRROR_GRP")
            pm.parent(mirror_grp, w=True)
        else:
            mirror_grp = mirror_grp[0]

        # create a new guide instance of same type and match position to original
        if self.prefix.startswith('l_'):
            prefix = self.prefix.replace('l_', 'r_')
            try:
                dup_parent = self.get_parent().name().replace('l_', 'r_')
            except:
                dup_parent = ''
            if not pm.objExists(dup_parent):
                dup_parent = self.get_parent()
            dup_axis = -1
        elif self.prefix.startswith('r_'):
            prefix = self.prefix.replace('r_', 'l_')
            try:
                dup_parent = self.get_parent().name().replace('r_', 'l_')
            except:
                dup_parent = ''
            if not pm.objExists(dup_parent):
                dup_parent = self.get_parent()
            dup_axis = -1
        else:
            # dup_parent = self.get_parent().name().replace('l_', 'r_')
            dup_parent = self.get_parent()
            dup_axis = -1

        pm.select(None)
        exec ('dup_guide = Draw{}(prefix=\'{}\')'.format(self.module_name, prefix))
        # if 'Foot' in self.module_name:
        #     dup_guide.parent = dup_parent
        dup_guide.draw()
        pm.parent(dup_guide.base_ctrl, w=True)
        self.mirror_guide = dup_guide
        pm.select(None)
        exec ('hidden_guide = Draw{}(prefix=\'{}\').draw()'.format(self.module_name, prefix + 'HIDDEN', 'draw'))
        pm.rename(hidden_guide.base_ctrl, 'HIDDEN_' + hidden_guide.base_ctrl)

        # set annotation with MIRROR prefix
        dup_guide.annotation.getShape().attr('text').set('MIRROR_' + self.name.split('__')[0] + '_' + prefix)
        hidden_guide.base_ctrl.attr('v').unlock()
        hidden_guide.base_ctrl.attr('v').set(0)

        pm.delete(pm.parentConstraint(self.base_ctrl, dup_guide.base_ctrl))
        for og_ctrl, dup_ctrl in zip(self.controllers, dup_guide.controllers):
            pm.delete(pm.parentConstraint(og_ctrl, dup_ctrl.getParent()))

        # create mirror grp to define what way the mirror module should be mirrored to
        dup_guide_mirror_grp = pm.createNode('transform',
                                             n=self.module_name + '___' + dup_guide.prefix + "MIRROR_GRP")
        dup_guide_mirror_grp.attr('sx').set(dup_axis)

        pm.parent(dup_guide.base_ctrl, dup_guide_mirror_grp)

        hidden_guide_offset_grp = pm.createNode('transform',
                                                n=self.module_name + '___' + dup_guide.prefix + "HIDOFFSET_GRP")

        if self.get_parent():
            tools.matrix_constraint(self.get_parent(), hidden_guide_offset_grp, mo=False)

        pm.parent(dup_guide.base_ctrl, w=True)
        pm.parent(hidden_guide.base_ctrl, hidden_guide_offset_grp)
        for attr in 'trs':
            pm.connectAttr(self.base_ctrl + '.' + attr, hidden_guide.base_ctrl + '.' + attr)
        dup_mirror_offset_grp = pm.createNode('transform',
                                              n=self.module_name + '___' + dup_guide.prefix + "MIRROROFFSET_GRP")
        if dup_parent:
            pm.delete(pm.parentConstraint(dup_parent, dup_mirror_offset_grp))
            d_matrix = pm.createNode('decomposeMatrix', n=prefix + 'mirror_d_matrix')
            pm.connectAttr(dup_parent + '.worldMatrix', d_matrix + '.inputMatrix')
            for attr in 'trs':
                pm.connectAttr(d_matrix + '.o' + attr, dup_mirror_offset_grp + '.' + attr)
            dup_mirror_offset_grp.attr('t').disconnect()
            dup_mirror_offset_grp.attr('r').disconnect()
            dup_mirror_offset_grp.attr('s').disconnect()

        pm.parent(dup_mirror_offset_grp, dup_guide_mirror_grp)
        pm.makeIdentity(dup_mirror_offset_grp, s=True, apply=True)
        pm.select(dup_mirror_offset_grp)
        DeleteHistory()
        pm.select(None)

        pm.parent(dup_guide.base_ctrl, dup_mirror_offset_grp)

        for og_ctrl, hid_ctrl in zip(self.controllers, hidden_guide.controllers):
            tools.matrix_constraint(og_ctrl, hid_ctrl)

        for attr in 'trs':
            pm.connectAttr(hidden_guide.base_ctrl + '.' + attr, dup_guide.base_ctrl + '.' + attr)
            if attr == 't':
                pm.connectAttr(hidden_guide.radius_ctrl + '.' + attr, dup_guide.radius_ctrl + '.' + attr)
                pm.connectAttr(self.radius_ctrl + '.' + attr, hidden_guide.radius_ctrl + '.' + attr)

        for hid_ctrl, dup_ctrl in zip(hidden_guide.controllers, dup_guide.controllers):
            for attr in 'trs':
                pm.connectAttr(hid_ctrl + '.' + attr, dup_ctrl + '.' + attr)

        pm.parent(dup_guide_mirror_grp, dup_parent)
        dup_guide.parent = dup_parent
        try:
            try:
                pm.delete(dup_guide.p_line)
            except:
                pass
            dup_guide.do_parent_line()
        except:
            pass

        if 'Foot' in self.module_name:
            dup_guide.set_parent()
        print dup_guide.base_ctrl.getAttr('module_joints')
        dup_guide.base_ctrl.attr('overrideEnabled').set(1)
        dup_guide.base_ctrl.attr('overrideDisplayType').set(1)
        pm.select(self.base_ctrl)

    @staticmethod
    def create_curve_from_sel():
        edge_sel = pm.ls(sl=True)[0]
        type(edge_sel)
        if pm.nodeType(edge_sel) == 'mesh':
            pm.polyToCurve(form=2, degree=1, conformToSmoothMeshPreview=1)
            edge = pm.ls(sl=True)[0]
            edge.attr('overrideEnabled').set(1)
            edge.attr('overrideColor').set(9)
            return edge
        else:
            print('No edges selected')

    @staticmethod
    def cv_loc(ctrl_name, r=0.3):
        """Create and return a cvLocator curve to be usually used in the guideSystem and the clusterHandle to shapeSize.
        """
        # create curve:
        curve = pm.curve(n=ctrl_name, d=1,
                         p=[(0, 0, r), (0, 0, -r), (0, 0, 0), (r, 0, 0), (-r, 0, 0), (0, 0, 0), (0, r, 0), (0, -r, 0)])
        # create an attribute to be used as guide by module:
        pm.addAttr(curve, longName="nJoint", attributeType='long')
        pm.setAttr(curve + ".nJoint", 1)
        # rename curveShape:
        tools.rename_shape([curve])

        return curve

    def cv_joint_loc(self, ctrl_name, r=0.3):
        """Create and return a cv_loc curve to be  used in the guideSystem and the clusterHandle to shapeSize.
        """
        # create locator curve:
        loc = pm.curve(n=ctrl_name + "_CvLoc", d=1,
                       p=[(0, 0, r), (0, 0, -r), (0, 0, 0), (r, 0, 0), (-r, 0, 0), (0, 0, 0), (0, r, 0),
                          (0, -r, 0)])
        arrow5 = pm.curve(n=ctrl_name + "_CvArrow5", d=1,
                          p=[(0, 0, 1.2 * r), (0.09 * r, 0, 1 * r), (-0.09 * r, 0, 1 * r), (0, 0, 1.2 * r)])
        arrow6 = pm.curve(n=ctrl_name + "_CvArrow6", d=1,
                          p=[(0, 0, 1.2 * r), (0, 0.09 * r, 1 * r), (0, -0.09 * r, 1 * r), (0, 0, 1.2 * r)])
        arrow5.attr('ry').set(90)
        arrow6.attr('ry').set(90)

        pm.makeIdentity([arrow5, arrow6], apply=True, r=True)
        DeleteHistory()

        # rename curveShape:
        # arrow1, arrow2, arrow3, arrow4,
        curve_list = [loc, arrow5, arrow6]

        tools.rename_shape(curve_list)
        # create ball curve:
        ball_ctrl = shapes.sphere(name=ctrl_name + 'ball', scale=0.7 * r)
        # parent shapes to transform:
        orient_offset = pm.createNode('transform', n=self.name + '_orient_offset')
        orient_offset.attr('ry').set(-90)
        loc_ctrl = pm.group(name=ctrl_name + '_guide', empty=True)
        pm.parent(loc_ctrl, orient_offset)
        ball_shapes = pm.listRelatives(ball_ctrl, shapes=True, children=True)
        for ballChildren in ball_shapes:
            pm.setAttr(ballChildren + ".template", 1)
            pm.parent(ballChildren, loc_ctrl, relative=True, shape=True)
        pm.delete(ball_ctrl)
        for transform in curve_list:
            pm.parent(pm.listRelatives(transform, shapes=True, children=True)[0], loc_ctrl, relative=True,
                      shape=True)
            pm.delete(transform)
        # create an attribute to be used as guide by module:
        pm.addAttr(loc_ctrl, longName="nJoint", attributeType='long')
        pm.setAttr(loc_ctrl + ".nJoint", 1)
        pm.select(None)
        loc_ctrl.attr('ry').set(0)

        temp_j = pm.joint(name=ctrl_name + '_jnt', p=[0, 0, 0], r=0.01)
        temp_j2 = pm.joint(name=ctrl_name + '_jnt', p=[0, 0, 2])
        pm.select(loc_ctrl)
        pm.toggle(localAxis=True)
        pm.select(None)

        pm.joint(temp_j, e=True, zso=True, oj='xyz', sao='yup')
        pm.delete(temp_j2)
        pm.parent(temp_j, loc_ctrl)
        temp_j.attr('overrideEnabled').set(1)
        temp_j.attr('overrideDisplayType').set(1)

        pm.select(None)
        return loc_ctrl, orient_offset, temp_j


class DrawArm(Guides):
    """
    """
    arm_guides_list = []

    def __init__(self, prefix, parent='', space_switches=''):
        super(DrawArm, self).__init__()
        self.prefix = prefix
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + prefix
        self.driven_joints = []
        self.controllers = []
        self.parent = parent
        self.space_switches = space_switches

    def draw(self):
        self.create()
        pm.select(None)

        self.center_loc_ctrl = pm.rename(self.center_loc_ctrl, self.center_loc_ctrl.replace('_guide', 'Upper_guide'))
        self.center_joint = pm.rename(self.center_joint, self.center_joint.replace('_jnt', 'Upper_jnt'))
        clavicle_loc, clavicle_offset, clavicle_joint = self.cv_joint_loc(self.name + 'Clavicle')
        clavicle_offset.attr('tz').set(-2)

        elbow_loc, elbow_offset, elbow_joint = self.cv_joint_loc(self.name + 'Lower')
        elbow_offset.attr('tz').set(3)

        wrist_loc, wrist_offset, wrist_joint = self.cv_joint_loc(self.name + 'End')
        wrist_offset.attr('tz').set(6)

        pm.parent(clavicle_offset, elbow_offset, wrist_offset, self.base_ctrl)

        self.base_ctrl.attr('rx').set(-90)
        self.base_ctrl.attr('rz').set(-90)

        l1 = tools.create_line(clavicle_loc, self.center_loc_ctrl, clavicle_loc + '_crv')
        l2 = tools.create_line(self.center_loc_ctrl, elbow_loc, self.center_loc_ctrl + '_crv')
        l3 = tools.create_line(elbow_loc, wrist_loc, elbow_loc + '_crv')
        pm.parent(l1[0], l2[0], l3[0], self.parts, r=True)

        a = pm.aimConstraint(self.center_loc_ctrl, clavicle_loc, mo=True)
        c = pm.aimConstraint(wrist_loc, elbow_offset, mo=True)

        pm.delete(a, c)
        pm.parent(elbow_offset, wrist_offset, self.center_loc_ctrl)

        pm.setAttr(elbow_loc + '.tz', l=True)
        pm.setAttr(wrist_loc + '.tz', l=True)

        pm.select(None)
        self.driven_joints.insert(0, clavicle_joint)
        self.driven_joints.append(elbow_joint)
        self.driven_joints.append(wrist_joint)

        for i, j in enumerate(self.driven_joints):
            if i > 0:
                b = pm.aimConstraint(self.driven_joints[i], self.driven_joints[i - 1],
                                     upVector=[0, 0, 0], worldUpType='none', mo=True)

        elbow_offset.attr('ty').set(1)

        self.controllers.insert(0, clavicle_loc)
        self.controllers.append(elbow_loc)
        self.controllers.append(wrist_loc)
        pm.select(None)
        self.do_parent_line()
        self.do_parent()

        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self


class DrawEye(Guides):
    def __init__(self,
                 prefix,
                 parent='',
                 space_switches=''):
        self.prefix = prefix
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + prefix
        self.driven_joints = []
        self.controllers = []
        self.parent = parent
        self.space_switches = space_switches

    def draw(self):
        self.create()
        pm.select(None)

        end_loc, end_offset, end_joint = self.cv_joint_loc(self.name + 'End')
        end_offset.attr('tz').set(0.5)

        lookat_loc, lookat_offset, lookat_joint = self.cv_joint_loc(self.name + 'LookAt')
        lookat_offset.attr('tz').set(5)

        tools.lock_channels(lookat_loc, channels=['t'], t_axis=['y', 'z'])
        tools.lock_channels(end_loc, channels=['t'], t_axis=['y', 'z'])

        pm.parent(end_offset, lookat_offset, self.center_loc_ctrl)

        l2 = tools.create_line(self.center_loc_ctrl, end_loc, self.center_loc_ctrl + '_crv')
        l3 = tools.create_line(end_loc, lookat_loc, end_loc + '_crv')
        pm.parent(l2[0], l3[0], self.parts, r=True)

        pm.delete(pm.aimConstraint(lookat_loc, end_offset, mo=True))

        pm.select(None)
        self.driven_joints.append(end_joint)
        self.driven_joints.append(lookat_joint)

        for i, j in enumerate(self.driven_joints):
            if i > 0:
                b = pm.aimConstraint(self.driven_joints[i], self.driven_joints[i - 1],
                                     upVector=[0, 0, 0], worldUpType='none', mo=True)

        self.controllers.append(end_loc)
        self.controllers.append(lookat_loc)
        pm.select(None)
        self.p_line = self.do_parent_line()
        self.do_parent()
        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self


class DrawFoot(Guides):
    def __init__(self,
                 prefix,
                 parent='',
                 space_switches=''):
        self.prefix = prefix
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + prefix
        self.driven_joints = []
        self.controllers = []
        self.parent = parent
        self.space_switches = space_switches

    def draw(self):
        self.create()
        pm.select(None)

        string_attr_list = ['toe_loc', 'heel_loc']
        for string_attr in string_attr_list:
            pm.addAttr(self.base_ctrl, longName=string_attr, dataType='string')

        ball_loc, ball_offset, ball_joint = self.cv_joint_loc(self.name + 'Ball')
        ball_offset.attr('tz').set(1.5)

        pm.select(None)
        # toe_tip_loc = pm.spaceLocator(n=self.prefix + 'toe_loc')

        toe_loc, toe_offset, toe_joint = self.cv_joint_loc(self.name + 'Toe')
        toe_tip_loc = ctrl.Control(prefix=self.prefix + 'toe_loc',
                                   scale=0.3,
                                   parent=toe_loc,
                                   shape='cube',
                                   channels=['v']).create()

        toe_offset.attr('tz').set(3)
        toe_tip_loc.get_offset().attr('ty').set(-0.5)

        heel_loc = ctrl.Control(prefix=self.prefix + 'heel_loc',
                                scale=0.3,
                                parent=self.base_ctrl,
                                shape='cube',
                                channels=['v']).create()
        heel_loc.get_offset().attr('tz').set(-1.5)
        heel_loc.get_offset().attr('ty').set(-1.5)
        self.base_ctrl.attr('toe_loc').set(toe_tip_loc.get_ctrl())
        self.base_ctrl.attr('heel_loc').set(heel_loc.get_ctrl())

        pm.parent(ball_offset, toe_offset, self.base_ctrl)

        l2 = tools.create_line(self.center_loc_ctrl, ball_loc, self.center_loc_ctrl + '_crv')
        l3 = tools.create_line(ball_loc, toe_loc, ball_loc + '_crv')
        pm.parent(l2[0], l3[0], self.parts, r=True)

        pm.delete(pm.aimConstraint(toe_loc, ball_offset, mo=True))

        pm.setAttr(ball_loc + '.tz', l=True)
        pm.setAttr(toe_loc + '.tz', l=True)

        pm.select(None)
        self.driven_joints.append(ball_joint)
        self.driven_joints.append(toe_joint)

        for i, j in enumerate(self.driven_joints):
            if i > 0:
                b = pm.aimConstraint(self.driven_joints[i], self.driven_joints[i - 1],
                                     upVector=[0, 0, 0], worldUpType='none', mo=True)

        ball_offset.attr('ty').set(-1)
        toe_offset.attr('ty').set(-1)

        self.controllers.extend([ball_loc, toe_loc, toe_tip_loc.get_ctrl(), heel_loc.get_ctrl()])

        pm.select(None)
        self.do_parent_line()
        self.do_parent()
        if self.get_parent_module():
            if 'Limb' in self.get_parent_module().name():
                pm.hide(self.center_loc_ctrl)
                self.base_ctrl.attr('tx').set(0)
                self.base_ctrl.attr('ty').set(0)
                self.base_ctrl.attr('tz').set(0)
                print "FOOT DRIVEN JOINTS BEFORE: " + str(self.driven_joints)
                self.driven_joints.pop(0)
                print "FOOT DRIVEN JOINTS AFTER: " + str(self.driven_joints)

        self.center_loc_ctrl = pm.rename(self.center_loc_ctrl,
                                         self.center_loc_ctrl.replace('_guide', 'Ankle_guide'))
        self.center_joint = pm.rename(self.center_joint, self.center_joint.replace('_jnt', 'Ankle_jnt'))
        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self

    def set_parent(self):
        self.do_parent()
        self.base_ctrl.attr('module_joints').set('')
        if self.get_parent_module():
            if 'Limb' in self.get_parent_module().name():

                pm.hide(self.center_loc_ctrl)
                print "FOOT DRIVEN JOINTS BEFORE: " + str(self.driven_joints)
                self.driven_joints.pop(0)
                print "FOOT DRIVEN JOINTS AFTER: " + str(self.driven_joints)
        self.get_module_joints()
        # self.base_one_scale()


class DrawLimb(Guides):
    """
    """
    arm_guides_list = []

    def __init__(self,
                 prefix,
                 parent='',
                 space_switches=''):
        self.prefix = prefix
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + prefix
        self.driven_joints = []
        self.controllers = []
        self.parent = parent
        self.space_switches = space_switches

    def draw(self):
        self.create()
        pm.select(None)

        self.center_loc_ctrl = pm.rename(self.center_loc_ctrl, self.center_loc_ctrl.replace('_guide', 'Upper_guide'))
        self.center_joint = pm.rename(self.center_joint, self.center_joint.replace('_jnt', 'Upper_jnt'))

        elbow_loc, elbow_offset, elbow_joint = self.cv_joint_loc(self.name + 'Lower')
        elbow_offset.attr('tz').set(3)
        # elbow_offset.attr('tz').set(-1)

        wrist_loc, wrist_offset, wrist_joint = self.cv_joint_loc(self.name + 'End')
        wrist_offset.attr('tz').set(6)
        # wrist_offset.attr('tz').set(0)

        pm.parent(elbow_offset, wrist_offset, self.base_ctrl)

        self.base_ctrl.attr('rx').set(90)

        l2 = tools.create_line(self.center_loc_ctrl, elbow_loc, self.center_loc_ctrl + '_crv')
        l3 = tools.create_line(elbow_loc, wrist_loc, elbow_loc + '_crv')
        pm.parent(l2[0], l3[0], self.parts, r=True)

        c = pm.aimConstraint(wrist_loc, elbow_offset, mo=True)

        pm.delete(c)
        pm.parent(elbow_offset, wrist_offset, self.center_loc_ctrl)

        pm.setAttr(elbow_loc + '.tz', l=True)
        pm.setAttr(wrist_loc + '.tz', l=True)

        pm.select(None)
        self.driven_joints.append(elbow_joint)
        self.driven_joints.append(wrist_joint)

        for i, j in enumerate(self.driven_joints):
            if i > 0:
                b = pm.aimConstraint(self.driven_joints[i], self.driven_joints[i - 1],
                                     upVector=[0, 0, 0], worldUpType='none', mo=True)

        elbow_offset.attr('ty').set(1)

        self.controllers.append(elbow_loc)
        self.controllers.append(wrist_loc)
        self.do_parent_line()
        self.do_parent()
        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self


class DrawMaster(Guides):
    def __init__(self, prefix=''):
        Guides.__init__(self)
        self.prefix = 'c_root'
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + self.prefix

    def draw(self):
        self.create()
        pm.select(None)

        self.base_ctrl.attr('rotateX').set(-90)

        temp_global = ctrl.Control(prefix=self.prefix, shape='master', channels=['t', 'r', 'v'])
        temp_global.create()

        pm.parent(temp_global.get_offset(), self.base_ctrl)

        for axis in 'XYZ':
            pm.connectAttr(self.radius_ctrl + '.ty', temp_global.get_ctrl() + '.scale' + axis)

        # tools.lock_channels(self.base_ctrl, channels=['s'])
        tools.unlock_channels(self.base_ctrl, channels=['v'])

        pm.select(None)

        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self


class DrawMeta(Guides):
    """TODO: Add finger function to draw finger joints from meta guides."""

    def __init__(self,
                 prefix,
                 parent='',
                 space_switches='',
                 amount=4):
        self.prefix = prefix
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + prefix
        self.driven_joints = []
        self.controllers = []
        self.parent = parent
        self.space_switches = space_switches
        self.amount = amount
        self.fingers_controllers = []

    def draw(self):
        self.create()
        pm.select(None)

        self.center_loc_ctrl = pm.rename(self.center_loc_ctrl, self.center_loc_ctrl.replace('_guide', 'A_guide'))
        self.center_joint = pm.rename(self.center_joint, self.center_joint.replace('_jnt', 'A_jnt'))
        self.loc_offset.attr('ry').set(-180)

        trans_mult = 0
        lines = []
        for i in range(self.amount - 1):
            i += 1
            alpha = i + 1
            trans_mult += 0.5
            meta_loc, meta_offset, meta_joint = self.cv_joint_loc(self.name + tools.int_to_letter(alpha))
            meta_offset.attr('tz').set(trans_mult)
            meta_offset.attr('ry').set(-180)

            pm.parent(meta_offset, self.base_ctrl)
            self.driven_joints.append(meta_joint)
            self.controllers.append(meta_loc)

            print meta_loc
            grp, line = tools.create_line(self.controllers[i - 1], meta_loc,
                                          self.controllers[i - 1] + '_crv')
            lines.append(grp)
            pm.parent(grp, self.parts, r=True)

        self.base_ctrl.attr('ry').set(90)

        self.do_parent_line()
        pm.select(None)

        splay_up_pos = ctrl.Control(prefix=self.prefix + 'splay_pos',
                                    scale=0.2,
                                    parent=self.base_ctrl,
                                    shape='diamond',
                                    channels=['v']).create()
        try:
            pm.delete(pm.parentConstraint(self.controllers[0], self.controllers[-1], splay_up_pos.get_offset()))
        except:
            pass

        splay_up_pos.get_offset().attr('ty').set(1.5)
        pm.addAttr(self.base_ctrl, longName='splay_up_pos', dataType='string')
        self.base_ctrl.attr('splay_up_pos').set(splay_up_pos.get_ctrl())

        self.do_parent()
        for j in self.driven_joints:
            value = self.base_ctrl.getAttr('module_joints')
            if value:
                self.base_ctrl.attr('module_joints').set(value + '.' + j)
            else:
                self.base_ctrl.attr('module_joints').set(j)
        self.base_one_scale()
        self.add_fingers()

        pm.select(self.base_ctrl)
        self.controllers.append(splay_up_pos.get_ctrl())

        return self

    def add_fingers(self):
        pm.addAttr(self.base_ctrl, longName='finger_joints', dataType='string')
        # loop through every meta controller and create a 4 chain finger (incl end joint)
        prefix = self.module_name + '___' + self.prefix.replace('meta', 'finger')
        first_finger_joints = []
        module_joints = ''
        for i, ctrl in enumerate(self.controllers):
            lines = []
            trans_mult = 0.5
            finger_joints = []
            finger_controls = []
            module_joints += '.' + self.driven_joints[i]
            for integer in range(4):
                finger_loc, finger_offset, finger_joint = self.cv_joint_loc(prefix + tools.int_to_letter(i)
                                                                            + tools.int_to_letter(integer))
                if integer == 0:
                    print 'FIRST INTEGER'
                    pm.delete(pm.parentConstraint(ctrl, finger_offset))
                    b = pm.aimConstraint(finger_loc, self.driven_joints[i],
                                         upVector=[0, 0, 0], worldUpType='none', mo=True)

                    pm.parent(finger_offset, self.controllers[i])
                    finger_offset.attr('tx').set(1.25)
                    finger_joints.append(finger_joint)
                    finger_controls.append(finger_loc)
                    pm.parent(finger_offset, self.base_ctrl)
                    grp, line = tools.create_line(self.controllers[i], finger_loc,
                                                  self.controllers[i] + '_crv')
                    lines.append(grp)
                    pm.parent(grp, self.parts, r=True)
                    first_finger_joints.append(finger_joint)
                    module_joints += '#' + finger_joint
                else:
                    print 'NOOOOOT FIRST INTEGER'

                    pm.delete(pm.parentConstraint(finger_controls[integer - 1], finger_offset))
                    b = pm.aimConstraint(finger_loc, finger_joints[integer - 1],
                                         upVector=[0, 0, 0], worldUpType='none', mo=True)
                    pm.parent(finger_offset, finger_controls[integer - 1])
                    finger_offset.attr('tx').set(trans_mult)
                    pm.parent(finger_offset, self.base_ctrl)
                    grp, line = tools.create_line(finger_controls[integer - 1], finger_loc,
                                                  finger_controls[integer - 1] + '_crv')
                    lines.append(grp)
                    pm.parent(grp, self.parts, r=True)
                    finger_joints.append(finger_joint)
                    finger_controls.append(finger_loc)
                    module_joints += '#' + finger_joint

        if first_finger_joints:
            for j in first_finger_joints:
                value = self.base_ctrl.getAttr('finger_joints')
                if value:
                    self.base_ctrl.attr('finger_joints').set(value + '#' + j)
                else:
                    self.base_ctrl.attr('finger_joints').set(j)
        self.base_ctrl.attr('module_joints').set(module_joints)

        pm.select(self.base_ctrl)


class DrawSpine(Guides):
    def __init__(self,
                 prefix,
                 parent='',
                 space_switches='',
                 amount=4,
                 ):
        Guides.__init__(self)
        self.prefix = prefix
        self.parent = parent
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + self.prefix
        self.amount = amount

    def draw(self):
        self.create()
        pm.select(None)

        self.center_loc_ctrl = pm.rename(self.center_loc_ctrl, self.center_loc_ctrl.replace('_guide', 'A_guide'))
        self.center_joint = pm.rename(self.center_joint, self.center_joint.replace('_jnt', 'A_jnt'))

        trans_mult = 0
        lines = []
        for i in range(self.amount - 1):
            i += 1
            alpha = i
            trans_mult += 2
            spine_loc, spine_offset, spine_joint = self.cv_joint_loc(self.name + tools.int_to_letter(alpha))
            spine_offset.attr('tz').set(trans_mult)

            pm.parent(spine_offset, self.base_ctrl)
            self.driven_joints.append(spine_joint)
            self.controllers.append(spine_loc)

            grp, line = tools.create_line(self.controllers[i - 1], self.controllers[i],
                                          self.controllers[i - 1] + '_crv')
            lines.append(grp)
            a = pm.aimConstraint(self.controllers[i], self.controllers[i - 1], mo=True)
            if self.driven_joints[i - 1] != self.driven_joints[0]:
                b = pm.aimConstraint(self.driven_joints[i], self.driven_joints[i - 1],
                                     upVector=[0, 0, 0], worldUpType='none', mo=True)
            pm.delete(a)

        self.base_ctrl.attr('rx').set(-90)
        pm.parent(lines, self.parts, r=True)
        self.do_parent_line()
        pm.select(None)

        self.do_parent()
        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self


class DrawNeck(Guides):
    def __init__(self,
                 prefix,
                 parent='',
                 space_switches='',
                 amount=5,
                 ):
        Guides.__init__(self)
        self.prefix = prefix
        self.parent = parent
        self.module_name = re.findall('[A-Z][^A-Z]*', str(self.__class__.__name__))[-1]
        self.name = self.module_name + '___' + self.prefix
        self.amount = amount

    def draw(self):
        self.create()
        pm.select(None)

        self.center_loc_ctrl = pm.rename(self.center_loc_ctrl, self.center_loc_ctrl.replace('_guide', 'A_guide'))
        self.center_joint = pm.rename(self.center_joint, self.center_joint.replace('_jnt', 'A_jnt'))

        trans_mult = 0
        lines = []
        for i in range(self.amount - 1):
            i += 1
            alpha = i + 1
            trans_mult += 0.5
            spine_loc, spine_offset, spine_joint = self.cv_joint_loc(self.name + tools.int_to_letter(alpha))

            spine_offset.attr('tz').set(trans_mult)

            pm.parent(spine_offset, self.base_ctrl)
            self.driven_joints.append(spine_joint)
            self.controllers.append(spine_loc)

            grp, line = tools.create_line(self.controllers[i - 1], self.controllers[i],
                                          self.controllers[i - 1] + '_crv')
            lines.append(grp)
            a = pm.aimConstraint(self.controllers[i], self.controllers[i - 1], mo=True)
            if self.driven_joints[i - 1] != self.driven_joints[0]:
                b = pm.aimConstraint(self.driven_joints[i], self.driven_joints[i - 1],
                                     upVector=[0, 0, 0], worldUpType='none', mo=True)
            pm.delete(a)

        self.base_ctrl.attr('rx').set(-90)
        pm.parent(lines, self.parts, r=True)
        self.do_parent_line()
        pm.select(None)

        self.do_parent()
        self.get_module_joints()
        self.base_one_scale()
        pm.select(self.base_ctrl)

        return self
