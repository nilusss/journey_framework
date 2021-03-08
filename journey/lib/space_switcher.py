"""
module for setting up space switching on objects

setup_switcher - creates space switching with the given arguments
add_space - adds a new space for the existing space switching system

TODO: split translate and rotate parent space in two different attributes if bool argument added
"""

import pymel.core as pm
import journey.lib.utils.tools as tools
reload(tools)


class SpaceSwitcherLogic(object):
    def __init__(self,
                 drivers,
                 driven,
                 channels=['t', 'r'],
                 base_rig=None):
        """First driver in drivers list will be set to default space

        Args:
            drivers:
            driven:
            channels:
            base_rig:
        """
        self.drivers = drivers
        self.driven = driven
        self.driven_offset = pm.listRelatives(self.driven, parent=True)[0]
        self.prefix = tools.split_at(self.driven, '_', 2)
        self.channels = channels
        self.base_rig = base_rig

    def setup_switcher(self, *args):
        world_space = pm.ls("WORLD_SPACE_NODE")
        if not world_space:
            world_space = pm.createNode('transform', n="WORLD_SPACE_NODE")
            try:
                # exec('return_module = {}.{}'.format(module.prefix, module_grp))
                pm.parent(world_space, self.base_rig.rig_grp)
            except AttributeError as e:
                print("No rig to parent under: \"{}\" ".format(str(e)))
        else:
            world_space = world_space[0]
        self.drivers = tools.list_check(self.drivers)

        # If the driver follows my naming convention split it at the second underscore
        drivers_nicename = 'World:'+''.join('%s:' % tools.split_at(driver, '_', 2) for driver in self.drivers)
        # setup switching attr on driven ctrl
        try:
            pm.getAttr(self.driven + '.pspace')
        except pm.MayaAttributeError:
            pm.addAttr(self.driven, longName='pspace', nn='PARENT SPACE',
                       at="enum", en='=======')
            pm.addAttr(self.driven, shortName='space', longName='space',
                       at="enum", enumName=drivers_nicename, keyable=False)
            pm.setAttr(self.driven + '.space', edit=True, channelBox=True)
            pm.setAttr(self.driven + '.pspace', edit=True, channelBox=True)

        # create necessary nodes for the space switching
        # create two choice nodes for the driver matrix and offset matrix
        self.space_offset_choice = pm.createNode('choice', n=self.prefix + '_space_offset_choice')
        self.space_choice = pm.createNode('choice', n=self.prefix + '_space_choice')

        #create multmatrix and decomposematrix to get the position of selected space
        space_mm = pm.createNode('multMatrix', n=self.prefix + '_space_mm')
        space_dm = pm.createNode('decomposeMatrix', n=self.prefix + '_space_dm')

        # create buffer node


        # setup initial connections between nodes
        for driver in world_space.name().split() + self.drivers:
            local_offset = tools.get_local_offset(pm.PyNode(driver).name(),
                                                  pm.PyNode(self.driven).name())
            idx = tools.get_next_free_multi_index(self.space_choice + '.input', 0)
            offset_matrix = pm.createNode('multMatrix', n=self.prefix + driver +'_offset_matrix')

            pm.connectAttr(offset_matrix + '.matrixSum', self.space_offset_choice + '.input[{}]'.format(idx), force=True)
            pm.setAttr(offset_matrix + '.matrixIn[{}]'.format(idx),
                       [local_offset(i, j) for i in range(4) for j in range(4)])
            pm.connectAttr(driver + '.worldMatrix', self.space_choice + '.input[{}]'.format(idx), force=True)

        pm.connectAttr(self.space_choice + '.output', space_mm + '.matrixIn[1]')
        driven_parent = pm.listRelatives(self.driven, parent=True)[0]
        driven_buffer = pm.listRelatives(self.driven, parent=True)[0]
        pm.connectAttr(driven_parent + '.parentInverseMatrix[0]', space_mm + '.matrixIn[2]')
        pm.connectAttr(space_mm + '.matrixSum', space_dm + '.inputMatrix')
        for m in self.channels:
            pm.connectAttr(space_dm + '.o' + m, self.driven_offset + '.' + m)
        # setup controller selection to choice node selector
        pm.connectAttr(self.driven + '.space', self.space_offset_choice + '.selector')
        pm.connectAttr(self.driven + '.space', self.space_choice + '.selector')

        pm.connectAttr(self.space_offset_choice + '.output', space_mm + '.matrixIn[0]')

    def add_space(self, drivers):
        drivers = tools.list_check(drivers)
        for driver in drivers:
            #   get local offset
            local_offset = tools.get_local_offset(driver, self.driven)
            idx = tools.get_next_free_multi_index(self.space_choice + '.input', 0)
            offset_matrix = pm.createNode('multMatrix', n=self.prefix + driver + '_offset_matrix')

            pm.connectAttr(offset_matrix + '.matrixSum', self.space_offset_choice + '.input[{}]'.format(idx),
                           force=True)
            pm.setAttr(offset_matrix + '.matrixIn[{}]'.format(idx),
                       [local_offset(i, j) for i in range(4) for j in range(4)])
            pm.connectAttr(driver + '.worldMatrix', self.space_choice + '.input[{}]'.format(idx), force=True)

            # If the driver follows my naming convention split it at the second underscore
            driver_nicename = tools.split_at(driver, '_', 2)
            get_enums = pm.attributeQuery('space', node=self.driven, listEnum=True)[0] + ':' + driver_nicename
            pm.addAttr(self.driven + '.space', edit=True, enumName=get_enums)

            idx = tools.get_next_free_multi_index(self.space_choice + '.input', 0)
            pm.connectAttr(driver + '.worldMatrix', self.space_choice + '.input[{}]'.format(idx), force=True)

    def set_space(self, space):
        pm.setAttr(self.driven + '.space', tools.split_at(space, '_', 2))