# TalorData SERP Dify Plugin

The TalorData SERP Dify plugin adds the TalorData SERP API as a Dify tool, helping you use search result data in Dify workflows and agents.

## Get an API Token

Enter your TalorData SERP API Token in the plugin authorization settings.

Don’t have a Token yet? Log in to the TalorData console to get one:

1.  [Log in to TalorData](https://www.talordata.com/serp-api/dify?campaignid=qYTZMwsIBdQYhx5y&utm_source=Dify&utm_term=Dify29)
2. Go to the SERP API Token page.
3. Create or copy an available API Token.
4. Paste the Token into the Dify plugin configuration.

New users receive free trial credits after logging in, so you can try the SERP API and Dify integration right away.

API Token format example:

```text
sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not use a Talordata login JWT token. Login JWT is only for Talordata dashboard APIs such as quota, token management, statistics, and Playground schema.

## Actions

This plugin exposes one Dify action for each supported Talordata SERP engine,
plus a raw request action for advanced use.

Generated actions include:

- Google: `google_search`, `google_image_search`, `google_news_search`, `google_shopping_search`, `google_maps_search`, `google_scholar_search`, `google_trends_search`, `google_play_product_search`, and other supported Google engines
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

For issues with the Dify plugin package, report an issue in the GitHub
repository:

```text
https://github.com/Talordata/talordata-serp
```

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

## GitHub Release Installation

Dify's "Install from GitHub" flow discovers formal plugin versions from GitHub
Releases. After packaging, publish a release whose tag matches the plugin
version in `manifest.yaml`, and attach the generated `.difypkg` file as a
release asset.

```powershell
cd C:\path\to\talordata-serp
.\scripts\publish_github_release.ps1
```

For version `0.1.9`, this creates or updates the `v0.1.9` release in
`Talordata/talordata-serp` with `talordata-serp.difypkg` attached. The script
requires `GH_TOKEN` or `GITHUB_TOKEN` in the current PowerShell session.
