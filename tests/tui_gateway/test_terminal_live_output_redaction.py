"""Regression coverage for streamed terminal output safety and profile scope."""

from types import SimpleNamespace

from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from tools.environments.base_output import _BoundedOutputCollector, _start_drain_thread
from tui_gateway.tool_progress import _StreamingRedactor


def test_streaming_redactor_holds_chunk_boundary_until_secret_is_complete(monkeypatch):
    emitted = []
    redactor = _StreamingRedactor(emitted.append)
    secret = "sk-" + "abcdefghijklmnopqrstuvwxyz0123456789"

    # Force one callback to cross the same 4096-byte boundary used by the
    # stdout drain, then finish the credential in a later callback.
    redactor("x" * 8190 + " sk-")
    assert secret not in "".join(emitted)
    redactor(secret[3:])
    redactor.flush()

    joined = "".join(emitted)
    assert secret not in joined
    assert joined != "x" * 8190 + " " + secret


def test_drain_thread_inherits_profile_scope_for_live_redaction(tmp_path):
    secondary_home = tmp_path / "secondary-hermes"
    token = "opaque-secondary-profile-password"
    override_token = set_hermes_home_override(secondary_home)
    try:
        from agent.redact import redact_sensitive_text, register_vault_redaction_value

        register_vault_redaction_value(token)
        captured = []
        collector = _BoundedOutputCollector(
            10_000,
            on_chunk=lambda chunk: captured.append(redact_sensitive_text(chunk, force=True)),
        )
        proc = SimpleNamespace(stdout=[token], returncode=0)
        thread = _start_drain_thread(proc, collector)
        thread.join(timeout=2)

        assert not thread.is_alive()
        assert token not in "".join(captured)
        assert "redacted-vault-secret" in "".join(captured)
    finally:
        reset_hermes_home_override(override_token)
