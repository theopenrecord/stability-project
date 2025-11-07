"""
SQLAlchemy models for Northwoods Housing Resource database
"""
from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, Enum, DECIMAL, ARRAY, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
import enum

from app.database import Base

# Enums matching database schema
class ResourceCategory(str, enum.Enum):
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

class AccessTier(str, enum.Enum):
    PUBLIC = "public"
    VERIFIED_USER = "verified_user"
    TRUSTED_VERIFIER = "trusted_verifier"
    ADMIN = "admin"

class VerificationMethod(str, enum.Enum):
    MANUAL_PHYSICAL = "manual_physical"
    MANUAL_PHONE = "manual_phone"
    AUTOMATED_WEB = "automated_web"
    COMMUNITY_REPORT = "community_report"
    PARTNER_VERIFIED = "partner_verified"

class ReportType(str, enum.Enum):
    STILL_OPEN = "still_open"
    CLOSED = "closed"
    CHANGED_HOURS = "changed_hours"
    CHANGED_SERVICES = "changed_services"
    NOT_HELPFUL = "not_helpful"
    SAFETY_CONCERN = "safety_concern"
    NEW_RESTRICTIONS = "new_restrictions"
    OTHER = "other"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    password_hash = Column(String(255))
    access_level = Column(Enum(AccessTier), default=AccessTier.PUBLIC, index=True)
    county = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    created_resources = relationship("Resource", back_populates="creator", foreign_keys="Resource.created_by")
    verification_logs = relationship("VerificationLog", back_populates="verifier")
    community_reports = relationship("CommunityReport", back_populates="reporter", foreign_keys="CommunityReport.reported_by")
    saved_resources = relationship("SavedResource", back_populates="user")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(Enum(ResourceCategory), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(Text)
    location = Column(Geography('POINT', srid=4326))
    county = Column(String(100), nullable=False, index=True)
    town = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(500))
    
    # Hours and availability
    hours_of_operation = Column(Text)
    seasonal_availability_summer = Column(Boolean, default=True)
    seasonal_availability_winter = Column(Boolean, default=True)
    
    # Access and restrictions
    restrictions = Column(Text)
    access_tier = Column(Enum(AccessTier), default=AccessTier.PUBLIC, index=True)
    
    # Verification tracking
    last_verified_date = Column(TIMESTAMP, index=True)
    verification_source = Column(String(255))
    verification_confidence = Column(Integer, default=50)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True, index=True)
    
    # Additional structured data
    capacity = Column(Integer)
    cost_info = Column(Text)
    languages_supported = Column(ARRAY(String))
    
    # Special fields for specific resource types
    dump_station_fee = Column(DECIMAL(10, 2))
    propane_price_per_gallon = Column(DECIMAL(10, 2))
    camping_nightly_rate = Column(DECIMAL(10, 2))
    
    # Relationships
    creator = relationship("User", back_populates="created_resources", foreign_keys=[created_by])
    verification_logs = relationship("VerificationLog", back_populates="resource", cascade="all, delete-orphan")
    community_reports = relationship("CommunityReport", back_populates="resource", cascade="all, delete-orphan")
    tags = relationship("ResourceTag", back_populates="resource", cascade="all, delete-orphan")
    saved_by = relationship("SavedResource", back_populates="resource")

class VerificationLog(Base):
    __tablename__ = "verification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    verified_by = Column(Integer, ForeignKey('users.id'))
    verification_method = Column(Enum(VerificationMethod), nullable=False)
    verified_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    notes = Column(Text)
    confidence_score = Column(Integer)
    
    # Relationships
    resource = relationship("Resource", back_populates="verification_logs")
    verifier = relationship("User", back_populates="verification_logs")

class CommunityReport(Base):
    __tablename__ = "community_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    reported_by = Column(Integer, ForeignKey('users.id'))
    report_type = Column(Enum(ReportType), nullable=False)
    details = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    status = Column(String(50), default='pending', index=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(TIMESTAMP)
    admin_notes = Column(Text)
    
    # Relationships
    resource = relationship("Resource", back_populates="community_reports")
    reporter = relationship("User", back_populates="community_reports", foreign_keys=[reported_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_tier = Column(String(20), nullable=False, index=True)
    county = Column(String(100), index=True)
    age_range = Column(String(20))
    household_size = Column(Integer)
    housing_situation = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    session_id = Column(String(255))

class ResourceTag(Base):
    __tablename__ = "resource_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    resource = relationship("Resource", back_populates="tags")

class SavedResource(Base):
    __tablename__ = "saved_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_resources")
    resource = relationship("Resource", back_populates="saved_by")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('user_id', 'resource_id', name='_user_resource_uc'),)
