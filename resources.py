"""
Resources API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from geoalchemy2.functions import ST_Distance, ST_GeogFromText
from geoalchemy2.elements import WKTElement
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.ResourceResponse, status_code=201)
def create_resource(
    resource: schemas.ResourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new resource.
    
    Requires resource_type, name, and county at minimum.
    Optional location (lat/long) for proximity searches.
    """
    # Create resource dict
    resource_data = resource.dict(exclude={'latitude', 'longitude'})
    
    # Handle location if provided
    if resource.latitude is not None and resource.longitude is not None:
        # Create PostGIS point
        resource_data['location'] = f'POINT({resource.longitude} {resource.latitude})'
    
    db_resource = models.Resource(**resource_data)
    
    try:
        db.add(db_resource)
        db.commit()
        db.refresh(db_resource)
        
        return db_resource
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating resource: {str(e)}")

@router.get("/", response_model=schemas.ResourceListResponse)
def list_resources(
    resource_type: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    radius_miles: Optional[float] = Query(None, gt=0, le=100),
    seasonal_winter: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List resources with optional filtering.
    
    Filters:
    - resource_type: Type of resource (food, shelter, etc.)
    - county: Filter by county
    - latitude/longitude + radius_miles: Proximity search
    - seasonal_winter: Only show resources available in winter
    - limit/offset: Pagination
    """
    query = db.query(models.Resource).filter(models.Resource.is_active == True)
    
    # Apply filters
    if resource_type:
        query = query.filter(models.Resource.resource_type == resource_type)
    
    if county:
        query = query.filter(models.Resource.county.ilike(f"%{county}%"))
    
    if seasonal_winter is not None:
        query = query.filter(models.Resource.seasonal_availability_winter == seasonal_winter)
    
    # Proximity search if coordinates provided
    if latitude is not None and longitude is not None and radius_miles is not None:
        # Convert miles to meters (PostGIS uses meters)
        radius_meters = radius_miles * 1609.34
        point = f'POINT({longitude} {latitude})'
        
        # Filter by distance
        query = query.filter(
            func.ST_DWithin(
                models.Resource.location,
                func.ST_GeogFromText(point),
                radius_meters
            )
        )
        
        # Order by distance (closest first)
        query = query.order_by(
            func.ST_Distance(
                models.Resource.location,
                func.ST_GeogFromText(point)
            )
        )
    else:
        # Default ordering
        query = query.order_by(models.Resource.name)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    resources = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "items": resources,
        "limit": limit,
        "offset": offset
    }

@router.get("/{resource_id}", response_model=schemas.ResourceResponse)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific resource by ID.
    """
    resource = db.query(models.Resource).filter(
        models.Resource.id == resource_id,
        models.Resource.is_active == True
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return resource

@router.put("/{resource_id}", response_model=schemas.ResourceResponse)
def update_resource(
    resource_id: int,
    resource_update: schemas.ResourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a resource.
    
    Only provided fields will be updated.
    """
    db_resource = db.query(models.Resource).filter(
        models.Resource.id == resource_id,
        models.Resource.is_active == True
    ).first()
    
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Update fields
    update_data = resource_update.dict(exclude_unset=True, exclude={'latitude', 'longitude'})
    
    # Handle location update if provided
    if resource_update.latitude is not None and resource_update.longitude is not None:
        update_data['location'] = f'POINT({resource_update.longitude} {resource_update.latitude})'
    
    for field, value in update_data.items():
        setattr(db_resource, field, value)
    
    try:
        db.commit()
        db.refresh(db_resource)
        return db_resource
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating resource: {str(e)}")

@router.delete("/{resource_id}", status_code=204)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a resource (marks as inactive).
    """
    db_resource = db.query(models.Resource).filter(
        models.Resource.id == resource_id
    ).first()
    
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    db_resource.is_active = False
    
    try:
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting resource: {str(e)}")

@router.get("/counties/list", response_model=List[str])
def list_counties(db: Session = Depends(get_db)):
    """
    Get list of all counties that have resources.
    """
    counties = db.query(models.Resource.county).filter(
        models.Resource.is_active == True
    ).distinct().order_by(models.Resource.county).all()
    
    return [county[0] for county in counties]

@router.get("/types/list", response_model=List[str])
def list_resource_types(db: Session = Depends(get_db)):
    """
    Get list of all resource types currently in database.
    """
    types = db.query(models.Resource.resource_type).filter(
        models.Resource.is_active == True
    ).distinct().all()
    
    return [t[0].value for t in types]
