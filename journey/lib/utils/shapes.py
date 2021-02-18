"""
library for creating shapes
"""
import pymel.core as pm
from journey.lib.utils.tools import convert_scale


def circle(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[1, 0, 0], degree=3,
                       sections=8, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def circleX(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[1, 0, 0], degree=3,
                       sections=8, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def circleY(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[0, 1, 0], degree=3,
                       sections=8, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def circleZ(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[0, 0, 1], degree=3,
                       sections=8, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def diamond(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[1, 0, 0], degree=1,
                       sections=4, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def diamondX(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[1, 0, 0], degree=1,
                       sections=4, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def diamondY(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[0, 1, 0], degree=1,
                       sections=4, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def diamondZ(scale, name=''):
    shape1 = pm.circle(name=name, constructionHistory=False,
                       normal=[0, 0, 1], degree=1,
                       sections=4, radius=scale)[0]
    pm.select(clear=True)

    return shape1


def sphere(scale, name=''):
    shape1 = circleX(scale, name)
    shape2 = circleY(scale, name)
    shape3 = circleZ(scale, name)

    pm.parent(shape2.getShape(), shape1,
              relative=1, shape=1)
    pm.parent(shape3.getShape(), shape1,
              relative=1, shape=1)
    pm.delete(shape2)
    pm.delete(shape3)
    pm.select(clear=True)

    return shape1


def cube(scale, name=''):
    scale = convert_scale(scale)
    cube1 = pm.curve(name=name, d=True,
                     p=[(0.5, 0.5, 0.5), (0.5, -0.5, 0.5),
                        (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5),
                        (0.5, 0.5, 0.5), (0.5, -0.5, 0.5),
                        (0.5, -0.5, -0.5), (0.5, 0.5, -0.5),
                        (0.5, 0.5, 0.5), (0.5, 0.5, -0.5),
                        (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5),
                        (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5),
                        (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5),
                        (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5),
                        (-0.5, 0.5, -0.5)],
                     k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                        12, 13, 14, 15, 16, 17, 18])

    pm.scale(cube1, scale[0], scale[1], scale[2])
    pm.makeIdentity(cube1, apply=True, s=1)
    pm.select(clear=True)

    return cube1


def rectangle(scale, name=''):
    scale = convert_scale(scale)
    rectangle1 = pm.curve(name=name, d=True,
                          p=[(0.7, 0.3, 0.5), (0.7, -0.3, 0.5),
                             (-0.7, -0.3, 0.5), (-0.7, 0.3, 0.5),
                             (0.7, 0.3, 0.5), (0.7, -0.3, 0.5),
                             (0.7, -0.3, -0.5), (0.7, 0.3, -0.5),
                             (0.7, 0.3, 0.5), (0.7, 0.3, -0.5),
                             (0.7, -0.3, -0.5), (-0.7, -0.3, -0.5),
                             (-0.7, 0.3, -0.5), (0.7, 0.3, -0.5),
                             (-0.7, 0.3, -0.5), (-0.7, -0.3, -0.5),
                             (-0.7, -0.3, 0.5), (-0.7, 0.3, 0.5),
                             (-0.7, 0.3, -0.5)])

    pm.scale(rectangle1, scale[0], scale[1], scale[2])
    pm.makeIdentity(rectangle1, apply=True, s=1)
    pm.select(clear=True)

    return rectangle1


def arrow3D(scale, name=''):
    scale = convert_scale(scale)
    arrow1 = pm.curve(name=name, d=True,
                      p=[(0, 0, -1.75), (0.75, 0, -0.75), (0.4, 0, -0.75),
                         (0.4, 0, 0), (-0.4, 0, 0), (-0.4, 0, -0.75),
                         (-0.75, 0, -0.75), (0, 0, -1.75), (0, -0.75, -0.75),
                         (0, -0.4, -0.75), (-0, -0.4, 0), (0, 0.4, 0),
                         (0, 0.4, -0.75), (0, 0.75, -0.75), (0, 0, -1.75)])

    pm.scale(arrow1, scale[0], scale[1], scale[2])
    pm.makeIdentity(arrow1, apply=True, s=1, n=0, pn=1)

    return arrow1


def master(scale, name=''):
    scale = convert_scale(scale)
    master1 = pm.curve(name='master', d=1,
                       p=[(-5.472546, 0, 1.778139), (-5.472546, 0, -1.778137),
                          (-4.655226, 0, -3.382219), (-3.38222, 0, -4.655226),
                          (-1.778138, 0, -5.472547), (1.778139, 0, -5.472547),
                          (3.382222, 0, -4.655227), (4.655229, 0, -3.38222),
                          (5.47255, 0, -1.778138), (5.472546, 0, 1.778139),
                          (4.655226, 0, 3.382221), (3.38222, 0, 4.655227),
                          (1.778138, 0, 5.472547), (-1.778137, 0, 5.472547),
                          (-3.382219, 0, 4.655227), (-4.655226, 0, 3.382221),
                          (-5.472546, 0, 1.778139)])

    master_forward = pm.curve(name='masterForward', d=1,
                              p=[(1.778138, 0, 5.472547),
                                 (6.55294e-07, 0, 8.059775),
                                 (-1.778137, 0, 5.472547)])
    master_backward = pm.curve(name='masterBackward', d=1,
                               p=[(-1.778138, 0, -5.472547),
                                  (8.61953e-07, 0, -6.934346),
                                  (1.778139, 0, -5.472547)])
    master_left = pm.curve(name='masterRight', d=1,
                           p=[(5.47255, 0, -1.778138),
                              (6.934345, 0, 1.43659e-06),
                              (5.472546, 0, 1.778139)])
    master_right = pm.curve(name='masterLeft', d=1,
                            p=[(-5.472546, 0, -1.778137),
                               (-6.934345, 0, 1.43659e-06),
                               (-5.472546, 0, 1.778139)])

    pm.rename(master1.getShape(), master1 + 'Shape')

    extra_shapes = [master_backward, master_forward, master_left, master_right]
    for shape in extra_shapes:
        pm.rename(shape.getShape(), shape + 'shape')
        pm.parent(shape.getShape(), master1, s=True, r=True)
        pm.delete(shape)

    pm.scale(master1, 0.1, 0.1, 0.1)
    pm.makeIdentity(master1, apply=True, s=1, n=0, pn=1)

    pm.scale(master1, scale[0], scale[1], scale[2])
    pm.makeIdentity(master1, apply=True, s=1, n=0, pn=1)
    pm.select(clear=True)

    return master1


def settings(scale, name=''):
    settings1 = pm.curve(name=name, d=1,
                         p=[(0, 0, 1), (-1, 0, 1), (-1, 0, 0),
                            (-2, 0, 0), (-2, 0, -1), (-1, 0, -1),
                            (-1, 0, -2), (0, 0, -2), (0, 0, -1),
                            (1, 0, -1), (1, 0, 0), (0, 0, 0),
                            (0, 0, 1)])

    pm.scale(settings1, scale, scale, scale)
    pm.xform(settings1, cp=True)
    pm.move(settings1, rpr=True)
    pm.makeIdentity(settings1, apply=True, s=1, t=1)
    pm.select(clear=True)

    return settings1


def offset(scale, name=''):
    scale = convert_scale(scale)
    offset1 = pm.curve(name=name, d=1,
                       p=[(-5.472546, 0, 1.778139), (-5.472546, 0, -1.778137),
                          (-4.655226, 0, -3.382219), (-3.38222, 0, -4.655226),
                          (-1.778138, 0, -5.472547), (1.778139, 0, -5.472547),
                          (3.382222, 0, -4.655227), (4.655229, 0, -3.38222),
                          (5.47255, 0, -1.778138), (5.472546, 0, 1.778139),
                          (4.655226, 0, 3.382221), (3.38222, 0, 4.655227),
                          (1.778138, 0, 5.472547), (-1.778137, 0, 5.472547),
                          (-3.382219, 0, 4.655227), (-4.655226, 0, 3.382221),
                          (-5.472546, 0, 1.778139)])

    pm.scale(offset1, 0.1, 0.1, 0.1)
    pm.makeIdentity(offset1, apply=True, s=1)
    pm.scale(offset1, scale[0], scale[1], scale[2])
    pm.makeIdentity(offset1, apply=True, s=1)
    pm.select(clear=True)

    return offset1


def fancy_sphere(scale, name=''):
    fancy_sphere1 = pm.curve(name=name, d=1,
                             p=[(0, 3.21, 0), (0, 2.96, 1.23), (0, 2.27, 2.27),
                                (0, 1.23, 2.96), (0, 0, 3.21), (0, -1.23, 2.96),
                                (0, -2.27, 2.27), (0, -2.97, 1.23), (0, -3.21, 0),
                                (0, -2.96, -1.23), (0, -2.27, -2.27), (0, -1.23, -2.96),
                                (0, 0, -3.21), (0, 1.23, -2.96), (0, 2.27, -2.27),
                                (0, 2.96, -1.23), (0, 3.21, 0), (-0.87, 2.96, 0.97),
                                (-1.60, 2.27, 1.60), (-2.09, 1.23, 2.09), (-2.27, 0, 2.27),
                                (-2.09, -1.23, 2.09), (-1.60, -2.27, 1.60), (-0.87, -2.96, 0.87),
                                (0, -3.21, 0), (0.87, -2.97, -0.87), (1.60, -2.27, -1.60),
                                (2.09, -1.23, -2.09), (2.27, 0, -2.27), (2.09, 1.23, -2.09),
                                (1.60, 2.27, -1.60), (0.87, 2.86, -0.87), (0, 3.21, 0),
                                (-1.23, 2.97, 0), (-2.27, 2.27, 0), (-2.97, 1.23, 0),
                                (-3.21, 0, 0), (-2.97, -1.23, 0), (-2.27, -2.27, 0),
                                (-1.23, -2.96, 0), (0, -3.21, 0), (1.23, -2.97, 0),
                                (2.27, -2.27, 0), (2.97, -1.23, 0), (3.21, 0, 0),
                                (2.97, 1.23, 0), (2.27, 2.27, 0), (1.23, 2.97, 0),
                                (0, 3.21, 0), (-0.87, 2.97, -0.87), (-1.60, 2.27, -1.60),
                                (-2.09, 1.23, -2.09), (-2.27, 0, -2.27), (-2.09, -1.23, -2.09),
                                (-1.60, -2.27, -1.60), (-0.87, -2.96, -0.87), (0, -3.21, 0),
                                (0.87, -2.97, 0.87), (1.60, -2.27, 1.60), (2.09, -1.23, 2.09),
                                (2.27, 0, 2.27), (2.09, 1.23, 2.09), (1.60, 2.27, 1.60),
                                (0.87, 2.97, 0.87), (0, 3.21, 0), (1.23, 2.97, 0),
                                (2.27, 2.27, 0), (2.97, 1.23, 0), (3.21, 0, 0),
                                (2.27, 0, 2.27), (0, 0, 3.21), (-2.27, 0, 2.27),
                                (-3.21, 0, 0), (-2.27, 0, -2.27), (0, 0, -3.21),
                                (2.27, 0, -2.27), (3.21, 0, 0), (2.27, 0, 2.27),
                                (0, 0, 3.21)])

    pm.scale(fancy_sphere1, 0.25, 0.25, 0.25)
    pm.makeIdentity(fancy_sphere1, apply=True, s=1)
    pm.scale(fancy_sphere1, scale, scale, scale)
    pm.makeIdentity(fancy_sphere1, apply=True, s=1)
    pm.select(clear=True)

    return fancy_sphere1


def line_sphere(scale, name=''):
    line_sphere1 = pm.curve(name=name, d=1,
                            p=[(0, 0, 0),
                               (0, 0, 4.6666666666666661),
                               (0, 0, 9.3333333333333321),
                               (0, 0, 7)])
    pm.getAttr(line_sphere1 + ".cv[3].zValue")
    sphere_attach = sphere(scale, name)
    pm.setAttr(sphere_attach + ".tz", 8.335)
    pm.makeIdentity(sphere_attach, apply=True, t=True)
    pm.parent(sphere_attach.getShapes(),
              line_sphere1, relative=1, shape=1)
    pm.delete(sphere_attach)
    pm.select(clear=True)

    return line_sphere1


def cog(scale, name=''):
    cog1 = pm.circle(name=name, s=16, nr=[0, 1, 0], radius=scale)[0]
    pm.select((cog1 + '.cv[1]'), (cog1 + '.cv[3]'), (cog1 + '.cv[5]'),
              (cog1 + '.cv[7]'), (cog1 + '.cv[9]'), (cog1 + '.cv[11]'),
              (cog1 + '.cv[13]'), (cog1 + '.cv[15]'), (cog1 + '.cv[17]'),
              (cog1 + '.cv[19]'), r=True)
    pm.scale(0.3, 0.3, 0.3, p=[0, 0, 0], r=True)
    pm.makeIdentity(cog1, apply=True, t=1, r=1, s=1, n=0)
    cog_circle = circleY(scale*0.2, name)

    pm.parent(cog_circle.getShape(),
              cog1, relative=1, shape=1)
    pm.delete(cog_circle)
    pm.select(clear=True)

    return cog1

