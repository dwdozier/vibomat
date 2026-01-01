import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ci
def test_site_sanity_check(page: Page):
    """Sanity Check: Verify the site is up and navigation elements are present."""
    base_url = "http://localhost"  # In CI/Docker this is the frontend service
    page.goto(base_url)

    # Verify Brand is visible
    brand = page.locator('[data-play="nav-brand"]')
    expect(brand).to_be_visible()
    expect(brand).to_have_text("VIB-O-MAT")

    # Verify Hero CTA for unauthenticated users
    hero_cta = page.locator('[data-play="hero-cta-login"]')
    expect(hero_cta).to_be_visible()
    expect(hero_cta).to_contain_text("JOIN THE FUTURE")

    # Verify Login Link in nav
    nav_login = page.locator('[data-play="nav-login"]')
    expect(nav_login).to_be_visible()

    # Navigate to login
    nav_login.click()
    expect(page).to_have_url(f"{base_url}/login")
    expect(page.get_by_text("Identification", exact=False)).to_be_visible()
