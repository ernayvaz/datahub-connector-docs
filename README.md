## AI-Powered Connector Documentation

### Quick Start (Local, Windows/Linux)
```bash
# clone & install dependencies
pip install -r requirements.txt

# copy environment example and update values
cp env.example .env

# run API server
uvicorn api.app:app --port 8080 --reload

# run docs site (optional live preview)
mkdocs serve
```
Visit http://127.0.0.1:8080/doc/{slug}?ai=true for AI-powered connector docs.
Visit http://127.0.0.1:8000/search/ for SPA search UI.

### GitHub Pages + GitHub Actions
* Workflow `gh-pages.yml` otomatik olarak manifests -> docs dönüşümünü ve MkDocs deploy’u yapar.
* API’yi Fly.io free tier’e yayınlamak için:
```bash
fly launch --image ghcr.io/superfly/machines-python --now
fly secrets set PROVIDER=ollama OLLAMA_MODEL=mistral
# copy model to volume or build dockerfile, see deploy/ folder
```

### Rate Limit
API 5 istek/dakika/IP sınırı uygular (in-memory). 429 alırsanız biraz bekleyin.

### Folder Structure
* `manifests/` – YAML/JSON tanımları
* `templates/connector.md.j2` – Doküman Jinja2 şablonu
* `scripts/` – Manifest zenginleştirme ve markdown üretimi
* `api/` – FastAPI sunucusu
* `docs/` – MkDocs site + SPA arama sayfası

## Technical Writer Workflow

Technical writers follow these steps to quickly generate and publish connector documentation:

1. Generate a draft using the CLI or API:
   - CLI: `python scripts/generate_doc.py --draft --ai manifests/<slug>.yaml`
   - API: GET `/doc/{slug}?ai=true`
2. Review and enrich the draft in `docs/drafts/<slug>.md`. Complete any ⚠️ TODO placeholders.
3. Move or copy the finalized markdown to `docs/connectors/<slug>.md` and commit.
4. Open a pull request for review; after approval, merge to `main`.
5. CI (GitHub Actions) automatically builds and publishes the updated site.

```mermaid
graph LR
  A[Generate draft] --> B[Review & enrich]
  B --> C[Finalize & commit]
  C --> D[Merge & publish]
```