"""
module containing eye setup.
"""
import sys
if sys.version_info.major >= 3:
    from importlib import reload
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.layout as lo
import journey.lib.space_switcher as space
reload(ctrl)
reload(tools)
reload(space)
reload(lo)
import journey.lib.layout as lo


class Eye(lo.Module):
    def __init__(self,
                 eye_center='',
                 eye_end='',
                 look_at='',
                 parent_joint='',
                 spaces=[],
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):

        self.CLASS_NAME = self.__class__.__name__
        self.eye_center = eye_center
        self.eye_end = eye_end
        self.look_at = look_at
        self.parent_joint = parent_joint
        self.spaces = spaces
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

    def create(self, *args):
        # create module from parent class
        super(Eye, self).create_structure()

        center_buffer_grp = pm.createNode('transform', n=self.prefix + '_centerbuffer_grp')
        pm.delete(pm.parentConstraint(self.eye_end, center_buffer_grp))
        pm.parent(center_buffer_grp, self.controls_grp)

        eye_center_ctrl = ctrl.Control(prefix=self.prefix + '_rot',
                                       scale=self.scale * 0.5,
                                       trans_to=self.eye_end,
                                       shape='arrow3D',
                                       parent=center_buffer_grp,
                                       channels=['t', 's', 'v'])
        eye_center_ctrl.create()
        eye_center_ctrl.set_pivot(self.eye_center)
        eye_center_ctrl.set_constraint(self.eye_center)

        lookat_buffer_grp = pm.createNode('transform', n=self.prefix + '_lookatbuffer_grp')
        pm.delete(pm.parentConstraint(self.eye_end, lookat_buffer_grp))
        pm.parent(lookat_buffer_grp, self.controls_grp)
        look_at_ctrl = ctrl.Control(prefix=self.prefix + '_lookAt',
                                    scale=self.scale * 0.6,
                                    trans_to=self.look_at,
                                    shape='circleZ',
                                    parent=self.controls_grp,
                                    channels=['r', 's', 'v'])

        look_at_ctrl.create()
        pm.aimConstraint(look_at_ctrl.get_ctrl(), eye_center_ctrl.get_offset(), mo=True)

        if self.spaces:
            lookat_ss = space.SpaceSwitcherLogic(self.spaces, look_at_ctrl.get_ctrl(), split=False)
            lookat_ss.setup_switcher()

        if self.parent_joint:
            tools.matrix_constraint(self.parent_joint, center_buffer_grp, mo=True)

        return self
