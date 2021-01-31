"""
module containing different class solvers for ik twisting, fk, etc.
"""
import pymel.core as pm
import journey.lib.control as ctrl
from journey.lib.utils.tools import matrix_constraint
from journey.lib.utils.tools import list_check
reload(ctrl)


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
        self.driven = list_check(self.driven)

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
                matrix_constraint(self.fk_dict[self.driven[i-1]].get_ctrl(),
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
        self.driven = list_check(self.driven)
        for driven in self.driven:
            matrix_constraint(self.fk_dict[''+driven+''].get_ctrl(), driven)


class IK:
    def __init__(self):
        pass
