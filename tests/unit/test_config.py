from gallop.core.config import GallopConfig, load_env


def test_config_does_not_execute_and_environment_wins(tmp_path, monkeypatch):
    for key in ("GALLOP_VAULT_PATH", "GALLOP_LOG_PATH"):
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / "config.env"
    path.write_text("GALLOP_VAULT_PATH=trial-vault\nGALLOP_LOG_PATH=literal-$(not-a-command)\n")
    monkeypatch.setenv("GALLOP_VAULT_PATH", "environment-vault")
    load_env(path)
    config = GallopConfig.from_environment()
    assert str(config.vault_path) == "environment-vault"
    assert str(config.log_path) == "literal-$(not-a-command)"
