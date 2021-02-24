"""
arm module inheriting from limb class
"""
import pymel.core as pm
import journey.lib.control as ctrl
import journey.lib.utils.tools as tools
import journey.lib.modules.limb as li
# reload(ctrl)
# reload(tools)
# reload(li)
import journey.lib.modules.limb as li


class Arm(li.Limb):
    def __init__(self,
                 clavicle='',
                 driven=[],
                 stretch=True,
                 joint_radius=0.4,
                 prefix='new',
                 scale=1.0,
                 base_rig=None,
                 ):
        super(Arm, self).__init__(driven, stretch, joint_radius, prefix, scale, base_rig)
        print("init arm")

    def create(self):
        super(Arm, self).create(self)
