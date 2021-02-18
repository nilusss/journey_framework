"""
module containing eye setup.

"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
from journey.lib.layout import Module
from journey.lib.layout import Base
reload(ctrl)
reload(tools)


class Eye():
    """

    """
    def __init__(self,
                 eye_center='',
                 eye_end='',
                 look_at='',
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):

        self.eye_center = eye_center
        self.eye_end = eye_end
        self.look_at = look_at
        self.prefix = prefix
        self.scale = scale
        self.rig_module = Module(self.prefix, base_rig)

    def create(self, *args):
        self.rig_module.create()

        eye_center_ctrl = ctrl.Control(prefix=self.prefix + '_rot',
                                       scale=self.scale,
                                       trans_to=self.eye_end,
                                       shape='arrow3D',
                                       parent=self.rig_module.controls_grp,
                                       channels=['t', 's', 'v'])
        eye_center_ctrl.create()
        eye_center_ctrl.set_pivot(self.eye_center)
        eye_center_ctrl.set_constraint(self.eye_center)

        look_at_ctrl = ctrl.Control(prefix=self.prefix + '_lookAt',
                                    scale=self.scale,
                                    trans_to=self.look_at,
                                    shape='circleZ',
                                    parent=self.rig_module.controls_grp,
                                    channels=['r', 's', 'v'])

        look_at_ctrl.create()
        pm.aimConstraint(look_at_ctrl.get_ctrl(), eye_center_ctrl.get_offset(), mo=True)
