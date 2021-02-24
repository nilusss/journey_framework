"""
module containing eye setup.

"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.layout as lo
# reload(ctrl)
# reload(tools)
# reload(lo)
import journey.lib.layout as lo


class Eye(lo.Module):
    def __init__(self,
                 eye_center='',
                 eye_end='',
                 look_at='',
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):

        self.CLASS_NAME = self.__class__.__name__
        self.eye_center = eye_center
        self.eye_end = eye_end
        self.look_at = look_at
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig

        # # init Module class
        # Module.__init__(self, self.prefix, self.base_rig)
        # init Module class
        print type(self)
        # import pdb; pdb.set_trace()
        # super(Eye, self).__init__(self.prefix, self.base_rig)
        super(Eye, self).__init__(self.prefix, self.base_rig)

    def create(self, *args):
        # create module from parent class
        super(Eye, self).create_structure()

        eye_center_ctrl = ctrl.Control(prefix=self.prefix + '_rot',
                                       scale=self.scale,
                                       trans_to=self.eye_end,
                                       shape='arrow3D',
                                       parent=self.controls_grp,
                                       channels=['t', 's', 'v'])
        eye_center_ctrl.create()
        eye_center_ctrl.set_pivot(self.eye_center)
        eye_center_ctrl.set_constraint(self.eye_center)

        look_at_ctrl = ctrl.Control(prefix=self.prefix + '_lookAt',
                                    scale=self.scale,
                                    trans_to=self.look_at,
                                    shape='circleZ',
                                    parent=self.controls_grp,
                                    channels=['r', 's', 'v'])

        look_at_ctrl.create()
        pm.aimConstraint(look_at_ctrl.get_ctrl(), eye_center_ctrl.get_offset(), mo=True)
