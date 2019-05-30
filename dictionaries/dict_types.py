from collections import namedtuple
Definition = namedtuple('definition', ('definition', 'type','markups') )
Definition.__new__.__defaults__ = (None,) * len(Definition._fields)