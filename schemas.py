"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums for validation
class ResourceCategory(str, Enum):
    FOOD = "food"
    SHELTER = "shelter"
    HEALTHCARE = "healthcare"
    WASTE_DISPOSAL = "waste_disposal"
    PROPANE = "propane"
    CAMPING = "camping"
    DAY_CENTER = "day_center"
    HYGIENE = "hygiene"
    MAIL_ADDRESS = "mail_address"
    WIFI_CHARGING = "wifi_charging"
    CASE_MANAGEMENT = "case_management"
    TRANSPORTATION = "transportation"
    ASSISTANCE_PROGRAM = "assistance_program"
    LAND_OPPORTUNITY = "land_opportunity"
    LEGAL_AID = "legal_aid"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    VETERANS = "veterans"
    OTHER = "other"

class AccessTier(str, Enum):
    PUBLIC = "public"
    VERIFIED_USER = "verified_user"
    TRUSTED_VERIFIER = "trusted_verifier"
    ADMIN = "admin"

# Location schema
class LocationCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class LocationResponse(BaseModel):
    latitude: float
    longitude: float

# Resource schemas
class ResourceBase(BaseModel):
    resource_type: ResourceCategory
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    county: str = Field(..., min_length=1, max_length=100)
    town: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    hours_of_operation: Optional[str] = None
    seasonal_availability_summer: bool = True
    seasonal_availability_winter: bool = True
    restrictions: Optional[str] = None
    access_tier: AccessTier = AccessTier.PUBLIC
    capacity: Optional[int] = None
    cost_info: Optional[str] = None
    languages_supported: Optional[List[str]] = None
    dump_station_fee: Optional[float] = None
    propane_price_per_gallon: Optional[float] = None
    camping_nightly_rate: Optional[float] = None

class ResourceCreate(ResourceBase):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    hours_of_operation: Optional[str] = None
    seasonal_availability_summer: Optional[bool] = None
    seasonal_availability_winter: Optional[bool] = None
    restrictions: Optional[str] = None
    capacity: Optional[int] = None
    cost_info: Optional[str] = None
    dump_station_fee: Optional[float] = None
    propane_price_per_gallon: Optional[float] = None
    camping_nightly_rate: Optional[float] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

class ResourceResponse(ResourceBase):
    id: int
    location: Optional[LocationResponse] = None
    last_verified_date: Optional[datetime] = None
    verification_confidence: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Search parameters
class ResourceSearchParams(BaseModel):
    resource_type: Optional[ResourceCategory] = None
    county: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_miles: Optional[float] = Field(None, gt=0, le=100)
    seasonal_winter: Optional[bool] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

# Community Report schemas
class CommunityReportCreate(BaseModel):
    resource_id: int
    report_type: str
    details: Optional[str] = None

class CommunityReportResponse(BaseModel):
    id: int
    resource_id: int
    report_type: str
    details: Optional[str]
    created_at: datetime
    status: str
    
    class Config:
        from_attributes = True

# Assessment schemas
class AssessmentCreate(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_tier: str
    county: Optional[str] = None
    age_range: Optional[str] = None
    household_size: Optional[int] = Field(None, ge=1)
    housing_situation: Optional[str] = None

class AssessmentResponse(BaseModel):
    id: int
    risk_score: int
    risk_tier: str
    county: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Response wrapper for lists
class ResourceListResponse(BaseModel):
    total: int
    items: List[ResourceResponse]
    limit: int
    offset: int
