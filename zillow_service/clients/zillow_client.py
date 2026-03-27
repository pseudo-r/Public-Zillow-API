"""Zillow API client with retry logic, timeouts, and error handling.

This module provides a centralized client for all Zillow API interactions.
All Zillow API calls should go through this client to ensure consistent
error handling, retries, and rate limiting.
"""

import json
import time
from dataclasses import dataclass
from typing import Any

import httpx
import structlog
from django.conf import settings
from parsel import Selector
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from apps.core.exceptions import (
    ZillowClientError,
    ZillowNotFoundError,
    ZillowRateLimitError,
)

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Zillow API Base URLs
# ─────────────────────────────────────────────────────────────────────────────

ZILLOW_BASE_URL = "https://www.zillow.com"
ZILLOW_GRAPHQL_URL = "https://www.zillow.com/graphql/"
ZILLOW_ZG_GRAPH_URL = "https://www.zillow.com/zg-graph"
ZILLOW_SEARCH_URL = "https://www.zillow.com/async-create-search-page-state"
ZILLOW_STATIC_URL = "https://photos.zillowstatic.com"


# ─────────────────────────────────────────────────────────────────────────────
# Browser-like headers required for all Zillow requests
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

GRAPHQL_HEADERS = {
    **DEFAULT_HEADERS,
    "Content-Type": "application/json",
    "client-id": "hdp-react-web-client",
    "x-caller-id": "hdp-react-web-client",
}

ZG_GRAPH_HEADERS = {
    **DEFAULT_HEADERS,
    "Content-Type": "application/json",
    "client-id": "search-sub-app-client",
}

SEARCH_HEADERS = {
    **DEFAULT_HEADERS,
    "Content-Type": "application/json",
}


@dataclass
class ZillowResponse:
    """Wrapper for Zillow API responses."""

    data: dict[str, Any] | list[Any]
    status_code: int
    url: str

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class ZillowClient:
    """Client for Zillow API interactions.

    This client handles:
    - Zillow's undocumented REST and GraphQL endpoints
    - Browser-like headers required to avoid 403 blocking
    - Automatic retries with exponential backoff
    - Request timeouts and rate limiting
    - Property page HTML parsing (__NEXT_DATA__ + Apollo cache)

    Usage:
        client = ZillowClient()

        # Search for properties
        results = client.search_for_sale("Seattle, WA", region_id=16163)

        # Get property by ZPID
        prop = client.get_property_detail(zpid=2077091803)

        # Zestimate history
        history = client.get_zestimate_history(zpid=2077091803)

        # Scores
        scores = client.get_walk_bike_transit_scores(zpid=2077091803)
    """

    def __init__(
        self,
        timeout: float | None = None,
        max_retries: int | None = None,
        request_delay: float | None = None,
    ):
        """Initialize Zillow client.

        Args:
            timeout: Request timeout in seconds (default: settings or 30.0)
            max_retries: Maximum retry attempts (default: settings or 3)
            request_delay: Delay between requests in seconds to avoid rate limiting
        """
        config = getattr(settings, "ZILLOW_CLIENT", {})

        self.timeout = timeout or config.get("TIMEOUT", 30.0)
        self.max_retries = max_retries or config.get("MAX_RETRIES", 3)
        self.retry_backoff = config.get("RETRY_BACKOFF", 1.0)
        self.request_delay = request_delay or config.get("REQUEST_DELAY", 1.0)

        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client (lazy initialization)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout),
                headers=DEFAULT_HEADERS,
                follow_redirects=True,
                http2=True,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            self._client.close()
            self._client = None

    def __enter__(self) -> "ZillowClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _handle_response(self, response: httpx.Response, url: str) -> ZillowResponse:
        """Handle HTTP response and convert to ZillowResponse."""
        if response.status_code == 403:
            logger.warning("zillow_blocked", url=url)
            raise ZillowRateLimitError(
                f"Zillow blocked request (403). Use session cookies or reduce request rate. URL: {url}"
            )

        if response.status_code == 404:
            logger.warning("zillow_not_found", url=url)
            raise ZillowNotFoundError(f"Zillow resource not found: {url}")

        if response.status_code == 429:
            logger.warning("zillow_rate_limited", url=url)
            raise ZillowRateLimitError("Zillow rate limit exceeded (429)")

        if response.status_code >= 500:
            logger.error("zillow_server_error", url=url, status_code=response.status_code)
            raise ZillowClientError(f"Zillow server error: {response.status_code}")

        if response.status_code >= 400:
            logger.error("zillow_client_error", url=url, status_code=response.status_code)
            raise ZillowClientError(f"Zillow API error: {response.status_code}")

        try:
            data = response.json()
        except Exception as e:
            logger.error("zillow_json_parse_error", url=url, error=str(e))
            raise ZillowClientError(f"Failed to parse Zillow response: {e}") from e

        return ZillowResponse(data=data, status_code=response.status_code, url=url)

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ZillowResponse:
        """Make HTTP request with retry logic."""

        @retry(
            retry=retry_if_exception_type((httpx.TransportError, ZillowClientError)),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.retry_backoff, min=1, max=10),
            reraise=True,
        )
        def _do_request() -> ZillowResponse:
            logger.debug("zillow_request", method=method, url=url)
            if self.request_delay > 0:
                time.sleep(self.request_delay)
            response = self.client.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=headers,
            )
            return self._handle_response(response, url)

        try:
            return _do_request()
        except RetryError as e:
            logger.error("zillow_request_failed", url=url, retries=self.max_retries)
            raise ZillowClientError(
                f"Zillow request failed after {self.max_retries} retries"
            ) from e
        except (ZillowNotFoundError, ZillowRateLimitError):
            raise
        except httpx.TransportError as e:
            logger.error("zillow_transport_error", url=url, error=str(e))
            raise ZillowClientError(f"Zillow connection error: {e}") from e

    # ─────────────────────────────────────────────────────────────────────────
    # Search Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    def search_for_sale(
        self,
        search_term: str,
        region_id: int | None = None,
        map_bounds: dict[str, float] | None = None,
        page: int = 1,
        price_min: int | None = None,
        price_max: int | None = None,
        beds_min: int | None = None,
        baths_min: int | None = None,
        sqft_min: int | None = None,
        sqft_max: int | None = None,
        sort: str = "globalrelevanceex",
        list_results: bool = True,
        map_results: bool = True,
    ) -> ZillowResponse:
        """Search for properties for sale.

        Args:
            search_term: Human-readable search text (e.g., "Seattle, WA")
            region_id: Zillow region ID (from autocomplete)
            map_bounds: Dict with west/east/south/north bounding box
            page: Page number (default 1)
            price_min: Minimum price filter
            price_max: Maximum price filter
            beds_min: Minimum bedrooms
            baths_min: Minimum bathrooms
            sqft_min: Minimum square footage
            sqft_max: Maximum square footage
            sort: Sort order (globalrelevanceex, days, priceDesc, priceAsc)
            list_results: Include list results
            map_results: Include map results

        Returns:
            ZillowResponse with search results
        """
        filter_state: dict[str, Any] = {
            "sortSelection": {"value": sort},
        }

        if price_min is not None:
            filter_state["price"] = {**filter_state.get("price", {}), "min": price_min}
        if price_max is not None:
            filter_state["price"] = {**filter_state.get("price", {}), "max": price_max}
        if beds_min is not None:
            filter_state["beds"] = {"min": beds_min}
        if baths_min is not None:
            filter_state["baths"] = {"min": baths_min}
        if sqft_min is not None:
            filter_state["sqft"] = {**filter_state.get("sqft", {}), "min": sqft_min}
        if sqft_max is not None:
            filter_state["sqft"] = {**filter_state.get("sqft", {}), "max": sqft_max}

        query_state: dict[str, Any] = {
            "pagination": {} if page == 1 else {"currentPage": page},
            "usersSearchTerm": search_term,
            "filterState": filter_state,
            "isMapVisible": map_results,
            "isListVisible": list_results,
        }

        if region_id:
            query_state["regionSelection"] = [{"regionId": region_id, "regionType": 6}]

        if map_bounds:
            query_state["mapBounds"] = map_bounds

        wants: dict[str, list[str]] = {}
        if list_results:
            wants.setdefault("cat1", []).append("listResults")
        if map_results:
            wants.setdefault("cat1", []).append("mapResults")
        wants["cat2"] = ["total"]

        payload: dict[str, Any] = {
            "searchQueryState": query_state,
            "wants": wants,
            "requestId": page + 1,
            "isDebugRequest": False,
        }

        logger.info("zillow_search_for_sale", search_term=search_term, page=page)
        return self._request_with_retry(
            "PUT",
            ZILLOW_SEARCH_URL,
            json_body=payload,
            headers=SEARCH_HEADERS,
        )

    def search_for_rent(
        self,
        search_term: str,
        region_id: int | None = None,
        map_bounds: dict[str, float] | None = None,
        page: int = 1,
        rent_min: int | None = None,
        rent_max: int | None = None,
        beds_min: int | None = None,
        sort: str = "days",
    ) -> ZillowResponse:
        """Search for rental properties.

        Args:
            search_term: Human-readable search text
            region_id: Zillow region ID from autocomplete
            map_bounds: Bounding box dict
            page: Page number
            rent_min: Minimum monthly rent
            rent_max: Maximum monthly rent
            beds_min: Minimum bedrooms
            sort: Sort order

        Returns:
            ZillowResponse with rental results
        """
        filter_state: dict[str, Any] = {
            "isForRent": {"value": True},
            "isForSaleByAgent": {"value": False},
            "isForSaleByOwner": {"value": False},
            "isNewConstruction": {"value": False},
            "isComingSoon": {"value": False},
            "isAuction": {"value": False},
            "isForSaleForeclosure": {"value": False},
            "sortSelection": {"value": sort},
        }

        if rent_min is not None:
            filter_state["monthlyPayment"] = {
                **filter_state.get("monthlyPayment", {}),
                "min": rent_min,
            }
        if rent_max is not None:
            filter_state["monthlyPayment"] = {
                **filter_state.get("monthlyPayment", {}),
                "max": rent_max,
            }
        if beds_min is not None:
            filter_state["beds"] = {"min": beds_min}

        query_state: dict[str, Any] = {
            "pagination": {} if page == 1 else {"currentPage": page},
            "usersSearchTerm": search_term,
            "filterState": filter_state,
            "isMapVisible": True,
            "isListVisible": True,
        }

        if region_id:
            query_state["regionSelection"] = [{"regionId": region_id, "regionType": 6}]
        if map_bounds:
            query_state["mapBounds"] = map_bounds

        payload: dict[str, Any] = {
            "searchQueryState": query_state,
            "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
            "requestId": page + 1,
            "isDebugRequest": False,
        }

        logger.info("zillow_search_for_rent", search_term=search_term, page=page)
        return self._request_with_retry(
            "PUT",
            ZILLOW_SEARCH_URL,
            json_body=payload,
            headers=SEARCH_HEADERS,
        )

    def search_recently_sold(
        self,
        search_term: str,
        region_id: int | None = None,
        map_bounds: dict[str, float] | None = None,
        days_max: int = 90,
        page: int = 1,
    ) -> ZillowResponse:
        """Search recently sold properties.

        Args:
            search_term: Human-readable search text
            region_id: Zillow region ID
            map_bounds: Bounding box dict
            days_max: Maximum days since sold (default 90)
            page: Page number

        Returns:
            ZillowResponse with recently sold results
        """
        filter_state: dict[str, Any] = {
            "isRecentlySold": {"value": True},
            "isForSaleByAgent": {"value": False},
            "isForSaleByOwner": {"value": False},
            "daysOnZillow": {"max": days_max},
            "sortSelection": {"value": "days"},
        }

        query_state: dict[str, Any] = {
            "pagination": {} if page == 1 else {"currentPage": page},
            "usersSearchTerm": search_term,
            "filterState": filter_state,
        }

        if region_id:
            query_state["regionSelection"] = [{"regionId": region_id, "regionType": 6}]
        if map_bounds:
            query_state["mapBounds"] = map_bounds

        payload: dict[str, Any] = {
            "searchQueryState": query_state,
            "wants": {"cat1": ["listResults"], "cat2": ["total"]},
            "requestId": page + 1,
        }

        logger.info("zillow_search_recently_sold", search_term=search_term)
        return self._request_with_retry(
            "PUT",
            ZILLOW_SEARCH_URL,
            json_body=payload,
            headers=SEARCH_HEADERS,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Autocomplete
    # ─────────────────────────────────────────────────────────────────────────

    def autocomplete(
        self,
        query: str,
        result_types: list[str] | None = None,
    ) -> ZillowResponse:
        """Autocomplete location and property suggestions.

        Args:
            query: Search text (city, ZIP, address, neighborhood)
            result_types: List of result types to include
                         (REGIONS, FORSALE, RENTALS, SOLD)

        Returns:
            ZillowResponse with autocomplete suggestions
        """
        if result_types is None:
            result_types = ["REGIONS", "FORSALE", "RENTALS", "SOLD"]

        payload = {
            "operationName": "GetAutocompleteResults",
            "variables": {
                "query": query,
                "resultType": result_types,
            },
            "query": (
                "query GetAutocompleteResults($query: String!, $resultType: [AutocompleteResultType!]) {"
                "  zgsAutoComplete(query: $query, resultType: $resultType) {"
                "    results {"
                "      display"
                "      resultType"
                "      metaData {"
                "        regionId"
                "        regionType"
                "        city"
                "        state"
                "        country"
                "        lat"
                "        lng"
                "      }"
                "    }"
                "  }"
                "}"
            ),
        }

        logger.info("zillow_autocomplete", query=query)
        return self._request_with_retry(
            "POST",
            ZILLOW_ZG_GRAPH_URL,
            json_body=payload,
            headers=ZG_GRAPH_HEADERS,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Property Detail
    # ─────────────────────────────────────────────────────────────────────────

    def get_property_from_page(self, zpid: int | str) -> dict[str, Any]:
        """Extract property data from Zillow property page HTML.

        Tries __NEXT_DATA__ first, falls back to hdpApolloPreloadedData.

        Args:
            zpid: Zillow Property ID

        Returns:
            Property data dict
        """
        url = f"{ZILLOW_BASE_URL}/homedetails/{zpid}_zpid/"

        logger.info("zillow_get_property_page", zpid=zpid)
        response = self._request_with_retry(
            "GET",
            url,
            headers=DEFAULT_HEADERS,
        )

        # response.data will be empty since it's HTML — we need raw response
        # Re-fetch as raw HTML
        raw = self.client.get(url, headers=DEFAULT_HEADERS)
        if raw.status_code == 404:
            raise ZillowNotFoundError(f"Property not found: zpid={zpid}")

        sel = Selector(raw.text)

        # Option 1: Next.js data
        next_data = sel.css("script#__NEXT_DATA__::text").get()
        if next_data:
            try:
                data = json.loads(next_data)
                cache_raw = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("componentProps", {})
                    .get("gdpClientCache")
                )
                if cache_raw:
                    cache = json.loads(cache_raw)
                    if cache:
                        key = list(cache)[0]
                        return cache[key].get("property", {})
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug("next_data_parse_failed", error=str(e))

        # Option 2: Apollo cache
        apollo_data = sel.css("script#hdpApolloPreloadedData::text").get()
        if apollo_data:
            try:
                outer = json.loads(apollo_data)
                api_cache = json.loads(outer.get("apiCache", "{}"))
                for key, val in api_cache.items():
                    if "ForSale" in key or "ForRent" in key or "property" in str(val):
                        if isinstance(val, dict) and "property" in val:
                            return val["property"]
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug("apollo_cache_parse_failed", error=str(e))

        raise ZillowClientError(f"Could not extract property data for zpid={zpid}")

    # ─────────────────────────────────────────────────────────────────────────
    # GraphQL Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _graphql_query(
        self,
        operation_name: str,
        variables: dict[str, Any],
        query: str,
    ) -> ZillowResponse:
        """Execute a GraphQL query against Zillow's graphql/ endpoint."""
        payload = {
            "operationName": operation_name,
            "variables": variables,
            "query": query,
        }
        return self._request_with_retry(
            "POST",
            ZILLOW_GRAPHQL_URL,
            json_body=payload,
            headers=GRAPHQL_HEADERS,
        )

    def get_zestimate(self, zpid: int | str) -> ZillowResponse:
        """Get Zestimate and value range for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with zestimate data
        """
        logger.info("zillow_get_zestimate", zpid=zpid)
        return self._graphql_query(
            operation_name="ZestimateDeepDiveQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query ZestimateDeepDiveQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    zestimate"
                "    zestimateMinus"
                "    zestimatePlus"
                "    valuationRange { low high }"
                "    priceHistory {"
                "      date price priceChangeRate event source pricePerSquareFoot"
                "    }"
                "  }"
                "}"
            ),
        )

    def get_zestimate_history(self, zpid: int | str) -> ZillowResponse:
        """Get Zestimate time series history for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with {t: timestamp_ms, v: usd_value} array
        """
        logger.info("zillow_get_zestimate_history", zpid=zpid)
        return self._graphql_query(
            operation_name="HomeValueChartDataQuery",
            variables={"zpid": int(zpid), "useHVChartDataSource": True},
            query=(
                "query HomeValueChartDataQuery($zpid: ID!, $useHVChartDataSource: Boolean) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    zestimateHistory(useHVChartDataSource: $useHVChartDataSource) {"
                "      t v"
                "    }"
                "  }"
                "}"
            ),
        )

    def get_rent_zestimate(self, zpid: int | str) -> ZillowResponse:
        """Get Rent Zestimate for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with rentZestimate and range
        """
        logger.info("zillow_get_rent_zestimate", zpid=zpid)
        return self._graphql_query(
            operation_name="RentEstimateQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query RentEstimateQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid rentZestimate rentZestimateMinus rentZestimatePlus"
                "  }"
                "}"
            ),
        )

    def get_walk_bike_transit_scores(self, zpid: int | str) -> ZillowResponse:
        """Get Walk Score, Transit Score, and Bike Score for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with score data
        """
        logger.info("zillow_get_scores", zpid=zpid)
        return self._graphql_query(
            operation_name="WalkTransitAndBikeScoreQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query WalkTransitAndBikeScoreQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    walkScore { walkscore description logo_url ws_link }"
                "    transitScore { transit_score description }"
                "    bikeScore { bikescore description }"
                "  }"
                "}"
            ),
        )

    def get_climate_risk(self, zpid: int | str) -> ZillowResponse:
        """Get climate risk scores for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with flood, fire, heat, and wind risk scores
        """
        logger.info("zillow_get_climate_risk", zpid=zpid)
        return self._graphql_query(
            operation_name="PropertyClimateRiskQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query PropertyClimateRiskQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    climateRiskData { floodFactor fireFactor heatFactor windFactor }"
                "  }"
                "}"
            ),
        )

    def get_comparable_sales(self, zpid: int | str) -> ZillowResponse:
        """Get comparable recently sold homes for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with comparable sales data
        """
        logger.info("zillow_get_comparable_sales", zpid=zpid)
        return self._graphql_query(
            operation_name="SimilarSalesQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query SimilarSalesQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    comparables {"
                "      zpid address price dateSold livingArea bedrooms bathrooms"
                "    }"
                "  }"
                "}"
            ),
        )

    def get_nearby_homes(self, zpid: int | str) -> ZillowResponse:
        """Get nearby active listings for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with nearby homes data
        """
        logger.info("zillow_get_nearby_homes", zpid=zpid)
        return self._graphql_query(
            operation_name="NearbyHomesQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query NearbyHomesQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    nearbyHomes {"
                "      zpid price bedrooms bathrooms livingArea homeType homeStatus"
                "    }"
                "  }"
                "}"
            ),
        )

    def get_schools(self, zpid: int | str) -> ZillowResponse:
        """Get nearby school ratings for a property.

        Args:
            zpid: Zillow Property ID

        Returns:
            ZillowResponse with school data
        """
        logger.info("zillow_get_schools", zpid=zpid)
        return self._graphql_query(
            operation_name="SchoolsQuery",
            variables={"zpid": int(zpid)},
            query=(
                "query SchoolsQuery($zpid: ID!) {"
                "  property(zpid: $zpid) {"
                "    zpid"
                "    schools { name rating distance type grades link }"
                "  }"
                "}"
            ),
        )
