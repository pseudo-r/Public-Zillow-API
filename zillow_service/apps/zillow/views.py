"""Zillow service views."""

from django.http import JsonResponse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import structlog

from apps.core.exceptions import ZillowClientError, ZillowNotFoundError, ZillowRateLimitError
from apps.zillow.models import Property
from apps.zillow.serializers import (
    AutocompleteResultSerializer,
    PropertyDetailSerializer,
    PropertyScoreSerializer,
    PropertySerializer,
    SearchResultSerializer,
    ZestimateHistorySerializer,
)
from clients.zillow_client import ZillowClient

logger = structlog.get_logger(__name__)


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok", "service": "zillow_service"})


class SearchView(APIView):
    """Search for properties by location and filters.

    POST /api/v1/search/
    Body: {
        "query": "Seattle, WA",
        "region_id": 16163,       # optional
        "type": "sale",           # sale | rent | sold (default: sale)
        "page": 1,
        "price_min": 200000,      # optional
        "price_max": 800000,      # optional
        "beds_min": 2,            # optional
        "baths_min": 1,           # optional
        "sort": "globalrelevanceex"
    }
    """

    def post(self, request: Request) -> Response:
        data = request.data
        query = data.get("query", "")
        if not query:
            return Response(
                {"error": "query is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_type = data.get("type", "sale")
        region_id = data.get("region_id")
        page = int(data.get("page", 1))

        try:
            client = ZillowClient()
            if search_type == "rent":
                resp = client.search_for_rent(
                    search_term=query,
                    region_id=region_id,
                    page=page,
                    rent_min=data.get("rent_min"),
                    rent_max=data.get("rent_max"),
                    beds_min=data.get("beds_min"),
                )
            elif search_type == "sold":
                resp = client.search_recently_sold(
                    search_term=query,
                    region_id=region_id,
                    page=page,
                    days_max=int(data.get("days_max", 90)),
                )
            else:
                resp = client.search_for_sale(
                    search_term=query,
                    region_id=region_id,
                    page=page,
                    price_min=data.get("price_min"),
                    price_max=data.get("price_max"),
                    beds_min=data.get("beds_min"),
                    baths_min=data.get("baths_min"),
                    sort=data.get("sort", "globalrelevanceex"),
                )

            cat1 = resp.data.get("cat1", {})
            results = cat1.get("searchResults", {}).get("listResults", [])
            search_list = cat1.get("searchList", {})
            total = resp.data.get("cat2", {}).get("total", {})

            return Response({
                "results": results,
                "total_count": total.get("totalResultCount", 0),
                "total_pages": search_list.get("totalPages", 1),
                "page": page,
            })

        except ZillowRateLimitError as e:
            return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ZillowClientError as e:
            logger.error("zillow_search_error", error=str(e))
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class PropertyDetailView(APIView):
    """Get property details by ZPID.

    GET /api/v1/properties/{zpid}/
    """

    def get(self, request: Request, zpid: int) -> Response:
        # Check local DB first
        try:
            prop = Property.objects.get(zpid=zpid)
            serializer = PropertyDetailSerializer(prop)
            return Response(serializer.data)
        except Property.DoesNotExist:
            pass

        # Fetch from Zillow
        try:
            client = ZillowClient()
            prop_data = client.get_property_from_page(zpid=zpid)

            return Response({
                "zpid": prop_data.get("zpid"),
                "address": prop_data.get("streetAddress"),
                "city": prop_data.get("city"),
                "state": prop_data.get("state"),
                "zipcode": prop_data.get("zipcode"),
                "price": prop_data.get("price"),
                "bedrooms": prop_data.get("bedrooms"),
                "bathrooms": prop_data.get("bathrooms"),
                "living_area": prop_data.get("livingArea"),
                "lot_size": prop_data.get("lotSize"),
                "year_built": prop_data.get("yearBuilt"),
                "home_type": prop_data.get("homeType"),
                "home_status": prop_data.get("homeStatus"),
                "days_on_zillow": prop_data.get("daysOnZillow"),
                "zestimate": prop_data.get("zestimate"),
                "rent_zestimate": prop_data.get("rentZestimate"),
                "tax_assessed_value": prop_data.get("taxAssessedValue"),
                "tax_annual_amount": prop_data.get("taxAnnualAmount"),
                "description": prop_data.get("description", ""),
                "photos": prop_data.get("photos", []),
                "price_history": prop_data.get("priceHistory", []),
                "tax_history": prop_data.get("taxHistory", []),
                "schools": prop_data.get("schools", []),
                "reso_facts": prop_data.get("resoFacts", {}),
            })

        except ZillowNotFoundError:
            return Response(
                {"error": f"Property with zpid={zpid} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ZillowRateLimitError as e:
            return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ZillowClientError as e:
            logger.error("zillow_property_detail_error", zpid=zpid, error=str(e))
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class ZestimateView(APIView):
    """Get Zestimate and history for a property.

    GET /api/v1/properties/{zpid}/zestimate/
    """

    def get(self, request: Request, zpid: int) -> Response:
        try:
            client = ZillowClient()
            resp = client.get_zestimate(zpid=zpid)
            hist_resp = client.get_zestimate_history(zpid=zpid)

            prop_data = resp.data.get("data", {}).get("property", {})
            hist_data = hist_resp.data.get("data", {}).get("property", {})

            return Response({
                "zpid": zpid,
                "zestimate": prop_data.get("zestimate"),
                "range_low": prop_data.get("zestimateMinus"),
                "range_high": prop_data.get("zestimatePlus"),
                "valuation_range": prop_data.get("valuationRange"),
                "price_history": prop_data.get("priceHistory", []),
                "zestimate_history": hist_data.get("zestimateHistory", []),
            })

        except ZillowNotFoundError:
            return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)
        except ZillowRateLimitError as e:
            return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ZillowClientError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class ScoresView(APIView):
    """Get Walk/Transit/Bike scores for a property.

    GET /api/v1/properties/{zpid}/scores/
    """

    def get(self, request: Request, zpid: int) -> Response:
        try:
            client = ZillowClient()
            resp = client.get_walk_bike_transit_scores(zpid=zpid)
            prop_data = resp.data.get("data", {}).get("property", {})

            return Response({
                "zpid": zpid,
                "walk_score": prop_data.get("walkScore"),
                "transit_score": prop_data.get("transitScore"),
                "bike_score": prop_data.get("bikeScore"),
            })

        except ZillowClientError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class ClimateRiskView(APIView):
    """Get climate risk scores for a property.

    GET /api/v1/properties/{zpid}/climate/
    """

    def get(self, request: Request, zpid: int) -> Response:
        try:
            client = ZillowClient()
            resp = client.get_climate_risk(zpid=zpid)
            prop_data = resp.data.get("data", {}).get("property", {})

            return Response({
                "zpid": zpid,
                "climate_risk": prop_data.get("climateRiskData"),
            })

        except ZillowClientError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class AutocompleteView(APIView):
    """Autocomplete location suggestions.

    GET /api/v1/autocomplete/?q=Seattle
    """

    def get(self, request: Request) -> Response:
        q = request.query_params.get("q", "")
        if not q:
            return Response(
                {"error": "q query param is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result_types = request.query_params.getlist("type") or [
            "REGIONS",
            "FORSALE",
            "RENTALS",
            "SOLD",
        ]

        try:
            client = ZillowClient()
            resp = client.autocomplete(query=q, result_types=result_types)
            results = (
                resp.data.get("data", {})
                .get("zgsAutoComplete", {})
                .get("results", [])
            )

            return Response({"query": q, "results": results})

        except ZillowClientError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class IngestPropertyView(APIView):
    """Ingest a property by ZPID.

    POST /api/v1/ingest/property/
    Body: {"zpid": 2077091803}
    """

    def post(self, request: Request) -> Response:
        zpid = request.data.get("zpid")
        if not zpid:
            return Response(
                {"error": "zpid is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = ZillowClient()
            prop_data = client.get_property_from_page(zpid=int(zpid))

            prop, created = Property.objects.update_or_create(
                zpid=int(zpid),
                defaults={
                    "street_address": prop_data.get("streetAddress", ""),
                    "unit": prop_data.get("unit", ""),
                    "city": prop_data.get("city", ""),
                    "state": prop_data.get("state", ""),
                    "zipcode": prop_data.get("zipcode", ""),
                    "latitude": prop_data.get("latitude"),
                    "longitude": prop_data.get("longitude"),
                    "price": prop_data.get("price"),
                    "status": prop_data.get("homeStatus", ""),
                    "home_type": prop_data.get("homeType", ""),
                    "bedrooms": prop_data.get("bedrooms"),
                    "bathrooms": prop_data.get("bathrooms"),
                    "living_area": prop_data.get("livingArea"),
                    "lot_size": prop_data.get("lotSize"),
                    "year_built": prop_data.get("yearBuilt"),
                    "days_on_zillow": prop_data.get("daysOnZillow"),
                    "zestimate": prop_data.get("zestimate"),
                    "rent_zestimate": prop_data.get("rentZestimate"),
                    "tax_assessed_value": prop_data.get("taxAssessedValue"),
                    "tax_annual_amount": prop_data.get("taxAnnualAmount"),
                    "description": prop_data.get("description", ""),
                    "raw_data": prop_data,
                },
            )

            from apps.zillow.services import ingest_price_history, ingest_zestimate_history
            ingest_price_history(prop, prop_data.get("priceHistory", []))

            serializer = PropertySerializer(prop)
            return Response(
                {
                    "created": created,
                    "property": serializer.data,
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        except ZillowNotFoundError:
            return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)
        except ZillowRateLimitError as e:
            return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ZillowClientError as e:
            logger.error("zillow_ingest_error", zpid=zpid, error=str(e))
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
