# Zillow API — Rental Endpoints

> Search for rental properties and retrieve rental data.

---

## 1. Rental Search

**Endpoint:** `https://www.zillow.com/async-create-search-page-state`  
**Method:** `PUT`  
**Verification:** ✅ VERIFIED

```bash
curl -X PUT "https://www.zillow.com/async-create-search-page-state" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -d '{
    "searchQueryState": {
      "pagination": {},
      "usersSearchTerm": "Denver, CO",
      "mapBounds": {"west": -105.1, "east": -104.8, "south": 39.6, "north": 39.9},
      "regionSelection": [{"regionId": 12447, "regionType": 6}],
      "filterState": {
        "isForRent": {"value": true},
        "isForSaleByAgent": {"value": false},
        "isForSaleByOwner": {"value": false},
        "isNewConstruction": {"value": false},
        "isComingSoon": {"value": false},
        "isAuction": {"value": false},
        "isForSaleForeclosure": {"value": false},
        "beds": {"min": 1},
        "monthlyPayment": {"max": 3000},
        "sortSelection": {"value": "days"}
      }
    },
    "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
    "requestId": 2
  }'
```

### Rental-Specific Response Fields

| Field | Description |
|-------|-------------|
| `price` | Monthly rent (formatted, e.g. `"$2,800/mo"`) |
| `unformattedPrice` | Monthly rent (numeric) |
| `statusType` | `FOR_RENT` |
| `hdpData.homeInfo.rentZestimate` | Estimated rent from Zillow |
| `hdpData.homeInfo.unit` | Unit number (apartments) |

### Rental `filterState` Options

| Key | Example | Description |
|-----|---------|-------------|
| `isForRent` | `{"value": true}` | Required for rentals |
| `isApartment` | `{"value": true}` | Apartments only |
| `isAllHomes` | `{"value": true}` | All home types |
| `beds.min` | `{"value": 1}` | Minimum bedrooms |
| `baths.min` | `{"value": 1}` | Minimum bathrooms |
| `monthlyPayment.min` | `{"value": 1000}` | Min monthly rent |
| `monthlyPayment.max` | `{"value": 3000}` | Max monthly rent |
| `isLaundryFacilities` | `{"value": true}` | Has laundry |
| `isPetsAllowed` | `{"value": true}` | Pets allowed |
| `isInUnitWasherDryer` | `{"value": true}` | In-unit W/D |

---

## 2. Rent Zestimate via GraphQL

**Endpoint:** `https://www.zillow.com/graphql/`  
**Method:** `POST`  
**Verification:** ⚠️ PARTIALLY VERIFIED

```bash
curl -X POST "https://www.zillow.com/graphql/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "client-id: hdp-react-web-client" \
  -d '{
    "operationName": "RentEstimateQuery",
    "variables": {"zpid": 2077091803},
    "query": "query RentEstimateQuery($zpid: ID!) { property(zpid: $zpid) { zpid rentZestimate rentZestimateMinus rentZestimatePlus } }"
  }'
```

---

## 3. Building / Apartment Detail

**Endpoint:** `https://www.zillow.com/b/{building-slug}/{building-id}_bld/`  
**Method:** `GET` (HTML with embedded JSON)  
**Verification:** ⚠️ PARTIALLY VERIFIED

Same `__NEXT_DATA__` extraction pattern as property pages. Building pages (`_bld`) contain unit listings, amenities, and building-level data.

```python
# Navigate to a building page found via rental search
resp = httpx.get(
    "https://www.zillow.com/b/the-clement-seattle-wa/5YGKWY/",
    headers={"User-Agent": "Mozilla/5.0 ..."}
)
sel = Selector(resp.text)
data = json.loads(sel.css("script#__NEXT_DATA__::text").get())
```

---

## Notes

- Rental prices are per-month; `price` field will include `/mo` suffix
- Use `monthlyPayment` for rent filtering (not `price` like for-sale)
- Building pages for apartment complexes use `_bld` suffix in URL (not `_zpid`)
- `rentZestimate` is also available in for-sale property details
