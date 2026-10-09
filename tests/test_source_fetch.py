import hashlib
from pathlib import Path

import pytest

from kb_build.source_fetch import SourceHashMismatchError, SourceSpec, fetch_to_cache, read_cached


def test_fetch_to_cache_rejects_wrong_sha256(tmp_path: Path) -> None:
    data = b"hello"
    spec = SourceSpec(
        key="x",
        url="https://example.invalid/x",
        version="v1",
        sha256="0" * 64,
        license="TEST",
        filename="x.bin",
    )

    def fake_fetch(_: str) -> bytes:
        return data

    with pytest.raises(SourceHashMismatchError):
        fetch_to_cache(spec, cache_dir=tmp_path, fetcher=fake_fetch)


def test_fetch_to_cache_rejects_tampered_cache_file(tmp_path: Path) -> None:
    spec = SourceSpec(
        key="x",
        url="https://example.invalid/x",
        version="v1",
        sha256=hashlib.sha256(b"hello").hexdigest(),
        license="TEST",
        filename="x.bin",
    )
    (tmp_path / "x.bin").write_bytes(b"tampered")

    with pytest.raises(SourceHashMismatchError):
        fetch_to_cache(spec, cache_dir=tmp_path, fetcher=lambda _: b"hello")


def test_fetch_to_cache_accepts_matching_sha256_and_caches(tmp_path: Path) -> None:
    data = b"hello"
    spec = SourceSpec(
        key="x",
        url="https://example.invalid/x",
        version="v1",
        sha256=hashlib.sha256(data).hexdigest(),
        license="TEST",
        filename="x.bin",
    )

    calls: list[str] = []

    def fake_fetch(url: str) -> bytes:
        calls.append(url)
        return data

    path1 = fetch_to_cache(spec, cache_dir=tmp_path, fetcher=fake_fetch)
    assert path1.read_bytes() == data
    assert calls == [spec.url]

    # second call must use cache, not refetch
    path2 = fetch_to_cache(spec, cache_dir=tmp_path, fetcher=fake_fetch)
    assert path2 == path1
    assert calls == [spec.url]


def test_read_cached_parses_json_and_keeps_other_formats_as_bytes(tmp_path: Path) -> None:
    (tmp_path / "cis.json").write_text('{"Requirements": []}', encoding="utf-8")
    (tmp_path / "sdm.pdf").write_bytes(b"%PDF-1.4")
    assert read_cached(tmp_path / "cis.json") == {"Requirements": []}
    assert read_cached(tmp_path / "sdm.pdf") == b"%PDF-1.4"
