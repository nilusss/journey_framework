"""
arm module inheriting from limb class
"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.modules.limb as li
import journey.lib.space_switcher as space
reload(ctrl)
reload(tools)
reload(li)
reload(space)
import journey.lib.modules.limb as li


class Arm(li.Limb):
    def __init__(self,
                 driven,
                 clavicle='',
                 spaces=[],
                 parent_joint='',
                 stretch=True,
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 do_spaces_in_limb=False
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        self.clavicle = clavicle
        self.spaces = spaces
        if self.spaces:
            self.spaces = tools.list_check(spaces)
        self.stretch = stretch
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig
        self.do_spaces_in_limb = do_spaces_in_limb

    def create(self):
        super(Arm, self).create()
        if self.clavicle:
            clavicle_ctrl = ctrl.Control(prefix=self.prefix + 'Clavicle', trans_to=self.clavicle,
                                         rot_to=self.clavicle, scale=self.scale, rot_shape=False,
                                         parent=self.controls_grp, shape='line_sphere')
            clavicle_ctrl.create()
            clavicle_chain = tools.joint_duplicate(joint_chain=[self.clavicle, self.driven[0]],
                                                   joint_type="FK", offset_grp=self.joints_offset_grp)
            clavicle_chain[-1].replace('_jnt1', 'Off_jnt')

            tools.matrix_constraint(clavicle_chain[-1], self.ik_joints[0], mo=True)

            clavicle_ctrl.set_constraint(clavicle_chain[0])
            if self.stretch:
                clavicle_ctrl.set_constraint(self.arm_ik.upper_null)

            clavicle_ctrl.set_constraint(self.arm_fk.fk_dict.values()[0].get_ctrl(), channels=['t'])

            tools.matrix_constraint(clavicle_chain[0], self.clavicle)

            ss_pole = space.SpaceSwitcherLogic(self.arm_ik.ik_ctrl.get_ctrl(), self.arm_ik.pv_ctrl.get_ctrl(),
                                               base_rig=self.base_rig)
            ss_pole.setup_switcher()

            ss_ik = space.SpaceSwitcherLogic(clavicle_ctrl.get_ctrl(), self.arm_ik.ik_ctrl.get_ctrl(),
                                             base_rig=self.base_rig)
            ss_ik.setup_switcher()

            ss_fk = space.SpaceSwitcherLogic(clavicle_ctrl.get_ctrl(), self.arm_fk.fk_dict.values()[0].get_ctrl(),
                                             base_rig=self.base_rig)
            ss_fk.setup_switcher()

            for i, s in enumerate(self.spaces):
                if not pm.objExists(s):
                    self.spaces.remove(s)

            if self.spaces:
                parent_space = space.SpaceSwitcherLogic(self.spaces, clavicle_ctrl.get_ctrl(), base_rig=self.base_rig)
                parent_space.setup_switcher()
                parent_space.set_space(self.spaces[0])

            # for i, ss in enumerate(self.spaces):
            #     print ss
            #     if i < 1:
            #         parent_space = space.SpaceSwitcherLogic(self.spaces, clavicle_ctrl.get_ctrl())
            #         parent_space.setup_switcher()
            #         parent_space.set_space(self.spaces)
            #     else:
            #         parent_space.add_space(ss)

        return self
