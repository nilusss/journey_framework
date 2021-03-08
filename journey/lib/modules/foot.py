"""
module containing foot setup.
create a three chain setup

NOTE: inherit set_base and set_prefix from Module class
TODO: Foot ik controller parent constraint til foot module, remove parent constraint to IK Handle. Parent constraint ball locator to IK Handle Offset grp.
TODO: parent constrain leg_end_joint to leg_endik_joint leg_endfk_jnt
TODO: add toe tap by constraining toe IK
TODO: SHOULD WORK, NEED MORE TESTING - module doesn't work correctly when parented to leg module. Leg end joint doesn't rotate when the ankle is lifted
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
import pdb


class Foot(lo.Module):
    def __init__(self,
                 ankle_joint,
                 ball_joint,
                 toe_joint,
                 toe_tip,
                 heel,
                 foot_ctrl='',
                 blend_ctrl='',
                 attach_joint='',
                 ik_hdl_offset='',
                 leg_ik_end='',
                 leg_fk_end='',
                 prefix='new',
                 scale=1.0,
                 base_rig=None
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.ankle_joint = ankle_joint
        self.ball_joint = ball_joint
        self.toe_joint = toe_joint
        self.toe_tip = toe_tip
        self.leg_ik_end = leg_ik_end
        self.leg_fk_end = leg_fk_end
        self.heel = heel
        self.foot_ctrl = foot_ctrl
        self.blend_ctrl = blend_ctrl
        self.attach_joint = attach_joint
        self.ik_hdl_offset = ik_hdl_offset
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

        self.foot_ctrl_nurb = ''

    def create(self, *args):
        # create module from parent class
        super(Foot, self).create_structure()

        if not self.foot_ctrl:
            self.foot_ctrl = ctrl.Control(prefix=self.prefix, trans_to=self.ankle_joint,
                                          scale=self.scale, parent=self.controls_grp, shape='cube')
            self.foot_ctrl.create()

            self.foot_ctrl_nurb = self.foot_ctrl.get_ctrl()

            ankle_ik = self.ankle_joint
            ball_ik = self.ball_joint
            toe_ik = self.toe_joint
        else:
            self.foot_ctrl_nurb = self.foot_ctrl
            # duplicate joints if there is a foot_ctrl attached to a leg - for ik fk switching
            if self.leg_fk_end and self.leg_ik_end:
                ankle_ik = self.leg_ik_end
                ankle_fk = self.leg_fk_end
            else:
                ankle_ik = pm.duplicate(self.ankle_joint, parentOnly=True,
                                        n=self.ankle_joint.replace('result_jnt', 'IK_jnt'))[0]
                ankle_fk = pm.duplicate(self.ankle_joint, parentOnly=True,
                                        n=self.ankle_joint.replace('result_jnt', 'FK_jnt'))[0]
                pm.parent(ankle_ik, ankle_fk, self.joints_offset_grp)

            ball_ik = pm.duplicate(self.ball_joint, parentOnly=True,
                                   n=self.ball_joint.replace('result_jnt', 'IK_jnt'))[0]
            toe_ik = pm.duplicate(self.toe_joint, parentOnly=True,
                                  n=self.toe_joint.replace('result_jnt', 'IK_jnt'))[0]

            ball_fk = pm.duplicate(self.ball_joint, parentOnly=True,
                                   n=self.ball_joint.replace('result_jnt', 'FK_jnt'))[0]
            toe_fk = pm.duplicate(self.toe_joint, parentOnly=True,
                                  n=self.toe_joint.replace('result_jnt', 'FK_jnt'))[0]

            # fix chains
            driven = [self.ankle_joint, self.ball_joint, self.toe_joint]
            # fk
            fk_chain = [ankle_fk, ball_fk, toe_fk]
            pm.parent(ball_fk, ankle_fk)
            pm.parent(toe_fk, ball_fk)

            # ik
            ik_chain = [ankle_ik, ball_ik, toe_ik]
            pm.parent(ball_ik, ankle_ik)
            pm.parent(toe_ik, ball_ik)


            # create controllers for toe, ball, and heel
            if ball_fk:
                # fk
                ball_fk_ctrl = ctrl.Control(prefix=self.prefix + 'BallFK', trans_to=self.ball_joint,
                                            scale=self.scale, parent=self.controls_grp, shape='circleZ')
                ball_fk_ctrl.create()

                pm.parentConstraint(ball_fk_ctrl.get_ctrl(), ball_fk, mo=True)


        # add attributes to the foot controller
        pm.addAttr(self.foot_ctrl_nurb, shortName='footsettings', longName='FootSettings', nn='FOOT SETTINGS',
                   at="enum", keyable=False, en="=======")
        pm.setAttr(self.foot_ctrl_nurb + '.footsettings', edit=True, channelBox=True)
        pm.addAttr(self.foot_ctrl_nurb, shortName='tsa', longName='ToeStraightAngle', defaultValue=70, k=True)
        pm.addAttr(self.foot_ctrl_nurb, shortName='bla', longName='BendLimitAngle', defaultValue=45, k=True)
        pm.addAttr(self.foot_ctrl_nurb, shortName='roll', longName='FootRoll', defaultValue=0, k=True)
        pm.addAttr(self.foot_ctrl_nurb, shortName='lean', longName='Lean', defaultValue=0, k=True)
        pm.addAttr(self.foot_ctrl_nurb, shortName='toespin', longName='ToeSpin', defaultValue=0, k=True)

        # create locator offset groups and reparent them
        heel_loc_grp = pm.createNode("transform", n=self.heel + '_offset_grp')
        pm.delete(pm.parentConstraint(self.heel, heel_loc_grp))
        pm.parent(self.heel, heel_loc_grp)
        pm.setAttr(heel_loc_grp + '.v', 0)

        toe_tip_loc_grp = pm.createNode("transform", n=self.toe_tip + '_offset_grp')
        pm.delete(pm.parentConstraint(self.toe_tip, toe_tip_loc_grp))
        pm.parent(self.toe_tip, toe_tip_loc_grp)
        pm.setAttr(toe_tip_loc_grp + '.v', 0)

        ball_loc = pm.spaceLocator(n=self.ball_joint.replace('result_jnt', 'loc'))
        ball_loc_grp = pm.createNode("transform", n=ball_loc + '_offset_grp')
        pm.parent(ball_loc, ball_loc_grp)
        pm.delete(pm.parentConstraint(self.ball_joint, ball_loc_grp))
        pm.setAttr(ball_loc + '.v', 0)

        # parent locators to the right hierarchy
        pm.parent(heel_loc_grp, self.controls_grp)
        pm.parent(toe_tip_loc_grp, self.heel)
        pm.parent(ball_loc_grp, self.toe_tip)

        # create IK Handles
        ankle_ik_hdl = pm.ikHandle(n=self.prefix + 'Ankle_ikh', sol='ikSCsolver', sj=ankle_ik, ee=ball_ik)[0]
        ball_ik_hdl = pm.ikHandle(n=self.prefix + 'Ball_ikh', sol='ikSCsolver', sj=ball_ik, ee=toe_ik)[0]

        # parent IK Handles
        pm.parent(ankle_ik_hdl, ball_loc)
        pm.parent(ball_ik_hdl, self.toe_tip)

        #tools.matrix_constraint(ball_loc, self.foot_ctrl.get_offset(), mo=True)

        # create controllers for toe, ball, and heel

        # ik
        toe_ctrl = ctrl.Control(prefix=self.prefix + 'ToeIK', trans_to=toe_ik, scale=self.scale,
                                parent=self.controls_grp, shape='circleZ')
        toe_ctrl.create()

        ball_ctrl = ctrl.Control(prefix=self.prefix + 'BallIK', trans_to=ball_ik, scale=self.scale,
                                 parent=self.controls_grp, shape='circleZ')
        ball_ctrl.create()

        heel_ctrl = ctrl.Control(prefix=self.prefix + 'HeelIK', trans_to=self.heel, scale=self.scale,
                                 parent=self.controls_grp, shape='circleX')
        heel_ctrl.create()

        # parent and constraint toe ball and heel controls
        pm.parent(toe_ctrl.get_offset(), heel_ctrl.get_ctrl())
        pm.parent(ball_ctrl.get_offset(), toe_ctrl.get_ctrl())

        ik_ctrl_grp = pm.createNode("transform", n=self.prefix + 'IKCtrlOffset_grp')
        pm.parent(heel_ctrl.get_offset(), ik_ctrl_grp)
        pm.parent(ik_ctrl_grp, self.controls_grp)
        tools.matrix_constraint(self.foot_ctrl_nurb, ik_ctrl_grp)

        tools.matrix_constraint(toe_ctrl.get_ctrl(), toe_tip_loc_grp, mo=True)
        tools.matrix_constraint(ball_ctrl.get_ctrl(), ball_loc_grp, mo=True)

        # parent foot controller and heel
        if self.attach_joint:
            pass
            ball_ctrl.set_constraint(self.ik_hdl_offset)
            #pm.aimConstraint(ball_loc_grp, self.ankle_joint, mo=True)
            #ball_ctrl.set_constraint()
            #ball_fk_ctrl.set_constraint(ankle_fk)
            #tools.matrix_constraint(self.attach_joint, ankle_ik, mo=True)
            #tools.matrix_constraint(self.attach_joint, ankle_fk, mo=True)
            #tools.matrix_constraint(self.attach_joint, ball_fk_ctrl.get_offset(), mo=True)
            # tools.matrix_constraint(self.body_attach_grp, ik_ctrl_grp, mo=True)
            # tools.matrix_constraint(self.body_attach_grp, self.joints_offset_grp, mo=True)
            # tools.matrix_constraint(self.body_attach_grp, ball_fk_ctrl.get_offset(), mo=True)
        else:
            ball_ctrl.set_constraint(self.ankle_joint)
            #tools.matrix_constraint(self.foot_ctrl_nurb, ik_ctrl_grp, mo=True)

        # create nodes for the controllers attributes
        bts_clamp = pm.createNode("clamp", n=self.prefix + 'BendToStraight_clamp')
        bts_percent = pm.createNode("setRange", n=self.prefix + 'BendToStraight_percent')
        invert_percentage = pm.createNode("plusMinusAverage", n=self.prefix + 'Invert_percentage')
        ball_perc_mult = pm.createNode("multiplyDivide", n=self.prefix + 'BallPerc_mult')
        ball_roll_mult = pm.createNode("multiplyDivide", n=self.prefix + 'BallRoll_mult')
        ztb_clamp = pm.createNode("clamp", n=self.prefix + 'BallZeroToBend_clamp')
        ztb_percent = pm.createNode("setRange", n=self.prefix + 'BallZeroToBend_percent')
        heel_rot_clamp = pm.createNode("clamp", n=self.prefix + 'HeelRot_clamp')
        foot_roll_mult = pm.createNode("multiplyDivide", n=self.prefix + 'Roll_mult')

        # connect attrs
        pm.connectAttr(self.foot_ctrl_nurb + '.bla', bts_clamp + '.minR')
        pm.connectAttr(self.foot_ctrl_nurb + '.tsa', bts_clamp + '.maxR')
        pm.connectAttr(self.foot_ctrl_nurb + '.roll', bts_clamp + '.inputR')

        pm.connectAttr(bts_clamp + '.inputR', bts_percent + '.valueX')
        pm.connectAttr(bts_clamp + '.inputR', foot_roll_mult + '.input2X')
        pm.connectAttr(bts_clamp + '.minR', bts_percent + '.oldMinX')
        pm.connectAttr(bts_clamp + '.maxR', bts_percent + '.oldMaxX')

        pm.connectAttr(bts_percent + '.outValueX', foot_roll_mult + '.input1X')
        pm.setAttr(bts_percent + '.maxX', 1)
        pm.setAttr(invert_percentage + '.op', 2)
        pm.setAttr(invert_percentage + '.input1D[0]', 1)
        pm.connectAttr(bts_percent + '.outValueX', invert_percentage + '.input1D[1]')

        pm.connectAttr(invert_percentage + '.output1D', ball_perc_mult + '.input2X')

        pm.connectAttr(self.foot_ctrl_nurb + '.bla', ztb_clamp + '.maxR')
        pm.connectAttr(self.foot_ctrl_nurb + '.roll', ztb_clamp + '.inputR')

        pm.connectAttr(ztb_clamp + '.inputR', ztb_percent + '.valueX')
        pm.connectAttr(ztb_clamp + '.maxR', ztb_percent + '.oldMaxX')
        pm.connectAttr(ztb_clamp + '.minR', ztb_percent + '.oldMinX')

        pm.setAttr(ztb_percent + '.maxX', 1)
        pm.connectAttr(ztb_percent + '.outValueX', ball_perc_mult + '.input1X')

        pm.connectAttr(ball_perc_mult + '.outputX', ball_roll_mult + '.input1X')
        pm.connectAttr(self.foot_ctrl_nurb + '.roll', ball_roll_mult + '.input2X')

        pm.connectAttr(ball_roll_mult + '.outputX', ball_ctrl.get_offset() + '.rotateX')
        pm.connectAttr(self.foot_ctrl_nurb + '.lean', ball_ctrl.get_offset() + '.rotateZ')

        pm.setAttr(heel_rot_clamp + '.minR', -90)
        pm.connectAttr(self.foot_ctrl_nurb + '.roll', heel_rot_clamp + '.inputR')

        pm.connectAttr(heel_rot_clamp + '.outputR', heel_ctrl.get_offset() + '.rotateX')

        pm.connectAttr(foot_roll_mult + '.outputX', toe_ctrl.get_offset() + '.rotateX')
        pm.connectAttr(self.foot_ctrl_nurb + '.toespin', toe_ctrl.get_offset() + '.rotateY')

        if self.blend_ctrl:
            for driver1, driven, driver2 in zip(fk_chain, driven, ik_chain):
                if driver2 != ik_chain[0]:
                    tools.matrix_blend(driver1, driven, blender=self.blend_ctrl, driver2=driver2, channels=['t', 'r'])

            pm.connectAttr(self.blend_ctrl + '.blend', ball_ctrl.get_offset() + '.v')
            pm.connectAttr(self.blend_ctrl + '.blend', toe_ctrl.get_offset() + '.v')
            pm.connectAttr(self.blend_ctrl + '.blend', heel_ctrl.get_offset() + '.v')
            reverse = pm.createNode('reverse', n=ball_fk_ctrl.get_ctrl() + 'rev_vis')
            pm.connectAttr(self.blend_ctrl + '.blend', reverse + '.inputX')
            pm.connectAttr(reverse + '.outputX', ball_fk_ctrl.get_offset() + '.v')