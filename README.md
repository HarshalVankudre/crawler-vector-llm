# Website-to-VectorDB — **Selenium Edition** (Streamlit + OpenAI + Pinecone)

JavaScript-heavy sites? No problem. This app uses **Selenium** (headless Chrome) to render pages,
then extracts text, chunks it, embeds with OpenAI, and uploads to a **Pinecone Serverless** index.

---

## ✨ What You Get

- ✅ Selenium-based crawler (respects `robots.txt`, internal links only, polite delay)
- ✅ Emergency **STOP** button for crawling and uploading
- ✅ Char-based chunking (defaults to `1000` chars) to mirror your original logic
- ✅ Batched embeddings + Pinecone upserts with progress via Streamlit status UI
- ✅ Clean, modular project structure and env-driven config

---

## 🧱 Project Structure

```text
website-to-vectordb-selenium/
├─ app.py                        # Streamlit UI (Selenium-driven pipeline)
├─ src/
│  ├─ config.py                  # API keys & settings
│  ├─ crawler/
│  │  ├─ webdriver.py            # Headless Chrome WebDriver (cached)
│  │  └─ selenium_crawler.py     # Polite Selenium crawler
│  ├─ embeddings/
│  │  ├─ clients.py              # OpenAI & Pinecone clients
│  │  └─ pipeline_selenium.py    # Char-chunk + embed + upsert
│  ├─ ui/                        # (reserved)
│  └─ utils/                     # (reserved)
├─ .env.example
├─ requirements.txt
├─ .gitignore
└─ README.md
```

---

## 🚀 Quickstart

**Prereqs**: Python 3.10+, **Google Chrome** installed on the host.

```bash
git clone <your-repo-url>.git
cd website-to-vectordb-selenium
cp .env.example .env  # add your keys
pip install -r requirements.txt
streamlit run app.py
```

### .env

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key | — |
| `PINECONE_API_KEY` | Your Pinecone API key | — |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | Vector dims | `1536` |
| `EMBEDDING_BATCH_SIZE` | Upsert batch size | `100` |
| `DEFAULT_POLITE_DELAY_SECONDS` | Delay after load (sec) | `2.0` |
| `CRAWLER_USER_AGENT` | HTTP UA string | Chrome-like UA |
| `PAGE_LOAD_TIMEOUT` | Max load time (sec) | `20` |
| `JS_CHUNK_SIZE` | Char limit per chunk | `1000` |

---

## 🧠 How It Works

1. **Crawl (Selenium)**: Headless Chrome loads each page so dynamic content renders.
   Basic `robots.txt` rules are respected, and only **internal** links are followed.
2. **Chunk**: Text is split into ~`JS_CHUNK_SIZE`-sized char chunks (to match your original script).
3. **Embed**: OpenAI Embeddings API runs in **batches** with robust error messages.
4. **Upload**: Vectors are upserted to a Pinecone **serverless** index.

---

## 🧪 Troubleshooting

- **Selenium/Chrome errors**: Ensure Google Chrome is installed and the machine has sufficient memory/CPU.
- **Keys missing**: The sidebar highlights which key is missing.
- **Permissions**: Always confirm you're allowed to crawl a domain, and respect each site's `robots.txt`.
- **Slow sites**: Increase `DEFAULT_POLITE_DELAY_SECONDS` in the sidebar or `.env`.

---

## 📄 License

MIT (or your preferred license).
