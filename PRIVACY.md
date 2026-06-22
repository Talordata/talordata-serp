# Privacy

This plugin sends the search parameters entered or configured in Dify to the Talordata SERP API in order to return search results.

Data that may be sent to Talordata SERP API includes:

- search query
- selected SERP engine
- country, region, market, and language parameters
- location, latitude, and longitude parameters when configured
- URL-based inputs, such as Google Lens image or page URLs, when configured
- pagination and result count parameters
- engine-specific identifiers, such as product IDs, patent IDs, author IDs, and finance or trend identifiers
- image, video, shopping, maps, news, scholar, finance, patent, hotel, flight, and other engine-specific filters
- advanced parameters provided through `raw_serp_request`

The plugin uses the SERP API Key configured by the Dify workspace user. The key is used only to authenticate requests to the Talordata SERP API.

The plugin returns API responses to the invoking Dify workflow or agent. It does not require or store Talordata dashboard login JWT tokens. The plugin does not intentionally persist search queries, API responses, or API keys outside of Dify's normal plugin runtime, workflow execution, logging, and credential storage behavior.

Users should avoid submitting unnecessary sensitive personal data in search queries or request parameters.

Talordata SERP API processing, retention, quota, and rate-limit behavior are governed by Talordata's service terms and privacy policy.
