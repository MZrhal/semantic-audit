"""Black-box-like CLI tests through the public main entrypoint."""

import json

from semantic_audit.cli import main


def test_cli_prints_valid_json(example_path, capsys):
    status = main(["inspect", str(example_path)])
    result = capsys.readouterr()
    assert status == 0
    assert result.err == ""
    payload = json.loads(result.out)
    assert payload["statistics"]["named_individuals"] == 5


def test_legacy_cli_syntax_is_supported(example_path, capsys):
    assert main([str(example_path)]) == 0
    assert json.loads(capsys.readouterr().out)["schema_version"] == "1.0"


def test_cli_writes_output_to_file(example_path, tmp_path, capsys):
    output = tmp_path / "reports" / "audit.json"
    assert main(["inspect", str(example_path), "--output", str(output)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Rapport enregistré" in captured.err
    assert json.loads(output.read_text(encoding="utf-8"))["statistics"]["declared_classes"] == 5


def test_cli_reports_missing_input_without_traceback(tmp_path, capsys):
    status = main(["inspect", str(tmp_path / "missing.ttl")])
    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert "introuvable" in captured.err
    assert "Traceback" not in captured.err


def test_cli_reports_invalid_rdf_without_traceback(tmp_path, capsys):
    path = tmp_path / "broken.ttl"
    path.write_text("bad turtle content", encoding="utf-8")
    status = main(["inspect", str(path)])
    captured = capsys.readouterr()
    assert status == 1
    assert "Impossible de lire" in captured.err
    assert "Traceback" not in captured.err


def test_cli_file_with_unrecognized_extension_works_with_override(tmp_path, capsys):
    path = tmp_path / "model.unknown"
    path.write_text(
        "@prefix : <https://example.org/> . :A a <http://www.w3.org/2002/07/owl#Class> .",
        encoding="utf-8",
    )
    status = main(["inspect", str(path), "--rdf-format", "turtle"])
    assert status == 0
    assert json.loads(capsys.readouterr().out)["statistics"]["declared_classes"] == 1


def test_cli_prevents_overwriting_input(example_path, capsys):
    original = example_path.read_bytes()
    status = main(["inspect", str(example_path), "--output", str(example_path)])
    captured = capsys.readouterr()
    assert status == 1
    assert "écraser" in captured.err
    assert example_path.read_bytes() == original
