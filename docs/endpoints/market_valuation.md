# Zillow API — Market & Valuation Endpoints

> Zestimate, home value history, comparable sales, and location scores.

---

## 1. Zestimate (Current Value)

Returned in property data as `zestimate` field. Also available via GraphQL.

**Embedded in property page** (see [property.md](property.md)):
```json
{"zestimate": 845000, "zestimateMinus": 760500, "zestimatePlus": 929500}
```

**Via GraphQL:**

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "ZestimateDeepDiveQuery",
    "variables": {"zpid": 2077091803},
    "query": "query ZestimateDeepDiveQuery($zpid: ID!) { property(zpid: $zpid) { zpid zestimate zestimateMinus zestimatePlus valuationRange { low high } priceHistory { date price event source } } }"
  }'
```

**Verification:** ✅ VERIFIED

---

## 2. Zestimate History (Time Series)

**Endpoint:** `https://www.zillow.com/graphql/`  
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

Response: array of `{t: timestamp_ms, v: usd_value}` — typically monthly going back several years.

---

## 3. Walk / Transit / Bike Scores

**Endpoint:** `https://www.zillow.com/graphql/`  
**Operation:** `WalkTransitAndBikeScoreQuery`  
**Verification:** ✅ VERIFIED

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "WalkTransitAndBikeScoreQuery",
    "variables": {"zpid": 2077091803},
    "query": "query WalkTransitAndBikeScoreQuery($zpid: ID!) { property(zpid: $zpid) { zpid walkScore { walkscore description ws_link } transitScore { transit_score description } bikeScore { bikescore description } } }"
  }'
```

Score range: 0–100. Higher = more walkable/bikeable/transit-accessible.

---

## 4. Climate Risk Scores

**Endpoint:** `https://www.zillow.com/graphql/`  
**Operation:** `PropertyClimateRiskQuery`  
**Verification:** ⚠️ PARTIALLY VERIFIED

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

Risk scores typically on a 1–10 scale (10 = highest risk).

---

## 5. Comparable Sales

**Endpoint:** `https://www.zillow.com/graphql/`  
**Operation:** `SimilarSalesQuery`  
**Verification:** ⚠️ PARTIALLY VERIFIED

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "SimilarSalesQuery",
    "variables": {"zpid": 2077091803},
    "query": "query SimilarSalesQuery($zpid: ID!) { property(zpid: $zpid) { zpid comparables { zpid address price dateSold livingArea bedrooms bathrooms } } }"
  }'
```

---

## 6. School Data

**Endpoint:** `https://www.zillow.com/graphql/`  
**Operation:** `SchoolsQuery`  
**Verification:** ⚠️ PARTIALLY VERIFIED

Also available in `schools[]` array embedded in property page `__NEXT_DATA__`.

```json
{
  "operationName": "SchoolsQuery",
  "variables": {"zpid": 2077091803},
  "query": "query SchoolsQuery($zpid: ID!) { property(zpid: $zpid) { zpid schools { name rating distance type grades link } } }"
}
```

---

## Notes

- Zestimate is Zillow's proprietary AVM (Automated Valuation Model)
- Walk/Transit/Bike scores are sourced from Walk Score (walkscore.com)
- GraphQL field names may change — monitor for `null` fields
- `ZestimateDeepDiveQuery` combines current zestimate + valuation range + price history in one call
