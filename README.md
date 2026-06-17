# Talordata SERP Dify Plugin

Talordata SERP Dify Plugin exposes Talordata SERP API as Dify tools.

## Credentials

Configure a Talordata SERP API Key in the plugin provider settings.

Use an API key with this shape:

```text
sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not use a Talordata login JWT token. Login JWT is only for Talordata dashboard APIs such as quota, token management, statistics, and Playground schema.

## Actions

This plugin exposes one Dify action for each enabled SERP engine in
`talor-pay-package-view/configs/serp_schemas/engines`, plus a raw request action
for advanced use.

Generated actions include:

- Google: `google_search`, `google_image_search`, `google_news_search`, `google_shopping_search`, `google_maps_search`, `google_scholar_search`, `google_trends_search`, `google_play_product_search`, and the other enabled Google engines in the schema directory
- Bing: `bing_search`, `bing_image_search`, `bing_maps_search`, `bing_news_search`, `bing_shopping_search`, `bing_videos_search`
- Other engines: `yandex_search`, `duckduckgo_search`
- Advanced: `raw_serp_request`

`google_product` is not exposed because its source schema is currently disabled. `google_play_product_search` is exposed separately for the `google_play_product` engine.

### SERP Engine Actions

Calls:

```text
POST https://serpapi.talordata.net/serp/v1/request
Authorization: Bearer <SERP_API_KEY>
Content-Type: application/x-www-form-urlencoded
```

Each generated action fixes its own `engine` parameter, validates the schema
query field, and exposes the common SERP parameters directly in the Dify node.
Use `raw_serp_request` when you need to pass a custom `params_json` override
object for advanced request parameters.

Image actions return normalized image result fields when possible. Web/news
actions return normalized web result fields when possible. Complex engines such
as hotels, flights, finance, maps, and product details return the raw upstream
payload in a stable wrapper.

### Bing Image Search Compatibility

The original `bing_image_search` action name is preserved for existing Dify
workflows.

Fixed parameter:

```text
engine=bing_images
```

Supported parameters:

- `q`
- `cc`
- `setlang`
- `mkt`
- `count`
- `first`
- `adlt`
- `imagesize`
- `no_cache`

### Raw SERP Request

Use this for advanced engines and parameters.

Input example:

```json
{
  "engine": "google",
  "q": "coffee",
  "params_json": "{\"gl\":\"us\",\"hl\":\"en\",\"num\":10}"
}
```

## Usage

1. Install the plugin package in Dify.
2. Configure the provider credentials with a Talordata SERP API key.
3. Add a search tool, such as Bing Search or Google Search, to a workflow or agent.
4. Map the user query to the tool's query field, for example `q`.
5. Run the workflow and consume the returned structured JSON results.

Example Bing Search input:

```json
{
  "q": "latest AI search trends",
  "cc": "us",
  "mkt": "en-us",
  "count": 10
}
```

Use `raw_serp_request` when advanced engine-specific parameters are required:

```json
{
  "engine": "google",
  "q": "coffee",
  "params_json": "{\"gl\":\"us\",\"hl\":\"en\",\"num\":10}"
}
```

## Limitations

- Search availability, freshness, latency, quota, and rate limits depend on the Talordata SERP API and the user's Talordata account plan.
- Some vertical engines return complex upstream payloads. The plugin wraps those responses in a stable JSON object instead of flattening every field.
- The plugin does not store Talordata dashboard login JWT tokens and does not require them for SERP requests.
- Avoid placing unnecessary sensitive personal data in search queries.

## Support

For issues with the Dify plugin package, report an issue in the GitHub repository where this plugin package is maintained.

For Talordata SERP API account, quota, or API key issues, contact Talordata support through the support channel listed in your Talordata account or dashboard.

## Development

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest -v
```

Regenerate schema-backed actions after SERP schema changes:

```powershell
python scripts/generate_serp_tools.py
```

Package:

```powershell
cd ..
dify plugin package talordata-serp
```

## Development Notes

The generated tools are based on Talordata SERP schema files. The internal
Talordata services that define or consume those schemas include:

- `talor-webui-dashboard/api/serp.js`
- `talor-pay-package-view/internal/router/serp_router.go`
- `talor-pay-package-view/internal/serp/service/playground_service.go`
- `talor-pay-package-view/configs/serp_schemas/engines/*.yaml`

## 🎁 Get Started for Free

Try TalorData SERP API with **1,000 free searches** and start building AI agents, SEO tools, and search-driven applications today.

- No infrastructure to manage
- Multi-engine search access
- Real-time structured results
- Developer-friendly integration

👉 [Start Free](https://talordata.com/?campaignid=hiy46bmdwF990Hqs&utm_source=Github29&utm_term=Github29)

---

## 🤝 Connect With Us

Have questions or want to collaborate? Reach out through any of the following channels:

- 📧 **Email:** [support@talordata.com](mailto:support@talordata.com)  
- 🌐 **Website:** [https://talordata.com](	https://talordata.com/?campaignid=hiy46bmdwF990Hqs&utm_source=Github29&utm_term=Github29)   
- 📱 **WhatsApp:** [+852 5628 3471](https://wa.me/85256283471)  
- 💼 **LinkedIn:** [TalorData](linkedin.com/company/talordata)

---

> **TalorData empowers developers and AI agents with fast, reliable search-data access through a single multi-engine SERP API.**