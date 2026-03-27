# Zillow API — GraphQL Endpoints

> Zillow uses two GraphQL endpoints for different data families.

---

## Endpoint Overview

| Endpoint | Use |
|----------|-----|
| `https://www.zillow.com/graphql/` | Property detail, Zestimate, scores, history, comps |
| `https://www.zillow.com/zg-graph` | Autocomplete, region metadata |

Both accept POST with `{operationName, variables, query}`.

---

## Headers

```
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
client-id: hdp-react-web-client           # for /graphql/
client-id: search-sub-app-client          # for /zg-graph
x-caller-id: hdp-react-web-client         # for /graphql/ (optional but improves reliability)
```

---

## Known Operations — `/graphql/`

| Operation | Variables | Returns |
|-----------|-----------|---------|
| `ZestimateDeepDiveQuery` | `zpid` | Zestimate, value range, price history |
| `HomeValueChartDataQuery` | `zpid`, `useHVChartDataSource` | Value time series |
| `WalkTransitAndBikeScoreQuery` | `zpid` | Walk/transit/bike scores |
| `PropertyClimateRiskQuery` | `zpid` | Flood, fire, heat, wind risk |
| `SimilarSalesQuery` | `zpid` | Comparable recently sold |
| `NearbyHomesQuery` | `zpid` | Nearby active listings |
| `SchoolsQuery` | `zpid` | Nearby school ratings |
| `HdpMortgageCalculatorQuery` | `zpid`, `price` | Monthly payment estimate |
| `ListingDetailsQuery` | `zpid` | Full listing detail |
| `RentEstimateQuery` | `zpid` | Rent Zestimate detail |
| `RentalCostAndFeesBuildingQuery` | `zpid` | Rental costs, fees, utilities breakdown |

---

## Known Operations — `/zg-graph`

| Operation | Variables | Returns |
|-----------|-----------|---------|
| `GetAutocompleteResults` | `query`, `resultType[]` | Location/listing suggestions |
| `CollectionOfRecentSearches` | (session cookie) | User's recent search history |

---

## Operation Examples

### `ZestimateDeepDiveQuery`

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "ZestimateDeepDiveQuery",
    "variables": {"zpid": 2077091803},
    "query": "query ZestimateDeepDiveQuery($zpid: ID!) { property(zpid: $zpid) { zpid zestimate zestimateMinus zestimatePlus valuationRange { low high } priceHistory { date price priceChangeRate event source pricePerSquareFoot } } }"
  }'
```

### `HomeValueChartDataQuery`

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

### `WalkTransitAndBikeScoreQuery`

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "WalkTransitAndBikeScoreQuery",
    "variables": {"zpid": 2077091803},
    "query": "query WalkTransitAndBikeScoreQuery($zpid: ID!) { property(zpid: $zpid) { zpid walkScore { walkscore description logo_url ws_link } transitScore { transit_score description } bikeScore { bikescore description } } }"
  }'
```

### `PropertyClimateRiskQuery`

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "PropertyClimateRiskQuery",
    "variables": {"zpid": 2077091803},
    "query": "query PropertyClimateRiskQuery($zpid: ID!) { property(zpid: $zpid) { zpid climateRiskData { floodFactor fireFactor heatFactor windFactor } } }"
  }'
```

### `GetAutocompleteResults` (via `/zg-graph`)

```bash
curl -X POST "https://www.zillow.com/zg-graph" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: search-sub-app-client" \
  -d '{
    "operationName": "GetAutocompleteResults",
    "variables": {
      "query": "Miami, FL",
      "resultType": ["REGIONS", "FORSALE", "RENTALS", "SOLD"]
    },
    "query": "query GetAutocompleteResults($query: String!, $resultType: [AutocompleteResultType!]) { zgsAutoComplete(query: $query, resultType: $resultType) { results { display resultType metaData { regionId regionType city state lat lng } } } }"
  }'
```

---

## Persisted Queries (GET)

Zillow internally uses APQ (Automatic Persisted Queries):

```
GET https://www.zillow.com/graphql/?operationName=ZestimateDeepDiveQuery&variables={"zpid":2077091803}&extensions={"persistedQuery":{"version":1,"sha256Hash":"<hash>"}}
```

> `sha256Hash` changes with each Zillow deployment. Use POST with inline query for reliable access.

---

## Notes

- GraphQL schema evolves frequently — some field names may return `null` without warning
- Zillow uses `ID!` type for `zpid` (pass as integer in `variables`, e.g. `{"zpid": 2077091803}`)
- Both endpoints accept CORS from browser context; direct server-side calls need proper headers
- `client-id` header is required for many operations to return non-null results
