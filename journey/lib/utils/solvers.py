"""
module containing different class solvers for ik twisting, fk, etc.
"""
import pymel.core as pm
import journey.lib.control as ctrl
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
        if type(self.driven) is str:
            self.driven = self.driven.split()

        for joint in self.driven:
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

        # fk.fk_dict['joint1'].set_color('blue') <-- FOR CALLING SPECIFIC FK JOINT CONTROLLER IF NEEDED.

        return self.fk_dict


class IK:
    def __init__(self):
        pass
