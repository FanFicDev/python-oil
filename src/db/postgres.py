"""oil.db.postgres exposes a simple postgres connection factory."""
from typing import TYPE_CHECKING, Optional, Dict
if TYPE_CHECKING:
	import psycopg2

class OilConnectionParameters:
	"""Provides a connection to a postgres db.

	Connection string components are overridable on a per object basis, or by
	using defaults set in environment variables."""
	def __init__(self) -> None:
		self.parts: Dict[str, Optional[str]] = {
				'dbname': 'minerva',
				'user': None,
				'password': None,
				'host': None,
				'port': None,
		}

	def __repr__(self) -> str:
		"""Convert ourselves into a form useful for passing to a postgres lib."""
		return ' '.join([
				f"{k}={v}" for k, v in self.parts.items() if v is not None
		])

	def open(self) -> 'psycopg2.connection':
		"""Open and return a connection to the database described by our parms."""
		import psycopg2
		return psycopg2.connect(self.__repr__())

	@staticmethod
	def fromEnvironment() -> 'OilConnectionParameters':
		"""Construct a new set of conneciton paramaters by reading defaults from
		the environment, if present."""
		import os
		self = OilConnectionParameters()
		for k in self.parts:
			envKey = f'OIL_DB_{k}'.upper()
			if envKey in os.environ:
				self.parts[k] = os.environ[envKey]
		return self

oil: OilConnectionParameters = OilConnectionParameters.fromEnvironment()

