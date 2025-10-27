import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from src.config import CRAWLER_USER_AGENT, PAGE_LOAD_TIMEOUT

@st.cache_resource
def get_webdriver():
    """Start a cached headless Chrome WebDriver with a custom user-agent."""
    st.write("Initializing Selenium WebDriver (this may take a moment)...")
    try:
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={CRAWLER_USER_AGENT}")
        options.add_argument("window-size=1920,1080")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        st.write("✅ WebDriver initialized successfully.")
        return driver
    except Exception as e:
        st.error(f"Error initializing Selenium WebDriver: {e}")
        st.error("Fatal Error: Could not start Selenium. Ensure Google Chrome is installed and the host has sufficient memory.")
        return None
