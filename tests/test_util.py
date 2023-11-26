import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import oil.util as util
import pytest
import requests


@dataclass
class Response:
    status_code: int
    text: str


UNIX_TIMESTAMPS = [0, 946684800, 1642956341, 1893456000]


@pytest.mark.parametrize("case", ["foo", "foo-", "-foo", "foo-!@#", "!@#-foo"])
def test_urlTitle_fold(case: str) -> None:
    assert util.urlTitle(case) == "foo"


@pytest.mark.parametrize("case", ["foo bar", "foo   bar", "  foo   bar  "])
def test_urlTitle_squeeze(case: str) -> None:
    assert util.urlTitle(case) == "foo-bar"


@pytest.mark.parametrize("case", ["January 10th", "Feb 11", "2021 Dec"])
def test_isWrittenDate_is(case: str) -> None:
    assert util.isWrittenDate(case)


@pytest.mark.parametrize("case", ["foo bar", "2022-01-01", "0"])
def test_isWrittenDate_is_not(case: str) -> None:
    assert not util.isWrittenDate(case)


@pytest.mark.parametrize("fetched", UNIX_TIMESTAMPS)
class TestParseDateAsUnix:
    @pytest.mark.parametrize("case", UNIX_TIMESTAMPS)
    def test_absolute(self, case: int, fetched: int) -> None:
        assert util.parseDateAsUnix(case, fetched) == case
        assert util.parseDateAsUnix(str(case), fetched) == case
        assert util.parseDateAsUnix(f"  {case}  ", fetched) == case

    @pytest.mark.parametrize("case", [1, 5])
    def test_relative(self, case: int, fetched: int) -> None:
        assert util.parseDateAsUnix("just", fetched) == fetched
        assert util.parseDateAsUnix("  just  ", fetched) == fetched

        # minutes ago
        expected = fetched - case * 60
        assert util.parseDateAsUnix(f"{case}m ago", fetched) == expected
        assert util.parseDateAsUnix(f"  {case}m  ago  ", fetched) == expected

        # hours ago
        expected = fetched - case * 60 * 60
        assert util.parseDateAsUnix(f"{case}h ago", fetched) == expected
        assert util.parseDateAsUnix(f"  {case}h  ago  ", fetched) == expected

    @pytest.mark.parametrize("suff", ["", " ", "m ago", "m ago ", "h ago", "h ago "])
    def test_negative_failure(self, suff: str, fetched: int) -> None:
        # invalid or negative dates
        with pytest.raises(Exception, match="error parsing date"):
            util.parseDateAsUnix(-5, fetched)
        with pytest.raises(Exception, match="error parsing date"):
            util.parseDateAsUnix(f"-5{suff}", fetched)

    @pytest.mark.parametrize("day", ["3", "03"])
    @pytest.mark.parametrize("month", ["2", "02"])
    @pytest.mark.parametrize("sep", ["/", "-", "."])
    def test_separated_triple(
        self, sep: str, month: str, day: str, fetched: int
    ) -> None:
        # dashed, slashed, or dotted year/date/month
        s = sep.join(["2020", month, day])
        assert util.parseDateAsUnix(s, fetched) == 1580688000

    @pytest.mark.parametrize("case", ["foo.bar.baz", "1.2.foo", "1.foo.3", "foo.2.3"])
    def test_dotted_failure(self, case: str, fetched: int) -> None:
        # dotted with non-numeric parts does not parse
        with pytest.raises(Exception, match="error parsing date"):
            util.parseDateAsUnix(case, fetched)

    @pytest.mark.parametrize("month", ["February", "Feb"])
    def test_written(self, month: str, fetched: int) -> None:
        # written dates are kinda wonky
        s = f"{month} 3rd 2020"
        assert util.parseDateAsUnix(s, fetched) == 1580688000


@pytest.mark.parametrize("day", ["3", "03"])
@pytest.mark.parametrize("month", ["2", "02"])
def test_parseDateAsUnix_separated_double(month: str, day: str) -> None:
    # slashed date/month, using relative year
    s = f"{month}/{day}"
    assert util.parseDateAsUnix(s, 0) == 2851200  # 1970/2/3
    assert util.parseDateAsUnix(s, 946684800) == 949536000  # 2000/2/3
    assert util.parseDateAsUnix(s, 1642956341) == 1643846400  # 2022/2/3
    assert util.parseDateAsUnix(s, 1893456000) == 1896307200  # 2030/2/3


def test_logMessage(tmp_path: Path) -> None:
    os.chdir(tmp_path)

    def mock_time_time() -> float:
        return 123.4

    import time

    time.time = mock_time_time

    def content() -> str:
        with open("./oil.log") as f:
            return f.read()

    def test(f: Callable[[], None], expected: str) -> None:
        with warnings.catch_warnings(record=True) as w:
            f()
            assert content() == expected

            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "logging" in str(w[-1].message)

    test(lambda: util.logMessage("foo"), "123|foo\n")
    test(lambda: util.logMessage("bar\n", fname="oil.log"), "123|foo\n123|bar\n")
    test(lambda: util.logMessage("baz", logDir="./"), "123|foo\n123|bar\n123|baz\n")
    test(
        lambda: util.logMessage("quux", fname="oil.log", logDir="./"),
        "123|foo\n123|bar\n123|baz\n123|quux\n",
    )
    test(
        lambda: util.logMessage("quiz\n"),
        "123|foo\n123|bar\n123|baz\n123|quux\n123|quiz\n",
    )


def test_lookupRemoteIP_success() -> None:
    def mock_get_success(url: str, timeout: Optional[int] = None) -> Response:
        assert timeout is not None
        assert timeout < 10.0
        return Response(text="\nfoo bar\n", status_code=200)

    requests.get = mock_get_success  # type: ignore

    assert util.lookupRemoteIP() == "foo bar"


def test_lookupRemoteIP_failure() -> None:
    def mock_get_failure(url: str, timeout: Optional[int] = None) -> Response:
        assert timeout is not None
        assert timeout < 10.0
        return Response(text="\nuh oh\n", status_code=500)

    requests.get = mock_get_failure  # type: ignore

    with pytest.raises(Exception, match="failed to determine remote address"):
        util.lookupRemoteIP()


@pytest.mark.parametrize("spread", [0.2, 0.4, 0.6])
@pytest.mark.parametrize("base", [1.0, 2.0, 3.0])
def test_getFuzz(base: float, spread: float) -> None:
    for _i in range(10):
        fuzz = util.getFuzz(base, spread)
        assert fuzz >= base
        assert fuzz < base + spread


@pytest.mark.parametrize("case", [b"", b"123", b"foo bar"])
def test_compress(case: bytes) -> None:
    # basic sanity
    r = util.compress(case)
    assert len(r) > 4
    assert r[0:3] == b"\x00\x00\x00"
    assert r[3] == len(case)

    # deterministic
    assert util.compress(case) == r


@pytest.mark.parametrize("case", [b"", b"123", b"foo bar"])
def test_uncompress_success(case: bytes) -> None:
    # round trips
    cc = util.compress(case)
    r = util.uncompress(cc)
    assert r == case


@pytest.mark.parametrize(
    "case",
    [
        b"",  # no header
        b"\x00\x00\x00\x00",  # zero length content
        # wrong header
        b"\x00\x00\x00\x01" + util.compress(b"foo")[4:],
        b"\x00\x00\x00\x0f" + util.compress(b"foo")[4:],
        # malformed data
        util.compress(b"foo")[:4] + b"\x00",
    ],
)
def test_uncompress_failure(case: bytes) -> None:
    with pytest.raises(
        Exception,
        match="(expected .* but got .* bytes|incomplete or truncated stream)",
    ):
        util.uncompress(case)


def test_getUniqueJobName() -> None:
    assert util.getUniqueJobName() != util.getUniqueJobName()
    assert util.getUniqueJobName(extra="foo").endswith("foo")
    assert len(util.getUniqueJobName(bits=64)) > len(util.getUniqueJobName(bits=32))
