import logging
from typing import Dict

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.taxi import TaxiTrip, TripAnalytics, VendorUpdateResponse

logger = logging.getLogger(__name__)


class TaxiService:
    """Business logic for taxi trip operations."""

    async def get_trip_analytics(self, db: AsyncSession) -> TripAnalytics:
        """
        Calculate comprehensive trip analytics including:
        - Total trips
        - Average trip duration
        - Peak hour analysis
        - Vendor distribution
        """
        logger.info("Calculating trip analytics")

        # Run all analytics queries
        total_trips = await self._get_total_trips(db)
        avg_duration = await self._calculate_avg_duration(db)
        peak_hour, peak_count = await self._find_peak_hour(db)
        vendor_dist = await self._get_vendor_distribution(db)

        return TripAnalytics(
            total_trips=total_trips,
            avg_trip_duration_minutes=avg_duration,
            peak_hour=peak_hour,
            peak_hour_trip_count=peak_count,
            vendor_distribution=vendor_dist,
        )

    async def _get_total_trips(self, db: AsyncSession) -> int:
        """Get total number of trips."""
        stmt = select(func.count(TaxiTrip.id))
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def _calculate_avg_duration(self, db: AsyncSession) -> float:
        """Calculate average trip duration in minutes."""
        # Use raw SQL for datetime arithmetic on text columns
        stmt = text("""
            SELECT AVG(
                EXTRACT(epoch FROM
                    dropoff_datetime::timestamp - pickup_datetime::timestamp
                ) / 60
            ) as avg_duration_minutes
            FROM public.nyc_train_synced
            WHERE dropoff_datetime::timestamp > pickup_datetime::timestamp
        """)
        result = await db.execute(stmt)
        avg_minutes = result.scalar()
        return round(avg_minutes or 0.0, 2)

    async def _find_peak_hour(self, db: AsyncSession) -> tuple[int, int]:
        """Find the hour with the most trips."""
        stmt = text("""
            SELECT
                EXTRACT(hour FROM pickup_datetime::timestamp) as hour,
                COUNT(*) as trip_count
            FROM public.nyc_train_synced
            GROUP BY EXTRACT(hour FROM pickup_datetime::timestamp)
            ORDER BY COUNT(*) DESC
            LIMIT 1
        """)
        result = await db.execute(stmt)
        row = result.first()

        if row:
            return int(row.hour), int(row.trip_count)
        return 0, 0

    async def _get_vendor_distribution(self, db: AsyncSession) -> Dict[str, int]:
        """Get distribution of trips by vendor."""
        stmt = (
            select(TaxiTrip.vendor_id, func.count(TaxiTrip.id).label("trip_count"))
            .group_by(TaxiTrip.vendor_id)
            .order_by(func.count(TaxiTrip.id).desc())
            .limit(10)  # Top 10 vendors
        )
        result = await db.execute(stmt)

        return {row.vendor_id: int(row.trip_count) for row in result}

    async def update_vendor_id(
        self, trip_id: int, new_vendor_id: str, db: AsyncSession
    ) -> VendorUpdateResponse:
        """Update the vendor ID for a specific trip in the writable table."""
        logger.info(f"Updating vendor ID for trip {trip_id} to {new_vendor_id}")

        # Check if trip exists in the read table first (for validation)
        check_stmt = select(TaxiTrip).where(TaxiTrip.id == trip_id)
        check_result = await db.execute(check_stmt)
        existing_trip = check_result.scalars().first()

        if not existing_trip:
            raise ValueError(f"Trip with ID {trip_id} not found")

        update_stmt = (
            update(TaxiTrip)
            .where(TaxiTrip.id == trip_id)
            .values(vendor_id=new_vendor_id)
        )
        await db.execute(update_stmt)
        await db.commit()

        logger.info(
            f"Successfully updated trip {trip_id} vendor ID to {new_vendor_id} in nyc_train_s3_read table"
        )

        return VendorUpdateResponse(
            id=trip_id,
            vendor_id=new_vendor_id,
            message="Vendor ID updated successfully in writable table",
        )


async def get_taxi_service() -> TaxiService:
    """Dependency injection for TaxiService."""
    return TaxiService()
