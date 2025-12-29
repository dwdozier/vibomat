import os
import json
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from backend.core.cli import app

runner = CliRunner()


def test_cli_build_success():
    """Test the build command."""
    with patch("backend.core.cli.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_get_builder.return_value = mock_builder
        # Create a dummy file for the argument
        with runner.isolated_filesystem():
            with open("playlist.json", "w") as f:
                f.write("{}")
            result = runner.invoke(app, ["build", "playlist.json", "--source", "env"])
            assert result.exit_code == 0
            mock_builder.build_playlist_from_json.assert_called_once()


def test_cli_build_error():
    """Test the build command handling errors."""
    with patch("backend.core.cli.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_builder.build_playlist_from_json.side_effect = Exception("Build failed")
        mock_get_builder.return_value = mock_builder
        with runner.isolated_filesystem():
            with open("playlist.json", "w") as f:
                f.write("{}")
            result = runner.invoke(app, ["build", "playlist.json"])
            assert result.exit_code == 1
            mock_builder.build_playlist_from_json.assert_called_once()


def test_cli_export_success():
    """Test the export command."""
    with patch("backend.core.cli.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_get_builder.return_value = mock_builder
        result = runner.invoke(app, ["export", "My Playlist", "out.json"])
        assert result.exit_code == 0
        mock_builder.export_playlist_to_json.assert_called_with("My Playlist", "out.json")


def test_cli_export_error():
    """Test export command error handling."""
    with patch("backend.core.cli.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_builder.export_playlist_to_json.side_effect = Exception("Export failed")
        mock_get_builder.return_value = mock_builder
        result = runner.invoke(app, ["export", "Playlist", "out.json"])
        assert result.exit_code == 1


def test_cli_backup_success():
    """Test the backup command."""
    with patch("backend.core.cli.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_get_builder.return_value = mock_builder
        result = runner.invoke(app, ["backup", "backups_dir"])
        assert result.exit_code == 0
        mock_builder.backup_all_playlists.assert_called_with("backups_dir")


def test_cli_backup_error():
    """Test backup command error handling."""
    with patch("backend.core.cli.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_builder.backup_all_playlists.side_effect = Exception("Backup failed")
        mock_get_builder.return_value = mock_builder
        result = runner.invoke(app, ["backup", "backups"])
        assert result.exit_code == 1


def test_cli_store_credentials():
    """Test storing credentials interactively."""
    with patch("backend.core.cli.store_credentials_in_keyring") as mock_store:
        # Simulate user input: client_id, then client_secret
        result = runner.invoke(app, ["store-credentials"], input="my_id\nmy_secret\n")
        assert result.exit_code == 0
        mock_store.assert_called_with("my_id", "my_secret")


def test_cli_store_credentials_missing_input():
    """Test error when input is missing."""
    result = runner.invoke(app, ["store-credentials"], input="\n\n")  # Empty inputs
    assert result.exit_code == 1


def test_cli_store_credentials_exception():
    """Test exception handling in store-credentials command."""
    with patch(
        "backend.core.cli.store_credentials_in_keyring",
        side_effect=Exception("Keyring error"),
    ):
        result = runner.invoke(app, ["store-credentials"], input="user\npass\n")
        assert result.exit_code == 1


def test_cli_main_verbose():
    """Test global options like verbose."""
    # Just checking it doesn't crash and sets level
    with patch("logging.basicConfig"):
        result = runner.invoke(app, ["--verbose", "build", "--help"])
        assert result.exit_code == 0


def test_cli_install_completion_success():
    """Test successful installation of zsh completion."""
    with (
        patch("pathlib.Path.home") as mock_home,
        patch("subprocess.run") as mock_run,
        patch("builtins.open", new_callable=MagicMock) as mock_open,
    ):
        # Setup mocks
        mock_omz = MagicMock()
        mock_omz.exists.return_value = True
        # Path configuration: home / .oh-my-zsh
        mock_home.return_value.__truediv__.return_value = mock_omz
        # Mock completions dir: omz / completions
        mock_completions = MagicMock()
        mock_omz.__truediv__.return_value = mock_completions
        # Mock target file: completions / _script
        mock_target = MagicMock()
        mock_completions.__truediv__.return_value = mock_target

        # Mock subprocess result
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "completion script content"

        result = runner.invoke(app, ["install-zsh-completion"])

        assert result.exit_code == 0
        # Check if subprocess was called to generate script
        mock_run.assert_called_once()
        # Check if file was written
        mock_open.assert_called_with(mock_target, "w")
        mock_open.return_value.__enter__.return_value.write.assert_called_with(
            "completion script content"
        )


def test_cli_install_completion_no_omz():
    """Test installation fails if Oh My Zsh is not found."""
    with patch("pathlib.Path.home") as mock_home:
        mock_omz = MagicMock()
        mock_omz.exists.return_value = False
        mock_home.return_value.__truediv__.return_value = mock_omz
        result = runner.invoke(app, ["install-zsh-completion"])
        assert result.exit_code == 1


def test_cli_install_completion_subprocess_error():
    """Test installation fails if completion generation fails."""
    with patch("pathlib.Path.home") as mock_home, patch("subprocess.run") as mock_run:
        mock_omz = MagicMock()
        mock_omz.exists.return_value = True
        mock_home.return_value.__truediv__.return_value = mock_omz
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error generating"
        result = runner.invoke(app, ["install-zsh-completion"])
        assert result.exit_code == 1


def test_cli_install_completion_empty_script():
    """Test error when generated completion script is empty."""
    with (
        patch("pathlib.Path.home") as mock_home,
        patch("subprocess.run") as mock_run,
    ):
        mock_omz = MagicMock()
        mock_omz.exists.return_value = True
        mock_home.return_value.__truediv__.return_value = mock_omz
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""  # Empty output
        result = runner.invoke(app, ["install-zsh-completion"])
        assert result.exit_code == 1


def test_cli_uninstall_completion():
    """Test uninstall instruction command."""
    result = runner.invoke(app, ["uninstall-completion"])
    assert result.exit_code == 0


def test_cli_setup_ai_success():
    """Test setup-ai command success."""
    # Since keyring is imported inside the function, we patch sys.modules to inject a mock
    mock_keyring = MagicMock()
    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        result = runner.invoke(app, ["setup-ai"], input="my_api_key\n")
        assert result.exit_code == 0
        mock_keyring.set_password.assert_called_with(
            "spotify-playlist-builder", "gemini_api_key", "my_api_key"
        )


def test_cli_setup_discogs_success():
    """Test setup-discogs command success."""
    mock_keyring = MagicMock()
    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        result = runner.invoke(app, ["setup-discogs"], input="my_token\n")
        assert result.exit_code == 0
        mock_keyring.set_password.assert_called_with(
            "spotify-playlist-builder", "discogs_pat", "my_token"
        )


def test_cli_generate_success():
    """Test generate command."""
    mock_tracks = [{"artist": "Artist", "track": "Track", "version": "studio"}]
    with (
        patch("backend.core.ai.generate_playlist", return_value=mock_tracks),
        patch("backend.core.ai.verify_ai_tracks", return_value=(mock_tracks, [])),
    ):
        result = runner.invoke(app, ["generate", "--prompt", "test mood"], input="\n")
        assert result.exit_code == 0
        # Check print output
        assert "Artist - Track" in result.stdout


def test_cli_generate_with_output():
    """Test generate command with --output flag."""
    mock_tracks = [{"artist": "A", "track": "B"}]
    with (
        patch("backend.core.ai.generate_playlist", return_value=mock_tracks),
        patch("backend.core.ai.verify_ai_tracks", return_value=(mock_tracks, [])),
        runner.isolated_filesystem(),
    ):
        result = runner.invoke(app, ["generate", "-p", "test", "-o", "out.json"])
        assert result.exit_code == 0
        assert os.path.exists("out.json")
        with open("out.json") as f:
            data = json.load(f)
            assert data["tracks"][0]["artist"] == "A"


def test_cli_generate_interactive_save():
    """Test interactive saving flow in generate command."""
    mock_tracks = [{"artist": "A", "track": "B"}]
    with (
        patch("backend.core.ai.generate_playlist", return_value=mock_tracks),
        patch("backend.core.ai.verify_ai_tracks", return_value=(mock_tracks, [])),
        runner.isolated_filesystem(),
    ):
        # input: Artist (empty) -> Confirm Save (y) -> Filename (default)
        result = runner.invoke(app, ["generate", "-p", "test mood"], input="\ny\n\n")
        assert result.exit_code == 0
        # Default filename for "test mood" should be test_mood.json
        assert os.path.exists("playlists/test_mood.json")


def test_cli_generate_interactive():
    """Test generate command with interactive input."""
    mock_tracks = [{"artist": "A", "track": "B"}]
    with (
        patch("backend.core.ai.generate_playlist", return_value=mock_tracks),
        patch("backend.core.ai.verify_ai_tracks", return_value=(mock_tracks, [])),
    ):
        # Mood -> Artist -> Save (y) -> Filename
        result = runner.invoke(app, ["generate"], input="my mood\nMy Artist\ny\nmy_list.json\n")
        assert result.exit_code == 0
        assert "A - B" in result.stdout


def test_cli_generate_failure():
    """Test generate command failure."""
    with patch("backend.core.ai.generate_playlist", side_effect=Exception("AI Error")):
        # Mood -> Artist (empty)
        result = runner.invoke(app, ["generate", "--prompt", "fail"], input="\n")
        assert result.exit_code == 0  # Typer doesn't crash, just logs error
        # Verify error log could be captured if we checked stderr/logging, but exit code 0 is what
        # we handle


def test_cli_ai_models_success():
    """Test ai-models command."""
    with patch("backend.core.ai.list_available_models", return_value=["model1"]):
        result = runner.invoke(app, ["ai-models"])
        assert result.exit_code == 0
        assert "model1" in result.stdout


def test_cli_generate_chain_build():
    """Test generate command chained with build."""
    mock_tracks = [{"artist": "A", "track": "B"}]
    with (
        patch("backend.core.ai.generate_playlist", return_value=mock_tracks),
        patch("backend.core.ai.verify_ai_tracks", return_value=(mock_tracks, [])),
        patch("backend.core.cli.build") as mock_build,
        runner.isolated_filesystem(),
    ):
        result = runner.invoke(app, ["generate", "-p", "test", "-o", "out.json", "--build"])
        assert result.exit_code == 0
        mock_build.assert_called_once()


def test_cli_generate_no_verified_tracks():
    """Test generate command when no tracks are verified."""
    with (
        patch(
            "backend.core.ai.generate_playlist",
            return_value=[{"artist": "A", "track": "T"}],
        ),
        patch("backend.core.ai.verify_ai_tracks", return_value=([], ["Rejected"])),
    ):
        # Provide empty input for the artists prompt
        result = runner.invoke(app, ["generate", "--prompt", "test"], input="\n")
        assert result.exit_code == 0
        assert "No tracks were verified" in result.output


def test_cli_generate_with_rejections():
    """Test generate command showing rejections."""
    mock_tracks = [{"artist": "A", "track": "T"}]
    with (
        patch("backend.core.ai.generate_playlist", return_value=mock_tracks),
        patch(
            "backend.core.ai.verify_ai_tracks",
            return_value=(mock_tracks, ["Rejected - Song"]),
        ),
        runner.isolated_filesystem(),
    ):
        result = runner.invoke(app, ["generate", "--prompt", "test", "--output", "out.json"])
        assert result.exit_code == 0
        assert "1 tracks could not be verified" in result.output


def test_cli_ai_models_error():
    """Test ai-models command failure."""
    with patch(
        "backend.core.ai.list_available_models",
        side_effect=Exception("API Error"),
    ):
        result = runner.invoke(app, ["ai-models"])
        assert result.exit_code == 0
        assert "Error fetching models" in result.output


def test_cli_setup_ai_error():
    """Test setup-ai command failure."""
    mock_keyring = MagicMock()
    mock_keyring.set_password.side_effect = Exception("Keyring error")
    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        result = runner.invoke(app, ["setup-ai"], input="key\n")
        assert result.exit_code == 0
        assert "Error: Keyring error" in result.output


def test_cli_setup_discogs_error():
    """Test setup-discogs command failure."""
    mock_keyring = MagicMock()
    mock_keyring.set_password.side_effect = Exception("Keyring error")
    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        result = runner.invoke(app, ["setup-discogs"], input="token\n")
        assert result.exit_code == 0
        assert "Error: Keyring error" in result.output
