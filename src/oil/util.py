"""Grab bag of various utility functions."""

import datetime
import os
import random
import re
import threading
import time
import warnings
import zlib
from http import HTTPStatus
from pathlib import Path

import dateutil.parser

DEFAULT_LOG_FILE = "oil.log"
DEFAULT_LOG_DIR = "./"


class LookupRemoteIPError(Exception):
    """Raised when we fail to lookup our remote IP."""


class MismatchedUncompressSizeError(Exception):
    """Raised when the uncompressed size does not match the expected length header."""


def url_title(title: str) -> str:
    """Turn `title` into a url safe slug string."""
    res = ""
    for char in title:
        if char.isalnum():
            res += char
        elif len(res) != 0 and res[-1] != "-":
            res += "-"
    return res.rstrip("-")


_WRITTEN_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
_WRITTEN_MONTHS += [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def is_written_date(val: str) -> bool:
    """Return True iff `val` contains an English month name."""
    return any(val.find(wm) >= 0 for wm in _WRITTEN_MONTHS)


def parse_date_as_unix(updated: str | int, fetched: int) -> int:  # noqa: C901 PLR0911
    """
    Parse a human readable date as a unix timestamp.

    Several formats are supported including relative dates. If `updated`
    represents a relative date, it is assumed to be relative to `fetched`.
    """
    current_year = datetime.datetime.fromtimestamp(
        fetched, tz=datetime.timezone.utc
    ).year

    if isinstance(updated, int):
        if updated < 0:
            msg = f"error parsing date: negative int: {updated}"
            raise ValueError(msg)
        return updated

    updated = updated.strip()

    if updated.isnumeric():
        return int(updated)

    if updated.endswith("ago"):
        updated = updated[: -len("ago")]
    updated = updated.strip()

    if re.match(r"^\d+m$", updated):
        return fetched - (60 * int(updated[:-1]))
    if re.match(r"^\d+h$", updated):
        return fetched - (60 * 60 * int(updated[:-1]))
    if re.match(r"^just", updated):
        return fetched

    month_day_part_count = 2
    full_date_part_count = 3

    slashed_parts = updated.split("/")
    if len(slashed_parts) == month_day_part_count:
        fdate = f"{current_year}/{slashed_parts[0]}/{slashed_parts[1]}"
        dt = dateutil.parser.parse(fdate)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())
    if len(slashed_parts) == full_date_part_count:
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    dashed_parts = updated.split("-")
    if len(dashed_parts) == full_date_part_count:
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    dotted_parts = updated.split(".")
    if (
        len(dotted_parts) == full_date_part_count
        and dotted_parts[0].isnumeric()
        and dotted_parts[1].isnumeric()
        and dotted_parts[2].isnumeric()
    ):
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    if is_written_date(updated):
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    msg = f"error parsing date: unknown format: {updated}"
    raise ValueError(msg)


def log_message(msg: str, fname: str | None = None, log_dir: str | None = None) -> None:
    """Write a given `msg` to the log file `fname` within `log_dir`."""
    warnings.warn("Use logging instead", DeprecationWarning, stacklevel=1)
    if fname is None:
        fname = DEFAULT_LOG_FILE
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    if not msg.endswith("\n"):
        msg += "\n"
    with Path(Path(log_dir) / Path(fname)).open("a") as f:
        f.write(str(int(time.time())) + "|" + msg)
        f.close()


def lookup_remote_ip() -> str:
    """Lookup and return the current public IP address."""
    import requests

    req = requests.get("https://weaver.fanfic.dev/v0/remote", timeout=5)
    if req.status_code != HTTPStatus.OK:
        msg = "failed to determine remote address"
        raise LookupRemoteIPError(msg)
    return req.text.strip()


def get_fuzz(base: float = 1.0, spread: float = 0.2) -> float:
    """Return a fuzzy random number in the range [`base`, `base` + `spread`)."""
    return base + spread * random.random()  # noqa: S311


def compress(data: bytes) -> bytes:
    """Return a compressed copy of data."""
    return len(data).to_bytes(4, byteorder="big") + zlib.compress(data, level=9)


def uncompress(data: bytes) -> bytes:
    """
    Return an uncompressed copy of `data`.

    `data` must be the result of an earlier `compress` call though not necessarily
    from within the same process.
    """
    elen = int.from_bytes(data[:4], byteorder="big")
    res = zlib.decompress(data[4:])
    if len(res) != elen:
        msg = f"expected {elen} but got {len(res)} bytes"
        raise MismatchedUncompressSizeError(msg)
    return res


def get_unique_job_name(extra: str = "job", bits: int = 32) -> str:
    """Return a machine-local unique job id."""
    rbits = random.getrandbits(bits)
    return f"{os.getpid()}_{threading.get_ident()}_{rbits:x}_{extra}"
