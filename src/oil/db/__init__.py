"""oil.db is a utility library around a postgres database."""
from oil.db.postgres import OilConnectionParameters, oil

__all__ = [
    "OilConnectionParameters",
    "oil",
]
