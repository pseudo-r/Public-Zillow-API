# Changelog

All notable changes to the Public Zillow API documentation are listed here.

---

## [Unreleased] — March 2026

### 🆕 Added

#### Documentation
- **Initial `README.md`** — full endpoint reference covering all discovered Zillow API families
- **Search endpoints** — `async-create-search-page-state` (PUT) with full `filterState`, `wants`, `searchQueryState` breakdown
- **Legacy search** — `GetSearchPageState.htm` documented with partial-verified status
- **GraphQL section** — `www.zillow.com/graphql/` and `www.zillow.com/zg-graph` documented with all known operations
  - `ZestimateDeepDiveQuery`, `HomeValueChartDataQuery`, `WalkTransitAndBikeScoreQuery`
  - `PropertyClimateRiskQuery`, `SimilarSalesQuery`, `NearbyHomesQuery`, `SchoolsQuery`
  - `HdpMortgageCalculatorQuery`, `ListingDetailsQuery`, `RentEstimateQuery`
  - `GetAutocompleteResults` (autocomplete via `zg-graph`)
- **Property detail extraction** — `__NEXT_DATA__` (Next.js) and `hdpApolloPreloadedData` (Apollo) patterns documented
- **Rental search** — same `async-create-search-page-state` with `isForRent` filter documented
- **Media / CDN section** — `photos.zillowstatic.com` image URL patterns and size variants
- **Additional domains** — `api.zillow.com` (deprecated), `bridgeinteractive.com` (restricted), `zillowstatic.com` (CDN)
- **Versioning notes** — confirmed Zillow does NOT use `/v1/` `/v2/` `/v3/` versioning
- **Headers & cookies reference** — `zguid`, `JSESSIONID`, `client-id`, `x-caller-id`
- **Parameters reference** — `searchQueryState`, `filterState`, `wants`, sort values, region types
- **Endpoint relationships** — chain from autocomplete → regionId → search → zpid → graphql
- **`docs/response_schemas.md`** — example JSON response structures for key endpoints
- **`docs/endpoints/search.md`** — dedicated search endpoint reference
- **`docs/endpoints/property.md`** — property detail endpoint reference
- **`docs/endpoints/rentals.md`** — rental endpoint reference
- **`docs/endpoints/market_valuation.md`** — Zestimate and market data reference
- **`docs/endpoints/graphql.md`** — GraphQL operations reference

#### Repository
- **`CONTRIBUTING.md`** — contribution guidelines and documentation style guide
- **`CHANGELOG.md`** (this file)
- **`.github/FUNDING.yml`** — sponsorship links
- **`.gitignore`** — standard Python/Django gitignore
- **`.env.example`** — environment variable template

#### Code (`zillow_service`)
- **Django `zillow_service`** — standalone REST API wrapping Zillow's endpoints
  - `ZillowClient` with retry, timeout, and structured logging
  - `SearchService` — search for-sale, rental, recently-sold
  - `PropertyService` — property detail by ZPID
  - `ZestimateService` — Zestimate and history
  - `ScoresService` — Walk/Transit/Bike/Climate scores
  - `AutocompleteService` — location suggestions
  - Celery background tasks for ingestion
  - Docker + docker-compose
  - OpenAPI docs via drf-spectacular

---

## [1.0.0] — Initial Release — March 2026

### 🆕 Added
- Initial repository created
- Base domain discovery (www.zillow.com, graphql, zg-graph, zillowstatic.com)
- Endpoint families identified and organized
