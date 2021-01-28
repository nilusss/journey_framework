
"""
various tools for the framework
"""

import pymel.core as pm
import maya.cmds as mc
import maya.OpenMaya as om


def colors(color):
    dict_colors = {
        "yellow": 17,
        "red": 13,
        "blue": 6,
        "cyan": 18,
        "green": 7,
        "darkRed": 4,
        "darkBlue": 15,
        "white": 16,
        "black": 1,
        "gray": 3,
        "none": 0,
    }

    if color in dict_colors:
        return dict_colors[color]


def lock_channels(obj='', channels=['t', 'r', 's']):
    # lock control channels
    single_attr_lock_list = []

    for ch in channels:
        if ch in ['t', 'r', 's']:
            for axis in ['x', 'y', 'z']:
                attr = ch + axis
                single_attr_lock_list.append(attr)
        else:
            single_attr_lock_list.append(ch)
    for attr in single_attr_lock_list:
        pm.setAttr(obj + '.' + attr, l=1, k=0)

    return single_attr_lock_list


def matrix_constraint(driver, driven, mo=True, channels=['t', 'r', 's']):

    mult_matrix = pm.createNode('multMatrix', n=driven + '_multMatrix')
    decompose_matrix = pm.createNode('decomposeMatrix', n=driven + '_decomposeMatrix')
    pm.connectAttr(mult_matrix + '.matrixSum', decompose_matrix + '.inputMatrix', force=True)
    driven_parent = pm.listRelatives(driven, parent=True)

    if pm.nodeType(driven) == 'joint':
        q_p = pm.createNode("quatProd", n=driven + '_quatProd')
        q_i = pm.createNode("quatInvert", n=driven + '_quatInvert')
        e_tq = pm.createNode("eulerToQuat", n=driven + '_eulerToQuat')
        q_te = pm.createNode("quatToEuler", n=driven + '_quatToEuler')
        pm.connectAttr(decompose_matrix + '.outputQuat', q_p + '.input1Quat')
        pm.connectAttr(driven + '.jointOrient', e_tq + '.inputRotate')
        pm.connectAttr(e_tq + '.outputQuat', q_i + '.inputQuat')
        pm.connectAttr(q_i + '.outputQuat', q_p + '.input2Quat')
        pm.connectAttr(q_p + '.outputQuat', q_te + '.inputQuat')

    if mo is True:
        local_off_matrix = pm.createNode('multMatrix', n=driven + 'localOffset_multMatrix')
        pm.connectAttr(driven + '.worldMatrix[0]', local_off_matrix + '.matrixIn[0]')
        pm.connectAttr(driver + '.worldInverseMatrix[0]', local_off_matrix + '.matrixIn[1]')
        local_offset = pm.getAttr(local_off_matrix + '.matrixSum')
        pm.setAttr(mult_matrix + '.matrixIn[0]', local_offset, type='matrix')
        pm.connectAttr(driver + '.worldMatrix[0]', mult_matrix + '.matrixIn[1]')
        if not driven_parent:
            pm.connectAttr(driven + '.parentInverseMatrix[0]', mult_matrix + '.matrixIn[2]')
        else:
            pm.connectAttr(driven_parent[0] + '.worldInverseMatrix[0]', mult_matrix + '.matrixIn[2]')
    else:
        pm.connectAttr(driver + '.worldMatrix[0]', mult_matrix + '.matrixIn[0]')
        pm.connectAttr(driven + '.parentInverseMatrix[0]', mult_matrix + '.matrixIn[1]')

    if pm.nodeType(driven) == 'joint':
        pm.connectAttr(decompose_matrix + '.o' + channels[0], driven + '.' + channels[0])
        pm.connectAttr(decompose_matrix + '.o' + channels[2], driven + '.' + channels[2])
        pm.connectAttr(q_te + '.outputRotate', driven + '.r')
    else:
        for m in channels:
            pm.connectAttr(decompose_matrix + '.o' + m, driven + '.' + m)


def joint_constraint(driver1, driven, blender='', driver2='', channels=['t', 'r', 's']):
    """Used for constraining joints to other joints. Mainly used for constraining triple chain setups.
    Can also be used for 1:1 joint connections

    Args:
        driver1 (str, list): joint(s) to control the driven joint chain. FK
        driven (str, list): joint(s) to be driven by driver(s)
        blender (str): controller used for blending between FK and IK
        driver2 (str, list): joint(s) to control the driven joint chain. IK
        channels (list): channels that should be constrained

    """
    if type(driver1) is str:
        driver1.split()
    if type(driver2) is str:
        driver2.split()
    if type(driven) is str:
        driven.split()

    if blender:
        for c in channels:
            for driven, fk, ik in zip(driven, driver1, driver2):
                # Create blendColors nodes for Translate, Rotate, and Scale.
                blend = pm.createNode('blendColors', name='blender_to_' + driven)

                pm.connectAttr(blender + '.blend', blend + '.blender')
                pm.connectAttr(ik + '.' + c, blend + '.color1')
                pm.connectAttr(fk + '.' + c, blend + '.color2')
                for color, axis in zip(['R', 'G', 'B'], ['x', 'y', 'z']):
                    pm.connectAttr(blend + '.output' + color, driven + '.' + c + axis)

                # Check if the blender controller as the .blend attribute, otherwise create one
                try:
                    pm.getAttr(blender + '.blend')
                except Exception as e:
                    pm.addAttr(blender, shortName='blend', longName='FKIKBlend',
                               defaultValue=0, minValue=0.0, maxValue=1.0, k=1)
    else:
        for i, driven in enumerate(driven):
            for c in channels:
                pm.connectAttr(driver1[i] + '.' + c, driven + '.' + c)
