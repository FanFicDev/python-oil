"""Grab bag of various utility functions."""

import datetime
import os
import random
import re
import threading
import time
import warnings
import zlib

import dateutil.parser

defaultLogFile = "oil.log"
defaultLogDir = "./"


def urlTitle(title: str) -> str:
    """Turn `title` into a url safe slug string."""
    res = ""
    for char in title:
        if char.isalnum():
            res += char
        elif len(res) != 0 and res[-1] != "-":
            res += "-"
    return res.rstrip("-")


_writtenMonths = [
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
_writtenMonths += [
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


def isWrittenDate(val: str) -> bool:
    """Return True iff `val` contains an English month name."""
    return any(val.find(wm) >= 0 for wm in _writtenMonths)


def parseDateAsUnix(updated: str | int, fetched: int) -> int:
    """Parse a human readable date as a unix timestamp.

    Several formats are supported including relative dates. If `updated`
    represents a relative date, it is assumed to be relative to `fetched`.
    """
    currentYear = datetime.datetime.utcfromtimestamp(fetched).year

    if isinstance(updated, int):
        if updated < 0:
            raise Exception(f"error parsing date: negative int: {updated}")
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

    slashedParts = updated.split("/")
    if len(slashedParts) == 2:
        fdate = f"{currentYear}/{slashedParts[0]}/{slashedParts[1]}"
        dt = dateutil.parser.parse(fdate)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())
    if len(slashedParts) == 3:
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    dashedParts = updated.split("-")
    if len(dashedParts) == 3:
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    dottedParts = updated.split(".")
    if (
        len(dottedParts) == 3
        and dottedParts[0].isnumeric()
        and dottedParts[1].isnumeric()
        and dottedParts[2].isnumeric()
    ):
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    if isWrittenDate(updated):
        dt = dateutil.parser.parse(updated)
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    raise Exception(f"error parsing date: unknown format: {updated}")


def logMessage(msg: str, fname: str | None = None, logDir: str | None = None) -> None:
    """Write a given `msg` to the log file `fname` within `logDir`."""
    warnings.warn("Use logging instead", DeprecationWarning, stacklevel=1)
    if fname is None:
        fname = defaultLogFile
    if logDir is None:
        logDir = defaultLogDir
    if not msg.endswith("\n"):
        msg += "\n"
    with open(os.path.join(logDir, fname), "a") as f:
        f.write(str(int(time.time())) + "|" + msg)
        f.close()


def lookupRemoteIP() -> str:
    """Lookup and return the current public IP address."""
    import requests

    req = requests.get("https://weaver.fanfic.dev/v0/remote", timeout=5)
    if req.status_code != 200:
        raise Exception("failed to determine remote address")
    return req.text.strip()


def getFuzz(base: float = 1.0, spread: float = 0.2) -> float:
    """Return a fuzzy random number in the range [`base`, `base` + `spread`)."""
    return base + spread * random.random()


def compress(data: bytes) -> bytes:
    """Return a compressed copy of data."""
    return len(data).to_bytes(4, byteorder="big") + zlib.compress(data, level=9)


def uncompress(data: bytes) -> bytes:
    """Return an uncompressed copy of `data`.

    `data` must be the result of an earlier `compress` call though not necessarily
    from within the same process.
    """
    elen = int.from_bytes(data[:4], byteorder="big")
    res = zlib.decompress(data[4:])
    if len(res) != elen:
        raise Exception(f"expected {elen} but got {len(res)} bytes")
    return res


def getUniqueJobName(extra: str = "job", bits: int = 32) -> str:
    """Return a machine-local unique job id."""
    rbits = random.getrandbits(bits)
    return f"{os.getpid()}_{threading.get_ident()}_{rbits:x}_{extra}"
