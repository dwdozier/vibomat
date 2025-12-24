# Setup and Installation

This guide covers the prerequisites, installation, and configuration required to run the
Spotify Playlist Builder.

## Prerequisites

- **Python 3.11+**
- **uv package manager**: [Installation Instructions](https://docs.astral.sh/uv/getting-started/)
- **Spotify Developer Credentials**: Follow the [App Registration Guide](APP_REGISTRATION.md) to
  get your Client ID and Client Secret.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/dwdozier/spotify-playlist-builder.git
    cd spotify-playlist-builder
    ```

2. **Create and activate the virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate  # macOS/Linux
    # or
    .venv\Scripts\activate  # Windows
    ```

3. **Install dependencies:**

    ```bash
    uv pip install -e .[dev]
    ```

    This installs the project in "editable" mode along with all development dependencies.

## Configuration

You need to provide your Spotify credentials to the application. You can do this using either a
`.env` file (easier) or your system's secure keychain (more secure).

### Option A: Use .env File (Default)

1. Create a `.env` file in the project root:

    ```bash
    touch .env
    ```

2. Add your credentials to the file:

    ```env
    SPOTIFY_CLIENT_ID=your_client_id_here
    SPOTIFY_CLIENT_SECRET=your_client_secret_here
    ```

    **Note:** The `.env` file is ignored by git to protect your secrets.

### Option B: Use System Keychain (Secure)

This method stores your credentials encrypted in your operating system's default keychain
(e.g., macOS Keychain, Windows Credential Manager).

1. Run the helper command:

    ```bash
    spotify-playlist-builder store-credentials
    ```

2. Enter your **Client ID** and **Client Secret** when prompted.

## Optional Setup

### Pre-commit Hooks

To ensure code quality checks run automatically before every commit:

```bash
pre-commit install
```

### Shell Completion (Zsh/Oh-My-Zsh)

To enable tab completion for commands and options:

```bash
spotify-playlist-builder install-zsh-completion
```

Follow the on-screen instructions to reload your shell.
