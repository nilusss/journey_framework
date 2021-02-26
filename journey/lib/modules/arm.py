"""
arm module inheriting from limb class
"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.modules.limb as li
reload(ctrl)
reload(tools)
reload(li)
import journey.lib.modules.limb as li


class Arm(li.Limb):
    def __init__(self,
                 driven,
                 clavicle='',
                 stretch=True,
                 joint_radius=0.4,
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):
        self.CLASS_NAME = self.__class__.__name__

        self.driven = driven
        self.clavicle = clavicle
        self.stretch = stretch
        self.joint_radius = joint_radius
        self.prefix = prefix
        self.scale = scale
        self.base_rig = base_rig
        #super(Arm, self).__init__(driven, stretch, joint_radius, prefix, scale, base_rig)
        print("init arm")

    def create(self):
        super(Arm, self).create()
        if self.clavicle:
            pass
