"""Zillow service URL routing."""

from django.urls import path

from apps.zillow import views

urlpatterns = [
    path(
        "properties/<int:zpid>/schools/",
        views.PropertyResourceView.as_view(client_method="get_schools"),
        name="zillow-schools",
    ),
    path(
        "properties/<int:zpid>/nearby/",
        views.PropertyResourceView.as_view(client_method="get_nearby_homes"),
        name="zillow-nearby",
    ),
    path(
        "properties/<int:zpid>/comparables/",
        views.PropertyResourceView.as_view(client_method="get_comparable_sales"),
        name="zillow-comparables",
    ),
    path(
        "properties/<int:zpid>/rent-zestimate/",
        views.PropertyResourceView.as_view(client_method="get_rent_zestimate"),
        name="zillow-rent-zestimate",
    ),
    path("search/", views.SearchView.as_view(), name="zillow-search"),
    path(
        "properties/<int:zpid>/", views.PropertyDetailView.as_view(), name="zillow-property-detail"
    ),
    path(
        "properties/<int:zpid>/zestimate/", views.ZestimateView.as_view(), name="zillow-zestimate"
    ),
    path("properties/<int:zpid>/scores/", views.ScoresView.as_view(), name="zillow-scores"),
    path("properties/<int:zpid>/climate/", views.ClimateRiskView.as_view(), name="zillow-climate"),
    path("autocomplete/", views.AutocompleteView.as_view(), name="zillow-autocomplete"),
    path("ingest/property/", views.IngestPropertyView.as_view(), name="zillow-ingest-property"),
]
