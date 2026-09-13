import sys
import tempfile
from pathlib import Path
import pytest
from harpy.cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ["harpy", "--help"]
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "init" in captured.out
    assert "test" in captured.out
    assert "setup-ai" in captured.out


def test_cli_init_command(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    sys.argv = ["harpy", "init"]
    code = main()
    assert code == 0
    assert (tmp_path / "problems").is_dir()
    assert (tmp_path / ".tabignore").is_file()
    assert "*.cpp" in (tmp_path / ".tabignore").read_text(encoding="utf-8")


def test_cli_completion(capsys):
    sys.argv = ["harpy", "completion", "bash"]
    code = main()
    assert code == 0
    captured = capsys.readouterr()
    assert "_harpy_completions()" in captured.out
    assert "*.cpp" in captured.out
