"""write_snapshot(): schema files of the scope types in, cfn_properties.json out (#17)."""

import json
from pathlib import Path

import pytest

from kb_build.paths import BuildPaths
from kb_build.reference.run import snapshot_scope, write_snapshot


def schema_file(directory: Path, name: str, type_name: str, prop: str) -> None:
    schema = {"typeName": type_name, "properties": {prop: {"type": "string"}}}
    (directory / name).write_text(json.dumps(schema), encoding="utf-8")


def test_only_scope_types_are_written_in_sorted_order(tmp_path: Path) -> None:
    schema_file(tmp_path, "aws-s3-bucket.json", "AWS::S3::Bucket", "BucketName")
    schema_file(tmp_path, "aws-ec2-ami.json", "AWS::EC2::Image", "Name")
    out = tmp_path / "out.json"

    write_snapshot(tmp_path, frozenset({"AWS::S3::Bucket"}), out)

    assert json.loads(out.read_text(encoding="utf-8")) == {"AWS::S3::Bucket": ["BucketName"]}


def test_a_scope_type_without_schema_stops_the_snapshot(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="AWS::KMS::Key"):
        write_snapshot(tmp_path, frozenset({"AWS::KMS::Key"}), tmp_path / "out.json")


def test_the_build_command_takes_the_types_from_scope_json(tmp_path: Path) -> None:
    # python -m kb_build cfn-properties: scope.json in, cfn_properties.json out
    paths, schemas = BuildPaths(input=tmp_path / "input"), tmp_path / "schemas"
    paths.input.mkdir(), schemas.mkdir()
    paths.scope.write_text(json.dumps({"S3": ["AWS::S3::Bucket"]}), encoding="utf-8")
    schema_file(schemas, "aws-s3-bucket.json", "AWS::S3::Bucket", "BucketName")

    snapshot_scope(schemas, paths)

    written = json.loads(paths.cfn_properties.read_text(encoding="utf-8"))
    assert written == {"AWS::S3::Bucket": ["BucketName"]}
