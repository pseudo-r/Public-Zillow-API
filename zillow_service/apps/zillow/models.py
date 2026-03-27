"""Zillow service Django models."""

from django.db import models


class Property(models.Model):
    """A Zillow property (for-sale, rental, or recently-sold)."""

    STATUS_FOR_SALE = "FOR_SALE"
    STATUS_FOR_RENT = "FOR_RENT"
    STATUS_RECENTLY_SOLD = "RECENTLY_SOLD"
    STATUS_CHOICES = [
        (STATUS_FOR_SALE, "For Sale"),
        (STATUS_FOR_RENT, "For Rent"),
        (STATUS_RECENTLY_SOLD, "Recently Sold"),
    ]

    TYPE_SINGLE_FAMILY = "SINGLE_FAMILY"
    TYPE_CONDO = "CONDO"
    TYPE_TOWNHOUSE = "TOWNHOUSE"
    TYPE_MULTI_FAMILY = "MULTI_FAMILY"
    TYPE_LAND = "LOT"
    TYPE_OTHER = "OTHER"

    # Zillow identifiers
    zpid = models.BigIntegerField(unique=True, db_index=True)

    # Address
    street_address = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=10)
    zipcode = models.CharField(max_length=20)
    country = models.CharField(max_length=10, default="USA")

    # Coordinates
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Listing details
    price = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    home_type = models.CharField(max_length=30, blank=True)

    # Facts
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.FloatField(null=True, blank=True)
    living_area = models.IntegerField(null=True, blank=True)  # sqft
    lot_size = models.IntegerField(null=True, blank=True)  # sqft
    year_built = models.IntegerField(null=True, blank=True)
    days_on_zillow = models.IntegerField(null=True, blank=True)

    # Valuation
    zestimate = models.BigIntegerField(null=True, blank=True)
    rent_zestimate = models.IntegerField(null=True, blank=True)
    tax_assessed_value = models.BigIntegerField(null=True, blank=True)
    tax_annual_amount = models.IntegerField(null=True, blank=True)

    # Details
    description = models.TextField(blank=True)
    detail_url = models.CharField(max_length=500, blank=True)
    primary_image_url = models.URLField(max_length=1000, blank=True)

    # Raw data
    raw_data = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.street_address}, {self.city}, {self.state} (zpid={self.zpid})"


class ZestimateHistory(models.Model):
    """Zillow home value history for a property."""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="zestimate_history"
    )
    timestamp_ms = models.BigIntegerField()  # Unix timestamp in milliseconds
    value = models.BigIntegerField()  # Zestimate in USD

    class Meta:
        ordering = ["timestamp_ms"]
        unique_together = ["property", "timestamp_ms"]

    def __str__(self) -> str:
        return f"zpid={self.property.zpid} @ {self.timestamp_ms}: ${self.value:,}"


class PriceHistory(models.Model):
    """Price event history for a property."""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="price_history"
    )
    event_date = models.DateField()
    price = models.BigIntegerField()
    event = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=200, blank=True)
    price_per_sqft = models.IntegerField(null=True, blank=True)
    price_change_rate = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-event_date"]

    def __str__(self) -> str:
        return f"zpid={self.property.zpid} {self.event_date}: ${self.price:,} ({self.event})"


class PropertyScore(models.Model):
    """Walk/Transit/Bike and climate risk scores for a property."""

    property = models.OneToOneField(
        Property, on_delete=models.CASCADE, related_name="scores"
    )

    # Walk Score
    walk_score = models.IntegerField(null=True, blank=True)
    walk_description = models.CharField(max_length=100, blank=True)

    # Transit Score
    transit_score = models.IntegerField(null=True, blank=True)
    transit_description = models.CharField(max_length=100, blank=True)

    # Bike Score
    bike_score = models.IntegerField(null=True, blank=True)
    bike_description = models.CharField(max_length=100, blank=True)

    # Climate Risk (1-10 scale)
    flood_factor = models.IntegerField(null=True, blank=True)
    fire_factor = models.IntegerField(null=True, blank=True)
    heat_factor = models.IntegerField(null=True, blank=True)
    wind_factor = models.IntegerField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Scores for zpid={self.property.zpid}"
