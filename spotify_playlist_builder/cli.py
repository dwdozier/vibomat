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
        format="%(message)s" if not verbose else "%(levelname)s: %(message)s",
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


@app.command("ai-models")
def ai_models_cmd() -> None:
    """List available Gemini models for your API key."""
    from .ai import list_available_models

    try:
        models = list_available_models()
        logger.info("Available Gemini Models:")
        for model in models:
            print(f"- {model}")
    except Exception as e:
        logger.error(f"Error fetching models: {e}")


@app.command("generate")
def generate_cmd(
    prompt: Annotated[
        str | None, typer.Option("--prompt", "-p", help="Description of playlist")
    ] = None,
    artists: Annotated[
        str | None, typer.Option("--artists", "-a", help="Preferred artists")
    ] = None,
    count: Annotated[int, typer.Option("--count", "-c", help="Number of songs")] = 20,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Path to save the JSON file")
    ] = None,
    build_playlist: Annotated[
        bool, typer.Option("--build", "-b", help="Immediately build playlist on Spotify")
    ] = False,
) -> None:
    """Generate a playlist using AI and verify tracks."""
    from .ai import generate_playlist, verify_ai_tracks
    import json
    from .utils.helpers import to_snake_case

    if not prompt:
        prompt = typer.prompt("Describe the playlist mood/theme")

    if not artists and not output:
        artists = typer.prompt("Preferred artists (optional)", default="", show_default=False)

    full_prompt = prompt
    if artists:
        full_prompt += f". Inspired by artists: {artists}"

    try:
        raw_tracks = generate_playlist(full_prompt, count)

        verified, rejected = verify_ai_tracks(raw_tracks)

        logger.info("\nVerification Results:")
        logger.info(f"✓ {len(verified)} tracks verified.")
        if rejected:
            logger.warning(f"✗ {len(rejected)} tracks could not be verified (rejected).")
            for r in rejected:
                logger.debug(f"  - {r}")

        if not verified:
            logger.error("No tracks were verified. Try a different prompt.")
            return

        # Prepare JSON data
        playlist_data = {
            "name": f"AI: {prompt[:30]}...",
            "description": f"AI generated playlist based on: {prompt}"
            + (f" (Artists: {artists})" if artists else ""),
            "tracks": verified,
        }

        final_path = None

        if output:
            # One-shot mode with output file
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as f:
                json.dump(playlist_data, f, indent=2)
            logger.info(f"\n✓ Playlist saved to {output}")
            final_path = output
        else:
            # Interactive review
            logger.info("\nProposed Playlist:")
            for i, t in enumerate(verified, 1):
                print(f"{i}. {t['artist']} - {t['track']} ({t.get('version', 'studio')})")

            if typer.confirm("\nSave this playlist?"):
                # Intelligent filename suggestion
                safe_prompt = to_snake_case(prompt)
                # Limit length to avoid filesystem errors (e.g. max 50 chars for slug)
                safe_prompt = safe_prompt[:50].rstrip("_")

                filename = typer.prompt("Enter filename", default=f"{safe_prompt}")

                # Handle extension
                if not filename.endswith(".json"):
                    filename += ".json"

                out_path = Path("playlists") / filename
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w") as f:
                    json.dump(playlist_data, f, indent=2)
                logger.info(f"✓ Saved to {out_path}")
                final_path = out_path

        if build_playlist and final_path:
            logger.info("\nBuilding playlist on Spotify...")
            build(final_path)
        elif final_path:
            logger.info(f"Run 'spotify-playlist-builder build {final_path}' to create it!")

    except Exception as e:
        logger.error(f"Generation failed: {e}")


if __name__ == "__main__":
    app()
