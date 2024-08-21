import os
from dataclasses import dataclass

import psycopg2

from oil.db import OilConnectionParameters


@dataclass
class Connection:
    closed: bool = False
    autocommit: bool = False

    def close(self) -> None:
        self.closed = True


def mock_connect(s: str) -> Connection:
    assert s == "dbname=minerva"
    return Connection()


psycopg2.connect = mock_connect  # type: ignore


class TestOilConnectionParameters:
    def test_init(self) -> None:
        OilConnectionParameters()

    def test_repr_default(self) -> None:
        ocp = OilConnectionParameters()
        assert ocp.parts["dbname"] == "minerva"
        assert repr(ocp) == "dbname=minerva"
        assert str(ocp) == repr(ocp)

    def test_repr_with_host(self) -> None:
        ocp = OilConnectionParameters()
        ocp.parts["host"] = "localhost"
        assert repr(ocp) == "dbname=minerva host=localhost sslmode=require"
        assert str(ocp) == repr(ocp)

    def test_repr(self) -> None:
        ocp = OilConnectionParameters()
        ocp.parts |= {
            "user": "test_user",
            "password": "test_pass",
            "port": "test_port",
        }
        assert (
            repr(ocp)
            == "dbname=minerva user=test_user password=test_pass port=test_port"
        )
        assert str(ocp) == repr(ocp)

    def test_open(self) -> None:
        ocp = OilConnectionParameters()
        c = ocp.open()

        assert not c.closed
        assert c.autocommit

        # Calling open again should return the cached conn.
        c2 = ocp.open()
        assert id(c) == id(c2)

        # If the cached connection is closed, a new one will be opened.
        c.close()
        c3 = ocp.open()
        assert id(c3) != id(c)

    def test_open_no_autocommit(self) -> None:
        ocp = OilConnectionParameters()
        ocp.autocommit = False

        c = ocp.open()

        assert not c.closed
        assert not c.autocommit

    def test_fromEnvironment(self) -> None:
        os.environ.clear()
        os.environ["OIL_DB_DBNAME"] = "foo"
        os.environ["OIL_DB_USER"] = "bar"
        os.environ["OIL_DB_PASSWORD"] = "baz"

        ocp = OilConnectionParameters.fromEnvironment()
        assert repr(ocp) == "dbname=foo user=bar password=baz"
