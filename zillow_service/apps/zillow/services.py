"""Ingestion services for Zillow data."""

from apps.zillow.models import PriceHistory, Property, ZestimateHistory


def ingest_price_history(prop: Property, price_history: list) -> int:
    """Ingest price history events for a property.

    Args:
        prop: Property instance
        price_history: List of price event dicts from Zillow API

    Returns:
        Number of records created
    """
    created_count = 0
    for event in price_history:
        date_str = event.get("date")
        price = event.get("price")
        if not date_str or not price:
            continue

        _, created = PriceHistory.objects.update_or_create(
            property=prop,
            event_date=date_str,
            defaults={
                "price": price,
                "event": event.get("event", ""),
                "source": event.get("source", ""),
                "price_per_sqft": event.get("pricePerSquareFoot"),
                "price_change_rate": event.get("priceChangeRate"),
            },
        )
        if created:
            created_count += 1

    return created_count


def ingest_zestimate_history(prop: Property, zestimate_history: list) -> int:
    """Ingest Zestimate time series for a property.

    Args:
        prop: Property instance
        zestimate_history: List of {t: timestamp_ms, v: value} dicts

    Returns:
        Number of records created
    """
    created_count = 0
    for point in zestimate_history:
        ts = point.get("t")
        val = point.get("v")
        if ts is None or val is None:
            continue

        _, created = ZestimateHistory.objects.update_or_create(
            property=prop,
            timestamp_ms=ts,
            defaults={"value": val},
        )
        if created:
            created_count += 1

    return created_count
