"""
module containing different class solvers for ik twisting, fk, etc.
"""


class FK:
    """
    TODO: Squash and stretch
    NOTE: feed driven FK chain. no additional chains should be included.
    """
    def __init__(self,
                 prefix='new',
                 driven='',
                 ):
        self.driven = driven
        pass

    def ctrl(self, *args):
        for chain in zip(self.driven):
            pass


class IK:
    def __init__(self):
        pass
