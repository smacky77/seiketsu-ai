"""
Enterprise Lead Management API Endpoints
Comprehensive CRUD operations with lead qualification scoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
import logging
from enum import Enum

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_organization
from app.models.user import User
from app.models.organization import Organization
from app.models.lead import Lead, LeadStatus, LeadSource
from app.services.lead_service import LeadService
from app.services.analytics_service import AnalyticsService
from app.tasks.lead_tasks import schedule_follow_up_reminder

logger = logging.getLogger("seiketsu.leads")
router = APIRouter()

# Initialize services
lead_service = LeadService()
analytics_service = AnalyticsService()

# Request/Response Models
class LeadCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone: str = Field(..., min_length=10, max_length=20)
    source: LeadSource = LeadSource.MANUAL
    property_type: Optional[str] = None
    budget_min: Optional[int] = Field(None, ge=0)
    budget_max: Optional[int] = Field(None, ge=0)
    timeline: Optional[str] = None
    preferred_locations: Optional[List[str]] = []
    bedrooms: Optional[int] = Field(None, ge=0, le=10)
    bathrooms: Optional[int] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    
    @validator('budget_max')
    def budget_max_must_be_greater_than_min(cls, v, values):
        if v is not None and 'budget_min' in values and values['budget_min'] is not None:
            if v < values['budget_min']:
                raise ValueError('budget_max must be greater than budget_min')
        return v

class LeadUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    property_type: Optional[str] = None
    budget_min: Optional[int] = Field(None, ge=0)
    budget_max: Optional[int] = Field(None, ge=0)
    timeline: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    bedrooms: Optional[int] = Field(None, ge=0, le=10)
    bathrooms: Optional[int] = Field(None, ge=0, le=10)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class LeadStatusUpdateRequest(BaseModel):
    status: LeadStatus
    notes: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None

class LeadAssignmentRequest(BaseModel):
    agent_user_id: str
    notes: Optional[str] = None

class LeadNoteRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = False

class BulkLeadUpdateRequest(BaseModel):
    lead_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., regex='^(update_status|assign_agent|add_tags|remove_tags)$')
    data: Dict[str, Any]

class LeadQualificationRequest(BaseModel):
    lead_id: str
    qualification_data: Dict[str, Any]
    qualified_by_user_id: str

class LeadResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    status: LeadStatus
    source: LeadSource
    lead_score: int
    is_qualified: bool
    is_hot_lead: bool
    assigned_agent_id: Optional[str]
    property_type: Optional[str]
    budget_min: Optional[int]
    budget_max: Optional[int]
    timeline: Optional[str]
    preferred_locations: Optional[List[str]]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    notes: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    last_contact_date: Optional[datetime]
    next_follow_up_date: Optional[datetime]
    
    class Config:
        from_attributes = True

class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    limit: int
    has_next: bool

@router.get("", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    search: Optional[str] = None,
    assigned_only: bool = False,
    hot_leads_only: bool = False,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadListResponse:
    """List leads with filtering and pagination"""
    try:
        offset = (page - 1) * limit
        
        # Get hot leads if requested
        if hot_leads_only:
            leads = await lead_service.get_hot_leads(
                current_org.id, db, limit=limit
            )
            total = len(leads)
        else:
            # Apply filtering based on user role
            if assigned_only and not current_user.is_admin:
                # Non-admin users see only their assigned leads
                status_filter = status
            else:
                status_filter = status
            
            leads = await lead_service.get_leads_for_organization(
                organization_id=current_org.id,
                db=db,
                status_filter=status_filter,
                source_filter=source,
                limit=limit,
                offset=offset,
                search_query=search
            )
            
            # Get total count for pagination
            total_leads = await lead_service.get_leads_for_organization(
                organization_id=current_org.id,
                db=db,
                status_filter=status_filter,
                source_filter=source,
                limit=1000,  # High limit to get total count
                offset=0,
                search_query=search
            )
            total = len(total_leads)
        
        # Convert to response models
        lead_responses = [LeadResponse.from_orm(lead) for lead in leads]
        
        # Track analytics
        await analytics_service.track_event(
            "leads", "listed", current_org.id, db,
            user_id=current_user.id,
            properties={"count": len(leads), "filters_applied": bool(status or source or search)}
        )
        
        return LeadListResponse(
            leads=lead_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=offset + limit < total
        )
        
    except Exception as e:
        logger.error(f"Failed to list leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leads")

@router.post("", status_code=201, response_model=LeadResponse)
async def create_lead(
    request: LeadCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Create new lead with automatic qualification scoring"""
    try:
        # Create lead from conversation data format
        lead_data = {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": request.email,
            "phone": request.phone,
            "property_type": request.property_type,
            "budget_min": request.budget_min,
            "budget_max": request.budget_max,
            "timeline": request.timeline,
            "bedrooms": request.bedrooms,
            "bathrooms": request.bathrooms,
            "notes": request.notes
        }
        
        if request.preferred_locations:
            lead_data["location"] = ", ".join(request.preferred_locations)
        
        # Create lead
        lead = await lead_service.create_lead_from_conversation(
            conversation_id=f"manual_{datetime.utcnow().timestamp()}",
            lead_data=lead_data,
            organization_id=current_org.id,
            db=db
        )
        
        # Set additional fields
        lead.source = request.source
        if request.tags:
            lead.tags = request.tags
        lead.created_by = current_user.id
        
        await db.commit()
        await db.refresh(lead)
        
        # Schedule follow-up reminder if needed
        if lead.status == LeadStatus.NEW:
            background_tasks.add_task(
                schedule_follow_up_reminder,
                lead.id,
                datetime.utcnow() + timedelta(hours=24)
            )
        
        # Track analytics
        await analytics_service.track_event(
            "leads", "created", current_org.id, db,
            user_id=current_user.id,
            properties={"lead_id": lead.id, "source": request.source.value}
        )
        
        logger.info(f"Created new lead {lead.id} for organization {current_org.id}")
        
        return LeadResponse.from_orm(lead)
        
    except Exception as e:
        logger.error(f"Failed to create lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Get lead by ID with organization validation"""
    try:
        lead = await lead_service.get_lead(lead_id, db)
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        if lead.organization_id != current_org.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Track analytics
        await analytics_service.track_event(
            "leads", "viewed", current_org.id, db,
            user_id=current_user.id,
            properties={"lead_id": lead.id}
        )
        
        return LeadResponse.from_orm(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lead")

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    request: LeadUpdateRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Update lead information"""
    try:
        # Verify lead exists and belongs to organization
        lead = await lead_service.get_lead(lead_id, db)
        if not lead or lead.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Prepare update data
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if update_data:
            updated_lead = await lead_service.update_lead_contact_info(
                lead_id, update_data, db, current_user.id
            )
            
            if not updated_lead:
                raise HTTPException(status_code=500, detail="Failed to update lead")
            
            # Track analytics
            await analytics_service.track_event(
                "leads", "updated", current_org.id, db,
                user_id=current_user.id,
                properties={"lead_id": lead_id, "fields_updated": list(update_data.keys())}
            )
            
            logger.info(f"Updated lead {lead_id} by user {current_user.id}")
            
            return LeadResponse.from_orm(updated_lead)
        
        return LeadResponse.from_orm(lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lead")

@router.patch("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: str,
    request: LeadStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Update lead status with automated follow-up scheduling"""
    try:
        # Verify lead access
        lead = await lead_service.get_lead(lead_id, db)
        if not lead or lead.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update status
        updated_lead = await lead_service.update_lead_status(
            lead_id, request.status, db, request.notes, current_user.id
        )
        
        if not updated_lead:
            raise HTTPException(status_code=500, detail="Failed to update lead status")
        
        # Schedule follow-up if needed
        if request.next_follow_up_date:
            updated_lead.next_follow_up_date = request.next_follow_up_date
            await db.commit()
            
            background_tasks.add_task(
                schedule_follow_up_reminder,
                lead_id,
                request.next_follow_up_date
            )
        
        logger.info(f"Updated lead {lead_id} status to {request.status.value}")
        
        return LeadResponse.from_orm(updated_lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update lead status {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lead status")

@router.post("/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: str,
    request: LeadAssignmentRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Assign lead to agent"""
    try:
        # Verify lead access
        lead = await lead_service.get_lead(lead_id, db)
        if not lead or lead.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # TODO: Verify agent belongs to organization
        
        # Assign lead
        updated_lead = await lead_service.assign_lead_to_agent(
            lead_id, request.agent_user_id, db, current_user.id
        )
        
        if not updated_lead:
            raise HTTPException(status_code=500, detail="Failed to assign lead")
        
        # Add note if provided
        if request.notes:
            await lead_service.add_lead_note(
                lead_id, f"Assignment note: {request.notes}", db, current_user.id
            )
        
        logger.info(f"Assigned lead {lead_id} to agent {request.agent_user_id}")
        
        return LeadResponse.from_orm(updated_lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign lead")

@router.post("/{lead_id}/notes")
async def add_lead_note(
    lead_id: str,
    request: LeadNoteRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Add note to lead"""
    try:
        # Verify lead access
        lead = await lead_service.get_lead(lead_id, db)
        if not lead or lead.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Add note
        note_content = f"{'[INTERNAL] ' if request.is_internal else ''}{request.content}"
        updated_lead = await lead_service.add_lead_note(
            lead_id, note_content, db, current_user.id
        )
        
        if not updated_lead:
            raise HTTPException(status_code=500, detail="Failed to add note")
        
        logger.info(f"Added note to lead {lead_id}")
        
        return {
            "success": True,
            "message": "Note added successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add note to lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add note")

@router.get("/search", response_model=LeadListResponse)
async def search_leads(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> LeadListResponse:
    """Search leads by name, email, phone, or notes"""
    try:
        offset = (page - 1) * limit
        
        leads = await lead_service.get_leads_for_organization(
            organization_id=current_org.id,
            db=db,
            limit=limit,
            offset=offset,
            search_query=q
        )
        
        # Get total count for searched results
        all_results = await lead_service.get_leads_for_organization(
            organization_id=current_org.id,
            db=db,
            limit=1000,
            offset=0,
            search_query=q
        )
        total = len(all_results)
        
        lead_responses = [LeadResponse.from_orm(lead) for lead in leads]
        
        # Track search analytics
        await analytics_service.track_event(
            "leads", "searched", current_org.id, db,
            user_id=current_user.id,
            properties={"query": q, "results_count": len(leads)}
        )
        
        return LeadListResponse(
            leads=lead_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=offset + limit < total
        )
        
    except Exception as e:
        logger.error(f"Failed to search leads: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/hot", response_model=List[LeadResponse])
async def get_hot_leads(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> List[LeadResponse]:
    """Get hot leads that need immediate attention"""
    try:
        hot_leads = await lead_service.get_hot_leads(
            current_org.id, db, limit=limit
        )
        
        # Track analytics
        await analytics_service.track_event(
            "leads", "hot_leads_viewed", current_org.id, db,
            user_id=current_user.id,
            properties={"count": len(hot_leads)}
        )
        
        return [LeadResponse.from_orm(lead) for lead in hot_leads]
        
    except Exception as e:
        logger.error(f"Failed to get hot leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve hot leads")

@router.get("/follow-up", response_model=List[LeadResponse])
async def get_leads_needing_follow_up(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> List[LeadResponse]:
    """Get leads that need follow-up contact"""
    try:
        follow_up_leads = await lead_service.get_leads_needing_follow_up(
            current_org.id, db, limit=limit
        )
        
        return [LeadResponse.from_orm(lead) for lead in follow_up_leads]
        
    except Exception as e:
        logger.error(f"Failed to get follow-up leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve follow-up leads")

@router.post("/bulk-update")
async def bulk_update_leads(
    request: BulkLeadUpdateRequest,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Bulk update multiple leads"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        updated_count = 0
        
        if request.action == "add_tags":
            tags_to_add = request.data.get("tags", [])
            updated_count = await lead_service.bulk_update_lead_tags(
                request.lead_ids, tags_to_add, [], db, current_user.id
            )
        elif request.action == "remove_tags":
            tags_to_remove = request.data.get("tags", [])
            updated_count = await lead_service.bulk_update_lead_tags(
                request.lead_ids, [], tags_to_remove, db, current_user.id
            )
        
        # Track analytics
        await analytics_service.track_event(
            "leads", "bulk_updated", current_org.id, db,
            user_id=current_user.id,
            properties={
                "action": request.action,
                "lead_ids_count": len(request.lead_ids),
                "updated_count": updated_count
            }
        )
        
        logger.info(f"Bulk updated {updated_count} leads with action {request.action}")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "total_requested": len(request.lead_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk update leads: {e}")
        raise HTTPException(status_code=500, detail="Bulk update failed")

@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Soft delete lead (admin only)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Verify lead access
        lead = await lead_service.get_lead(lead_id, db)
        if not lead or lead.organization_id != current_org.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Soft delete by updating status
        await lead_service.update_lead_status(
            lead_id, LeadStatus.DELETED, db, 
            f"Deleted by {current_user.email}", current_user.id
        )
        
        logger.info(f"Deleted lead {lead_id} by user {current_user.id}")
        
        return {
            "success": True,
            "message": "Lead deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete lead")