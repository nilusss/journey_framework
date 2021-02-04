"""
various tools for the framework
"""

import pymel.core as pm
from pymel.all import *
import maya.cmds as mc
import maya.OpenMaya as om


# def colors(color):
#     dict_colors = {
#         "yellow": 17,
#         "red": 13,
#         "blue": 6,
#         "cyan": 18,
#         "green": 7,
#         "darkRed": 4,
#         "darkBlue": 15,
#         "white": 16,
#         "black": 1,
#         "gray": 3,
#         "none": 0,
#     }
#
#     if color in dict_colors:
#         return dict_colors[color]


def list_check(check):
    if type(check) is str:
        check = check.split()

    return check


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
    """
    TODO: If constraint already exists on driven make it able to blend with new driver
    Args:
        driver:
        driven:
        mo:
        channels:

    Returns:

    """
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
        try:
            pm.connectAttr(decompose_matrix + '.o' + channels[2], driven + '.' + channels[2])
        except:
            pass
        pm.connectAttr(q_te + '.outputRotate', driven + '.r')
    else:
        for m in channels:
            pm.connectAttr(decompose_matrix + '.o' + m, driven + '.' + m)


def matrix_blend(driver1, driven, blender, driver2, channels=['t', 'r', 's']):
    for i, j in enumerate(driven):
        qP = mc.createNode("quatProd")
        qI = mc.createNode("quatInvert")
        eTQ = mc.createNode("eulerToQuat")
        qTE = mc.createNode("quatToEuler")
        ikMult = mc.createNode("multMatrix")
        fkMult = mc.createNode("multMatrix")
        blendMatrix = mc.createNode("wtAddMatrix")
        blendMult = mc.createNode("multMatrix")
        blendDecomp = mc.createNode("decomposeMatrix")
        reverse = mc.createNode("reverse")

        mc.connectAttr(driver2[i] + '.worldMatrix', ikMult + '.matrixIn[1]')
        mc.connectAttr(driver1[i] + '.worldMatrix', fkMult + '.matrixIn[1]')

        mc.connectAttr(ikMult + '.matrixSum', blendMatrix + '.wtMatrix[0].matrixIn')
        mc.connectAttr(fkMult + '.matrixSum', blendMatrix + '.wtMatrix[1].matrixIn')

        mc.connectAttr(blendMatrix + '.matrixSum', blendMult + '.matrixIn[0]')
        mc.connectAttr(j + '.parentInverseMatrix[0]', blendMult + '.matrixIn[1]')
        mc.connectAttr(blendMult + '.matrixSum', blendDecomp + '.inputMatrix')

        mc.connectAttr(blendDecomp + '.outputQuat', qP + '.input1Quat')
        mc.connectAttr(j + '.jointOrient', eTQ + '.inputRotate')
        mc.connectAttr(eTQ + '.outputQuat', qI + '.inputQuat')
        mc.connectAttr(qI + '.outputQuat', qP + '.input2Quat')
        mc.connectAttr(qP + '.outputQuat', qTE + '.inputQuat')

        mc.connectAttr(blender + '.blend', blendMatrix + '.wtMatrix[0].weightIn')
        mc.connectAttr(blender + '.blend', reverse + '.inputX')
        mc.connectAttr(reverse + '.outputX', blendMatrix + '.wtMatrix[1].weightIn')

        mc.connectAttr(qTE + '.outputRotate', j + '.r')
        mc.connectAttr(blendDecomp + '.outputTranslate', j + '.t')
        mc.connectAttr(blendDecomp + '.outputScale', j + '.s')


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
    driver1 = list_check(driver1)
    driver2 = list_check(driver2)
    driven = list_check(driven)

    if blender:
        # Check if the blender controller has the .blend attribute, otherwise create one
        try:
            pm.getAttr(blender + '.blend')
        except Exception as e:
            pm.addAttr(blender, shortName='blend', longName='FKIKBlend',
                       defaultValue=0, minValue=0.0, maxValue=1.0, k=1)
        for c in channels:
            for drive, fk, ik in zip(driven, driver1, driver2):
                # Create blendColors nodes for Translate, Rotate, and Scale.
                blend = pm.createNode('blendColors', name='blender_to_' + drive)

                pm.connectAttr(blender + '.blend', blend + '.blender')
                pm.connectAttr(ik + '.' + c, blend + '.color1')
                pm.connectAttr(fk + '.' + c, blend + '.color2')
                for color, axis in zip(['R', 'G', 'B'], ['x', 'y', 'z']):
                    pm.connectAttr(blend + '.output' + color, drive + '.' + c + axis)

    else:
        for i, drive in enumerate(driven):
            for c in channels:
                pm.connectAttr(driver1[i] + '.' + c, drive + '.' + c)


def insert_joints(start, end, amount, trans_first=False, parent=True, first=False, both=False):
    amount = float(amount)
    spacing = 1/float(amount+1)
    inbt_list = []
    positions = [mc.xform(obj, q=True, ws=True, translation=True) for obj in [start, end]]

    pos = spacing

    if trans_first:
        inbt_joint = pm.duplicate(start, parentOnly=True,
                                  n=start.replace('result_jnt', 'inbt0_result_jnt'))[0]
        pm.parent(inbt_joint, world=True)
        inbt_list.append(inbt_joint)

    for i in range(int(amount+1)):
        if i != 0 or amount:

            # create motion path curve
            m_curve = pm.curve(d=1, p=positions, k=[0, 1])
            # duplicate start joint to get same attributes on all the joints
            inbt_joint = pm.duplicate(start, parentOnly=True,
                                      n=start.replace('result_jnt', 'inbt{0}_result_jnt'.format(i)))[0]
            pm.parent(inbt_joint, world=True)
            inbt_list.append(inbt_joint)

            # append the joint to the motion path and move it down the curve
            m_path = pm.pathAnimation(inbt_joint, su=pos, curve=m_curve, follow=False)
            u_value = pm.listConnections(inbt_joint, type='motionPath')[0] + '.u'

            # breaking the connection with mel
            mel.eval("source channelBoxCommand; CBdeleteConnection \"%s\"" % u_value)
            # delete motion path and curve
            pm.delete(u_value, m_curve)

            # freeze transforms and reparent the joints
            pm.makeIdentity(inbt_joint, apply=True)
            if trans_first:
                li = i
            else:
                li = i - 1
            if li > 0:
                pm.parent(inbt_list[li], inbt_list[li - 1])

            pos += spacing

    pm.delete(inbt_list[-1])
    del inbt_list[-1]
    if first:
        pm.parent(inbt_list[0], start)
    if both:
        pm.parent(inbt_list[0], start)
        pm.parent(end, inbt_list[-1])

    return inbt_list


def simple_twist(end, twist_joints='', start='', amount=''):
    """Create a simple twist setup. Can also create the twist joints

    Args:
        end (str): last joint in the joint chain to compare twist joint rotations to
        twist_joints (list): joints to be twisted
        start (str): first joint to place the twist joints between - optional
        amount (str): amount of twist joints - optional

    Returns:

    """
    # if arguments are passed create a twist joint chain
    if start and end and amount:
        twist_joints = insert_joints(start, end, amount, trans_first=True, first=True)

    # create mult node to calculate twisting
    mult = pm.createNode('multiplyDivide')
    mult.operation.set(2)
    mult.input2X.set(-1)
    mult.input2Y.set(amount)
    pm.connectAttr(end + '.rx', mult + '.input1Y')

    # for slower first twist
    # pm.connectAttr(conv + '.output', mult + '.input1X')

    # connect twist calculation to joint rotate
    for joint in twist_joints:
        pm.connectAttr(mult + '.outputY', joint + '.rotateX')


