# Helper function to verify trip ownership
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from ...models.trip import Trip
from ...models.user import User


def verify_trip_ownership(trip_id: str, user: User, db: Session) -> Trip:
    """Verify that the user owns the trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    if trip.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this trip"
        )
    
    return trip

