"""
Lead management service for real estate prospects
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.models.lead import Lead, LeadStatus, LeadSource
from app.models.conversation import Conversation
from app.services.webhook_service import WebhookService
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger("seiketsu.lead_service")


class LeadService:
    """Service for managing real estate leads"""
    
    def __init__(self):
        self.webhook_service = WebhookService()
        self.analytics_service = AnalyticsService()
    
    async def create_lead_from_conversation(
        self,
        conversation_id: str,
        lead_data: Dict[str, Any],
        organization_id: str,
        db: Optional[AsyncSession] = None
    ) -> Lead:
        """Create lead from conversation data"""
        try:
            # Create lead instance
            lead = Lead(
                first_name=lead_data.get("first_name", ""),
                last_name=lead_data.get("last_name", ""),
                email=lead_data.get("email"),
                phone=lead_data.get("phone"),
                organization_id=organization_id,
                conversation_id=conversation_id,
                source=LeadSource.VOICE_CALL,
                status=LeadStatus.NEW,
                created_at=datetime.utcnow()
            )
            
            # Set additional fields from lead_data
            if "budget_min" in lead_data:
                lead.budget_min = lead_data["budget_min"]
            if "budget_max" in lead_data:
                lead.budget_max = lead_data["budget_max"]
            if "timeline" in lead_data:
                lead.timeline = lead_data["timeline"]
            if "property_type" in lead_data:
                lead.preferred_property_type = lead_data["property_type"]
            if "bedrooms" in lead_data:
                lead.preferred_bedrooms = lead_data["bedrooms"]
            if "bathrooms" in lead_data:
                lead.preferred_bathrooms = lead_data["bathrooms"]
            if "location" in lead_data:
                lead.preferred_locations = [lead_data["location"]]
            if "notes" in lead_data:
                lead.qualification_notes = lead_data["notes"]
            
            # Calculate initial lead score
            lead.update_lead_score()
            
            # Set as qualified if score is high enough
            if lead.lead_score >= 60:
                lead.status = LeadStatus.QUALIFIED
            
            # Add to database if session provided
            if db:
                db.add(lead)
                await db.commit()
                await db.refresh(lead)
            
            logger.info(f"Created lead {lead.id} from conversation {conversation_id}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Failed to create lead from conversation {conversation_id}: {e}")
            raise
    
    async def get_lead(
        self,
        lead_id: str,
        db: AsyncSession
    ) -> Optional[Lead]:
        """Get lead by ID"""
        try:
            stmt = select(Lead).where(Lead.id == lead_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            return None
    
    async def get_leads_for_organization(
        self,
        organization_id: str,
        db: AsyncSession,
        status_filter: Optional[LeadStatus] = None,
        source_filter: Optional[LeadSource] = None,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> List[Lead]:
        """Get leads for organization with filtering"""
        try:
            conditions = [Lead.organization_id == organization_id]
            
            if status_filter:
                conditions.append(Lead.status == status_filter)
            
            if source_filter:
                conditions.append(Lead.source == source_filter)
            
            if search_query:
                search_conditions = [
                    Lead.first_name.ilike(f"%{search_query}%"),
                    Lead.last_name.ilike(f"%{search_query}%"),
                    Lead.email.ilike(f"%{search_query}%"),
                    Lead.phone.ilike(f"%{search_query}%")
                ]
                conditions.append(or_(*search_conditions))
            
            stmt = (
                select(Lead)
                .where(and_(*conditions))
                .order_by(desc(Lead.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get leads for organization {organization_id}: {e}")
            return []
    
    async def update_lead_status(
        self,
        lead_id: str,
        new_status: LeadStatus,
        db: AsyncSession,
        notes: Optional[str] = None,
        updated_by_user_id: Optional[str] = None
    ) -> Optional[Lead]:
        """Update lead status"""
        try:
            lead = await self.get_lead(lead_id, db)
            if not lead:
                return None
            
            old_status = lead.status
            lead.status = new_status
            lead.updated_at = datetime.utcnow()
            
            if notes:
                current_notes = lead.notes or ""
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                lead.notes = f"{current_notes}\n[{timestamp}] Status changed from {old_status.value} to {new_status.value}: {notes}".strip()
            
            if updated_by_user_id:
                lead.updated_by = updated_by_user_id
            
            await db.commit()
            
            # Send webhook notification
            await self.webhook_service.send_webhook(
                lead.organization_id,
                "lead.updated",
                {
                    "lead_id": lead.id,
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "updated_at": lead.updated_at.isoformat()
                },
                db
            )
            
            # Track analytics event
            await self.analytics_service.track_event(
                "lead",
                "status_updated",
                lead.organization_id,
                db,
                user_id=updated_by_user_id,
                properties={
                    "lead_id": lead.id,
                    "old_status": old_status.value,
                    "new_status": new_status.value
                }
            )
            
            logger.info(f"Updated lead {lead_id} status from {old_status} to {new_status}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Failed to update lead status {lead_id}: {e}")
            return None
    
    async def assign_lead_to_agent(
        self,
        lead_id: str,
        agent_user_id: str,
        db: AsyncSession,
        assigned_by_user_id: Optional[str] = None
    ) -> Optional[Lead]:
        """Assign lead to agent"""
        try:
            lead = await self.get_lead(lead_id, db)
            if not lead:
                return None
            
            old_agent_id = lead.assigned_agent_id
            lead.assigned_agent_id = agent_user_id
            lead.updated_at = datetime.utcnow()
            
            # Add note about assignment
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            assignment_note = f"[{timestamp}] Lead assigned to agent {agent_user_id}"
            if old_agent_id:
                assignment_note = f"[{timestamp}] Lead reassigned from {old_agent_id} to {agent_user_id}"
            
            current_notes = lead.notes or ""
            lead.notes = f"{current_notes}\n{assignment_note}".strip()
            
            if assigned_by_user_id:
                lead.updated_by = assigned_by_user_id
            
            await db.commit()
            
            # Send webhook notification
            await self.webhook_service.send_webhook(
                lead.organization_id,
                "lead.assigned",
                {
                    "lead_id": lead.id,
                    "assigned_to_user_id": agent_user_id,
                    "assigned_by_user_id": assigned_by_user_id,
                    "assigned_at": lead.updated_at.isoformat()
                },
                db
            )
            
            logger.info(f"Assigned lead {lead_id} to agent {agent_user_id}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Failed to assign lead {lead_id}: {e}")
            return None
    
    async def update_lead_contact_info(
        self,
        lead_id: str,
        contact_data: Dict[str, Any],
        db: AsyncSession,
        updated_by_user_id: Optional[str] = None
    ) -> Optional[Lead]:
        """Update lead contact information"""
        try:
            lead = await self.get_lead(lead_id, db)
            if not lead:
                return None
            
            # Update fields
            if "first_name" in contact_data:
                lead.first_name = contact_data["first_name"]
            if "last_name" in contact_data:
                lead.last_name = contact_data["last_name"]
            if "email" in contact_data:
                lead.email = contact_data["email"]
            if "phone" in contact_data:
                lead.phone = contact_data["phone"]
            if "address_line1" in contact_data:
                lead.address_line1 = contact_data["address_line1"]
            if "city" in contact_data:
                lead.city = contact_data["city"]
            if "state" in contact_data:
                lead.state = contact_data["state"]
            if "postal_code" in contact_data:
                lead.postal_code = contact_data["postal_code"]
            
            lead.updated_at = datetime.utcnow()
            if updated_by_user_id:
                lead.updated_by = updated_by_user_id
            
            # Recalculate lead score
            lead.update_lead_score()
            
            await db.commit()
            
            logger.info(f"Updated contact info for lead {lead_id}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Failed to update lead contact info {lead_id}: {e}")
            return None
    
    async def add_lead_note(
        self,
        lead_id: str,
        note: str,
        db: AsyncSession,
        user_id: Optional[str] = None
    ) -> Optional[Lead]:
        """Add note to lead"""
        try:
            lead = await self.get_lead(lead_id, db)
            if not lead:
                return None
            
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            user_info = f" by {user_id}" if user_id else ""
            new_note = f"[{timestamp}]{user_info}: {note}"
            
            current_notes = lead.notes or ""
            lead.notes = f"{current_notes}\n{new_note}".strip()
            lead.updated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Added note to lead {lead_id}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Failed to add note to lead {lead_id}: {e}")
            return None
    
    async def get_hot_leads(
        self,
        organization_id: str,
        db: AsyncSession,
        limit: int = 20
    ) -> List[Lead]:
        """Get hot leads for organization (high score, urgent timeline, etc.)"""
        try:
            stmt = (
                select(Lead)
                .where(
                    and_(
                        Lead.organization_id == organization_id,
                        Lead.status.in_([LeadStatus.NEW, LeadStatus.QUALIFIED, LeadStatus.CONTACTED])
                    )
                )
                .order_by(desc(Lead.lead_score), desc(Lead.created_at))
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            all_leads = result.scalars().all()
            
            # Filter for hot leads
            hot_leads = [lead for lead in all_leads if lead.is_hot_lead]
            
            return hot_leads
            
        except Exception as e:
            logger.error(f"Failed to get hot leads for organization {organization_id}: {e}")
            return []
    
    async def get_leads_needing_follow_up(
        self,
        organization_id: str,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Lead]:
        """Get leads that need follow-up"""
        try:
            now = datetime.utcnow()
            
            stmt = (
                select(Lead)
                .where(
                    and_(
                        Lead.organization_id == organization_id,
                        Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED]),
                        or_(
                            Lead.next_follow_up_date <= now,
                            and_(
                                Lead.last_contact_date.is_(None),
                                Lead.created_at <= now - timedelta(days=1)
                            )
                        )
                    )
                )
                .order_by(Lead.next_follow_up_date.asc().nullsfirst(), desc(Lead.lead_score))
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get leads needing follow-up: {e}")
            return []
    
    async def bulk_update_lead_tags(
        self,
        lead_ids: List[str],
        tags_to_add: List[str],
        tags_to_remove: List[str],
        db: AsyncSession,
        updated_by_user_id: Optional[str] = None
    ) -> int:
        """Bulk update tags for multiple leads"""
        updated_count = 0
        
        try:
            for lead_id in lead_ids:
                lead = await self.get_lead(lead_id, db)
                if not lead:
                    continue
                
                current_tags = set(lead.tags or [])
                
                # Add new tags
                for tag in tags_to_add:
                    current_tags.add(tag)
                
                # Remove tags
                for tag in tags_to_remove:
                    current_tags.discard(tag)
                
                lead.tags = list(current_tags)
                lead.updated_at = datetime.utcnow()
                if updated_by_user_id:
                    lead.updated_by = updated_by_user_id
                
                updated_count += 1
            
            await db.commit()
            
            logger.info(f"Bulk updated tags for {updated_count} leads")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to bulk update lead tags: {e}")
            return updated_count