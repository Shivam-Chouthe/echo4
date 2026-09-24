import logging
import re
from typing import Optional
from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*"
)


class ExtractedMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    site_name: Optional[str] = None
    canonical_url: Optional[str] = None


class URLUnfurler:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def extract_first_url(self, text: str) -> Optional[str]:
        match = URL_REGEX.search(text)
        return match.group(0) if match else None

    async def fetch_metadata(self, url: str) -> ExtractedMetadata:
        target_url = url if url.startswith(("http://", "https://")) else f"https://{url}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.headers,
            ) as client:
                response = await client.get(target_url)
                if response.status_code >= 400:
                    logger.warning("Unfurler received status %s for %s", response.status_code, target_url)
                    return ExtractedMetadata(canonical_url=target_url)

                soup = BeautifulSoup(response.text, "html.parser")

                # Parse OpenGraph & standard meta tags
                og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
                og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "twitter:description"}) or soup.find("meta", attrs={"name": "description"})
                og_site = soup.find("meta", property="og:site_name")

                title = (og_title.get("content") if og_title else None) or (soup.title.string if soup.title else None)
                description = og_desc.get("content") if og_desc else None
                site_name = og_site.get("content") if og_site else None

                return ExtractedMetadata(
                    title=title.strip() if title else None,
                    description=description.strip() if description else None,
                    site_name=site_name.strip() if site_name else None,
                    canonical_url=str(response.url),
                )
        except Exception as exc:
            logger.warning("Failed to unfurl %s: %s", target_url, exc)
            return ExtractedMetadata(canonical_url=target_url)


url_unfurler = URLUnfurler()