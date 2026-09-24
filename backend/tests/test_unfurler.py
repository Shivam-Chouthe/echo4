from unittest.mock import AsyncMock, patch
import httpx
import pytest
from httpx import Response
from app.services.extractors.url_unfurler import url_unfurler


def test_extract_first_url():
    text = "Check out this cafe https://maps.app.goo.gl/xyz123 it's great!"
    url = url_unfurler.extract_first_url(text)
    assert url == "https://maps.app.goo.gl/xyz123"


def test_extract_first_url_none():
    text = "Just some raw text with no link"
    assert url_unfurler.extract_first_url(text) is None


@pytest.mark.asyncio
async def test_fetch_metadata_success():
    html_content = """
    <html>
      <head>
        <meta property="og:title" content="Roastery Coffee House" />
        <meta property="og:description" content="Specialty coffee and breakfast cafe." />
        <meta property="og:site_name" content="Google Maps" />
      </head>
      <body></body>
    </html>
    """
    mock_resp = Response(
        status_code=200,
        text=html_content,
        request=httpx.Request("GET", "https://maps.app.goo.gl/xyz123"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        metadata = await url_unfurler.fetch_metadata("https://maps.app.goo.gl/xyz123")
        assert metadata.title == "Roastery Coffee House"
        assert metadata.description == "Specialty coffee and breakfast cafe."
        assert metadata.site_name == "Google Maps"