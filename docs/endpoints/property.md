# Zillow API — Property & Listing Endpoints

> Retrieve full property data by ZPID.

---

## Getting a ZPID

1. From search results: `cat1.searchResults.listResults[N].zpid`
2. From URL: `https://www.zillow.com/homedetails/{slug}/{zpid}_zpid/`
3. From autocomplete then search

---

## 1. Property Detail Page (HTML + Embedded JSON)

**Endpoint:** `https://www.zillow.com/homedetails/{slug}/{zpid}_zpid/`  
**Method:** `GET`  
**Verification:** ✅ VERIFIED

Data is embedded in the HTML in two possible locations:

### Option A — Next.js (`__NEXT_DATA__`)

```python
import httpx, json
from parsel import Selector

resp = httpx.get(
    "https://www.zillow.com/homedetails/123-Main-St-Seattle-WA-98101/2077091803_zpid/",
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
)
sel = Selector(resp.text)
raw = sel.css("script#__NEXT_DATA__::text").get()
data = json.loads(raw)
cache = json.loads(data["props"]["pageProps"]["componentProps"]["gdpClientCache"])
prop = cache[list(cache)[0]]["property"]
```

### Option B — Apollo Cache (`hdpApolloPreloadedData`)

```python
raw = sel.css("script#hdpApolloPreloadedData::text").get()
data = json.loads(json.loads(raw)["apiCache"])
prop = next(v["property"] for k, v in data.items() if "ForSale" in k or "ForRent" in k)
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `zpid` | int | Zillow Property ID |
| `streetAddress` | string | Street address |
| `city` | string | City |
| `state` | string | State abbreviation |
| `zipcode` | string | ZIP code |
| `price` | int | Listing price |
| `bedrooms` | int | Bedroom count |
| `bathrooms` | float | Bathroom count |
| `livingArea` | int | Square footage |
| `lotSize` | int | Lot size (sq ft) |
| `yearBuilt` | int | Year built |
| `homeType` | string | `SINGLE_FAMILY`, `CONDO`, `TOWNHOUSE`, `MULTI_FAMILY` |
| `homeStatus` | string | `FOR_SALE`, `FOR_RENT`, `RECENTLY_SOLD` |
| `daysOnZillow` | int | Days on market |
| `zestimate` | int | Zestimate value |
| `rentZestimate` | int | Monthly rent estimate |
| `taxAssessedValue` | int | Tax assessed value |
| `taxAnnualAmount` | int | Annual tax amount |
| `description` | string | Listing description |
| `photos` | array | Photo objects with URLs |
| `priceHistory` | array | Price event history |
| `taxHistory` | array | Annual tax history |
| `schools` | array | Nearby school data |
| `resoFacts` | object | Home features (garage, cooling, etc.) |
| `listingAgent` | object | Agent name and profile URL |

---

## 2. Property Detail via GraphQL

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Verification:** ✅ VERIFIED

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "ZestimateDeepDiveQuery",
    "variables": {"zpid": 2077091803},
    "query": "query ZestimateDeepDiveQuery($zpid: ID!) { property(zpid: $zpid) { zpid zestimate zestimateMinus zestimatePlus valuationRange { low high } priceHistory { date price event source pricePerSquareFoot } } }"
  }'
```

---

## 3. Price History

Embedded in `priceHistory[]` array from both `__NEXT_DATA__` and `ZestimateDeepDiveQuery`.

| Field | Description |
|-------|-------------|
| `date` | ISO date string |
| `price` | Price in USD |
| `priceChangeRate` | Rate of change (negative = price cut) |
| `event` | `Listed for sale`, `Price cut`, `Sold`, `Relisted` |
| `source` | MLS number |
| `pricePerSquareFoot` | $/sqft at that price |

---

## 4. Tax History

Embedded in `taxHistory[]` array from `__NEXT_DATA__`.

| Field | Description |
|-------|-------------|
| `time` | Year (int) |
| `taxPaid` | Annual tax paid |
| `taxIncreaseRate` | YoY tax increase rate |
| `value` | Assessed value |
| `valueIncreaseRate` | YoY assessment increase |

---

## 5. Home Facts / Features (`resoFacts`)

| Field | Description |
|-------|-------------|
| `hasGarage` | boolean |
| `garageParkingCapacity` | number of spaces |
| `hasCooling` | boolean |
| `cooling` | type string |
| `hasHeating` | boolean |
| `heating` | type string |
| `hasFireplace` | boolean |
| `flooring` | floor type string |
| `appliances` | comma-separated list |
| `parkingFeatures` | string |
| `basement` | has basement / type |
| `roofType` | roof material |
| `architecturalStyle` | style string |
| `stories` | number of floors |
| `lotFeatures` | lot description string |

---

## 6. Photos

Returned as `photos[]` in property detail. Each photo has URLs at multiple sizes.

```json
{
  "caption": "",
  "mixedSources": {
    "jpeg": [
      {"url": "https://photos.zillowstatic.com/fp/abc123-cc_ft_384.webp", "width": 384},
      {"url": "https://photos.zillowstatic.com/fp/abc123-uncropped_scaled_within_1536_1152.webp", "width": 1536}
    ]
  }
}
```

Direct URL pattern:
```
https://photos.zillowstatic.com/fp/{photo-id}-{size-variant}.webp
```

Size variants: `cc_ft_384`, `scaled_within_800_600`, `uncropped_scaled_within_1536_1152`, `p_e`

---

## 7. Agent Profile Page

**Endpoint:** `https://www.zillow.com/profile/{AgentName}/`  
**Method:** `GET` (HTML with embedded JSON)  
**Verification:** ✅ VERIFIED

Agent profile pages embed full agent data in `__NEXT_DATA__`. The `encodedZuid` extracted here is required for `AgentReviewQuery` via GraphQL.

```python
import httpx, json
from parsel import Selector

resp = httpx.get(
    "https://www.zillow.com/profile/JohnSmithRealtor/",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
)
data = json.loads(Selector(resp.text).css("script#__NEXT_DATA__::text").get())
agent = data["props"]["pageProps"]["agentProfile"]
encoded_zuid = agent["encodedZuid"]
```

**Key fields in `agentProfile`:**

| Field | Description |
|-------|-------------|
| `encodedZuid` | Unique agent ID (use with `AgentReviewQuery`) |
| `displayName` | Agent full name |
| `profilePhotoSrc` | Profile photo URL |
| `businessName` | Brokerage name |
| `phoneNumber` | Contact phone |
| `reviewsSummary.averageRating` | Star rating (0–5) |
| `reviewsSummary.reviewCount` | Number of reviews |
| `profileStats.totalSales` | Total sales count |
| `currentUrl` | Canonical profile URL |

> Use `encodedZuid` with `AgentReviewQuery` on `www.zillow.com/graphql/` to fetch reviews and recent sales via API.

