import streamlit as st
import time
import requests
import markdown2
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from requests.exceptions import RequestException
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.config import CRAWLER_USER_AGENT, PAGE_LOAD_TIMEOUT

class PoliteCrawler:
    """Selenium-based crawler that respects robots.txt and adds polite delays."""
    def __init__(self, driver, start_url: str, delay_seconds: float):
        self.driver = driver
        self.base_url = start_url
        self.netloc = urlparse(start_url).netloc
        self.delay = delay_seconds

        self.data = {}      # {url: text_content}
        self.queue = [start_url]
        self.visited = set([start_url])

        self.disallowed = []
        self._parse_robots_txt()

    def _parse_robots_txt(self):
        robots_url = urljoin(self.base_url, "/robots.txt")
        headers = {"User-Agent": CRAWLER_USER_AGENT}
        try:
            resp = requests.get(robots_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                user_agent_block = False
                for raw in resp.text.splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.lower().startswith("user-agent:"):
                        user_agent_block = (line.split(":", 1)[1].strip() == "*")
                    elif line.lower().startswith("disallow:") and user_agent_block:
                        path = line.split(":", 1)[1].strip()
                        if path:
                            self.disallowed.append(path)
        except RequestException as e:
            print(f"Warning: Could not fetch robots.txt from {robots_url}. Proceeding with caution. Error: {e}")

    def _can_fetch(self, url_path: str) -> bool:
        for path in self.disallowed:
            if url_path.startswith(path):
                return False
        return True

    def _extract_text_and_links(self, html_content: str, url: str):
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract text (preserve the original logic using markdown2 roundtrip)
        for tag in soup(["script", "style"]):
            tag.decompose()
        text_raw = soup.get_text()
        html_from_text = markdown2.markdown(text_raw)
        text_from_html = BeautifulSoup(html_from_text, "html.parser").get_text()
        lines = (line.strip() for line in text_from_html.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        # Extract internal links
        links = []
        for a in soup.find_all("a", href=True):
            link = a["href"]
            full = urljoin(url, link)
            parsed = urlparse(full)
            clean = parsed._replace(query="", fragment="").geturl()
            if urlparse(clean).netloc == self.netloc and clean not in self.visited:
                links.append(clean)

        return text, links

    def start_crawl(self):
        safety_break = 1000
        while self.queue:
            if st.session_state.get('stop_pressed'):
                yield "🛑 CRAWL STOPPED BY USER."
                break

            if len(self.visited) > safety_break:
                yield f"⚠️ Safety break triggered after {safety_break} pages."
                break

            current_url = self.queue.pop(0)
            url_path = urlparse(current_url).path
            if not self._can_fetch(url_path):
                yield f"🚫 Skipping (robots.txt): {current_url}"
                continue

            time.sleep(self.delay)
            try:
                yield f"Crawling (JS Render): {current_url}"
                self.driver.get(current_url)
                time.sleep(1)  # let JS render a bit

                html = self.driver.page_source
                text, new_links = self._extract_text_and_links(html, current_url)

                if text:
                    self.data[current_url] = text
                for link in new_links:
                    self.visited.add(link)
                    self.queue.append(link)

            except TimeoutException:
                yield f"❌ Page timed out (> {PAGE_LOAD_TIMEOUT}s): {current_url}"
            except WebDriverException as e:
                yield f"❌ WebDriver error on {current_url}: {e}"
            except Exception as e:
                yield f"❌ Unexpected error processing {current_url}: {e}"

        if not st.session_state.get('stop_pressed'):
            yield f"✅ Crawl finished. Found {len(self.data)} pages with content."
