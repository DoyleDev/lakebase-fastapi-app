from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TaxiTripBase(SQLModel):
    vendor_id: str
    pickup_datetime: datetime
    dropoff_datetime: datetime


class TaxiTrip(TaxiTripBase, table=True):
    __tablename__ = "nyc_train_synced"
    __table_args__ = {"schema": "public"}
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
