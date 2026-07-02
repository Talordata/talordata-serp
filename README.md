## 🚀 TalorData SERP Plugin for Dify

**Connect Dify to real-time Google, Bing, News, Maps, Images, Shopping, Scholar, Trends, and more with the TalorData SERP API. Build AI agents and workflows powered by fresh, structured, and reliable search data.**

The TalorData SERP Dify plugin adds the TalorData SERP API as a Dify tool, helping you use search result data in Dify workflows and agents.

**Perfect for AI Search, Live RAG, SEO Research, Sales Prospecting, Competitor Monitoring, Market Research, and Brand Intelligence. Learn more in the **[**TalorData Dify Integration Guide**](https://www.talordata.com/serp-api/dify?campaignid=qYTZMwsIBdQYhx5y&utm_source=Dify&utm_term=Dify29)**.**

### Get an API Token

Enter your TalorData SERP API Token in the plugin authorization settings.

**Create a free TalorData account and get your API Token:**

1. [**Get Free API Token**](https://www.talordata.com/serp-api/dify?campaignid=qYTZMwsIBdQYhx5y&utm_source=Dify&utm_term=Dify29)
2. Go to the SERP API Token page.
3. Create or copy an available API Token.
4. Paste the Token into the Dify plugin configuration.

🎉 New users receive free trial credits after signing up, allowing you to start building with Dify immediately.

API Token format example:

```
sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not use a Talordata login JWT token. Login JWT is only for Talordata dashboard APIs such as quota, token management, statistics, and Playground schema.

### **Why TalorData?**

**TalorData provides real-time, structured search data designed for AI applications. With a single plugin, your Dify workflows can access multiple search engines and return LLM-ready JSON responses.**

**Key benefits:**

- **Real-time Google, Bing, News, Maps, Images, Shopping, Scholar, and Trends search**
- **Structured JSON responses optimized for LLMs**
- **20+ supported search engines**
- **Native integration with Dify workflows and agents**
- **Free trial credits for new users**

### **Actions**

This plugin exposes one Dify action for each supported Talordata SERP engine, plus a raw request action for advanced use.

Generated actions include:

- Google: `google_search`, `google_image_search`, `google_news_search`, `google_shopping_search`, `google_maps_search`, `google_scholar_search`, `google_trends_search`, `google_play_product_search`, and other supported Google engines
- Bing: `bing_search`, `bing_image_search`, `bing_maps_search`, `bing_news_search`, `bing_shopping_search`, `bing_videos_search`
- Other engines: `yandex_search`, `duckduckgo_search`
- Advanced: `raw_serp_request`
`google_product` is not exposed because its source schema is currently disabled. `google_play_product_search` is exposed separately for the `google_play_product` engine.

### **SERP Engine Actions**

Calls:

```
POST https://serpapi.talordata.net/serp/v1/request
Authorization: Bearer <SERP_API_KEY>
Content-Type: application/x-www-form-urlencoded
```

Each generated action fixes its own `engine` parameter, validates the schema query field, and exposes the common SERP parameters directly in the Dify node. Use `raw_serp_request` when you need to pass a custom `params_json` override object for advanced request parameters.

Image actions return normalized image result fields when possible. Web/news actions return normalized web result fields when possible. Complex engines such as hotels, flights, finance, maps, and product details return the raw upstream payload in a stable wrapper.

**Bing Image Search Compatibility**

The original `bing_image_search` action name is preserved for existing Dify workflows.

Fixed parameter:

```
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

### **Raw SERP Request**

Use this for advanced engines and parameters.

Input example:

```
{
  "engine": "google",
  "q": "coffee",
  "params_json": "{\"gl\":\"us\",\"hl\":\"en\",\"num\":10}"
}
```

### Usage

1. Install the plugin package in Dify.
2. Configure the provider credentials with a Talordata SERP API key.
3. Add a search tool, such as Bing Search or Google Search, to a workflow or agent.
4. Map the user query to the tool's query field, for example `q`.
5. Run the workflow and consume the returned structured JSON results.
**Typical workflow:**

**User Query → TalorData Search → Fresh Search Results → LLM → AI Response**

Example Bing Search input:

```
{
  "q": "latest AI search trends",
  "cc": "us",
  "mkt": "en-us",
  "count": 10
}
```

Use `raw_serp_request` when advanced engine-specific parameters are required:

```
{
  "engine": "google",
  "q": "coffee",
  "params_json": "{\"gl\":\"us\",\"hl\":\"en\",\"num\":10}"
}
```

### **Popular Use Cases**

**The TalorData SERP Plugin can be used to build:**

- **AI Search Assistants**
- **Retrieval-Augmented Generation (RAG) with live web search**
- **SEO keyword and competitor research**
- **Sales prospecting and lead generation**
- **Competitor and brand monitoring**
- **Market and industry research**

### **Limitations**

- Search availability, freshness, latency, quota, and rate limits depend on the Talordata SERP API and the user's Talordata account plan.
- Some vertical engines return complex upstream payloads. The plugin wraps those responses in a stable JSON object instead of flattening every field.
- The plugin does not store Talordata dashboard login JWT tokens and does not require them for SERP requests.
- Avoid placing unnecessary sensitive personal data in search queries.

### Support

For issues with the Dify plugin package, report an issue in the [**GitHub repository**](https://github.com/Talordata/talordata-serp).

For Talordata SERP API account, quota, or API key issues, contact Talordata support through the support channel listed in your Talordata account or dashboard.

**For detailed integration tutorials and API documentation, visit the TalorData Documentation.**

### Learn More

Ready to build AI agents with real-time search?

- Explore the [**TalorData Dify Integration Guide**](https://www.talordata.com/serp-api/dify)
- Read the [**Integration Documentation**](https://docs.talordata.com/serp-api/integration)
- [**Create a free TalorData account and start with free trial credits**](https://www.talordata.com/serp-api/dify?campaignid=qYTZMwsIBdQYhx5y&utm_source=Dify&utm_term=Dify29)

TalorData brings real-time search to Dify, helping developers build AI agents and workflows with fresh, structured, and reliable search data.
