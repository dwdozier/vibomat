import os
import sys
import time
import typer
from pathlib import Path
from google import genai
from google.genai import types

app = typer.Typer()

# Initialize Gemini Client
# We use the new google-genai SDK as per project dependencies
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GOOGLE_STYLE_GUIDE_PROMPT = """
You are a Senior Technical Writer at Google. You strictly follow the
Google Developer Documentation Style Guide.

**Voice & Tone:**
- **Active Voice**: Use "Run the command" (Imperative) or "The API returns..." (Active).
  AVOID "You should run" or "The API will be returning".
- **Present Tense**: Describe what the code *does*, not what it *will do*.
- **Second Person**: Address the user as "you".
- **Clarity**: Be concise. Avoid fluff like "please", "simply", "just", "basically", "in order to".
- **Formatting**: Use Sentence case for all headings (e.g., "Configure the application",
  NOT "Configure The Application").

**Task:**
Analyze the provided "Code Changes" (Git Diff) and the "Current Documentation".
Update the documentation to accurately reflect the code changes.
Maintain the existing structure of the document unless a structural change is absolutely necessary
for clarity.
Do not remove existing sections that are unrelated to the changes.

**Output:**
Return ONLY the full updated markdown content for the file. Do not include markdown code fences
(```markdown) around the output unless they are part of the documentation itself.
"""


def get_file_content(path: Path) -> str:
    if not path.exists():
        return ""
    with open(path, "r") as f:
        return f.read()


@app.command()
def update_readme(
    diff_path: Path = typer.Option(..., help="Path to the git diff file"),
    readme_path: Path = typer.Option("README.md", help="Path to the README.md file"),
    openapi_path: Path = typer.Option(None, help="Path to openapi.json if available"),
):
    """
    Updates README.md based on code changes.
    Checks for:
    - New Core Features (backend/app endpoints)
    - Tech Stack updates (pyproject.toml, package.json)
    - Quick Start changes (docker-compose, SETUP.md)
    """
    diff_content = get_file_content(diff_path)
    readme_content = get_file_content(readme_path)

    if not diff_content:
        typer.echo("No diff content found.")
        return

    # Context assembly
    prompt = f"""
{GOOGLE_STYLE_GUIDE_PROMPT}

**Target File:** README.md

**Current Content:**
{readme_content}

**Code Changes (Git Diff):**
{diff_content}

**Instructions:**
1. Check "pyproject.toml" or "package.json" in the diff for **Tech Stack** updates.
2. Check "backend/app" or "frontend/src" for new **Core Features**.
3. Check "docker-compose.yml" or "SETUP.md" for **Quick Start** instructions.
4. If no relevant changes are found for README.md, return the **Current Content** exactly as is.
5. If changes are needed, integrate them seamlessly.
"""

    _generate_and_save(prompt, readme_path)


@app.command()
def update_contributing(
    diff_path: Path = typer.Option(..., help="Path to the git diff file"),
    contributing_path: Path = typer.Option("CONTRIBUTING.md", help="Path to CONTRIBUTING.md"),
):
    """
    Updates CONTRIBUTING.md based on tooling/workflow changes.
    Checks for:
    - Pre-commit config changes
    - CI/CD workflow updates
    - Testing framework changes (pyproject.toml)
    """
    diff_content = get_file_content(diff_path)
    current_content = get_file_content(contributing_path)

    if not diff_content:
        return

    prompt = f"""
{GOOGLE_STYLE_GUIDE_PROMPT}

**Target File:** CONTRIBUTING.md

**Current Content:**
{current_content}

**Code Changes:**
{diff_content}

**Instructions:**
1. Check ".pre-commit-config.yaml" for new hooks or rules.
2. Check ".github/workflows" for CI pipeline changes affecting the PR workflow.
3. Check "pyproject.toml" for testing tool updates.
4. Update the "Testing Requirements" or "Workflow" sections if necessary.
5. If no relevant changes, return the **Current Content** exactly.
"""
    _generate_and_save(prompt, contributing_path)


@app.command()
def update_setup(
    diff_path: Path = typer.Option(..., help="Path to the git diff file"),
    setup_path: Path = typer.Option("SETUP.md", help="Path to SETUP.md"),
):
    """
    Updates SETUP.md based on environment changes.
    Checks for:
    - Dockerfile updates
    - New environment variables (.env.example or code references)
    - Python dependency changes requiring system libs
    """
    diff_content = get_file_content(diff_path)
    current_content = get_file_content(setup_path)

    if not diff_content:
        return

    prompt = f"""
{GOOGLE_STYLE_GUIDE_PROMPT}

**Target File:** SETUP.md

**Current Content:**
{current_content}

**Code Changes:**
{diff_content}

**Instructions:**
1. Check "Dockerfile" or "docker-compose.yml" for installation step changes.
2. Check for new REQUIRED environment variables in "backend/app/core/config.py".
3. Update installation commands if dependency managers change (e.g., pip vs uv).
4. If no relevant changes, return the **Current Content** exactly.
"""
    _generate_and_save(prompt, setup_path)


def _generate_and_save(prompt: str, output_path: Path):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        updated_content = response.text
        if not updated_content or len(updated_content) < 10:
            typer.echo(f"Skipping {output_path}: Content empty/short.")
            return

        with open(output_path, "w") as f:
            f.write(updated_content)
        typer.echo(f"Successfully updated {output_path}")
    except Exception as e:
        typer.echo(f"Error updating {output_path}: {e}")
        sys.exit(1)


@app.command()
def generate_guide(
    diff_path: Path = typer.Option(..., help="Path to the git diff file"),
    output_dir: Path = typer.Option("docs/guides", help="Directory to save the new guide"),
):
    """
    Generates a new Usage Guide if significant API changes are detected.
    """
    diff_content = get_file_content(diff_path)

    if not diff_content:
        typer.echo("No diff content found.")
        return

    prompt = f"""
{GOOGLE_STYLE_GUIDE_PROMPT}

**Task:**
Determine if the "Code Changes" introduce a new feature that requires a usage guide.
If yes, write a new markdown file content.
If no (e.g., minor bug fix, dependency update), return "NO_GUIDE".

**Code Changes:**
{diff_content}

**Guide Structure:**
# [Feature Name]
[Short Description]

## Prerequisites
[List]

## Usage
[Step-by-step instructions with code blocks]

## Implementation Notes
[Edge cases or constraints]
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        content = response.text.strip()

        if content == "NO_GUIDE":
            typer.echo("No guide generated (changes deemed minor).")
            return

        # Extract a filename suggestion (simplified approach)
        # In a real scenario, we ask Gemini for filename too.
        filename = f"guide_{int(time.time())}.md"

        output_path = output_dir / filename
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(content)

        typer.echo(f"Generated new guide: {output_path}")

    except Exception as e:
        typer.echo(f"Error generating guide: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
