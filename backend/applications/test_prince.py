"""Unit tests for the Prince command wrapper used by PDF generation."""

import subprocess

import pytest

from applications.prince import Prince


pytestmark = [pytest.mark.unit]


class _FakeProcess:
    """Test double for subprocess.Popen with controllable communicate behaviour."""

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        """Store process outcome and capture interaction details for assertions."""
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self.input_seen = None
        self.timeout_seen = None
        self.killed = False
        self.communicate_calls = 0

    def communicate(self, input=None, timeout=None):
        """Simulate process communicate and record call arguments."""
        self.communicate_calls += 1
        self.input_seen = input
        self.timeout_seen = timeout
        return self._stdout, self._stderr

    def kill(self):
        """Track whether timeout cleanup kills the child process."""
        self.killed = True


def test_prepare_options_normalises_prefix_and_case():
    """Normalise option keys to lowercase long-form switches with -- prefix."""
    prince = Prince(
        prince_bin="prince",
        options={"Output": "file.pdf", "--BASEURL": "http://example.test"},
    )

    assert prince.options["--output"] == "file.pdf"
    assert prince.options["--baseurl"] == "http://example.test"


def test_command_args_include_stdin_flag_files_and_mixed_options():
    """Build command args with stdin marker, files, list options, and valueless flags."""
    prince = Prince(prince_bin="prince")

    args = prince._command_args(
        files=["input.html"],
        input_data="<html />",
        options={
            "--output": "-",
            "--style": ["one.css", "two.css"],
            "--javascript": "",
        },
    )

    assert args == [
        "prince",
        "-",
        "input.html",
        "--output",
        "-",
        "--style",
        "one.css",
        "--style",
        "two.css",
        "--javascript",
    ]


def test_from_string_returns_stdout_bytes_and_encodes_text_input(monkeypatch):
    """Return PDF bytes from stdout mode and encode text input as UTF-8 bytes."""
    fake_process = _FakeProcess(returncode=0, stdout=b"%PDF-1.7", stderr=b"")

    def _fake_popen(*_args, **_kwargs):
        """Return the configured fake process for this test case."""
        return fake_process

    monkeypatch.setattr("applications.prince.subprocess.Popen", _fake_popen)

    prince = Prince(prince_bin="prince")
    result = prince.from_string("<html>hello</html>", timeout=12)

    assert result == b"%PDF-1.7"
    assert fake_process.input_seen == b"<html>hello</html>"
    assert fake_process.timeout_seen == 12


def test_from_file_returns_true_when_output_written_to_file(monkeypatch):
    """Return True when Prince writes to an explicit output file instead of stdout."""
    fake_process = _FakeProcess(returncode=0, stdout=b"", stderr=b"")

    def _fake_popen(*_args, **_kwargs):
        """Return the configured fake process for this test case."""
        return fake_process

    monkeypatch.setattr("applications.prince.subprocess.Popen", _fake_popen)

    prince = Prince(prince_bin="prince", options={"output": "out.pdf"})
    result = prince.from_file("input.html")

    assert result is True


def test_from_file_accepts_existing_file_list_without_rewrapping(monkeypatch):
    """Pass an existing file list through unchanged so Prince receives each input file once."""
    fake_process = _FakeProcess(returncode=0, stdout=b"%PDF", stderr=b"")
    popen_args = {}

    def _fake_popen(args, **_kwargs):
        """Capture command args so list-handling behaviour can be asserted."""
        popen_args["args"] = args
        return fake_process

    monkeypatch.setattr("applications.prince.subprocess.Popen", _fake_popen)

    prince = Prince(prince_bin="prince")
    result = prince.from_file(["one.html", "two.html"])

    assert result == b"%PDF"
    assert popen_args["args"][:3] == ["prince", "one.html", "two.html"]


def test_to_pdf_raises_exception_with_stderr_when_process_fails(monkeypatch):
    """Raise an exception that carries stderr when Prince exits non-zero."""
    fake_process = _FakeProcess(returncode=1, stdout=b"", stderr=b"render failed")

    def _fake_popen(*_args, **_kwargs):
        """Return the configured fake process for this test case."""
        return fake_process

    monkeypatch.setattr("applications.prince.subprocess.Popen", _fake_popen)

    prince = Prince(prince_bin="prince")

    with pytest.raises(Exception, match="render failed"):
        prince.from_string("<html />")


def test_to_pdf_kills_process_and_reraises_timeout(monkeypatch):
    """Kill the child process and re-raise TimeoutExpired when rendering times out."""
    fake_process = _FakeProcess(returncode=0, stdout=b"", stderr=b"")

    def _timeout_communicate(input=None, timeout=None):
        """Raise timeout on first communicate call and return cleanup result after kill."""
        fake_process.communicate_calls += 1
        fake_process.input_seen = input
        fake_process.timeout_seen = timeout
        if fake_process.communicate_calls == 1:
            raise subprocess.TimeoutExpired(cmd="prince", timeout=timeout)
        return b"", b""

    fake_process.communicate = _timeout_communicate

    def _fake_popen(*_args, **_kwargs):
        """Return the configured fake process for this test case."""
        return fake_process

    monkeypatch.setattr("applications.prince.subprocess.Popen", _fake_popen)

    prince = Prince(prince_bin="prince")

    with pytest.raises(subprocess.TimeoutExpired):
        prince.from_string("<html />", timeout=1)

    assert fake_process.killed is True
    assert fake_process.communicate_calls == 2
