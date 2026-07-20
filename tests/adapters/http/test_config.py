import textwrap

from router.adapters.http.config import load_config

SAMPLE_YAML = textwrap.dedent(
    """
    default_provider: antigravity

    providers:
      claude:
        auth_source: local_oauth
        scope: personal_only
        model: claude-sonnet-5
        effort: medium

      antigravity:
        auth_source: local_oauth
        scope: personal_only
        model: gemini-3-pro
        retry:
          max_attempts: 3
          on_empty_output: true
    """
)


def write_config(tmp_path, content=SAMPLE_YAML):
    path = tmp_path / "provider.yaml"
    path.write_text(content)
    return path


def test_load_config_reads_default_provider(tmp_path):
    config = load_config(write_config(tmp_path))

    assert config.default_provider == "antigravity"


def test_load_config_reads_provider_settings(tmp_path):
    config = load_config(write_config(tmp_path))

    claude = config.providers["claude"]
    assert claude.model == "claude-sonnet-5"
    assert claude.effort == "medium"

    antigravity = config.providers["antigravity"]
    assert antigravity.model == "gemini-3-pro"
    assert antigravity.retry_max_attempts == 3
    assert antigravity.retry_on_empty_output is True


def test_load_config_applies_retry_defaults_when_absent(tmp_path):
    config = load_config(write_config(tmp_path))

    claude = config.providers["claude"]
    assert claude.retry_max_attempts == 2
    assert claude.retry_on_empty_output is True


def test_load_config_reads_fresh_from_disk_on_each_call(tmp_path):
    path = write_config(tmp_path)

    first = load_config(path)
    assert first.default_provider == "antigravity"

    path.write_text(SAMPLE_YAML.replace("default_provider: antigravity", "default_provider: claude"))
    second = load_config(path)

    assert second.default_provider == "claude"
