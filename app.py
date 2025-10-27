import streamlit as st
import json

from src.config import (
    OPENAI_API_KEY, PINECONE_API_KEY,
    DEFAULT_POLITE_DELAY_SECONDS, CRAWLER_USER_AGENT
)
from src.crawler.webdriver import get_webdriver
from src.crawler.selenium_crawler import PoliteCrawler
from src.embeddings.pipeline_selenium import embed_and_upload

st.set_page_config(page_title="RAG Data Pipeline (Selenium)", layout="wide", initial_sidebar_state="expanded")
st.title("🤖 RAG Data Pipeline (Selenium Edition)")
st.markdown("This app uses a Selenium-based crawler to handle JavaScript-rendered websites.")

# Session state
if 'crawled_data' not in st.session_state:
    st.session_state['crawled_data'] = None
if 'data_confirmed' not in st.session_state:
    st.session_state['data_confirmed'] = False
if 'stop_pressed' not in st.session_state:
    st.session_state['stop_pressed'] = False

# --- Sidebar: config ---
with st.sidebar:
    st.title("🛠️ Configuration")
    st.caption("API keys must be set in a `.env` file in the same folder as this app.")
    st.success("OpenAI Key Loaded" if OPENAI_API_KEY and "sk-" in OPENAI_API_KEY else "OpenAI Key Not Found")
    st.success("Pinecone Key Loaded" if PINECONE_API_KEY else "Pinecone Key Not Found")

    st.markdown("---")
    st.subheader("Crawler Settings")
    polite_delay = st.number_input(
        "Polite Delay (seconds)",
        min_value=0.5,
        value=DEFAULT_POLITE_DELAY_SECONDS,
        step=0.25,
        help="Delay after each page load. 2.0+ is recommended for JS-heavy sites.",
    )
    st.markdown(f"**User Agent:** `{CRAWLER_USER_AGENT[:60]}...`")

# --- Step 1: Crawl ---
with st.container(border=True):
    st.header("1️⃣ Step 1: Crawl Website(s)")

    driver = get_webdriver()
    if driver is None:
        st.error("Selenium WebDriver failed to start. Ensure Google Chrome is installed and the host has enough memory.")
        st.stop()

    urls_to_crawl_input = st.text_area(
        "Enter one or more full URLs to crawl (one per line)",
        placeholder="https://example.com\nhttps://another-site.com/blog",
        height=100,
        disabled=st.session_state.get('data_confirmed', False),
    )

    if st.button("Start Crawl", type="primary", disabled=(not urls_to_crawl_input or st.session_state.get('data_confirmed', False))):
        if not OPENAI_API_KEY or not PINECONE_API_KEY:
            st.error("Please set your API keys before starting.")
        else:
            st.session_state['crawled_data'] = {}
            st.session_state['data_confirmed'] = False
            st.session_state['stop_pressed'] = False

            urls_to_crawl = [u.strip() for u in urls_to_crawl_input.splitlines() if u.strip()]
            if not urls_to_crawl:
                st.error("Please enter at least one valid URL.")
            else:
                all_crawled = {}
                with st.status("Crawling websites with Selenium...", expanded=True) as status_box:
                    st.button("🛑 EMERGENCY STOP", key="stop_crawl", on_click=lambda: st.session_state.update(stop_pressed=True))

                    for url in urls_to_crawl:
                        if st.session_state.get('stop_pressed'):
                            status_box.write("🛑 CRAWL STOPPED BY USER.")
                            break
                        if not (url.startswith("http://") or url.startswith("https://")):
                            status_box.write(f"⚠️ Skipping invalid URL (must start with http/https): {url}")
                            continue

                        status_box.write(f"--- Starting crawl for: {url} ---")
                        try:
                            crawler = PoliteCrawler(driver=driver, start_url=url, delay_seconds=polite_delay)
                            for update in crawler.start_crawl():
                                if st.session_state.get('stop_pressed'):
                                    break
                                status_box.write(update)
                            all_crawled.update(crawler.data)
                            if not st.session_state.get('stop_pressed'):
                                status_box.write(f"--- Finished crawl for: {url} ---")
                        except Exception as e:
                            status_box.write(f"❌ Failed to crawl {url}: {e}")

                st.session_state['crawled_data'] = all_crawled
                if not st.session_state.get('stop_pressed'):
                    st.success(f"Crawl finished! Found a total of {len(all_crawled)} pages with content.")
                else:
                    st.warning(f"Crawl stopped. Found {len(all_crawled)} pages before stopping.")

                st.session_state['stop_pressed'] = False
                st.rerun()

# --- Step 2: Preview & Confirm ---
with st.container(border=True):
    st.header("2️⃣ Step 2: Preview & Confirm Data")

    if st.session_state['crawled_data'] and not st.session_state['data_confirmed']:
        st.info(f"**{len(st.session_state['crawled_data'])}** total pages are ready to be embedded.")
        col1, col2 = st.columns(2)
        with col1:
            try:
                json_data = json.dumps(st.session_state['crawled_data'], indent=2, ensure_ascii=False)
            except Exception as e:
                st.error(f"Error preparing JSON for download: {e}")
                json_data = "{}"
            st.download_button(
                label="Download Crawled Data as JSON",
                data=json_data,
                file_name="scraped_data.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            if st.button("Confirm Data & Proceed to Upload", type="primary", use_container_width=True):
                st.session_state['data_confirmed'] = True
                st.rerun()

        with st.expander("Click to preview crawled data (first 5 pages)"):
            preview = dict(list(st.session_state['crawled_data'].items())[:5])
            st.json(preview, expanded=False)

    elif st.session_state['data_confirmed']:
        st.write("Data confirmed and ready for upload in Step 3.")
    else:
        st.info("You must crawl in Step 1 before previewing.")

# --- Step 3: Embed & Upload ---
with st.container(border=True):
    st.header("3️⃣ Step 3: Embed & Upload to Pinecone")

    if st.session_state['data_confirmed']:
        st.success("Data confirmed. Please enter your Pinecone index name to begin the upload.")
        index_name = st.text_input("Enter the name for your Pinecone index", placeholder="my-chatbot-index")

        if st.button("Embed and Upload", type="primary", disabled=(not index_name)):
            st.session_state['stop_pressed'] = False
            with st.status("Embedding and uploading data...", expanded=True) as status_box:
                st.button("🛑 EMERGENCY STOP", key="stop_embed", on_click=lambda: st.session_state.update(stop_pressed=True))

                for msg in embed_and_upload(st.session_state['crawled_data'], index_name):
                    if st.session_state.get('stop_pressed'):
                        status_box.write("🛑 UPLOAD STOPPED BY USER.")
                        break
                    status_box.write(msg)

            if not st.session_state.get('stop_pressed'):
                st.success("Data processing complete!")
                st.balloons()
                st.session_state['crawled_data'] = None
                st.session_state['data_confirmed'] = False
            else:
                st.warning("Upload process was stopped by the user. Data is still loaded; you can try again.")

            st.session_state['stop_pressed'] = False
            st.rerun()
    elif st.session_state['crawled_data']:
        st.info("Please confirm your data in Step 2 to proceed.")
    else:
        st.info("You must crawl a website in Step 1 first.")
