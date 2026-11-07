"""Regression coverage for streamed terminal output safety and profile scope."""

import contextvars
import os


def test_streaming_redactor_preserves_secret_context_across_chunks():
    from agent.redact import redact_sensitive_text
    from tui_gateway.tool_progress import _StreamingRedactor

    secret = "split-secret-value-1234567890"
    text = "prefix api_key=" + secret + " suffix"
    split = text.index(secret) + 7
    redactor = _StreamingRedactor(lambda value: redact_sensitive_text(value, force=True))

    emitted = redactor.feed(text[:split]) + redactor.feed(text[split:]) + redactor.flush()

    assert secret not in emitted
    assert "api_key=" in emitted
    assert "suffix" in emitted


def test_terminal_drain_thread_inherits_profile_context():
    from tools.environments.base_output import _BoundedOutputCollector, _start_drain_thread

    profile = contextvars.ContextVar("test_terminal_profile")
    seen = []
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"output")
    os.close(write_fd)

    class Process:
        stdout = os.fdopen(read_fd, "rb")

        @staticmethod
        def poll():
            return 0

    collector = _BoundedOutputCollector(100, on_chunk=lambda _chunk: seen.append(profile.get(None)))
    token = profile.set("secondary-profile")
    try:
        thread = _start_drain_thread(Process(), collector)
    finally:
        profile.reset(token)
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert seen == ["secondary-profile"]
    assert collector.render() == "output"
