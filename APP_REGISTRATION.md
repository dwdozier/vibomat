# Spotify App Registration Guide

To use the Spotify Playlist Builder, you must first register an application in the
Spotify Developer Dashboard. This will provide you with the necessary credentials
(`Client ID` and `Client Secret`) to authenticate with the Spotify API.

## Prerequisites

- A Spotify account (free or premium).

## Step-by-Step Instructions

1. **Log in to the Developer Dashboard**
    - Navigate to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
    - Log in with your Spotify account credentials.

2. **Create a New App**
    - Click the **"Create app"** button.
    - **App Name**: Enter a name for your application (e.g., `My Playlist Builder`).
    - **App Description**: Enter a brief description (e.g., `CLI tool for managing playlists`).
    - **Redirect URI**: This is a critical step for OAuth authentication.
      You **must** add the following URI:

      ```text
      https://127.0.0.1:8888/callback
      ```

    - Check the box to agree to the Developer Terms of Service.
    - Click **"Save"**.

3. **Retrieve Your Credentials**
    - Once the app is created, you will be taken to the app's overview page.
    - Click on the **"Settings"** button (or "Basic Information").
    - Locate your **Client ID**.
    - Click on **"View client secret"** to reveal your **Client Secret**.

## Next Steps

Copy your **Client ID** and **Client Secret**. You will need these to configure the
Playlist Builder. Return to [SETUP.md](SETUP.md) to continue the installation process.
