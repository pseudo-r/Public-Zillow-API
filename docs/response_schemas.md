# Zillow API — Response Schemas

Example JSON response structures for key endpoints.

---

## Search Response (`async-create-search-page-state`)

```json
{
  "cat1": {
    "searchResults": {
      "listResults": [
        {
          "zpid": "2077091803",
          "id": "2077091803",
          "providerListingId": null,
          "imgSrc": "https://photos.zillowstatic.com/fp/abc123-uncropped_scaled_within_1536_1152.webp",
          "hasImage": true,
          "detailUrl": "/homedetails/123-Main-St-Seattle-WA-98101/2077091803_zpid/",
          "statusType": "FOR_SALE",
          "statusText": "House for sale",
          "countryCurrency": "USD",
          "price": "$850,000",
          "unformattedPrice": 850000,
          "address": "123 Main St, Seattle, WA 98101",
          "addressStreet": "123 Main St",
          "addressCity": "Seattle",
          "addressState": "WA",
          "addressZip": "98101",
          "beds": 3,
          "baths": 2,
          "area": 1850,
          "latLong": {"latitude": 47.6062, "longitude": -122.3321},
          "isZillowOwned": false,
          "isFeatured": false,
          "isShowcaseListing": false,
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
              "bathrooms": 2.0,
              "bedrooms": 3,
              "livingArea": 1850,
              "homeType": "SINGLE_FAMILY",
              "homeStatus": "FOR_SALE",
              "daysOnZillow": 12,
              "isFeatured": false,
              "shouldHighlight": false,
              "taxAssessedValue": 620000,
              "lotAreaValue": 5200.0,
              "lotAreaUnit": "sqft",
              "priceForHDP": 850000,
              "zestimate": 845000,
              "rentZestimate": 3200,
              "currency": "USD",
              "country": "USA",
              "unit": null,
              "streetAddress": "123 Main St"
            }
          }
        }
      ],
      "mapResults": [
        {
          "zpid": "2077091803",
          "latLong": {"latitude": 47.6062, "longitude": -122.3321}
        }
      ]
    },
    "searchList": {
      "totalPages": 12,
      "totalResultCount": 489,
      "resultCount": 40
    }
  },
  "cat2": {
    "total": {"totalResultCount": 489}
  }
}
```

---

## Autocomplete Response (`zg-graph` — `GetAutocompleteResults`)

```json
{
  "data": {
    "zgsAutoComplete": {
      "results": [
        {
          "display": "Seattle, WA",
          "resultType": "REGIONS",
          "metaData": {
            "regionId": 16163,
            "regionType": 6,
            "city": "Seattle",
            "state": "WA",
            "country": "United States",
            "lat": 47.606209,
            "lng": -122.332071
          }
        },
        {
          "display": "98101, Seattle, WA",
          "resultType": "REGIONS",
          "metaData": {
            "regionId": 88135,
            "regionType": 7,
            "lat": 47.6,
            "lng": -122.33
          }
        }
      ]
    }
  }
}
```

---

## Zestimate History (`graphql/` — `HomeValueChartDataQuery`)

```json
{
  "data": {
    "property": {
      "zpid": "2077091803",
      "zestimateHistory": [
        {"t": 1672531200000, "v": 798000},
        {"t": 1675209600000, "v": 805000},
        {"t": 1677628800000, "v": 818000},
        {"t": 1680307200000, "v": 822000},
        {"t": 1682899200000, "v": 831000},
        {"t": 1685577600000, "v": 839000},
        {"t": 1688169600000, "v": 843000},
        {"t": 1690848000000, "v": 841000},
        {"t": 1693526400000, "v": 845000}
      ]
    }
  }
}
```

> `t` = Unix timestamp in milliseconds, `v` = Zestimate in USD

---

## Zestimate Deep Dive (`graphql/` — `ZestimateDeepDiveQuery`)

```json
{
  "data": {
    "property": {
      "zpid": "2077091803",
      "zestimate": 845000,
      "zestimateMinus": 760500,
      "zestimatePlus": 929500,
      "valuationRange": {
        "low": 760500,
        "high": 929500
      },
      "priceHistory": [
        {
          "date": "2024-03-15",
          "price": 850000,
          "priceChangeRate": 0.0,
          "event": "Listed for sale",
          "source": "MLS #NW12345",
          "pricePerSquareFoot": 459,
          "sellerAgent": null,
          "buyerAgent": null
        },
        {
          "date": "2022-07-20",
          "price": 795000,
          "priceChangeRate": null,
          "event": "Sold",
          "source": "MLS #NW99876",
          "pricePerSquareFoot": 430
        }
      ]
    }
  }
}
```

---

## Walk / Transit / Bike Scores (`graphql/` — `WalkTransitAndBikeScoreQuery`)

```json
{
  "data": {
    "property": {
      "zpid": "2077091803",
      "walkScore": {
        "walkscore": 92,
        "description": "Walker's Paradise",
        "logo_url": "https://cdn.walkscore.com/img/logo-compact.png",
        "ws_link": "https://www.walkscore.com/"
      },
      "transitScore": {
        "transit_score": 75,
        "description": "Excellent Transit",
        "logo_url": null
      },
      "bikeScore": {
        "bikescore": 68,
        "description": "Bikeable",
        "logo_url": null
      }
    }
  }
}
```

---

## Property Detail (`__NEXT_DATA__` or `hdpApolloPreloadedData`)

```json
{
  "zpid": 2077091803,
  "streetAddress": "123 Main St",
  "city": "Seattle",
  "state": "WA",
  "zipcode": "98101",
  "country": "USA",
  "latitude": 47.6062,
  "longitude": -122.3321,
  "price": 850000,
  "bedrooms": 3,
  "bathrooms": 2.0,
  "livingArea": 1850,
  "lotSize": 5200,
  "yearBuilt": 1998,
  "homeType": "SINGLE_FAMILY",
  "homeStatus": "FOR_SALE",
  "daysOnZillow": 12,
  "zestimate": 845000,
  "rentZestimate": 3200,
  "taxAssessedValue": 620000,
  "taxAnnualAmount": 7832,
  "description": "Beautiful 3-bed, 2-bath home in the heart of Seattle...",
  "listingSubType": {"is_FSBA": true},
  "resoFacts": {
    "hasGarage": true,
    "garageParkingCapacity": "2",
    "hasCooling": true,
    "cooling": "Central Air",
    "hasHeating": true,
    "heating": "Forced Air",
    "hasFireplace": false,
    "flooring": "Hardwood, Carpet",
    "appliances": "Dishwasher, Refrigerator, Dryer, Washer",
    "parkingFeatures": "Attached Garage"
  },
  "photos": [
    {
      "caption": "",
      "mixedSources": {
        "jpeg": [
          {"url": "https://photos.zillowstatic.com/fp/abc123-cc_ft_384.webp", "width": 384},
          {"url": "https://photos.zillowstatic.com/fp/abc123-uncropped_scaled_within_1536_1152.webp", "width": 1536}
        ]
      }
    }
  ],
  "priceHistory": [
    {
      "date": "2024-03-15",
      "price": 850000,
      "priceChangeRate": 0,
      "event": "Listed for sale",
      "source": "MLS #NW12345",
      "pricePerSquareFoot": 459
    }
  ],
  "taxHistory": [
    {"time": 2023, "taxPaid": 7832, "taxIncreaseRate": 0.04, "value": 620000, "valueIncreaseRate": 0.08},
    {"time": 2022, "taxPaid": 7530, "taxIncreaseRate": 0.02, "value": 574000, "valueIncreaseRate": 0.06}
  ],
  "schools": [
    {
      "name": "Washington Middle School",
      "rating": 8,
      "distance": 0.4,
      "type": "Middle",
      "grades": "6-8",
      "link": "https://www.greatschools.org/..."
    }
  ],
  "listingAgent": {
    "displayName": "Jane Smith",
    "profileUrl": "https://www.zillow.com/profile/janesmith/"
  },
  "attributionInfo": {
    "mlsId": "NW12345",
    "mlsName": "Northwest MLS",
    "brokerName": "Premier Realty",
    "agentEmail": "jane@premierrealty.com",
    "agentLicenseNumber": "123456"
  }
}
```
