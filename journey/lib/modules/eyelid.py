"""
module containing eyelid setup.

Setup inspired by Marco Giordano
https://vimeo.com/66583205
"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
from journey.lib.layout import Module
reload(ctrl)
reload(tools)


class Eyelid():
    """
    TODO:
    NOTE: inherit set_base and set_prefix from Module class
    When creating upper and lower curves untick: Conform to smooth mesh preview and set to 1 linear

    """
    def __init__(self,
                 prefix='new',
                 scale=1.0,
                 upper_crv='',
                 lower_crv='',
                 eye_center='',
                 joint_radius=0.4,
                 base_rig=None,
                 ):

        self.prefix = prefix
        self.scale = scale
        self.upper_crv = upper_crv
        self.lower_crv = lower_crv
        self.eye_center = eye_center
        self.joint_radius = joint_radius
        self.rig_module = Module(self.prefix, base_rig)
        self.main_controllers = []
        self.constrain_controllers = []
        self.helper_groups = []

    def build(self, *args):
        self.rig_module.create()
        upper_joints = tools.joint_on_curve(self.upper_crv, prefix=self.prefix+'Upper',
                                            parent=False, radius=self.joint_radius)
        lower_joints = tools.joint_on_curve(self.lower_crv, prefix=self.prefix+'Lower',
                                            parent=False, radius=self.joint_radius)

        pm.delete(lower_joints[0], lower_joints[-1])
        del(lower_joints[0])
        del(lower_joints[-1])
        aim_loc_upper_list = []
        aim_loc_lower_list = []
        loc_grp = pm.createNode('transform', n=self.prefix + '_loc_offset_grp')
        # create locators and bind them to high res curve
        for seq in upper_joints, lower_joints:
            for joint in seq:
                print joint
                position = pm.xform(joint, query=True, worldSpace=True, translation=True)

                aim_loc = pm.spaceLocator(absolute=True, name=joint.replace('_result_jnt', '_aim_loc'))
                aim_loc.translate.set(position)
                aim_loc.centerPivots()
                aim_loc.getShape().localScaleX.set(self.joint_radius)
                aim_loc.getShape().localScaleY.set(self.joint_radius)
                aim_loc.getShape().localScaleZ.set(self.joint_radius)

                if 'Upper' in joint.name():
                    aim_loc_upper_list.append(aim_loc)
                else:
                    aim_loc_lower_list.append(aim_loc)

                # create center joints
                pm.select(None)
                center_joint = pm.joint(name=joint.replace('_result', '_center'), radius=0.1)
                pm.delete(pm.pointConstraint(self.eye_center, center_joint))

                pm.aimConstraint(aim_loc, center_joint, maintainOffset=True, weight=1, aimVector=(1, 0, 0),
                                 upVector=(0, 1, 0), worldUpType="scene")

                # parent stuff
                pm.parent(joint, center_joint)
                pm.parent(self.rig_module.joints_grp, center_joint)
                pm.parent(self.rig_module.joints_grp, loc_grp)
                pm.parent(aim_loc, loc_grp, )

        # connect the locators to the high res curve
        self.loc_on_curve(aim_loc_upper_list, self.upper_crv)
        self.loc_on_curve(aim_loc_lower_list, self.lower_crv)

        # create low res curves with controllers
        upper_lowres_curve = self.create_lowres_crv(self.upper_crv)
        lower_lowres_curve = self.create_lowres_crv(self.lower_crv)

        # apply wire deformer to high res curves
        pm.wire(self.upper_crv, groupWithBase=False, envelope=1, crossingEffect=0, localInfluence=0,
                wire=upper_lowres_curve.name())
        pm.wire(self.lower_crv, groupWithBase=False, envelope=1, crossingEffect=0, localInfluence=0,
                wire=lower_lowres_curve.name())

        # create control joints for low res curve
        c_upper, c_joint_upper = self.create_control_joints(upper_lowres_curve)
        pm.skinCluster(c_joint_upper, upper_lowres_curve, toSelectedBones=True)
        c_lower, c_joint_lower = self.create_control_joints(lower_lowres_curve, lower=True)
        pm.skinCluster(c_joint_lower, c_joint_upper[0], c_joint_upper[-1], lower_lowres_curve, toSelectedBones=True)



        # constrain the inbetween helper groups to the 4 main controllers
        # on the edges and top and top bottom of the eye
        tools.matrix_blend(self.constrain_controllers[0], self.helper_groups[0],
                           self.main_controllers[0], self.constrain_controllers[1], mo=True, blend_value=0.5)
        tools.matrix_blend(self.constrain_controllers[1], self.helper_groups[1],
                           self.main_controllers[0], self.constrain_controllers[2], mo=True)
        tools.matrix_blend(self.constrain_controllers[0], self.helper_groups[2],
                           self.main_controllers[0], self.constrain_controllers[3], mo=True)
        tools.matrix_blend(self.constrain_controllers[3], self.helper_groups[3],
                           self.main_controllers[0], self.constrain_controllers[2], mo=True)

        # add blink and blink height attr
        for i, controller in enumerate(self.main_controllers):
            if i == 0:
                pm.addAttr(controller, shortName='blinkH', longName='BlinkHeight',
                           defaultValue=0.9, minValue=0.0, maxValue=1.0, k=1)
            pm.addAttr(controller, shortName='blink', longName='Blink',
                       defaultValue=0, minValue=0.0, maxValue=1.0, k=1)

        # setup blink height
        blink_height_crv = pm.duplicate(upper_lowres_curve, name=self.prefix + "_blink_height_crv")[0]
        blink_height_bs = pm.blendShape(lower_lowres_curve, upper_lowres_curve, blink_height_crv,
                                        name=self.prefix + "_blink_height_shapes")[0]
        pm.connectAttr(self.main_controllers[0] + ".BlinkHeight",
                       blink_height_bs.name() + '.' + lower_lowres_curve.name())

        reverse_node = pm.createNode("reverse", name=self.prefix + "_blink_reverse")
        pm.connectAttr(self.main_controllers[0] + ".BlinkHeight", "%s.inputX" % reverse_node.name())
        pm.connectAttr(reverse_node + ".outputX",
                       blink_height_bs.name() + '.' + upper_lowres_curve.name())

        # setup the blink
        blink_curve_upper = pm.duplicate(self.upper_crv, name=self.prefix + "_upper_blink_curve")[0]
        blink_curve_lower = pm.duplicate(self.lower_crv, name=self.prefix + "_lower_blink_curve")[0]

        self.main_controllers[0].blinkH.set(0)
        up_blink_wire_deformer = pm.wire(blink_curve_upper, groupWithBase=False, envelope=1, crossingEffect=0, localInfluence=0,  wire=blink_height_crv.name())[0]
        self.main_controllers[0].blinkH.set(1)
        low_blink_wire_deformer = pm.wire(blink_curve_lower, groupWithBase=False, envelope=1, crossingEffect=0, localInfluence=0, wire=blink_height_crv.name())[0]
        self.main_controllers[0].blinkH.set(0.9)

        up_blink_wire_deformer.setWireScale(0, 0)
        low_blink_wire_deformer.setWireScale(0, 0)

        blink_up_blend_shape = pm.blendShape(blink_curve_upper, self.upper_crv,
                                             name=self.prefix + "_up_blink_shapes")[0]
        blink_down_blend_shape = pm.blendShape(blink_curve_lower, self.lower_crv,
                                               name=self.prefix + "_down_blink_shapes")[0]

        pm.connectAttr(self.main_controllers[0] + ".blink",
                       blink_up_blend_shape + '.' + blink_curve_upper.name())
        pm.connectAttr(self.main_controllers[1] + ".blink",
                       blink_down_blend_shape + '.' + blink_curve_lower.name())

    def create_control_joints(self, curve, lower=False):
        control_joints = []
        controllers = []

        for i, cv in enumerate(curve.getCVs()):
            if lower is True and (i == 0 or i == 4):
                pass
            else:
                jnt = pm.joint(name='{}_cv{}_jnt'.format(curve.replace('_crv', ''), i+1),
                               position=cv, radius=self.joint_radius)
                pm.parent(jnt, world=True)
                control_joints.append(jnt)
                controller = ctrl.Control(prefix=curve.replace('_lowres_crv', '{}_lowres'.format(i+1)),
                                          scale=self.scale * 0.5,
                                          trans_to=jnt,
                                          shape='circleZ',
                                          channels=['r', 's', 'v'])
                controller.create()
                controller.set_constraint(jnt)
                controllers.append(controller)

                if i == 2:
                    self.main_controllers.append(controller.get_ctrl())
                if i == 0 or i == 2 or i == 4:
                    self.constrain_controllers.append(controller.get_ctrl())
                if i == 1 or i == 3:
                    self.helper_groups.append(controller.get_offset())

        return controllers, control_joints

    @staticmethod
    def create_lowres_crv(highres_curve):
        # create low res lower curves
        lowres_curve = pm.duplicate(highres_curve, name=highres_curve.replace('crv', 'lowres_crv'))[0]
        pm.displaySmoothness(lowres_curve, divisionsU=3, divisionsV=3, pointsWire=16)
        pm.rebuildCurve(lowres_curve, degree=3, endKnots=True, spans=2, keepRange=1, replaceOriginal=True,
                        rebuildType=0)
        # eyelid_low_res_curve.curve.set("%s_%s_low" % (self.side_prefix, self.up_down_prefix))

        # lower_lowres_curve = pm.listRelatives(eyelid_low_res_curve, shapes=True)[0]
        # self.set_shape_node_color(lower_lowres_curve.getShape(), (0, 0, 1))
        lowres_curve.centerPivots()

        return lowres_curve

    @staticmethod
    def loc_on_curve(loc_list, curve):
        curve = pm.PyNode(curve)
        # connect the locators to the high res curve
        for loc in loc_list:
            npoc = pm.createNode("nearestPointOnCurve", name=loc + "npoc")
            position = loc.getTranslation(space="world")
            curve.getShape().worldSpace >> npoc.inputCurve
            npoc.inPosition.set(position)

            u = npoc.parameter.get()

            pci_node = pm.createNode("pointOnCurveInfo", name=loc.name().replace("locator", "PCI"))
            curve.getShape().worldSpace >> pci_node.inputCurve
            pci_node.parameter.set(u)
            pci_node.position >> loc.translate

            pm.delete(npoc)
