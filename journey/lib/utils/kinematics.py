"""
module containing different class kinematics for ik and fk.
"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
reload(ctrl)
reload(tools)


class FK:
    """
    TODO: Squash and stretch
    NOTE: feed driven FK chain. no additional chains should be included.
    """
    fk_dict = {}

    def __init__(self,
                 prefix='new',
                 scale=1.0,
                 driven='',
                 rot_to=True,
                 parent=True,
                 shape='circle',
                 channels=['s', 'v'],
                 rig_module=None,
                 ):

        self.prefix = prefix
        self.scale = scale
        self.driven = driven
        self.rot_to = rot_to
        self.parent = parent
        self.shape = shape
        self.channels = channels
        self.rig_module = rig_module
        self.fk_ctrl = None

    def ctrl(self, *args):
        # Check if driven is a str, then convert to list
        self.driven = tools.list_check(self.driven)

        for i, joint in enumerate(self.driven):
            fk_ctrl = ctrl.Control(prefix=self.prefix,
                                   scale=self.scale,
                                   trans_to=joint,
                                   rot_to=joint,
                                   rot_shape=True,
                                   parent='',
                                   shape='circle',
                                   channels=['s', 'v'])

            if self.rot_to is False:
                fk_ctrl.rot_to = False

            fk_ctrl.create()
            self.fk_dict.update({joint: fk_ctrl})

            if joint != self.driven[0]:
                tools.matrix_constraint(self.fk_dict[self.driven[i-1]].get_ctrl(),
                                        self.fk_dict[self.driven[i]].get_offset())

        # fk.fk_dict['joint1'].set_color('blue') <-- FOR CALLING SPECIFIC FK JOINT CONTROLLER IF NEEDED.
        # for i, ctl in enumerate(self.fk_dict):
        #     if ctl is not list(self.fk_dict.keys())[-1]:
        #         ctl1 = list(self.fk_dict.keys())[i]
        #         ctl2 = list(self.fk_dict.keys())[i+1]
        #         matrix_constraint(self.fk_dict[ctl1].get_ctrl(), self.fk_dict[ctl2].get_offset())

        return self.fk_dict

    def create(self, *args):
        ctrls = self.ctrl()
        self.driven = tools.list_check(self.driven)
        for driven in self.driven:
            tools.matrix_constraint(self.fk_dict[''+driven+''].get_ctrl(), driven)


class IK:
    def __init__(self,
                 prefix='new',
                 scale=1.0,
                 driven='',
                 rot_to=True,
                 parent=True,
                 shape='circle',
                 channels=['s', 'v'],
                 rig_module=None,
                 ):
        self.prefix = prefix
        self.scale = scale
        self.driven = driven
        self.rot_to = rot_to
        self.parent = parent
        self.shape = shape
        self.channels = channels
        self.rig_module = rig_module
        self.ik_ctrl = ''
        self.ik_hdl = ''
        self.pv_ctrl = ''
        self.pv_loc = ''

    def create(self, *args):
        self.ik_ctrl = ctrl.Control(prefix=self.prefix + 'IK', trans_to=self.driven[-1],
                                    rot_to=self.driven[-1], scale=self.scale, shape='cube')
        self.ik_ctrl.create()
        tools.parent_rm(self.ik_ctrl.get_offset(), self.rig_module, 'controls_grp')

        ik_hdl_grp = pm.createNode("transform", n=self.prefix + 'HdlOffset_grp')
        self.ik_hdl = pm.ikHandle(n=self.prefix + 'Main_hdl', sol='ikSCsolver',
                                  sj=self.driven[0], ee=self.driven[-1])[0]
        pm.parent(self.ik_hdl, ik_hdl_grp)
        pm.parent(ik_hdl_grp, self.ik_ctrl.get_ctrl())
        tools.matrix_constraint(self.ik_ctrl.get_ctrl(), self.driven[-1], mo=True, channels=['r'])

    def pole_vector(self, *args):
        # change main ik handle to RP solver
        temp_hdl = pm.ikHandle(n=self.prefix + 'Temp_hdl', sol='ikRPsolver',
                               sj=self.driven[0], ee=self.driven[-1])[0]
        pm.ikHandle(self.ik_hdl, edit=True, solver='ikRPsolver')

        for axis in ['X', 'Y', 'Z']:
            self.ik_hdl.attr('poleVector' + axis).set(temp_hdl.getAttr('poleVector' + axis))
            self.ik_hdl.attr('rotate' + axis).set(0)

        pm.delete(temp_hdl)

        # create pv ctrl and pv constraint
        self.pv_ctrl = ctrl.Control(prefix=self.prefix + 'PoleVec', scale=self.scale,
                                    shape='fancy_sphere', channels=['r', 's', 'v'])
        self.pv_ctrl.create()
        tools.parent_rm(self.pv_ctrl, self.rig_module, 'controls_grp')

        self.pv_loc = tools.get_pole_vec_pos(self.driven)
        self.pv_loc.attr('visibility').set(0)
        pm.rename(self.pv_loc, self.prefix + 'poleVec_loc')

        tools.parent_rm(self.pv_loc, self.rig_module, 'part_grp')
        pm.delete(pm.parentConstraint(self.pv_loc, self.pv_ctrl.get_offset()))

        tools.matrix_constraint(self.pv_ctrl.get_ctrl(), self.pv_loc, mo=True)
        pm.poleVectorConstraint(self.pv_ctrl.get_ctrl(), self.ik_hdl)
        tools.create_line(start=self.driven[tools.get_mid_joint(self.driven)], end=self.pv_ctrl.get_ctrl(), prefix="")

    def stretch(self, *args):
        if not self.pv_ctrl.get_ctrl():
            self.pole_vector()
        # define joints to stretch
        def_joints = []
        mid_joint = tools.get_mid_joint(self.driven)
        upper_joint = self.driven[0]
        mid_joint = self.driven[mid_joint]
        end_joint = self.driven[-1]

        def_joints = tools.joint_duplicate(joint_chain=[upper_joint, mid_joint, end_joint], joint_type='DEF')

        # create IK options
        pm.addAttr(self.ik_ctrl.get_ctrl(), longName='IKOptions', nn='IK OPTIONS',
                   at="enum", en='=======')
        pm.setAttr(self.ik_ctrl.get_ctrl() + '.IKOptions', e=True, channelBox=True)
        pm.addAttr(self.ik_ctrl.get_ctrl(), shortName='stretchP', longName='Stretch',
                   dv=0, min=0, max=1, at="float", k=1)
        pm.addAttr(self.ik_ctrl.get_ctrl(), shortName='softP', longName='SoftenIK',
                   dv=0, min=0, max=100, at="float", k=1)
        pm.addAttr(self.ik_ctrl.get_ctrl(), shortName='pinP', longName='PinElbow',
                   dv=0, min=0, max=1, at="float", k=1)

        # create nodes for the stretchy setup
        const = pm.createNode('multiplyDivide', n=self.prefix + 'constant_md')
        const.attr('input1X').set(1)
        def_full_dist = pm.createNode('addDoubleLinear', n=self.prefix + '_def_full_dist')
        # stretch nodes
        mp_div = pm.createNode('multiplyDivide', n=self.prefix + '_stretch_val_md')
        cnd = pm.createNode('condition', n=self.prefix + '_stretch_cnd')
        bta = pm.createNode('blendTwoAttr', n=self.prefix + '_up_stretch_bta')
        # soften nodes
        mdl = pm.createNode('multDoubleLinear', n=self.prefix + '_soften_normalize_mdl')
        adl = pm.createNode('addDoubleLinear', n=self.prefix + '_soften_val_adl')
        # lock nodes
        lock_md = pm.createNode('multiplyDivide', n=self.prefix + '_lock_val_md')
        lock_up_bta = pm.createNode('blendTwoAttr', n=self.prefix + '_lock_up_bta')
        lock_lo_bta = pm.createNode('blendTwoAttr', n=self.prefix + '_lock_lo_bta')
        # end mdl nodes
        up_dist_mdl = pm.createNode('multDoubleLinear', n=self.prefix + '_up_dist_mdl')
        lo_dist_mdl = pm.createNode('multDoubleLinear', n=self.prefix + '_lo_dist_mdl')
        # empty node at first joint
        upper_null = pm.createNode('transform', n=self.prefix + 'upper_null')
        pm.delete(pm.parentConstraint(upper_joint, upper_null))

        # change operations
        mp_div.attr('operation').set(2)
        cnd.attr('operation').set(2)
        lock_md.attr('operation').set(2)

        # make three measurements - upper, lower, and first to last joint
        up_def_dist = tools.measure(def_joints[0], def_joints[1])
        lo_def_dist = tools.measure(def_joints[1], def_joints[-1])
        full_dist = tools.measure(upper_null, self.ik_ctrl.get_ctrl())

        # make measurements from start and end to pole vector
        pole_up_dist = tools.measure(upper_null, self.pv_ctrl.get_ctrl())
        pole_lo_dist = tools.measure(self.ik_ctrl.get_ctrl(), self.pv_ctrl.get_ctrl())

        # get joints chain distance
        pm.connectAttr(up_def_dist + '.distance', def_full_dist + '.input1')
        pm.connectAttr(lo_def_dist + '.distance', def_full_dist + '.input2')

        # stretch setup
        pm.connectAttr(full_dist + '.distance', mp_div + '.input1X')
        pm.connectAttr(full_dist + '.distance', cnd + '.firstTerm')
        pm.connectAttr(def_full_dist + '.output', mp_div + '.input2X')
        pm.connectAttr(def_full_dist + '.output', cnd + '.secondTerm')
        pm.connectAttr(mp_div + '.output', cnd + '.colorIfTrue')

        pm.connectAttr(const + '.outputX', bta + '.input[0]')
        pm.connectAttr(cnd + '.outColorR', bta + '.input[1]')
        pm.connectAttr(self.ik_ctrl.get_ctrl() + '.stretchP', bta + '.attributesBlender')

        pm.connectAttr(self.ik_ctrl.get_ctrl() + '.softP', mdl + '.input1')
        mdl.attr('input2').set(0.001)

        pm.connectAttr(bta + '.output', adl + '.input1')
        pm.connectAttr(mdl + '.output', adl + '.input2')

        pm.connectAttr(pole_up_dist + '.distance', lock_md + '.input1X')
        pm.connectAttr(pole_lo_dist + '.distance', lock_md + '.input1Y')
        pm.connectAttr(up_def_dist + '.distance', lock_md + '.input2X')
        pm.connectAttr(lo_def_dist + '.distance', lock_md + '.input2Y')

        pm.connectAttr(self.ik_ctrl.get_ctrl() + '.pinP', lock_up_bta + '.attributesBlender')
        pm.connectAttr(adl + '.output', lock_up_bta + '.input[0]')
        pm.connectAttr(lock_md + '.outputX', lock_up_bta + '.input[1]')
        pm.connectAttr(self.ik_ctrl.get_ctrl() + '.pinP', lock_lo_bta + '.attributesBlender')
        pm.connectAttr(adl + '.output', lock_lo_bta + '.input[0]')
        pm.connectAttr(lock_md + '.outputY', lock_lo_bta + '.input[1]')

        up_dist_mdl.attr('input1').set(pm.getAttr(up_def_dist + '.distance'))
        lo_dist_mdl.attr('input1').set(pm.getAttr(lo_def_dist + '.distance'))
        pm.connectAttr(lock_up_bta + '.output', up_dist_mdl + '.input2')
        pm.connectAttr(lock_lo_bta + '.output', lo_dist_mdl + '.input2')

        pm.connectAttr(up_dist_mdl + '.output', mid_joint + '.tx')
        pm.connectAttr(lo_dist_mdl + '.output', end_joint + '.tx')


class Spline:
    def __init__(self, *args):
        pass

    def make_stretchy(self, *args):
        pass