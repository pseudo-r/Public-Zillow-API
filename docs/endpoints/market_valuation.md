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

---

## 7. Current Mortgage Rates

**Endpoint:** `https://mortgageapi.zillow.com/getCurrentRates`  
**Method:** `GET`  
**Auth:** None required  
**Verification:** ✅ VERIFIED (live network capture)

Returns current mortgage rates by loan program, loan amount, and credit score.

```bash
curl "https://mortgageapi.zillow.com/getCurrentRates?partnerId=RD-ZZRCT81&rateQuery.program=Fixed30Year&rateQuery.loanAmountBucket=bucket400To500k&rateQuery.creditScoreBucket=bucket740to759" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

### Query Parameters

| Parameter | Description | Example Values |
|-----------|-------------|---------------|
| `partnerId` | Zillow partner ID | `RD-ZZRCT81` (public default) |
| `rateQuery.program` | Loan type / term | See table below |
| `rateQuery.loanAmountBucket` | Loan amount range | See table below |
| `rateQuery.creditScoreBucket` | Credit score range | See table below |
| `rateQuery.state` | State code filter | `WA`, `CA`, `TX` |

### `rateQuery.program` Values

| Value | Description |
|-------|-------------|
| `Fixed30Year` | 30-year fixed (most common) |
| `Fixed20Year` | 20-year fixed |
| `Fixed15Year` | 15-year fixed |
| `Fixed10Year` | 10-year fixed |
| `ARM5` | 5/1 adjustable rate |
| `ARM7` | 7/1 adjustable rate |
| `ARM10` | 10/1 adjustable rate |

### `rateQuery.loanAmountBucket` Values

| Value | Loan Range |
|-------|-----------|
| `bucket0To100k` | $0–$100k |
| `bucket100To200k` | $100k–$200k |
| `bucket200To400k` | $200k–$400k |
| `bucket400To500k` | $400k–$500k |
| `bucket500kPlus` | $500k+ |

### `rateQuery.creditScoreBucket` Values

| Value | Credit Score Range |
|-------|-------------------|
| `bucket620to639` | 620–639 |
| `bucket640to659` | 640–659 |
| `bucket660to679` | 660–679 |
| `bucket680to699` | 680–699 |
| `bucket700to719` | 700–719 |
| `bucket720to739` | 720–739 |
| `bucket740to759` | 740–759 |
| `bucket760Plus` | 760+ |

**Example Response (trimmed):**
```json
{
  "rates": [
    {
      "lenderName": "Rocket Mortgage",
      "rate": 6.875,
      "apr": 7.103,
      "monthlyPayment": 2303,
      "fees": 1200,
      "points": 0.0,
      "program": "Fixed30Year",
      "nmlsId": "3030"
    },
    {
      "lenderName": "Better Mortgage",
      "rate": 6.750,
      "apr": 6.921,
      "monthlyPayment": 2271,
      "fees": 0,
      "points": 0.5,
      "program": "Fixed30Year"
    }
  ],
  "nationalAverage": {
    "rate": 6.92,
    "apr": 7.04
  }
}
```

> **No auth or cookies required** — this is one of the few Zillow endpoints that works cleanly with just a browser-like `User-Agent`.

