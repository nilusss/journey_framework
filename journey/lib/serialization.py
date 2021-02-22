"""
serialization module for serializing and deserializing

Extending the json.JSONEncoder to support custom classes

TODO: make code more readable.
TODO: Test with other modules
TODO: update imports for cleaner look
"""

import json
import journey
from journey.lib.modules.eyelid import Eyelid


def decode(o):
    if o.get('CLASS_NAME'):
        exec ("return_class = {}()".format(o.get('CLASS_NAME')))
        a = return_class
        a.__dict__.update((k, v) for k, v in o.iteritems())
        return (a)
    return o


def deserialize(serialized_object):
    return json.loads(serialized_object, object_hook=decode)


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if "pymel.core.nodetypes." in str(type(obj)):
            return obj.name()
        if isinstance(obj, journey.lib.control.Control):
            return obj.__dict__
            # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class Serialize():
    def serialize(self):
        return json.dumps(self.__dict__, cls=Encoder)
        # return dict(class_name='__{}__'.format(self.__class__.__name__), struct=json.dumps(self.__dict__, cls=Encoder))
        # json.dumps(self, default=lambda o: o.get_dict())


