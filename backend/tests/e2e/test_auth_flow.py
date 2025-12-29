import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip(reason="Needs running frontend and backend servers")
def test_navigation_to_login(page: Page):
    """Test that a user can navigate from the home page to the login page."""
    page.goto("http://localhost:5173")  # Vite dev server

    # Check home page
    expect(page.get_by_text("Welcome to Playlist Builder")).to_be_visible()

    # Click Login
    page.get_by_role("link", name="Login").click()

    # Verify login page
    expect(page.get_by_text("Welcome back")).to_be_visible()
    expect(page.get_by_role("button", name="Continue with Google")).to_be_visible()
