"""oil.db.postgres exposes a simple postgres connection factory."""

import typing

if typing.TYPE_CHECKING:
    from psycopg2 import connection  # type: ignore[attr-defined]


class OilConnectionParameters:
    """
    Provides a connection to a postgres db.

    Connection string components are overridable on a per object basis, or by
    using defaults set in environment variables.
    """

    def __init__(self) -> None:
        """Construct a default value."""
        self.parts: dict[str, str | None] = {
            "dbname": "minerva",
            "user": None,
            "password": None,
            "host": None,
            "port": None,
            "sslmode": None,
        }
        self.autocommit = True
        self.conn: connection | None = None

    def __repr__(self) -> str:
        """Convert ourselves into a form useful for passing to a postgres lib."""
        return " ".join(
            [f"{k}={v}" for k, v in self.parts.items() if v is not None]
        ) + (
            " sslmode=require"
            if self.parts["host"] is not None and self.parts["sslmode"] is None
            else ""
        )

    def open(self) -> "connection":
        """Open and return a connection to the database described by our parms."""
        if self.conn is not None and self.conn.closed:
            self.conn = None
        if self.conn is not None:
            return self.conn
        import psycopg2

        self.conn = psycopg2.connect(repr(self))
        if self.autocommit:
            self.conn.autocommit = True
        return self.conn

    @staticmethod
    def from_environment() -> "OilConnectionParameters":
        """Construct by reading defaults from the environment, if present."""
        import os

        self = OilConnectionParameters()
        for k in self.parts:
            env_key = f"OIL_DB_{k}".upper()
            if env_key in os.environ:
                self.parts[k] = os.environ[env_key]
        return self


oil: OilConnectionParameters = OilConnectionParameters.from_environment()
