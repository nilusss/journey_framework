"""
module containing eyebrow setup.

NOTE: inherit set_base and set_prefix from Module class
NOTE: When creating upper and lower curves untick: Conform to smooth mesh preview and set to 1 linear
"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.layout as lo
reload(ctrl)
reload(tools)
reload(lo)
import journey.lib.layout as lo


class Eyebrow(lo.Module):
    def __init__(self,
                 upper_crv,
                 center_joint,
                 joint_radius=0.4,
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):

        self.CLASS_NAME = self.__class__.__name__

        self.upper_crv = upper_crv
        self.eye_joint = center_joint
        self.joint_radius = joint_radius
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

        # init empty public variables
        self.main_controllers = []
        self.constrain_controllers = []
        self.helper_groups = []
        self.lid_affector = ''

    def create(self, *args):
        # init empty public variables
        self.main_controllers = []
        self.constrain_controllers = []
        self.helper_groups = []
        self.lid_affector = ''
        # create module from parent class
        super(Eyebrow, self).create_structure()

        upper_joints = tools.joint_on_curve(self.upper_crv, prefix=self.prefix+'Upper',
                                            parent=False, radius=self.joint_radius)

        aim_loc_upper_list = []
        loc_grp = pm.createNode('transform', n=self.prefix + '_loc_offset_grp')

        # create locators and bind them to high res curve
        for joint in upper_joints:
            position = pm.xform(joint, query=True, worldSpace=True, translation=True)

            aim_loc = pm.spaceLocator(absolute=True, name=joint.replace('_result_jnt', '_aim_loc'))
            aim_loc.translate.set(position)
            aim_loc.centerPivots()
            aim_loc.getShape().localScaleX.set(self.joint_radius)
            aim_loc.getShape().localScaleY.set(self.joint_radius)
            aim_loc.getShape().localScaleZ.set(self.joint_radius)

            if 'Upper' in joint.name():
                aim_loc_upper_list.append(aim_loc)

            # create center joints
            pm.select(None)
            center_joint = pm.joint(name=joint.replace('_result', '_center'), radius=0.1)
            pm.delete(pm.pointConstraint(self.eye_joint, center_joint))

            pm.aimConstraint(aim_loc, center_joint, maintainOffset=True, weight=1, aimVector=(1, 0, 0),
                             upVector=(0, 1, 0), worldUpType="scene")

            # parent stuff
            pm.parent(joint, center_joint)
            pm.parent(center_joint, self.joints_grp)
            pm.parent(aim_loc, loc_grp)

        pm.parent(loc_grp, self.parts_grp)

        # connect the locators to the high res curve
        tools.loc_on_curve(aim_loc_upper_list, self.upper_crv)

        # create low res curves with controllers
        upper_lowres_curve = tools.create_lowres_crv(self.upper_crv)

        # create control joints for low res curve
        c_upper, c_joint_upper = self.create_control_joints(upper_lowres_curve)
        pm.skinCluster(c_joint_upper, upper_lowres_curve, toSelectedBones=True)

        # constrain the inbetween helper groups to the 4 main controllers
        # on the edges and top and top bottom of the eye
        tools.matrix_blend(self.constrain_controllers[0], self.helper_groups[0],
                           self.main_controllers[0].get_ctrl(), self.constrain_controllers[1], mo=True, blend_value=0.5)
        tools.matrix_blend(self.constrain_controllers[1], self.helper_groups[1],
                           self.main_controllers[0].get_ctrl(), self.constrain_controllers[2], mo=True)

        # parent controllers to control group
        for c in c_upper:
            pm.parent(c.get_offset(), self.controls_grp)

        cv_jnt_grp = pm.createNode('transform', n=self.prefix + 'cv_jnt_grp')
        pm.parent(cv_jnt_grp, self.joints_grp)
        for j in c_joint_upper:
            pm.parent(j, cv_jnt_grp)

        self.main_offset = pm.createNode('transform', n=self.prefix + '_main_controllers_offset_grp')
        pm.delete(pm.pointConstraint(self.eye_joint, self.main_offset))
        pm.parent(self.main_offset, self.controls_grp)
        pm.parent(self.main_controllers[0].get_offset(), self.main_offset)
        pm.parent(self.upper_crv, upper_lowres_curve, self.parts_grp)

        return self

    def create_control_joints(self, curve, lower=False):
        control_joints = []
        controllers = []

        for i, cv in enumerate(curve.getCVs()):
            # TODO: fix if statement. works for now, but is super ugly.
            jnt = pm.joint(name='{}_cv{}_jnt'.format(curve.replace('_crv', ''), i+1),
                           position=cv, radius=self.joint_radius)
            pm.parent(jnt, world=True)
            control_joints.append(jnt)
            controller = ctrl.Control(prefix=curve.replace('_lowres_crv', '{}_lowres'.format(i+1)),
                                      scale=self.scale * 0.3,
                                      trans_to=jnt,
                                      shape='sphere',
                                      channels=['r', 's', 'v'])
            controller.create()

            if i == 2:
                controller.set_shape('circleZ')
                controller.set_shape_scale(self.scale * 1.3)
                self.main_controllers.append(controller)
                self.constrain_controllers.append(controller.get_ctrl())
            if i == 0 or i == 4:
                if lower is False:
                    self.constrain_controllers.append(controller.get_ctrl())
            if i == 1 or i == 3:
                self.helper_groups.append(controller.get_offset())

            controllers.append(controller)

        # position eyelid controllers
        pm.delete(pm.pointConstraint(controllers[0].get_ctrl(), controllers[2].get_ctrl(),
                                     controllers[1].get_offset(), skip=['x', 'y']))
        pm.delete(pm.pointConstraint(controllers[2].get_ctrl(), controllers[4].get_ctrl(),
                                     controllers[3].get_offset(), skip=['x', 'y']))

        pm.delete(pm.pointConstraint(controllers[0].get_offset(), controllers[1].get_offset(),
                                     controllers[0].get_ctrl(), skip=['x', 'y']))
        pm.delete(pm.pointConstraint(controllers[4].get_offset(), controllers[3].get_ctrl(),
                                     controllers[4].get_ctrl(), skip=['x', 'y']))

        if lower is True:
            pm.delete(controllers[0].get_offset(), controllers[-1].get_offset(), control_joints[0], control_joints[-1])
            del (controllers[0], controllers[-1], control_joints[0], control_joints[-1])

        # setup controller constraints
        for j, c in zip(control_joints, controllers):
            c.set_constraint(j)
            #c.set_pivot(j)

        return controllers, control_joints

    def set_lid_affector(self, affector):
        """Make affector drive the eyelid controllers for a more natural look

        Args:
            affector:

        Returns:

        """
        # TODO: affector can currently only be set once - when initializing the class
        # check if affector object exists and whether an affector is already set.
        if pm.objExists(affector):
            if not self.get_lid_affector():
                # create nodes necessary for the setup
                rotate_helper = pm.createNode('transform', n=self.prefix + '_rotate_helper')
                al_mult = pm.createNode('multiplyDivide', n=self.prefix + '_lid_md')
                al_clamp = pm.createNode('clamp', n=self.prefix + '_lid_clamp')

                # add attrs to control up/down/left/right auto lid drag limits
                pm.addAttr(self.main_controllers[0].get_ctrl(), shortName='aldud', longName='AutoLidDragUpDown',
                           defaultValue=5, minValue=0.0, maxValue=100, k=1)
                pm.addAttr(self.main_controllers[0].get_ctrl(), shortName='aldlr', longName='AutoLidDragLeftRight',
                           defaultValue=10, minValue=0.0, maxValue=100, k=1)

                # connect attrs - check node editor for better visuals. Select 1 main and 1 corner lid controller
                pm.connectAttr(self.main_controllers[0].get_ctrl() + '.aldud', al_clamp + '.maxR')
                pm.connectAttr(self.main_controllers[0].get_ctrl() + '.aldlr', al_clamp + '.maxG')
                pm.connectAttr(self.main_controllers[0].get_ctrl() + '.aldud', al_clamp + '.maxB')

                pm.connectAttr(self.main_controllers[0].get_ctrl() + '.aldud', al_mult + '.input1X')
                pm.connectAttr(self.main_controllers[0].get_ctrl() + '.aldlr', al_mult + '.input1Y')
                pm.connectAttr(self.main_controllers[0].get_ctrl() + '.aldud', al_mult + '.input1Z')
                al_mult.attr('input2X').set(-1)
                al_mult.attr('input2Y').set(-1)
                al_mult.attr('input2Z').set(-1)
                pm.connectAttr(al_mult + '.output', al_clamp + '.min')
                pm.connectAttr(rotate_helper + '.rotate', al_clamp + '.input')
                pm.connectAttr(al_clamp + '.output', self.main_offset + '.rotate')

                # parent and constrain for clean outliner
                pm.parent(rotate_helper, self.parts_grp)
                tools.matrix_constraint(affector, rotate_helper, mo=True)

                # set lid affector
                self.lid_affector = affector
            else:
                # affector can currently only be set once - when initializing the class
                # setting this up right now seems too extensive.
                pass

    def get_lid_affector(self, *args):
        return self.lid_affector

    def set_attach_parent(self, driver):
        tools.matrix_constraint(driver, self.body_attach_grp)


