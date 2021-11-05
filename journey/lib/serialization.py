"""
serialization module for serializing and deserializing

Extending the json.JSONEncoder to support custom classes

TODO: make code more readable.
TODO: Test with other modules
"""

import sys
import json
import importlib


def decode_module(o):
    import journey.lib.modules as mo
    if o.get('CLASS_NAME'):
        module = str(o.get('CLASS_NAME')).lower()
        class_ = getattr(importlib.import_module("journey.lib.modules"), o.get('CLASS_NAME'))
        # exec ("return_class = mo.{}.{}()".format(module, o.get('CLASS_NAME')))
        # return_class = locals()['return_class']
        a = class_()
        if sys.version_info.major >= 3:
            a.__dict__.update((k, v) for k, v in o.items())
        else:
            a.__dict__.update((k, v) for k, v in o.iteritems())
        return (a)
    return o


def decode_guide(o):
    import journey.lib.guides as guides
    if o.get('CLASS_NAME'):
        # print(o.get('prefix')
        # exec("return_class = guides.{}(prefix='{}')".format(o.get('CLASS_NAME'), o.get('prefix')))
        # return_class = locals()['return_class']
        class_ = getattr(importlib.import_module("journey.lib.guides"), o.get('CLASS_NAME'))
        return_class = class_(o.get('prefix'))
        a = return_class
        if sys.version_info.major >= 3:
            a.__dict__.update((k, v) for k, v in o.items())
        else:
            a.__dict__.update((k, v) for k, v in o.iteritems())
        return (a)
    return o


def deserialize_module(serialized_object):
    return json.loads(serialized_object, object_hook=decode_module)


def deserialize_guide(serialized_object):
    return json.loads(serialized_object, object_hook=decode_guide)


class Encoder(json.JSONEncoder):
    def default(self, obj):
        import journey.lib.control as ctrl
        if "pymel.core.nodetypes." in str(type(obj)):
            return obj.name()
        if isinstance(obj, ctrl.Control):
            return obj.__dict__
        if "Draw" in str(obj.__class__.__name__):
            return ''
            # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class Serialize(object):
    def __init__(self):
        super(Serialize, self).__init__()

    def serialize(self):
        """TODO: serialize position rotation scale, mirror and other string attributes on controllers"""
        try:
            self.get_controllers_trs()
        except:
            pass
        return json.dumps(self.__dict__, cls=Encoder)
        # return dict(class_name='__{}__'.format(self.__class__.__name__), struct=json.dumps(self.__dict__, cls=Encoder))
        # json.dumps(self, default=lambda o: o.get_dict())
