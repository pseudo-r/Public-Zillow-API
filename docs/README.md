# Zillow API — Documentation Index

This directory contains detailed endpoint references organized by category.

## Endpoint Categories

| Category | File | Endpoints Covered |
|----------|------|-------------------|
| Search & Discovery | [endpoints/search.md](endpoints/search.md) | Home search, rental search, map search, legacy search |
| Property / Listing | [endpoints/property.md](endpoints/property.md) | Property detail, price history, tax history, photos |
| Rentals | [endpoints/rentals.md](endpoints/rentals.md) | Rental search, building detail, rent estimates |
| Market & Valuation | [endpoints/market_valuation.md](endpoints/market_valuation.md) | Zestimate, history, comps, climate risk, scores |
| GraphQL Operations | [endpoints/graphql.md](endpoints/graphql.md) | All known GraphQL operations and schemas |

## Response Schemas

Full JSON response examples: [response_schemas.md](response_schemas.md)

## Quick Reference

**Primary domains:**
- `www.zillow.com` — REST search and property pages
- `www.zillow.com/graphql/` — Property GraphQL
- `www.zillow.com/zg-graph` — Autocomplete GraphQL

**Getting a ZPID:**
1. Autocomplete → `regionId` to scope search
2. Search → `cat1.searchResults.listResults[].zpid`
3. Or extract from URL: `zillow.com/homedetails/.../{zpid}_zpid/`
