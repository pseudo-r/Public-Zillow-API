"""Zillow service serializers."""

from rest_framework import serializers

from .models import PriceHistory, Property, PropertyScore, ZestimateHistory


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            "id",
            "zpid",
            "street_address",
            "unit",
            "city",
            "state",
            "zipcode",
            "latitude",
            "longitude",
            "price",
            "status",
            "home_type",
            "bedrooms",
            "bathrooms",
            "living_area",
            "lot_size",
            "year_built",
            "days_on_zillow",
            "zestimate",
            "rent_zestimate",
            "tax_assessed_value",
            "tax_annual_amount",
            "description",
            "detail_url",
            "primary_image_url",
            "updated_at",
        ]


class ZestimateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ZestimateHistory
        fields = ["timestamp_ms", "value"]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = [
            "event_date",
            "price",
            "event",
            "source",
            "price_per_sqft",
            "price_change_rate",
        ]


class PropertyScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyScore
        fields = [
            "walk_score",
            "walk_description",
            "transit_score",
            "transit_description",
            "bike_score",
            "bike_description",
            "flood_factor",
            "fire_factor",
            "heat_factor",
            "wind_factor",
            "updated_at",
        ]


class PropertyDetailSerializer(PropertySerializer):
    zestimate_history = ZestimateHistorySerializer(many=True, read_only=True)
    price_history = PriceHistorySerializer(many=True, read_only=True)
    scores = PropertyScoreSerializer(read_only=True)

    class Meta(PropertySerializer.Meta):
        fields = PropertySerializer.Meta.fields + [
            "zestimate_history",
            "price_history",
            "scores",
        ]


class SearchResultSerializer(serializers.Serializer):
    zpid = serializers.CharField()
    address = serializers.CharField()
    price = serializers.CharField()
    unformatted_price = serializers.IntegerField(source="unformattedPrice", default=None)
    beds = serializers.IntegerField(default=None)
    baths = serializers.FloatField(default=None)
    area = serializers.IntegerField(default=None)
    status_type = serializers.CharField(source="statusType", default=None)
    detail_url = serializers.CharField(source="detailUrl")
    img_src = serializers.URLField(source="imgSrc", default=None)
    zestimate = serializers.IntegerField(default=None)
    latitude = serializers.FloatField(source="latLong.latitude", default=None)
    longitude = serializers.FloatField(source="latLong.longitude", default=None)


class AutocompleteResultSerializer(serializers.Serializer):
    display = serializers.CharField()
    result_type = serializers.CharField(source="resultType", default=None)
    region_id = serializers.IntegerField(source="metaData.regionId", default=None)
    region_type = serializers.IntegerField(source="metaData.regionType", default=None)
    city = serializers.CharField(source="metaData.city", default=None)
    state = serializers.CharField(source="metaData.state", default=None)
    lat = serializers.FloatField(source="metaData.lat", default=None)
    lng = serializers.FloatField(source="metaData.lng", default=None)
