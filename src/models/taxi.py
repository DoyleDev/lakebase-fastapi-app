import os
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TaxiTripBase(SQLModel):
    vendor_id: str
    pickup_datetime: datetime
    dropoff_datetime: datetime


class TaxiTrip(TaxiTripBase, table=True):
    __tablename__ = os.getenv("DEFAULT_POSTGRES_TABLE", None)
    __table_args__ = {"schema": os.getenv("DEFAULT_POSTGRES_SCHEMA", "public")}
    id: Optional[int] = Field(default=None, primary_key=True)


class TaxiTripRead(TaxiTripBase):
    id: int


class TripCount(SQLModel):
    total_trips: int


class TripSample(SQLModel):
    sample_trip_ids: list[int]


class TripAnalytics(SQLModel):
    total_trips: int
    avg_trip_duration_minutes: float
    peak_hour: int
    peak_hour_trip_count: int
    vendor_distribution: dict[str, int]


class VendorUpdate(SQLModel):
    vendor_id: str


class VendorUpdateResponse(SQLModel):
    id: int
    vendor_id: str
    message: str


class TripListResponse(SQLModel):
    trips: list[TaxiTripRead]
    pagination: "PaginationInfo"


class PaginationInfo(SQLModel):
    page: int
    page_size: int
    total_pages: int
    total_count: int
    has_next: bool
    has_previous: bool
    next_cursor: int | None = None
    previous_cursor: int | None = None


class CursorPaginationInfo(SQLModel):
    page_size: int
    has_next: bool
    has_previous: bool
    next_cursor: int | None = None
    previous_cursor: int | None = None


class TripListCursorResponse(SQLModel):
    trips: list[TaxiTripRead]
    pagination: CursorPaginationInfo
