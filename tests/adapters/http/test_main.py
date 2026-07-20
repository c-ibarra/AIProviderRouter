from unittest.mock import patch

from router.adapters.http.main import main


def test_main_binds_uvicorn_to_localhost_only():
    with (
        patch("router.adapters.http.main.validate_startup") as mock_validate,
        patch("router.adapters.http.main.uvicorn.run") as mock_run,
    ):
        main()

    mock_validate.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["host"] != "0.0.0.0"
