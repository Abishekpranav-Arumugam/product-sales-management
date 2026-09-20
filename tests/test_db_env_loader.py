import app.dal.database_manager as database_manager_module


def test_resolve_database_env_file_uses_single_dotenv(monkeypatch, tmp_path):
    monkeypatch.setattr(database_manager_module, "BASE_DIR", tmp_path)

    (tmp_path / ".env").write_text("DB_HOST=localhost\n")

    assert database_manager_module.resolve_env_file() == tmp_path / ".env"
