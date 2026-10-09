from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen


class SourceHashMismatchError(ValueError):
    pass


@dataclass(frozen=True)
class SourceSpec:
    """Entry from data/sources.json.

    `url` must be stable (ideally pinned to a commit SHA) and `sha256` is enforced.
    """

    key: str
    url: str
    version: str
    sha256: str
    license: str
    filename: str


def load_sources_json(path: str | Path) -> dict[str, SourceSpec]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    specs: dict[str, SourceSpec] = {}
    for key, item in raw.items():
        specs[key] = SourceSpec(
            key=key,
            url=item["url"],
            version=item["version"],
            sha256=item["sha256"],
            license=item["license"],
            filename=item["filename"],
        )
    return specs


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes_http(url: str) -> bytes:
    """The only place that performs HTTP in the build (Issue #4)."""

    req = Request(url, headers={"User-Agent": "GovGuard-kb-build"})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 (pinned URLs + hash gate)
        return resp.read()


def fetch_to_cache(
    spec: SourceSpec,
    *,
    cache_dir: str | Path = "data/sources",
    fetcher: Callable[[str], bytes] = fetch_bytes_http,
) -> Path:
    """Fetches a source, enforces its SHA-256 and stores it in the local cache.

    The cache is deterministic: a single `filename` per source key.
    """

    cache_path = Path(cache_dir) / spec.filename
    if cache_path.exists():
        _verify(spec, cache_path.read_bytes())
        return cache_path

    data = fetcher(spec.url)
    _verify(spec, data)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return cache_path


def _verify(spec: SourceSpec, data: bytes) -> None:
    actual = sha256_hex(data)
    if actual != spec.sha256:
        raise SourceHashMismatchError(
            f"sha256 mismatch for {spec.key}: expected {spec.sha256}, got {actual}"
        )
