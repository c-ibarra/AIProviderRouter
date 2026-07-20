import pytest

from router.adapters.http.startup import StartupValidationError, validate_startup


def test_validate_startup_passes_when_all_commands_found():
    validate_startup(["claude", "agy"], which=lambda cmd: f"/usr/local/bin/{cmd}")


def test_validate_startup_raises_when_a_command_is_missing():
    which = lambda cmd: None if cmd == "agy" else "/usr/local/bin/claude"

    with pytest.raises(StartupValidationError) as exc_info:
        validate_startup(["claude", "agy"], which=which)

    assert "agy" in str(exc_info.value)


def test_validate_startup_lists_all_missing_commands():
    with pytest.raises(StartupValidationError) as exc_info:
        validate_startup(["claude", "agy"], which=lambda cmd: None)

    assert "claude" in str(exc_info.value)
    assert "agy" in str(exc_info.value)
