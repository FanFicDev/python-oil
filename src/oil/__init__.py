"""oil is a utility library.

oil.util contains various general purpose utility functions.
oil.db contains a utility library around a postgres database.
"""
from oil.db import OilConnectionParameters, oil

__all__ = [
    "OilConnectionParameters",
    "oil",
]
