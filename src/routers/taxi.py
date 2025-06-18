import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_db
from ..models.taxi import (
    CursorPaginationInfo,
    PaginationInfo,
    TaxiTrip,
    TaxiTripRead,
    TripAnalytics,
    TripCount,
    TripListCursorResponse,
    TripListResponse,
    TripSample,
    VendorUpdate,
    VendorUpdateResponse,
)
from ..services.taxi_service import TaxiService, get_taxi_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["taxi"])


@router.get("/count", response_model=TripCount, summary="Get total trip count")
async def get_trip_count(db: AsyncSession = Depends(get_async_db)):
    """Get the total number of trips in the database."""
    try:
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
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")


@router.get(
    "/pages",
    response_model=TripListResponse,
    summary="Get trips with page-based pagination",
)
async def get_trips_by_page(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        100, ge=1, le=1000, description="Number of records per page (max 1000)"
    ),
    include_count: bool = Query(
        True, description="Include total count for pagination info"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get trips using traditional page-based pagination.

    **Best for:**
    - Small to medium datasets
    - Building traditional pagination UI with page numbers
    - When users need to jump to specific pages

    **Usage:**
    - `/trips/pages?page=1&page_size=100`
    - `/trips/pages?page=5&page_size=50&include_count=false`
    """
    try:
        if include_count:
            count_stmt = select(func.count(TaxiTrip.id))
            count_result = await db.execute(count_stmt)
            total_count = count_result.scalar()
            total_pages = (total_count + page_size - 1) // page_size
        else:
            total_count = -1
            total_pages = -1

        offset = (page - 1) * page_size
        stmt = (
            select(
                TaxiTrip.id,
                TaxiTrip.vendor_id,
                TaxiTrip.pickup_datetime,
                TaxiTrip.dropoff_datetime,
            )
            .order_by(TaxiTrip.id)
            .offset(offset)
            .limit(page_size + 1)  # Get one extra to check has_next
        )

        result = await db.execute(stmt)
        all_trips = result.all()

        has_next = len(all_trips) > page_size
        trips_data = all_trips[:page_size]
        has_previous = page > 1

        trips = [
            TaxiTripRead(
                id=row[0],
                vendor_id=row[1],
                pickup_datetime=row[2],
                dropoff_datetime=row[3],
            )
            for row in trips_data
        ]

        next_cursor = trips[-1].id if trips and has_next else None
        previous_cursor = trips[0].id - page_size if trips and has_previous else None

        pagination_info = PaginationInfo(
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_count=total_count,
            has_next=has_next,
            has_previous=has_previous,
            next_cursor=next_cursor,
            previous_cursor=max(0, previous_cursor) if previous_cursor else None,
        )

        return TripListResponse(trips=trips, pagination=pagination_info)

    except Exception as e:
        logger.error(f"Error getting page-based trips: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trips")


@router.get(
    "/stream",
    response_model=TripListCursorResponse,
    summary="Get trips with cursor-based pagination",
)
async def get_trips_by_cursor(
    cursor: int = Query(
        0, ge=0, description="Start after this trip ID (0 for beginning)"
    ),
    page_size: int = Query(
        100, ge=1, le=1000, description="Number of records to fetch (max 1000)"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get trips using efficient cursor-based pagination.

    **Best for:**
    - Large datasets (millions of records)
    - High-performance applications
    - Infinite scroll UIs
    - Real-time data feeds

    **Usage:**
    - First page: `/trips/stream?cursor=0&page_size=100`
    - Next page: `/trips/stream?cursor=100&page_size=100`
    - Jump to ID: `/trips/stream?cursor=12345&page_size=100` (shows records after ID 12345)
    """
    try:
        stmt = (
            select(
                TaxiTrip.id,
                TaxiTrip.vendor_id,
                TaxiTrip.pickup_datetime,
                TaxiTrip.dropoff_datetime,
            )
            .where(TaxiTrip.id > cursor)
            .order_by(TaxiTrip.id)
            .limit(page_size + 1)  # Get one extra to check has_next
        )

        result = await db.execute(stmt)
        all_trips = result.all()

        has_next = len(all_trips) > page_size
        trips_data = all_trips[:page_size]
        has_previous = cursor > 0

        trips = [
            TaxiTripRead(
                id=row[0],
                vendor_id=row[1],
                pickup_datetime=row[2],
                dropoff_datetime=row[3],
            )
            for row in trips_data
        ]

        next_cursor = trips[-1].id if trips and has_next else None
        previous_cursor = max(0, cursor - page_size) if has_previous else None

        pagination_info = CursorPaginationInfo(
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
        )

        return TripListCursorResponse(trips=trips, pagination=pagination_info)

    except Exception as e:
        logger.error(f"Error getting cursor-based trips: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trips")


@router.post(
    "/{trip_id}/vendor",
    response_model=VendorUpdateResponse,
    summary="Update trip vendor ID",
)
async def update_trip_vendor(
    trip_id: int,
    vendor_data: VendorUpdate,
    taxi_service: TaxiService = Depends(get_taxi_service),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update the vendor ID for a specific trip.

    - **trip_id**: The ID of the trip to update
    - **vendor_id**: The new vendor ID to assign
    """
    try:
        return await taxi_service.update_vendor_id(trip_id, vendor_data.vendor_id, db)
    except ValueError as e:
        logger.info(f"Trip not found for update: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vendor for trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vendor ID")
