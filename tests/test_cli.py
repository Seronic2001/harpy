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
    rule_file = tmp_path / ".agents" / "rules" / "harpy.md"
    assert rule_file.is_file()
    assert "Harpy Fast Execution Rule" in rule_file.read_text(encoding="utf-8")


def test_cli_completion(capsys):
    sys.argv = ["harpy", "completion", "bash"]
    code = main()
    assert code == 0
    captured = capsys.readouterr()
    assert "_harpy_completions()" in captured.out
    assert "*.cpp" in captured.out


def test_cli_setup_ai(monkeypatch, tmp_path):
    import json
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    sys.argv = ["harpy", "setup-ai"]
    code = main()
    assert code == 0

    # Verify skill installed
    skill_file = tmp_path / ".gemini" / "config" / "skills" / "harpy-cp" / "SKILL.md"
    assert skill_file.is_file()

    # Verify rule installed
    rule_file = tmp_path / ".gemini" / "config" / "rules" / "harpy.md"
    assert rule_file.is_file()
    assert "Harpy Fast Execution Rule" in rule_file.read_text(encoding="utf-8")

    # Verify mcp_config.json created with mcpServers.harpy
    mcp_config_file = tmp_path / ".gemini" / "config" / "mcp_config.json"
    assert mcp_config_file.is_file()
    data = json.loads(mcp_config_file.read_text(encoding="utf-8"))
    assert "mcpServers" in data
    assert "harpy" in data["mcpServers"]
    assert "command" in data["mcpServers"]["harpy"]
    assert "args" in data["mcpServers"]["harpy"]
