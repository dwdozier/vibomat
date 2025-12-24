import logging
import sys
import subprocess
from pathlib import Path
from typing import Annotated
import typer
from .auth import CredentialSource, get_builder, store_credentials_in_keyring

logger = logging.getLogger("spotify_playlist_builder")
app = typer.Typer(help="Spotify Playlist Builder CLI")


@app.callback()
def main(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
) -> None:
    """Spotify Playlist Builder CLI to create and manage playlists from JSON files."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s" if not verbose else "% (levelname)s: %(message)s",
        force=True,
    )


@app.command()
def build(
    json_file: Annotated[Path, typer.Argument(exists=True, help="Path to playlist JSON file")],
    source: Annotated[CredentialSource | None, typer.Option(help="Credential source")] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Verify tracks without creating playlist")
    ] = False,
) -> None:
    """Build or update a Spotify playlist from a JSON file."""
    try:
        builder = get_builder(source)
        builder.build_playlist_from_json(str(json_file), dry_run=dry_run)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def export(
    playlist_name: Annotated[str, typer.Argument(help="Name of the Spotify playlist to export")],
    output_file: Annotated[Path, typer.Argument(help="Path to save the JSON file")],
    source: Annotated[CredentialSource | None, typer.Option(help="Credential source")] = None,
) -> None:
    """Export an existing Spotify playlist to a JSON file."""
    try:
        builder = get_builder(source)
        builder.export_playlist_to_json(playlist_name, str(output_file))
    except Exception as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def backup(
    output_dir: Annotated[Path, typer.Argument(help="Directory to save backup files")] = Path(
        "backups"
    ),
    source: Annotated[CredentialSource | None, typer.Option(help="Credential source")] = None,
) -> None:
    """Backup all user playlists to JSON files."""
    try:
        builder = get_builder(source)
        builder.backup_all_playlists(str(output_dir))
    except Exception as e:
        logger.error(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command("store-credentials")
def store_credentials_cmd() -> None:
    """Store Spotify credentials in macOS Keychain."""
    logger.info("Store Spotify credentials in macOS Keychain")
    client_id = typer.prompt("Enter Spotify Client ID")
    client_secret = typer.prompt("Enter Spotify Client Secret", hide_input=True)
    if client_id and client_secret:
        try:
            store_credentials_in_keyring(client_id, client_secret)
            logger.info("\nCredentials stored! You can now use: --source keyring")
        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            raise typer.Exit(code=1)
    else:
        logger.error("Error: Both Client ID and Client Secret are required")
        raise typer.Exit(code=1)


@app.command("install-zsh-completion")
def install_zsh_completion() -> None:
    """Install Zsh completion for Oh My Zsh users."""
    omz_dir = Path.home() / ".oh-my-zsh"
    if not omz_dir.exists():
        logger.error(f"Error: Oh My Zsh directory not found at {omz_dir}")
        raise typer.Exit(code=1)
    completions_dir = omz_dir / "completions"
    completions_dir.mkdir(parents=True, exist_ok=True)
    target_file = completions_dir / "_spotify-playlist-builder"
    logger.info("Generating Zsh completion script...")
    result = subprocess.run(
        [sys.executable, "-m", "spotify_playlist_builder.cli", "--show-completion", "zsh"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Error generating completion script: {result.stderr}")
        raise typer.Exit(code=1)

    completion_script = result.stdout
    if not completion_script.strip():
        logger.error("Error: Generated completion script is empty.")
        raise typer.Exit(code=1)

    with open(target_file, "w") as f:
        f.write(completion_script)
    logger.info(f"✓ Completion script installed to: {target_file}")


@app.command("uninstall-completion")
def uninstall_completion_cmd() -> None:
    """Show instructions to uninstall shell completion."""
    logger.info("To uninstall shell completion, identify which method you used...")


@app.command("setup-ai")
def setup_ai_cmd() -> None:
    """Store Gemini API Key in system keyring."""
    logger.info("Setup Gemini API Key")
    key = typer.prompt("Enter your Google Gemini API Key", hide_input=True)
    if key:
        try:
            import keyring

            keyring.set_password("spotify-playlist-builder", "gemini_api_key", key)
            logger.info("✓ API Key stored in keyring.")
        except ImportError:
            logger.error("Keyring not available. Please set GEMINI_API_KEY env var.")
        except Exception as e:
            logger.error(f"Error: {e}")


@app.command("generate")
def generate_cmd(
    prompt: Annotated[
        str | None, typer.Option("--prompt", "-p", help="Description of playlist")
    ] = None,
    count: Annotated[int, typer.Option("--count", "-c", help="Number of songs")] = 20,
) -> None:
    """Generate a playlist using AI."""
    from .ai import generate_playlist

    if not prompt:
        prompt = typer.prompt("Describe the playlist mood/theme")

    try:
        tracks = generate_playlist(prompt, count)
        import json

        print(json.dumps(tracks, indent=2))
    except Exception as e:
        logger.error(f"Generation failed: {e}")


if __name__ == "__main__":
    app()
