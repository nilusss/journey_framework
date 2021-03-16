"""
various tools for the framework
"""

import pymel.core as pm
from pymel.all import mel
import maya.OpenMaya as om
from maya.cmds import ReverseCurve
# import journey.lib.control as ctrl


def list_check(check):
    """Convert argument to a list and return the list
    Args:
        check: str, argument to be converted to list
    Returns:
        list, converted list
    """
    rtrn_list = check
    if type(check) is not list:
        rtrn_list = [check]

    return rtrn_list


def convert_scale(scale):
    if type(scale) is not list:
        scale = [scale, scale, scale]
    return scale


def letter_to_int(letter):
    alpha = list('abcdefghijklmnopqrstuvwxyz')
    return alpha.index(letter) + 1


def int_to_letter(int):
    alpha = list('abcdefghijklmnopqrstuvwxyz')
    return alpha[int]


def split_at(s, c, n):
    words = s.split(c)
    return c.join(words[:n])


def parent_rm(child, module, module_grp):
    """Used to check if parenting objects to a specific rig module group is possible
    Args:
        child: str, object to be parented
        module: str, class module, often written as rig_module
        module_grp: str, a rig module class group
    """
    try:
        #exec('return_module = {}.{}'.format(module.prefix, module_grp))
        pm.parent(child, '{}_{}'.format(module.prefix, module_grp))
    except AttributeError as e:
        print("No rig module to parent under: \"{}\" ".format(str(e)))


def lock_channels(obj, channels=['t', 'r', 's'], t_axis=['x', 'y', 'z'], r_axis=['x', 'y', 'z'], s_axis=['x', 'y', 'z']):
    """Lock objects specified channel
    Args:
        obj: str, node to have it's channels locked
        channels: list(str), main channels to lock
        t_axis: list(str), translate axises to lock
        r_axis: list(str), rotate axises to lock
        s_axis: list(str), scale axises to lock
    Returns:
        list, of all attributes that has been locked
    """
    # lock control channels
    single_attr_lock_list = []

    for ch in channels:
        if ch in ['t', 'r', 's']:
            exec('return_axis = {}_axis'.format(ch))
            for axis in return_axis:
                attr = ch + axis
                single_attr_lock_list.append(attr)
        else:
            single_attr_lock_list.append(ch)
    for attr in single_attr_lock_list:
        pm.setAttr(obj + '.' + attr, l=1, k=0)

    return single_attr_lock_list


def unlock_channels(obj, channels=['t', 'r', 's'], t_axis=['x', 'y', 'z'], r_axis=['x', 'y', 'z'], s_axis=['x', 'y', 'z']):
    """Unlocks objects specified channel
    Args:
        obj: str, node to have it's channels unlocked
        channels: list(str), main channels to unlock
        t_axis: list(str), translate axises to unlock
        r_axis: list(str), rotate axises to unlock
        s_axis: list(str), scale axises to unlock
    Returns:
        list, of all attributes that has been unlocked
    """
    # unlock control channels
    single_attr_unlock_list = []

    for ch in channels:
        if ch in ['t', 'r', 's']:
            exec('return_axis = {}_axis'.format(ch))
            for axis in return_axis:
                attr = ch + axis
                single_attr_unlock_list.append(attr)
        else:
            single_attr_unlock_list.append(ch)
    for attr in single_attr_unlock_list:
        pm.setAttr(obj + '.' + attr, l=0, k=1)

    return single_attr_unlock_list


# python wrapper of the mel command getNextFreeMultiIndex
def get_next_free_multi_index( attr_name, start_index ):
    """Find the next unconnected multi index starting at the passed in index."""
    # assume a max of 10 million connections
    while start_index < 10000000:
        if len(pm.connectionInfo('{}[{}]'.format(attr_name,start_index), sfd=True) or []) == 0:
            return start_index
        start_index += 1

    # No connections means the first index is available
    return 0


# calculating the offset matrix between driven and driver using code instead of nodes
# Setup from https://bindpose.com/maya-matrix-based-functions-part-1-node-based-matrix-constraint/
# Code below is to set the offset in the matrixIn[0]
# localOffset = getLocalOffset(parent, child)
# mc.setAttr("multMatrix1.matrixIn[0]", [localOffset(i, j) for i in range(4) for j in range(4)], type="matrix"
# START
def get_dag_path(node=None):
    # print node
    # if type(node) is not str:
    #     print type(node)
    #     node.name()
    sel = om.MSelectionList()
    sel.add(node)
    d = om.MDagPath()
    sel.getDagPath(0, d)
    return d


def get_local_offset(parent, child):
    parent_wm = get_dag_path(parent).inclusiveMatrix()
    child_wm = get_dag_path(child).inclusiveMatrix()
    return child_wm * parent_wm.inverse()
# END


def matrix_constraint(driver, driven, mo=True, channels=['t', 'r', 's']):
    """
    TODO: If constraint already exists on driven make it able to blend with new driver
    Args:
        driver: str, object to drive the constraint
        driven: str, object to be driven by the constraint
        mo: bool, whether the driven object to maintain offset compared to driver
        channels: list(str), attributes to constrain
    """
    driver = pm.PyNode(driver)
    driven = pm.PyNode(driven)
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
        pm.connectAttr(driven + '.parentInverseMatrix[0]', mult_matrix + '.matrixIn[2]')

        # if not driven_parent:
        #     pm.connectAttr(driven + '.parentInverseMatrix[0]', mult_matrix + '.matrixIn[2]')
        # else:
        #     pm.connectAttr(driven_parent[0] + '.worldInverseMatrix[0]', mult_matrix + '.matrixIn[2]')
    else:
        pm.connectAttr(driver + '.worldMatrix[0]', mult_matrix + '.matrixIn[0]')
        pm.connectAttr(driven + '.parentInverseMatrix[0]', mult_matrix + '.matrixIn[1]')

    for m in channels:
        if m == 'r' and pm.nodeType(driven) == 'joint':
            pm.connectAttr(q_te + '.outputRotate', driven + '.r')
        else:
            pm.connectAttr(decompose_matrix + '.o' + m, driven + '.' + m)

    # if pm.nodeType(driven) == 'joint':
    #     pm.connectAttr(decompose_matrix + '.o' + channels[0], driven + '.' + channels[0])
    #     try:
    #         pm.connectAttr(decompose_matrix + '.o' + channels[2], driven + '.' + channels[2])
    #     except:
    #         pass
    #     pm.connectAttr(q_te + '.outputRotate', driven + '.r')
    # else:
    #     for m in channels:
    #         pm.connectAttr(decompose_matrix + '.o' + m, driven + '.' + m)


def matrix_blend(driver1, driven, blender, driver2, mo=False, blend_value=0.0, force=False, channels=['t', 'r', 's']):
    """Create a matrix blend constraint
    Args:
        driver1: list(str), first object to drive the driven
        driven: list(str), object to be driven by driver1 and driver2
        blender: str, object to be used as the blender controller
        driver2: list(str), second object to drive the driven
        mo: bool, whether the driven object to maintain offset compared to driver
        blend_value: float
        channels: list(str), attributes to be driven
    """

    # driver1 = list_check(driver1)
    # driver2 = list_check(driver2)
    # driven = list_check(driven)
    try:
        pm.getAttr(blender + '.blend')
    except pm.MayaAttributeError:
        pm.addAttr(blender, shortName='blend', longName='FKIKBlend',
                   defaultValue=blend_value, minValue=0.0, maxValue=1.0, k=1)

    # for driver1, driven, driver2 in zip(driver1, driven, driver2):
    # print driver1, driven, driver2
    ik_mult = pm.createNode("multMatrix", n=driver2 + '_multMatrix')
    fk_mult = pm.createNode("multMatrix", n=driver1 + '_multMatrix')
    blend_matrix = pm.createNode("wtAddMatrix", n=driven + '_wtAddMatrix')
    blend_mult = pm.createNode("multMatrix", n=driven + '_multMatrix')
    blend_decomp = pm.createNode("decomposeMatrix", n=driven + '_decomposeMatrix')
    reverse = pm.createNode("reverse", n=driven + '_reverse')

    if mo is True:
        driver1_lo_matrix = pm.createNode('multMatrix', n=driver1 + 'localOffset_multMatrix')
        driver2_lo_matrix = pm.createNode('multMatrix', n=driver1 + 'localOffset_multMatrix')
        pm.connectAttr(driven + '.worldMatrix[0]', driver1_lo_matrix + '.matrixIn[0]', force=force)
        pm.connectAttr(driven + '.worldMatrix[0]', driver2_lo_matrix + '.matrixIn[0]', force=force)
        pm.connectAttr(driver1 + '.worldInverseMatrix[0]', driver1_lo_matrix + '.matrixIn[1]', force=force)
        pm.connectAttr(driver2 + '.worldInverseMatrix[0]', driver2_lo_matrix + '.matrixIn[1]', force=force)
        driver1_lo = pm.getAttr(driver1_lo_matrix + '.matrixSum')
        driver2_lo = pm.getAttr(driver2_lo_matrix + '.matrixSum')
        pm.setAttr(ik_mult + '.matrixIn[0]', driver1_lo, type='matrix')
        pm.setAttr(fk_mult + '.matrixIn[0]', driver2_lo, type='matrix')
        pm.connectAttr(driver1 + '.worldMatrix[0]', ik_mult + '.matrixIn[1]', force=force)
        pm.connectAttr(driver2 + '.worldMatrix[0]', fk_mult + '.matrixIn[1]', force=force)
        pm.connectAttr(driven + '.parentInverseMatrix[0]', ik_mult + '.matrixIn[2]', force=force)
        pm.connectAttr(driven + '.parentInverseMatrix[0]', fk_mult + '.matrixIn[2]', force=force)

    else:
        pm.connectAttr(driver2 + '.worldMatrix', ik_mult + '.matrixIn[1]', force=force)
        pm.connectAttr(driver1 + '.worldMatrix', fk_mult + '.matrixIn[1]', force=force)

    pm.connectAttr(ik_mult + '.matrixSum', blend_matrix + '.wtMatrix[0].matrixIn', force=force)
    pm.connectAttr(fk_mult + '.matrixSum', blend_matrix + '.wtMatrix[1].matrixIn', force=force)

    pm.connectAttr(blend_matrix + '.matrixSum', blend_mult + '.matrixIn[0]', force=force)
    pm.connectAttr(driven + '.parentInverseMatrix[0]', blend_mult + '.matrixIn[1]', force=force)
    pm.connectAttr(blend_mult + '.matrixSum', blend_decomp + '.inputMatrix', force=force)

    if pm.nodeType(driven) == 'joint':
        q_p = pm.createNode("quatProd", n=driven + '_quatProd')
        q_i = pm.createNode("quatInvert", n=driven + '_quatInvert')
        e_tq = pm.createNode("eulerToQuat", n=driven + '_eulerToQuat')
        q_te = pm.createNode("quatToEuler", n=driven + '_quatToEuler')
        pm.connectAttr(blend_decomp + '.outputQuat', q_p + '.input1Quat', force=force)
        pm.connectAttr(driven + '.jointOrient', e_tq + '.inputRotate', force=force)
        pm.connectAttr(e_tq + '.outputQuat', q_i + '.inputQuat', force=force)
        pm.connectAttr(q_i + '.outputQuat', q_p + '.input2Quat', force=force)
        pm.connectAttr(q_p + '.outputQuat', q_te + '.inputQuat', force=force)

    pm.connectAttr(blender + '.blend', blend_matrix + '.wtMatrix[0].weightIn', force=force)
    pm.connectAttr(blender + '.blend', reverse + '.inputX', force=force)
    pm.connectAttr(reverse + '.outputX', blend_matrix + '.wtMatrix[1].weightIn', force=force)

    for m in channels:
        if m == 'r' and pm.nodeType(driven) == 'joint':
            pm.connectAttr(q_te + '.outputRotate', driven + '.r', force=force)
        else:
            pm.connectAttr(blend_decomp + '.o' + m, driven + '.' + m, force=force)
    # pm.connectAttr(q_te + '.outputRotate', driven + '.r')
    # pm.connectAttr(blend_decomp + '.outputTranslate', driven + '.t')
    # pm.connectAttr(blend_decomp + '.outputScale', driven + '.s')


def joint_duplicate(joint_chain, joint_type, offset_grp='', skip=0):
    """Duplicate a joint chain and change the type
    Args:
        joint_chain: list(str), joint chain to duplicate
        joint_type: str, new joint chain type, eg. FK/IK
        offset_grp: str, group to parent the new joint chain under
        skip: int, nth number to skip in the joint chain
    Returns:
        list, new joint chain
    """
    chain = []
    joint_chain = list_check(joint_chain)

    if not skip:
        skip = 1

    for i, j in enumerate(joint_chain[::skip]):
        chain.extend(pm.duplicate(j, parentOnly=True,
                                  n=j.replace('result_jnt', joint_type + '_jnt')))
        try:
            pm.parent(chain[i], offset_grp)
        except pm.MayaNodeError:
            pass
        if i > 0:
            pm.parent(chain[i], chain[i-1])

    return chain


def get_mid_joint(joint_chain):
    """Get the middle joint in a joint chain
    Args:
        joint_chain: list(str), joint chain to get the mid joint from
    Returns:
        int, mid joint number
    """

    if (len(joint_chain) % 2) == 0:
        mid_joint = int(len(joint_chain) / 2) - 1
    else:
        mid_joint = int(len(joint_chain) / 2)

    return mid_joint


def measure(start, end):
    """Create measure distance between to objects
    Args:
        start: str, where the measure tool should start
        end: str, where the measure tool should end
    Returns:
        distanceBetween node
    """

    dist = pm.createNode('distanceBetween', n='{}_{}_DIST'.format(start, end))
    pm.connectAttr(start + '.worldMatrix[0]', dist + '.inMatrix1')
    pm.connectAttr(end + '.worldMatrix[0]', dist + '.inMatrix2')

    return pm.PyNode(dist)


def create_line(start, end, prefix="new"):
    """Create a template line between two objects
    Args:
        start: str, object to start the line from
        end: str, object to end the line
        prefix: str, what to call the new line
    Returns:
        dict, curve object and curve offset group
    """

    pos1 = pm.xform(start, q=1, t=1, ws=1)
    pos2 = pm.xform(end, q=1, t=1, ws=1)
    crv = pm.curve(n=prefix + 'Line_crv', d=1, p=[pos1, pos2])
    cls1 = pm.cluster(crv + '.cv[0]', n=prefix + 'Line1_cls', wn=[start, start], bs=True)
    cls2 = pm.cluster(crv + '.cv[1]', n=prefix + 'Line2_cls', wn=[end, end], bs=True)
    crv.attr('template').set(1)
    offset_grp = pm.createNode("transform", name=prefix + 'CrvOffset_grp')
    offset_grp.attr('inheritsTransform').set(0)
    pm.parent(crv, offset_grp)

    return offset_grp, crv


def create_loc(pos):
    """Create a locator a the given position
    Args:
        pos: maya.OpenMaya.MVector, a vector of x, y, z
    Returns:
        str, locator name
    """

    loc = pm.spaceLocator()
    pm.move(pos.x, pos.y, pos.z, loc)

    return loc


def get_pole_vec_pos(joint_list):
    """Create a locator from the joint list
    Args:
        joint_list: list(str), joint list to get the pole vector position from
    Returns:
        str, newly created locator
    """

    mid_joint = get_mid_joint(joint_list)

    upper_pos = pm.xform(joint_list[0], q=True, ws=True, t=True)
    mid_pos = pm.xform(joint_list[mid_joint], q=True, ws=True, t=True)
    end_pos = pm.xform(joint_list[-1], q=True, ws=True, t=True)

    upper_joint_vec = om.MVector(upper_pos[0], upper_pos[1], upper_pos[2])
    mid_joint_vec = om.MVector(mid_pos[0], mid_pos[1], mid_pos[2])
    end_joint_vec = om.MVector(end_pos[0], end_pos[1], end_pos[2])

    line = (end_joint_vec - upper_joint_vec)
    point = (mid_joint_vec - upper_joint_vec)

    scale_value = (line * point) / (line * line)
    proj_vec = line * scale_value + upper_joint_vec

    upper_to_mid_len = (mid_joint_vec - upper_joint_vec).length()
    mid_to_end_len = (end_joint_vec - mid_joint_vec).length()
    total_length = upper_to_mid_len + mid_to_end_len

    pole_vec_pos = (mid_joint_vec - proj_vec).normal() * total_length + mid_joint_vec

    return create_loc(pole_vec_pos)


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
        except pm.MayaAttributeError:
            pm.addAttr(blender, shortName='blend', longName='FKIKBlend',
                       defaultValue=0, minValue=0.0, maxValue=1.0, k=1)

        # create the blending between fk and ik to the result chain
        for c in channels:
            for drive, fk, ik in zip(driven, driver1, driver2):
                # Create blendColors nodes for Translate, Rotate, and Scale.
                blend = pm.createNode('blendColors', name='blender_to_' + drive)

                pm.connectAttr(blender + '.blend', blend + '.blender')
                pm.connectAttr(ik + '.' + c, blend + '.color1')
                pm.connectAttr(fk + '.' + c, blend + '.color2')
                for color, axis in zip(['R', 'G', 'B'], ['x', 'y', 'z']):
                    pm.connectAttr(blend + '.output' + color, drive + '.' + c + axis)

    # if there is no blender constrain the driver and driven
    else:
        for i, drive in enumerate(driven):
            for c in channels:
                pm.connectAttr(driver1[i] + '.' + c, drive + '.' + c)


def joint_on_curve(curve, prefix='new', parent=False, radius=0.5):
    curve_cvs = pm.ls(curve + '.cv[:]', fl=True)
    # pm.delete(curve_cvs[1])
    # pm.delete(curve_cvs[-2])
    joint_list = []
    for i, cv in enumerate(curve_cvs):
        x, y, z = pm.pointPosition(cv)
        j = pm.joint(n='{}{}_result_jnt'.format(prefix, i+1), radius=radius)
        pm.parent(j, world=True)
        pm.move(j, x, y, z, pm.ls(sl=True))
        joint_list.append(j)

    return joint_list


def check_curves_order(first_crv, secnd_crv):
    cv = pm.getAttr(secnd_crv + '.spans')
    upper_cv1 = pm.xform(first_crv + '.cv[0]', q=True, translation=True, ws=True)
    # lower_cv1 = pm.xform(secnd_crv + '.cv[0]', q=True, translation=True, ws=True)
    lower_cv2 = pm.xform(secnd_crv + '.cv[{}]'.format(cv), q=True, translation=True, ws=True)

    # cv1_deltax = lower_cv1[0] - upper_cv1[0]
    # cv1_deltay = lower_cv1[1] - upper_cv1[1]
    # cv1_deltaz = lower_cv1[2] - upper_cv1[2]

    cv2_deltax = lower_cv2[0] - upper_cv1[0]
    cv2_deltay = lower_cv2[1] - upper_cv1[1]
    cv2_deltaz = lower_cv2[2] - upper_cv1[2]

    if cv2_deltax + cv2_deltay + cv2_deltaz == 0.0:
        pm.select(secnd_crv)
        ReverseCurve()
        pm.select(None)
    return secnd_crv


def create_lowres_crv(highres_curve):
    # create low res lower curves
    lowres_curve = pm.duplicate(highres_curve, name=highres_curve.replace('crv', 'lowres_crv'))[0]
    pm.displaySmoothness(lowres_curve, divisionsU=3, divisionsV=3, pointsWire=16)
    pm.rebuildCurve(lowres_curve, degree=3, endKnots=True, spans=2, keepRange=1, replaceOriginal=True,
                    rebuildType=0)
    # eyelid_low_res_curve.curve.set("%s_%s_low" % (self.side_prefix, self.up_down_prefix))

    # lower_lowres_curve = pm.listRelatives(eyelid_low_res_curve, shapes=True)[0]
    # self.set_shape_node_color(lower_lowres_curve.getShape(), (0, 0, 1))
    lowres_curve.centerPivots()

    return lowres_curve


def loc_on_curve(loc_list, curve):
    curve = pm.PyNode(curve)
    # connect the locators to the high res curve
    for loc in loc_list:
        npoc = pm.createNode("nearestPointOnCurve", name=loc + "npoc")
        position = loc.getTranslation(space="world")
        curve.getShape().worldSpace >> npoc.inputCurve
        npoc.inPosition.set(position)

        u = npoc.parameter.get()

        pci_node = pm.createNode("pointOnCurveInfo", name=loc.name().replace("locator", "PCI"))
        curve.getShape().worldSpace >> pci_node.inputCurve
        pci_node.parameter.set(u)
        pci_node.position >> loc.translate

        pm.delete(npoc)


def insert_joints(start, end, amount, trans_first=False, first=False, both=False):
    """Insert new joints between two joints
    Args:
        start: str, start joint to insert the new joints between
        end: str, end joint to insert the new joints between
        amount: int, amount of new joints to be inserted
        trans_first: bool, whether the first inserted joint should be translated to the start joint
        first: bool, whether to parent the inserted joints to the first joint
        both: bool, whether to parent the inserted joints between the first and last joint
    Returns:
        list, inserted joint chain
    """
    amount = float(amount)
    spacing = 1/float(amount+1)
    inbt_list = []
    positions = [pm.xform(obj, q=True, ws=True, translation=True) for obj in [start, end]]

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

    # parent in-between joints to start or start and end joint
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
        list, twist joint chain
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

    return twist_joints


def setup_splay(splay_mid_ctrl, splay_ctrl, drivens, meta_ctrls_offset=[], prefix='new', scale=1):
    # mid splay multiplier
    mid_param = 0.5
    mid_joint = get_mid_joint(drivens)

    # loop through every driven, create controller and setup splay node system
    for i, driven in enumerate(drivens):
        letter = int_to_letter(i).capitalize()
        flt_int = float(i)
        mid_attr_name = "splayMidMultiplier" + letter
        mid_attr_value = (1.0 / float(len(drivens) - 1)) * flt_int
        mid_attr_value = abs(mid_param - mid_attr_value)

        end_attr_name = "splayMultiplier" + letter
        end_attr_value = (1.0 / float(len(drivens) - 1)) * flt_int

        pm.addAttr(splay_mid_ctrl, shortName=mid_attr_name, longName=mid_attr_name, min=0.0, max=1.0,
                   defaultValue=mid_attr_value, k=True)
        pm.addAttr(splay_ctrl, shortName=end_attr_name, longName=end_attr_name, min=0.0, max=1.0,
                   defaultValue=end_attr_value, k=True)
        meta_ctrl_offset = meta_ctrls_offset[i]

        # setup splay rotation
        mid_md = pm.createNode('multiplyDivide', n=prefix + letter + '_mid_md')
        end_md = pm.createNode('multiplyDivide', n=prefix + letter + '_end_md')

        pma = pm.createNode('plusMinusAverage', n=prefix + letter + '_pma')

        if i <= mid_joint:
            mid_rev = pm.createNode('multiplyDivide', n=prefix + letter + '_mid_rev_md')
            pm.connectAttr(splay_mid_ctrl + '.rotate', mid_rev + '.input1')
            mid_rev.attr('input2X').set(-1)
            mid_rev.attr('input2Y').set(-1)
            mid_rev.attr('input2Z').set(-1)

            mid_rev.output.connect(mid_md.input1)
        else:
            pm.connectAttr(splay_mid_ctrl + '.rotate', mid_md + '.input1')

        pm.connectAttr(splay_ctrl + '.rotate', end_md + '.input1')
        pm.connectAttr(splay_mid_ctrl + '.' + mid_attr_name, mid_md + '.input2X')
        pm.connectAttr(splay_mid_ctrl + '.' + mid_attr_name, mid_md + '.input2Y')
        pm.connectAttr(splay_mid_ctrl + '.' + mid_attr_name, mid_md + '.input2Z')

        pm.connectAttr(splay_ctrl + '.' + end_attr_name, end_md + '.input2X')
        pm.connectAttr(splay_ctrl + '.' + end_attr_name, end_md + '.input2Y')
        pm.connectAttr(splay_ctrl + '.' + end_attr_name, end_md + '.input2Z')

        end_md.output.connect(pma.input3D[0])
        mid_md.output.connect(pma.input3D[1])

        pma.output3D.connect(meta_ctrl_offset.rotate)