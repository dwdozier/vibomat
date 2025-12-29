import runpy
from unittest.mock import patch


def test_core_main_execution():
    """Test the execution of backend.core.main entry point."""
    with patch("backend.core.cli.app") as mock_app:
        # We use runpy to execute the module as if it were the main script
        # This covers the if __name__ == "__main__": block
        with patch("backend.core.main.__name__", "__main__"):
            runpy.run_module("backend.core.main", run_name="__main__")
            mock_app.assert_called_once()
