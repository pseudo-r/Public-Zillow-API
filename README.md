# Zillow Public API Documentation

**Disclaimer:** This is documentation for Zillow's undocumented internal API. I am not affiliated with Zillow. Use responsibly and follow Zillow's terms of service.

---

## ☕ Support This Project

If this documentation has saved you time, consider supporting ongoing development and maintenance:

| Platform | Link |
|----------|------|
| ☕ Buy Me a Coffee | [buymeacoffee.com/pseudo_r](https://buymeacoffee.com/pseudo_r) |
| 💖 GitHub Sponsors | [github.com/sponsors/Kloverdevs](https://github.com/sponsors/Kloverdevs) |
| 💳 PayPal Donate | [PayPal (CAD)](https://www.paypal.com/donate/?business=H5VPFZ2EHVNBU&no_recurring=0&currency_code=CAD) |

Every contribution helps keep this project updated as Zillow changes their API.

---

## 📱 Real-World Apps Built With This API

These apps are live examples of what you can build using this documentation and the included Django service:

### 🏠 [Sportly: Basketball Live](https://play.google.com/store/apps/details?id=com.sportly.basketball)
> Real-time NBA, college basketball, and international leagues — scores, standings, player stats, and live game tracking.

---

## Table of Contents

- [Overview](#overview)
- [Base Domains](#base-domains)
- [Quick Start](#quick-start)
- [Versioned Endpoints](#versioned-endpoints)
- [Search / Discovery Endpoints](#search--discovery-endpoints)
- [Property / Listing Endpoints](#property--listing-endpoints)
- [Rental Endpoints](#rental-endpoints)
- [Market / Valuation Endpoints](#market--valuation-endpoints)
- [GraphQL Endpoints](#graphql-endpoints)
- [Media / Asset Endpoints](#media--asset-endpoints)
- [Additional Domains / Endpoint Families](#additional-domains--endpoint-families)
- [Endpoint Relationships](#endpoint-relationships)
- [Headers & Cookies](#headers--cookies)
- [Parameters Reference](#parameters-reference)
- [Zillow Service (Django Implementation)](#zillow-service-django-implementation)
- [Response Schemas](docs/response_schemas.md)
- [CHANGELOG](CHANGELOG.md)

---

## Overview

Zillow provides undocumented internal APIs that power their website and mobile apps. These endpoints return JSON data for property listings, home values, rental data, market trends, and more.

**Four main API families:**
- `www.zillow.com` — Main site API (search, property pages, rentals, nav)
- `www.zillow.com/graphql/` — GraphQL (property detail, estimates, scores)
- `www.zillow.com/zg-graph` — Secondary GraphQL (autocomplete, recent searches)
- `mortgageapi.zillow.com` — Mortgage rates API (live-verified, no auth)

**Additional domains documented:** `zillowstatic.com` (CDN/images) · `zillow.com/search/` (legacy search) · `zillow.com/rentals/api/rcf/` (rental fees microservice) · `bridgeinteractive.com` (official partner API, access-restricted)

### Important Notes

- **Unofficial:** These APIs are not officially supported and may change without notice
- **Bot Detection:** Zillow actively blocks scrapers — browser-like headers and valid cookies are required
- **Rate Limiting:** Aggressive — implement delays and caching
- **Session Required:** Many endpoints require a valid browser session (`zguid` cookie set on first page load)
- **No API Key:** No authentication key needed, but session cookies are often required for reliable access

---

## Base Domains

| Domain | Purpose |
|--------|---------|
| `www.zillow.com` | Main site — search, property pages, rentals, rent costs |
| `www.zillow.com/graphql/` | GraphQL endpoint — property detail, Zestimate, scores |
| `www.zillow.com/zg-graph` | Secondary GraphQL — autocomplete, recent searches |
| `www.zillow.com/rentals/api/rcf/v1/` | Rental costs and fees microservice |
| `www.zillow.com/search/` | Legacy search endpoints (partially active) |
| `mortgageapi.zillow.com` | Mortgage rates API — no auth required |
| `zillowstatic.com` | CDN — listing images, map tiles |
| `bridgeinteractive.com` | Official partner/Zestimate API (requires approval) |

---

## Quick Start

```bash
# Property search (for sale) in Seattle — PUT with JSON body
curl -X PUT "https://www.zillow.com/async-create-search-page-state" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: */*" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -d '{
    "searchQueryState": {
      "pagination": {},
      "usersSearchTerm": "Seattle, WA",
      "mapBounds": {"west": -122.5, "east": -122.2, "south": 47.5, "north": 47.7},
      "regionSelection": [{"regionId": 16163, "regionType": 6}],
      "filterState": {"sortSelection": {"value": "globalrelevanceex"}},
      "isMapVisible": true,
      "isListVisible": true
    },
    "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
    "requestId": 2,
    "isDebugRequest": false
  }'

# Autocomplete via GraphQL
curl -X POST "https://www.zillow.com/zg-graph" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -d '{
    "operationName": "GetAutocompleteResults",
    "variables": {"query": "Seattle, WA", "resultType": ["REGIONS", "FORSALE", "RENTALS"]},
    "query": "query GetAutocompleteResults($query: String!, $resultType: [AutocompleteResultType!]) { zgsAutoComplete(query: $query, resultType: $resultType) { results { display metaData { regionId regionType } } } }"
  }'
```

---

## Versioned Endpoints

Zillow does not use explicit `/v1/`, `/v2/`, `/v3/` versioning in most cases.

| Family | Path Pattern | Notes |
|--------|-------------|-------|
| Main search (current) | `www.zillow.com/async-create-search-page-state` | PUT — current primary search API |
| Legacy search | `www.zillow.com/search/GetSearchPageState.htm` | GET/PUT — older, still partially active |
| GraphQL (current) | `www.zillow.com/graphql/` | POST or persisted GET — primary property data |
| GraphQL v2 | `www.zillow.com/zg-graph` | POST — autocomplete and regional data |
| Property pages | `www.zillow.com/homedetails/{address}/{zpid}_zpid/` | HTML with embedded `__NEXT_DATA__` JSON |
| Old API (deprecated) | `api.zillow.com/webservice/GetDeepSearchResults.htm` | Zillow legacy XML API — **no longer works** |
| Bridge API | `api.bridgeinteractive.com` | Partner access only, requires approval |

> **v1/v2/v3 verdict:** Zillow does **not** use explicit version prefixes in URL paths. The "versioning" is implicit — the GraphQL schema evolves in-place, and old REST paths like `GetSearchPageState.htm` coexist alongside `async-create-search-page-state`.

---

## Search / Discovery Endpoints

### 1. Home Search (For Sale)

**Endpoint:** `https://www.zillow.com/async-create-search-page-state`  
**Method:** `PUT`  
**Version:** Unversioned (current)  
**Verification:** ✅ VERIFIED

**Required Headers:**
```
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept: */*
Accept-Language: en-US,en;q=0.9
```

**Required Body:**

```json
{
  "searchQueryState": {
    "pagination": {},
    "usersSearchTerm": "Seattle, WA",
    "mapBounds": {
      "west": -122.5,
      "east": -122.2,
      "south": 47.5,
      "north": 47.7
    },
    "regionSelection": [
      {"regionId": 16163, "regionType": 6}
    ],
    "filterState": {
      "sortSelection": {"value": "globalrelevanceex"}
    },
    "isMapVisible": true,
    "isListVisible": true
  },
  "wants": {
    "cat1": ["listResults", "mapResults"],
    "cat2": ["total"]
  },
  "requestId": 2,
  "isDebugRequest": false
}
```

**Optional `filterState` Keys:**

| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `price.min` | object | `{"value": 200000}` | Minimum price |
| `price.max` | object | `{"value": 800000}` | Maximum price |
| `beds.min` | object | `{"value": 2}` | Min bedrooms |
| `baths.min` | object | `{"value": 1}` | Min bathrooms |
| `sqft.min` | object | `{"value": 1000}` | Min square footage |
| `sqft.max` | object | `{"value": 3000}` | Max square footage |
| `isForRent` | object | `{"value": true}` | Rental listings |
| `isForSaleByAgent` | object | `{"value": false}` | Exclude agent listings |
| `isForSaleByOwner` | object | `{"value": true}` | FSBO only |
| `isNewConstruction` | object | `{"value": true}` | New construction only |
| `isRecentlySold` | object | `{"value": true}` | Recently sold |
| `isComingSoon` | object | `{"value": true}` | Coming soon listings |
| `isAuction` | object | `{"value": false}` | Exclude auctions |
| `hasPool` | object | `{"value": true}` | Has pool |
| `sortSelection` | object | `{"value": "globalrelevanceex"}` | Sort order |

**Sort Values:**

| Value | Description |
|-------|-------------|
| `globalrelevanceex` | Best match (default) |
| `days` | Newest listings |
| `priceDesc` | Price high to low |
| `priceAsc` | Price low to high |
| `beds` | Most bedrooms |
| `baths` | Most bathrooms |
| `sqftDesc` | Largest |

**Pagination:**
```json
"pagination": {"currentPage": 2}
```
> Max ~40 results/page, up to 500 total per query. Use tighter `mapBounds` to get more results.

**Example Response (trimmed):**
```json
{
  "cat1": {
    "searchResults": {
      "listResults": [
        {
          "zpid": "2077091803",
          "id": "2077091803",
          "detailUrl": "/homedetails/123-Main-St-Seattle-WA-98101/2077091803_zpid/",
          "statusType": "FOR_SALE",
          "statusText": "House for sale",
          "price": "$850,000",
          "unformattedPrice": 850000,
          "address": "123 Main St, Seattle, WA 98101",
          "beds": 3,
          "baths": 2,
          "area": 1850,
          "latLong": {"latitude": 47.6062, "longitude": -122.3321},
          "imgSrc": "https://photos.zillowstatic.com/fp/abc123-uncropped_scaled_within_1536_1152.webp",
          "hasVideo": false,
          "isFeatured": false,
          "shouldShowZestimate": true,
          "zestimate": 845000,
          "hdpData": {
            "homeInfo": {
              "zpid": 2077091803,
              "zipcode": "98101",
              "city": "Seattle",
              "state": "WA",
              "latitude": 47.6062,
              "longitude": -122.3321,
              "price": 850000,
              "dateSold": null,
              "homeType": "SINGLE_FAMILY",
              "homeStatus": "FOR_SALE",
              "livingArea": 1850,
              "bedrooms": 3,
              "bathrooms": 2,
              "taxAssessedValue": 620000,
              "zestimate": 845000,
              "rentZestimate": 3200
            }
          }
        }
      ],
      "mapResults": [...]
    },
    "searchList": {
      "totalPages": 12,
      "totalResultCount": 489
    }
  },
  "cat2": {
    "total": {"totalResultCount": 489}
  }
}
```

**Notes:**
- `wants.cat1` keys: `listResults`, `mapResults` — use `mapResults` for map view data only
- `wants.cat2`: `total` returns count only (fast)
- Start from a real Zillow search to get valid `regionId` and `mapBounds` from `__NEXT_DATA__`
- Requires browser-like headers; returns 403 without proper `User-Agent`
- Session cookies (`zguid`) improve reliability

---

### 2. Legacy Search (Partially Active)

**Endpoint:** `https://www.zillow.com/search/GetSearchPageState.htm`  
**Method:** `GET` or `PUT`  
**Version:** Legacy (older pattern)  
**Verification:** ⚠️ PARTIALLY VERIFIED

```bash
curl "https://www.zillow.com/search/GetSearchPageState.htm?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%22Seattle%2C+WA%22%7D&wants=%7B%22cat1%22%3A%5B%22listResults%22%5D%7D&requestId=2" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

> **Note:** Same response structure as `async-create-search-page-state`. The `.htm` suffix is legacy. May return 403 or redirect. Prefer `async-create-search-page-state`.

---

### 3. Autocomplete / Location Suggestions

**Endpoint:** `https://www.zillow.com/zg-graph`  
**Method:** `POST`  
**Version:** GraphQL (current)  
**Verification:** ✅ VERIFIED

**Headers:**
```
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
client-id: search-sub-app-client
```

**Request Body:**
```json
{
  "operationName": "GetAutocompleteResults",
  "variables": {
    "query": "Seattle, WA",
    "resultType": ["REGIONS", "FORSALE", "RENTALS", "SOLD"]
  },
  "query": "query GetAutocompleteResults($query: String!, $resultType: [AutocompleteResultType!]) { zgsAutoComplete(query: $query, resultType: $resultType) { results { display metaData { regionId regionType } } } }"
}
```

**`resultType` Values:**

| Value | Description |
|-------|-------------|
| `REGIONS` | City, zip, neighborhood, county |
| `FORSALE` | Active for-sale listings |
| `RENTALS` | Active rental listings |
| `SOLD` | Recently sold |

**Example Response (trimmed):**
```json
{
  "data": {
    "zgsAutoComplete": {
      "results": [
        {
          "display": "Seattle, WA",
          "metaData": {
            "regionId": 16163,
            "regionType": 6,
            "city": "Seattle",
            "state": "WA",
            "country": "United States",
            "lat": 47.6062,
            "lng": -122.3321
          }
        },
        {
          "display": "Seattle Hill-Silver Firs, WA",
          "metaData": {
            "regionId": 394855,
            "regionType": 8
          }
        }
      ]
    }
  }
}
```

**Region Types:**

| regionType | Description |
|------------|-------------|
| 6 | City |
| 7 | ZIP code |
| 8 | Neighborhood |
| 4 | County |
| 2 | State |

---

### 4. Region / Map Search (Map Results Only)

**Endpoint:** `https://www.zillow.com/async-create-search-page-state`  
**Method:** `PUT`  
**Verification:** ✅ VERIFIED

Use `wants.cat1: ["mapResults"]` only for lightweight map pin data:

```json
{
  "searchQueryState": {
    "mapBounds": {"west": -122.5, "east": -122.2, "south": 47.5, "north": 47.7},
    "filterState": {}
  },
  "wants": {"cat1": ["mapResults"]},
  "requestId": 3
}
```

Returns minimal data per listing: `zpid`, `latLong`, `price`, `statusType`.

---

## Property / Listing Endpoints

### 5. Property Detail Page (HTML + Embedded JSON)

**Endpoint:** `https://www.zillow.com/homedetails/{address-slug}/{zpid}_zpid/`  
**Method:** `GET`  
**Version:** Unversioned (Next.js)  
**Verification:** ✅ VERIFIED

Full property data is embedded in two script tags on the HTML page:

**Option 1 — Next.js data cache (`__NEXT_DATA__`):**
```python
import httpx, json
from parsel import Selector

resp = httpx.get(
    "https://www.zillow.com/homedetails/123-Main-St-Seattle-WA-98101/2077091803_zpid/",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
)
sel = Selector(resp.text)
data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
property_data = json.loads(
    data["props"]["pageProps"]["componentProps"]["gdpClientCache"]
)
prop = property_data[list(property_data)[0]]["property"]
```

**Option 2 — Apollo cache (`hdpApolloPreloadedData`):**
```python
data = json.loads(sel.css("script#hdpApolloPreloadedData::text").get())
cache = json.loads(json.loads(data)["apiCache"])
prop = next(v["property"] for k, v in cache.items() if "ForSale" in k)
```

**Key fields returned in `property`:**
```json
{
  "zpid": 2077091803,
  "streetAddress": "123 Main St",
  "city": "Seattle",
  "state": "WA",
  "zipcode": "98101",
  "price": 850000,
  "bedrooms": 3,
  "bathrooms": 2,
  "livingArea": 1850,
  "lotSize": 5200,
  "yearBuilt": 1998,
  "homeType": "SINGLE_FAMILY",
  "homeStatus": "FOR_SALE",
  "zestimate": 845000,
  "rentZestimate": 3200,
  "taxAssessedValue": 620000,
  "taxAnnualAmount": 7800,
  "description": "...",
  "photos": [...],
  "priceHistory": [...],
  "taxHistory": [...],
  "schools": [...],
  "nearbyHomes": [...],
  "resoFacts": {
    "hasGarage": true,
    "parkingSpaces": 2,
    "hasCooling": true,
    "hasHeating": true,
    "hasFireplace": false,
    "flooring": "Hardwood"
  },
  "listingAgent": {
    "displayName": "...",
    "profileUrl": "..."
  }
}
```

**Notes:**
- `zpid` is obtainable from search results (`hdpData.homeInfo.zpid`) or from the URL
- Requires browser-like headers and often valid session cookies
- Works for for-sale, rental, and sold properties

---

### 6. Property Detail via GraphQL

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST` (or `GET` with persisted query hash)  
**Version:** GraphQL (current)  
**Verification:** ✅ VERIFIED

Zillow uses persisted queries (sha256 hashes) internally. Direct POST with inline query also works.

**Headers:**
```
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
client-id: hdp-react-web-client
x-caller-id: hdp-react-web-client
```

**Operation: `ZestimateDeepDiveQuery`**
```json
{
  "operationName": "ZestimateDeepDiveQuery",
  "variables": {"zpid": 2077091803},
  "query": "query ZestimateDeepDiveQuery($zpid: ID!) { property(zpid: $zpid) { zpid zestimate zestimateMinus zestimatePlus valuationRange { low high } priceHistory { date price priceChangeRate event source pricePerSquareFoot } } }"
}
```

**Operation: `HomeValueChartDataQuery`**
```json
{
  "operationName": "HomeValueChartDataQuery",
  "variables": {"zpid": 2077091803, "useHVChartDataSource": true},
  "query": "query HomeValueChartDataQuery($zpid: ID!, $useHVChartDataSource: Boolean) { property(zpid: $zpid) { zpid zestimateHistory(useHVChartDataSource: $useHVChartDataSource) { t v } } }"
}
```

**Operation: `WalkTransitAndBikeScoreQuery`**
```json
{
  "operationName": "WalkTransitAndBikeScoreQuery",
  "variables": {"zpid": 2077091803},
  "query": "query WalkTransitAndBikeScoreQuery($zpid: ID!) { property(zpid: $zpid) { zpid walkScore { walkscore description logo_url ws_link } transitScore { transit_score description logo_url } bikeScore { bikescore description } } }"
}
```

**Other known GraphQL operations:**

| Operation | Description |
|-----------|-------------|
| `ZestimateDeepDiveQuery` | Zestimate value, range, history |
| `HomeValueChartDataQuery` | Home value time series |
| `WalkTransitAndBikeScoreQuery` | Walk/Transit/Bike scores |
| `PropertyClimateRiskQuery` | Flood, fire, wind, heat risk scores |
| `SimilarSalesQuery` | Comparable recently sold homes |
| `NearbyHomesQuery` | Nearby active listings |
| `SchoolsQuery` | School ratings and proximity |
| `HdpMortgageCalculatorQuery` | Mortgage calculator data |
| `ListingDetailsQuery` | Full listing detail |
| `RentEstimateQuery` | Rent Zestimate detail |

**Example Response — `ZestimateDeepDiveQuery` (trimmed):**
```json
{
  "data": {
    "property": {
      "zpid": "2077091803",
      "zestimate": 845000,
      "zestimateMinus": 760500,
      "zestimatePlus": 929500,
      "valuationRange": {"low": 760500, "high": 929500},
      "priceHistory": [
        {
          "date": "2024-03-15",
          "price": 850000,
          "priceChangeRate": 0.0,
          "event": "Listed for sale",
          "source": "MLS #12345",
          "pricePerSquareFoot": 459
        },
        {
          "date": "2021-08-10",
          "price": 720000,
          "priceChangeRate": null,
          "event": "Sold",
          "source": "MLS"
        }
      ]
    }
  }
}
```

---

### 7. Price History (via Property Page)

Price history is embedded within `priceHistory` array in both `__NEXT_DATA__` and graphql `ZestimateDeepDiveQuery`. No separate dedicated endpoint.

**Fields per entry:**
```json
{
  "date": "2024-03-15",
  "price": 850000,
  "priceChangeRate": -0.058,
  "event": "Price cut",
  "source": "MLS #12345",
  "pricePerSquareFoot": 459,
  "sellerAgent": {"displayName": "...", "profileUrl": "..."},
  "buyerAgent": null
}
```

---

### 8. Tax History (via Property Page)

Embedded in `taxHistory` array in `__NEXT_DATA__`:

```json
{
  "time": 2023,
  "taxPaid": 7800,
  "taxIncreaseRate": 0.04,
  "value": 620000,
  "valueIncreaseRate": 0.08
}
```

---

## Rental Endpoints

### 9. Rental Search

**Endpoint:** `https://www.zillow.com/async-create-search-page-state`  
**Method:** `PUT`  
**Verification:** ✅ VERIFIED

Use `isForRent: {value: true}` in `filterState`:

```json
{
  "searchQueryState": {
    "pagination": {},
    "usersSearchTerm": "Seattle, WA",
    "mapBounds": {"west": -122.5, "east": -122.2, "south": 47.5, "north": 47.7},
    "regionSelection": [{"regionId": 16163, "regionType": 6}],
    "filterState": {
      "isForRent": {"value": true},
      "isForSaleByAgent": {"value": false},
      "isForSaleByOwner": {"value": false},
      "isNewConstruction": {"value": false},
      "isComingSoon": {"value": false},
      "isAuction": {"value": false},
      "isForSaleForeclosure": {"value": false},
      "monthlyPayment": {"max": 3000},
      "beds": {"min": 1},
      "sortSelection": {"value": "days"}
    },
    "isMapVisible": true,
    "isListVisible": true
  },
  "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
  "requestId": 2
}
```

**Response** — same `cat1.searchResults.listResults` structure, with additional rental fields:
```json
{
  "zpid": "123456",
  "price": "$2,800/mo",
  "unformattedPrice": 2800,
  "statusType": "FOR_RENT",
  "hdpData": {
    "homeInfo": {
      "rentZestimate": 2750,
      "priceChangeDate": null,
      "unit": "Apt 4B"
    }
  }
}
```

---

### 10. Rental Building / Apartment Detail

**Endpoint:** `https://www.zillow.com/b/{building-slug}/{building-id}_bld/`  
**Method:** `GET` (HTML with embedded JSON)  
**Verification:** ⚠️ PARTIALLY VERIFIED

Building pages for multi-family/apartment complexes — same `__NEXT_DATA__` pattern applies. The `bld` suffix indicates building-level data.

---

### 11. Rent Zestimate

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Verification:** ⚠️ PARTIALLY VERIFIED

```json
{
  "operationName": "RentEstimateQuery",
  "variables": {"zpid": 2077091803},
  "query": "query RentEstimateQuery($zpid: ID!) { property(zpid: $zpid) { zpid rentZestimate rentZestimateMinus rentZestimatePlus } }"
}
```

---

### 12. Rental Costs and Fees (RCF)

**Endpoint:** `https://www.zillow.com/rentals/api/rcf/v1/rcf`  
**Method:** `POST`  
**Verification:** ✅ VERIFIED (live network capture)

A dedicated microservice returning transparent fee breakdowns for rental properties and apartment buildings. Powers the "Total monthly cost" breakdown shown on rental listings.

**Headers:**
```
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
```

**Request Body:**
```json
{
  "zpid": 2077091803,
  "listingId": "<listing-id>"
}
```

**Example Response (trimmed):**
```json
{
  "zpid": 2077091803,
  "monthlyRent": 2800,
  "fees": [
    {"name": "Parking", "amount": 150, "frequency": "monthly", "required": false},
    {"name": "Pet fee", "amount": 50, "frequency": "monthly", "required": false}
  ],
  "utilities": [
    {"name": "Water", "includedInRent": true},
    {"name": "Trash", "includedInRent": true},
    {"name": "Electricity", "includedInRent": false}
  ],
  "totalMonthlyMin": 2800,
  "totalMonthlyMax": 3000
}
```

> Also available via `graphql/` as `RentalCostAndFeesBuildingQuery` for building-level fee data.

---

## Market / Valuation Endpoints

### 12. Zestimate History (Home Value Over Time)

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Operation:** `HomeValueChartDataQuery`  
**Verification:** ✅ VERIFIED

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "HomeValueChartDataQuery",
    "variables": {"zpid": 2077091803, "useHVChartDataSource": true},
    "query": "query HomeValueChartDataQuery($zpid: ID!, $useHVChartDataSource: Boolean) { property(zpid: $zpid) { zpid zestimateHistory(useHVChartDataSource: $useHVChartDataSource) { t v } } }"
  }'
```

**Example Response:**
```json
{
  "data": {
    "property": {
      "zpid": "2077091803",
      "zestimateHistory": [
        {"t": 1704067200000, "v": 820000},
        {"t": 1706745600000, "v": 828000},
        {"t": 1709251200000, "v": 839000},
        {"t": 1711929600000, "v": 845000}
      ]
    }
  }
}
```

> `t` = Unix timestamp (ms), `v` = Zestimate value in USD

---

### 13. Climate Risk Scores

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Operation:** `PropertyClimateRiskQuery`  
**Verification:** ⚠️ PARTIALLY VERIFIED

```json
{
  "operationName": "PropertyClimateRiskQuery",
  "variables": {"zpid": 2077091803},
  "query": "query PropertyClimateRiskQuery($zpid: ID!) { property(zpid: $zpid) { zpid climateRiskData { floodFactor fireFactor heatFactor windFactor } } }"
}
```

---

### 14. Comparable Sales

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Operation:** `SimilarSalesQuery`  
**Verification:** ⚠️ PARTIALLY VERIFIED

```json
{
  "operationName": "SimilarSalesQuery",
  "variables": {"zpid": 2077091803},
  "query": "query SimilarSalesQuery($zpid: ID!) { property(zpid: $zpid) { zpid comparables { zpid address price dateSold livingArea bedrooms bathrooms } } }"
}
```

---

### 15. Walk / Transit / Bike Scores

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Operation:** `WalkTransitAndBikeScoreQuery`  
**Verification:** ✅ VERIFIED

**Example Response:**
```json
{
  "data": {
    "property": {
      "zpid": "2077091803",
      "walkScore": {
        "walkscore": 92,
        "description": "Walker's Paradise",
        "logo_url": "https://cdn.walkscore.com/...",
        "ws_link": "https://www.walkscore.com/..."
      },
      "transitScore": {
        "transit_score": 75,
        "description": "Excellent Transit"
      },
      "bikeScore": {
        "bikescore": 68,
        "description": "Bikeable"
      }
    }
  }
}
```

---

## GraphQL Endpoints

### GraphQL Entry Points

| Endpoint | Primary Use |
|----------|-------------|
| `www.zillow.com/graphql/` | Property detail, Zestimate, scores, history, comps |
| `www.zillow.com/zg-graph` | Autocomplete, region search, map data |

### Persisted Queries (GET)

Zillow internally uses persisted queries (APQ — Automatic Persisted Queries):

```
GET https://www.zillow.com/graphql/?operationName=ZestimateDeepDiveQuery&variables={"zpid":2077091803}&extensions={"persistedQuery":{"version":1,"sha256Hash":"<hash>"}}
```

The `sha256Hash` values change with Zillow deployments. Use POST with inline query for reliability.

### Known GraphQL Operations Summary

| Operation | Endpoint | Variables | Returns |
|-----------|----------|-----------|---------|
| `GetAutocompleteResults` | `/zg-graph` | `query`, `resultType[]` | Location suggestions |
| `CollectionOfRecentSearches` | `/zg-graph` | (session) | User's recent searches |
| `GetCarouselPhotos` | `/zg-graph` | `zpid` | Listing photo carousel URLs |
| `ForSalePriorityQuery` | `/graphql/` | `zpid` | Core property facts (price, beds, baths, Zestimate) |
| `ForSaleNonPriorityQuery` | `/graphql/` | `zpid` | Secondary property data (days on market, open house schedule) |
| `RichMediaWebHDPQuery` | `/graphql/` | `zpid` | High-res photos, virtual tour URLs |
| `ZestimateDeepDiveQuery` | `/graphql/` | `zpid` | Zestimate, value range, history |
| `HomeValueChartDataQuery` | `/graphql/` | `zpid`, `useHVChartDataSource` | Value time series |
| `WalkTransitAndBikeScoreQuery` | `/graphql/` | `zpid` | Walk/transit/bike scores |
| `OfferStrengthQuery` | `/graphql/` | `zpid` | Market competitiveness / offer strength |
| `GetContactButtonForProperty` | `/graphql/` | `zpid` | Contact agent lead form config |
| `GetBuyabilityFinancialProfile` | `/graphql/` | `zpid`, `downPayment`, `loanType` | Mortgage calculator payment breakdown |
| `LocalLegalProtectionQuery` | `/graphql/` | `zpid` | Fair housing + legal disclosure notices |
| `GetUserAccountQuery` | `/graphql/` | (session cookie) | Viewer auth state, saved homes |
| `PropertyClimateRiskQuery` | `/graphql/` | `zpid` | Flood, fire, heat, wind risk |
| `SimilarSalesQuery` | `/graphql/` | `zpid` | Comparable sold homes |
| `NearbyHomesQuery` | `/graphql/` | `zpid` | Nearby active listings |
| `SchoolsQuery` | `/graphql/` | `zpid` | Nearby school ratings |
| `HdpMortgageCalculatorQuery` | `/graphql/` | `zpid`, `price` | Monthly payment estimates |
| `ListingDetailsQuery` | `/graphql/` | `zpid` | Full listing detail |
| `RentEstimateQuery` | `/graphql/` | `zpid` | Rent Zestimate detail |
| `RentalCostAndFeesBuildingQuery` | `/graphql/` | `zpid` | Rental costs, fees, utilities |
| `BuildingPageOverviewQuery` | `/graphql/` | `zpid` | Unit availability, rent ranges, amenities |
| `AgentReviewQuery` | `/graphql/` | `encodedZuid` | Agent reviews, ratings, recent sales |

---

## Media / Asset Endpoints

### 16. Property Photos

Photos are served from `zillowstatic.com`. URLs are returned in the `photos` array within property detail data.

**Pattern:**
```
https://photos.zillowstatic.com/fp/{photo-id}-uncropped_scaled_within_{width}_{height}.webp
https://photos.zillowstatic.com/fp/{photo-id}-p_e.webp
```

**Size variants:**

| Suffix | Approx Size |
|--------|-------------|
| `uncropped_scaled_within_1536_1152` | 1536×1152 (full) |
| `scaled_within_800_600` | 800×600 (medium) |
| `cc_ft_384` | 384px (thumbnail) |
| `p_e` | Extra large |

**Example:**
```
https://photos.zillowstatic.com/fp/abc123def456-uncropped_scaled_within_1536_1152.webp
```

---

### 17. Map Tiles

**Pattern:**
```
https://maps.zillowstatic.com/...
https://www.zillowstatic.com/bedrock/app/maps/...
```

Used for map overlay tiles (heat maps, region overlays). Not easily consumable outside browser context.

---

## Additional Domains / Endpoint Families

| Domain | Purpose | Status |
|--------|---------|--------|
| `www.zillow.com` | Main site — search, detail, rentals | ✅ Current, primary |
| `www.zillow.com/graphql/` | GraphQL — property data, scores, estimates | ✅ Current, primary |
| `www.zillow.com/zg-graph` | GraphQL — autocomplete, recent searches | ✅ Current |
| `www.zillow.com/rentals/api/rcf/v1/` | Rental costs and fees microservice | ✅ Current |
| `www.zillow.com/search/GetSearchPageState.htm` | Legacy REST search | ⚠️ Legacy, partially active |
| `mortgageapi.zillow.com` | Mortgage rates — no auth required | ✅ Current |
| `photos.zillowstatic.com` | Property listing photos (CDN) | ✅ Current, static |
| `maps.zillowstatic.com` | Map tile CDN | ✅ Current, static |
| `www.zillowstatic.com` | Static assets (JS, CSS, images) | ✅ Current, static |
| `api.zillow.com` | Old official XML API (`GetDeepSearchResults`, `GetUpdatedPropertyDetails`) | ❌ **Deprecated/offline** |
| `api.bridgeinteractive.com` | Official partner API — Zestimate, public records data | 🔒 Requires approval, access-restricted |
| `zillow.com/rental-manager` | Rental syndication portal | 🔒 Requires account login |

### Legacy API Note (`api.zillow.com`)
The old `api.zillow.com` SOAP/XML API (`GetDeepSearchResults.htm`, `GetUpdatedPropertyDetails.htm`) is no longer publicly accessible. Requests return 404 or blank responses. All requests via `pyzillow` and similar old wrappers will fail.

### Bridge Interactive (`bridgeinteractive.com`)
The official, access-gated Zillow data API. Provides: public records, Zestimates, market data. Requires approval. Not reverse-engineered here.

---

## Endpoint Relationships

```
Autocomplete (zg-graph GetAutocompleteResults)
  → regionId + region metadata
  → used in searchQueryState.regionSelection[]

Recent Searches (zg-graph CollectionOfRecentSearches)
  → requires session cookie (zguid)
  → returns user's last N searched locations

Search (async-create-search-page-state)
  → returns zpid for each listing
  → returns hdpData.homeInfo (price, beds, baths, coords)

zpid
  → Property Detail Page (__NEXT_DATA__ / hdpApolloPreloadedData)
    → photos[], priceHistory[], taxHistory[], schools[], resoFacts
  → GraphQL /graphql/
    → ZestimateDeepDiveQuery → Zestimate, value range, history
    → HomeValueChartDataQuery → value time series
    → WalkTransitAndBikeScoreQuery → Walk/Transit/Bike scores
    → PropertyClimateRiskQuery → climate risk scores
    → SimilarSalesQuery → comparable homes
    → HdpMortgageCalculatorQuery → payment estimates
    → RentalCostAndFeesBuildingQuery → rent fees (rentals only)
  → /rentals/api/rcf/v1/rcf → rental costs + utilities breakdown

Mortgage rates (mortgageapi.zillow.com/getCurrentRates)
  → no auth, GET with params
  → returns current rates by loan program, credit score, loan amount

photos[] from property
  → zillowstatic.com image CDN
  → URL pattern with size variants
```

---

## Headers & Cookies

### Required Headers

```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept: */*
Accept-Language: en-US,en;q=0.9
Accept-Encoding: gzip, deflate, br
```

### Endpoint-Specific Headers

| Endpoint | Additional Headers |
|----------|--------------------|
| `async-create-search-page-state` | `Content-Type: application/json` |
| `www.zillow.com/graphql/` | `client-id: hdp-react-web-client`, `x-caller-id: hdp-react-web-client` |
| `www.zillow.com/zg-graph` | `client-id: search-sub-app-client` |

### Key Cookies

| Cookie | Description |
|--------|-------------|
| `zguid` | Zillow user GUID — set on first page load, improves reliability |
| `JSESSIONID` | Java session ID |
| `AWSALB` | AWS load balancer affinity cookie |
| `search` | Stores local search context |
| `zjs_anonymous_id` | Analytics anonymous ID |

> **Getting cookies:** Load `https://www.zillow.com` in a browser once, copy cookies from DevTools → Application → Cookies. Add as `-H "Cookie: zguid=...; JSESSIONID=..."` to curl.

---

## Parameters Reference

### `searchQueryState` Fields

| Field | Type | Description |
|-------|------|-------------|
| `pagination` | object | `{}` = page 1, `{currentPage: N}` = page N |
| `usersSearchTerm` | string | Human-readable search text |
| `mapBounds` | object | `{west, east, south, north}` bounding box |
| `regionSelection` | array | `[{regionId, regionType}]` from autocomplete |
| `filterState` | object | All filter criteria |
| `isMapVisible` | bool | Include map results |
| `isListVisible` | bool | Include list results |

### `wants` Options

| Key | Values | Description |
|-----|--------|-------------|
| `cat1` | `listResults`, `mapResults` | Main listing data |
| `cat2` | `total` | Total result count only |

### Common Response Fields

| Field | Description |
|-------|-------------|
| `zpid` | Zillow Property ID (primary key) |
| `detailUrl` | Relative URL to property detail page |
| `statusType` | `FOR_SALE`, `FOR_RENT`, `RECENTLY_SOLD` |
| `price` | Formatted price string |
| `unformattedPrice` | Numeric price |
| `hdpData.homeInfo` | Core property facts |
| `latLong` | `{latitude, longitude}` |
| `imgSrc` | Primary listing photo URL |
| `zestimate` | Zillow estimated value |
| `rentZestimate` | Zillow estimated monthly rent |

---

## Zillow Service (Django Implementation)

This repository includes a Django REST API that wraps Zillow's endpoints.

### Features

- Property search (for-sale, rental, recently-sold)
- Property detail retrieval via ZPID
- Zestimate and home value history
- Walk/Transit/Bike score lookup
- Autocomplete / location suggestions
- Background ingestion (Celery)
- Docker support
- OpenAPI documentation via drf-spectacular

### Quick Start

```bash
cd zillow_service
docker compose up --build

# API: http://localhost:8001
# Docs: http://localhost:8001/api/docs/
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check |
| `/api/v1/search/` | POST | Property search |
| `/api/v1/properties/{zpid}/` | GET | Property detail |
| `/api/v1/properties/{zpid}/zestimate/` | GET | Zestimate + history |
| `/api/v1/properties/{zpid}/scores/` | GET | Walk/Transit/Bike scores |
| `/api/v1/autocomplete/` | GET | Location suggestions (`?q=Seattle`) |
| `/api/v1/ingest/property/` | POST | Ingest property by ZPID |

### Zillow Client Methods

| Category | Methods |
|----------|---------|
| Search | `search_for_sale()`, `search_for_rent()`, `search_recently_sold()` |
| Property | `get_property_detail()`, `get_property_from_page()` |
| Estimates | `get_zestimate()`, `get_zestimate_history()`, `get_rent_zestimate()` |
| Scores | `get_walk_bike_transit_scores()`, `get_climate_risk()` |
| Search Tools | `autocomplete()`, `get_region_id()` |
| Comps | `get_comparable_sales()`, `get_nearby_homes()` |

See [zillow_service/README.md](zillow_service/README.md) for full service documentation.

---

## Notes / Quirks

- **403 responses:** Almost always a header/cookie issue. Add a full browser `User-Agent` and a `zguid` cookie.
- **Rate limiting:** Zillow actively rate-limits and blocks IPs. Use delays of 2–5 seconds between requests.
- **Result cap:** Search returns a maximum of ~500 results per query region. Use smaller `mapBounds` areas to paginate through large markets.
- **ZPID in URLs:** Format is `https://www.zillow.com/homedetails/{slug}/{zpid}_zpid/`
- **GraphQL schema changes:** Zillow updates its GraphQL schema frequently. Monitor for `null` fields in responses.
- **`__NEXT_DATA__` vs Apollo cache:** Newer property pages use Apollo cache (`hdpApolloPreloadedData`). Try both.
- **Rentals vs For-Sale:** Same endpoint, different `filterState`. Rental prices are per-month.
- **RCF endpoint:** `/rentals/api/rcf/v1/rcf` returns detailed fee/utility breakdowns for rentals — useful for "total monthly cost" displays.
- **Mortgage rates:** `mortgageapi.zillow.com/getCurrentRates` works without auth or cookies — great for a standalone rate widget.
- **`api.zillow.com` is dead:** The old official XML API no longer works. Do not use `pyzillow` or similar old wrappers.
- **No versioned paths:** Zillow does not use `/v1/` `/v2/` `/v3/` in public-facing URLs.

---

## Contributing

Found a new endpoint? Please open an issue or PR!

## License

MIT License — See LICENSE file

---

*Last Updated: March 2026 · 17+ endpoints · 3 API domains · GraphQL + REST*
