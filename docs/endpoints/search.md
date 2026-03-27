# Zillow API — Search & Discovery Endpoints

> Search for properties by location, filter, price range, and type.

---

## Base URL

```
https://www.zillow.com/async-create-search-page-state  (PUT)
```

---

## 1. Home Search (For Sale)

**Endpoint:** `https://www.zillow.com/async-create-search-page-state`  
**Method:** `PUT`  
**Verification:** ✅ VERIFIED

```bash
curl -X PUT "https://www.zillow.com/async-create-search-page-state" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: */*" \
  -d '{
    "searchQueryState": {
      "pagination": {},
      "usersSearchTerm": "Austin, TX",
      "mapBounds": {"west": -97.92, "east": -97.56, "south": 30.17, "north": 30.52},
      "regionSelection": [{"regionId": 28598, "regionType": 6}],
      "filterState": {"sortSelection": {"value": "globalrelevanceex"}},
      "isMapVisible": true,
      "isListVisible": true
    },
    "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
    "requestId": 2,
    "isDebugRequest": false
  }'
```

### `filterState` Keys

| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `price.min` | object | `{"value": 200000}` | Minimum price |
| `price.max` | object | `{"value": 800000}` | Maximum price |
| `beds.min` | object | `{"value": 2}` | Min bedrooms |
| `baths.min` | object | `{"value": 1}` | Min bathrooms |
| `sqft.min` | object | `{"value": 1000}` | Min sq ft |
| `sqft.max` | object | `{"value": 3000}` | Max sq ft |
| `isForRent` | object | `{"value": true}` | Rental only |
| `isForSaleByAgent` | object | `{"value": true}` | Agent listings |
| `isForSaleByOwner` | object | `{"value": true}` | FSBO only |
| `isNewConstruction` | object | `{"value": true}` | New construction |
| `isRecentlySold` | object | `{"value": true}` | Recently sold |
| `isComingSoon` | object | `{"value": true}` | Coming soon |
| `isAuction` | object | `{"value": false}` | Exclude auctions |
| `hasPool` | object | `{"value": true}` | Has pool |
| `sortSelection` | object | `{"value": "days"}` | Sort order |

### Sort Values

| Value | Description |
|-------|-------------|
| `globalrelevanceex` | Best match (default) |
| `days` | Newest listings |
| `priceDesc` | Price high → low |
| `priceAsc` | Price low → high |
| `sqftDesc` | Largest |
| `beds` | Most bedrooms |

### Pagination

```json
"pagination": {"currentPage": 2}
```

> ~40 results/page, max ~500 per region. Use tighter `mapBounds` to get all listings.

---

## 2. Rental Search

Same endpoint, `isForRent: {value: true}` in `filterState`:

```bash
curl -X PUT "https://www.zillow.com/async-create-search-page-state" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -d '{
    "searchQueryState": {
      "pagination": {},
      "usersSearchTerm": "Austin, TX",
      "mapBounds": {"west": -97.92, "east": -97.56, "south": 30.17, "north": 30.52},
      "filterState": {
        "isForRent": {"value": true},
        "isForSaleByAgent": {"value": false},
        "isForSaleByOwner": {"value": false},
        "isNewConstruction": {"value": false},
        "isComingSoon": {"value": false},
        "isAuction": {"value": false},
        "isForSaleForeclosure": {"value": false},
        "beds": {"min": 1},
        "monthlyPayment": {"max": 3500},
        "sortSelection": {"value": "days"}
      }
    },
    "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
    "requestId": 2
  }'
```

---

## 3. Recently Sold

```json
"filterState": {
  "isRecentlySold": {"value": true},
  "isForSaleByAgent": {"value": false},
  "isForSaleByOwner": {"value": false},
  "daysOnZillow": {"max": 90}
}
```

---

## 4. Map-Only Search (Lightweight)

Use `wants.cat1: ["mapResults"]` for map pin data only:

```json
{
  "searchQueryState": {
    "mapBounds": {"west": -97.92, "east": -97.56, "south": 30.17, "north": 30.52},
    "filterState": {}
  },
  "wants": {"cat1": ["mapResults"]},
  "requestId": 3
}
```

Returns: `zpid`, `latLong`, `price`, `statusType` per listing.

---

## 5. Autocomplete

**Endpoint:** `https://www.zillow.com/zg-graph`  
**Method:** `POST`  
**Verification:** ✅ VERIFIED

```bash
curl -X POST "https://www.zillow.com/zg-graph" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: search-sub-app-client" \
  -d '{
    "operationName": "GetAutocompleteResults",
    "variables": {
      "query": "Austin, TX",
      "resultType": ["REGIONS", "FORSALE", "RENTALS", "SOLD"]
    },
    "query": "query GetAutocompleteResults($query: String!, $resultType: [AutocompleteResultType!]) { zgsAutoComplete(query: $query, resultType: $resultType) { results { display metaData { regionId regionType } } } }"
  }'
```

### Region Types

| regionType | Description |
|------------|-------------|
| 2 | State |
| 4 | County |
| 6 | City |
| 7 | ZIP code |
| 8 | Neighborhood |

---

## 6. Legacy Search (Partially Active)

**Endpoint:** `https://www.zillow.com/search/GetSearchPageState.htm`  
**Method:** `GET`  
**Verification:** ⚠️ PARTIALLY VERIFIED

```bash
# GET with URL-encoded searchQueryState
curl "https://www.zillow.com/search/GetSearchPageState.htm?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%22Austin%2C+TX%22%7D&wants=%7B%22cat1%22%3A%5B%22listResults%22%5D%7D&requestId=2" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

> Same response structure as `async-create-search-page-state`. Legacy `.htm` suffix. May 403. Use `async-create-search-page-state` instead.
