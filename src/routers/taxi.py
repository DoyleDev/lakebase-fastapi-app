import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_db
from ..models.taxi import TaxiTrip, TaxiTripRead, TripAnalytics, TripCount, TripSample
from ..services.taxi_service import TaxiService, get_taxi_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["taxi"])


@router.get("/count", response_model=TripCount, summary="Get total trip count")
async def get_trip_count(db: AsyncSession = Depends(get_async_db)):
    """Get the total number of trips in the database."""
    try:
        from sqlalchemy import func

        stmt = select(func.count(TaxiTrip.id))
        result = await db.execute(stmt)
        count = result.scalar()
        return TripCount(total_trips=count)
    except Exception as e:
        logger.error(f"Error getting trip count: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trip count")


@router.get("/sample", response_model=TripSample, summary="Get 5 random trip IDs")
async def get_sample_trips(db: AsyncSession = Depends(get_async_db)):
    """Get 5 random trip IDs for testing."""
    try:
        stmt = select(TaxiTrip.id).limit(5)
        result = await db.execute(stmt)
        trip_ids = result.scalars().all()
        return TripSample(sample_trip_ids=trip_ids)
    except Exception as e:
        logger.error(f"Error getting sample trips: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sample trips")


@router.get("/analytics", response_model=TripAnalytics, summary="Get trip analytics")
async def get_trip_analytics(
    taxi_service: TaxiService = Depends(get_taxi_service),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get comprehensive trip analytics including:
    - Total trip count
    - Average trip duration
    - Peak hour analysis
    - Vendor distribution
    """
    try:
        return await taxi_service.get_trip_analytics(db)
    except Exception as e:
        logger.error(f"Error getting trip analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trip analytics")


@router.get(
    "/{trip_id}", response_model=TaxiTripRead, summary="Get a taxi trip by its ID"
)
async def read_trip(
    trip_id: int, response: Response, db: AsyncSession = Depends(get_async_db)
):
    """
    Fetch a single taxi trip by its ID, returning only the four fields:
    id, vendor_id, pickup_datetime, dropoff_datetime.
    """
    try:
        # Validate trip_id (basic validation)
        if trip_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid trip ID provided")

        stmt = select(TaxiTrip).where(TaxiTrip.id == trip_id)
        result = await db.execute(stmt)
        trip = result.scalars().first()

        if not trip:
            logger.info(f"Trip not found: {trip_id}")
            raise HTTPException(
                status_code=404, detail=f"Trip with ID '{trip_id}' not found"
            )

        return trip

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")
