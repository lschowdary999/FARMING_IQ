import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.government_schemes import GovernmentScheme, SchemeRefreshLog
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

class GovernmentSchemeService:
    def __init__(self):
        self.external_apis = [
            {
                "name": "Government of India Schemes API",
                "url": "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                "params": {"api-key": "your-api-key", "format": "json", "limit": 100}
            },
            {
                "name": "Ministry of Agriculture Schemes",
                "url": "https://api.agriculture.gov.in/schemes",
                "params": {"format": "json"}
            }
        ]
    
    async def refresh_schemes_from_external_apis(self, db: Session) -> Dict:
        """Fetch and update schemes from external APIs"""
        refresh_log = SchemeRefreshLog(
            refresh_type="external_api",
            refresh_date=datetime.utcnow(),
            next_refresh=datetime.utcnow() + timedelta(hours=24)
        )
        
        new_schemes_count = 0
        updated_schemes_count = 0
        error_messages = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for api in self.external_apis:
                    try:
                        response = await client.get(api["url"], params=api["params"])
                        if response.status_code == 200:
                            data = response.json()
                            schemes_data = self._parse_external_data(data, api["name"])
                            
                            for scheme_data in schemes_data:
                                existing_scheme = db.query(GovernmentScheme).filter(
                                    GovernmentScheme.name == scheme_data["name"]
                                ).first()
                                
                                if existing_scheme:
                                    # Update existing scheme
                                    self._update_scheme(existing_scheme, scheme_data)
                                    updated_schemes_count += 1
                                else:
                                    # Create new scheme
                                    new_scheme = self._create_scheme(scheme_data)
                                    new_scheme.is_new = True
                                    db.add(new_scheme)
                                    new_schemes_count += 1
                            
                            db.commit()
                            
                    except Exception as e:
                        error_msg = f"Error fetching from {api['name']}: {str(e)}"
                        error_messages.append(error_msg)
                        logger.error(error_msg)
            
            refresh_log.new_schemes_count = new_schemes_count
            refresh_log.updated_schemes_count = updated_schemes_count
            refresh_log.refresh_status = "success" if not error_messages else "partial"
            refresh_log.error_message = "; ".join(error_messages) if error_messages else None
            
        except Exception as e:
            refresh_log.refresh_status = "failed"
            refresh_log.error_message = str(e)
            logger.error(f"Error in refresh_schemes_from_external_apis: {str(e)}")
        
        db.add(refresh_log)
        db.commit()
        
        return {
            "new_schemes": new_schemes_count,
            "updated_schemes": updated_schemes_count,
            "status": refresh_log.refresh_status,
            "errors": error_messages
        }
    
    def _parse_external_data(self, data: Dict, source: str) -> List[Dict]:
        """Parse external API data into our scheme format"""
        schemes = []
        
        # This is a mock implementation - in reality, you'd parse the actual API response
        # For now, we'll create some sample new schemes
        sample_schemes = [
            {
                "name": "Digital Agriculture Mission 2024",
                "description": "Promoting digital technologies in agriculture for better productivity",
                "eligibility_criteria": "Farmers with smartphone and internet access",
                "benefits": "Up to ₹25,000 for digital tools and training",
                "subsidy_percentage": "75%",
                "category": "Digital Agriculture",
                "applicable_states": ["All India"],
                "applicable_crops": ["All Crops"],
                "application_process": "Online application through official portal",
                "required_documents": ["Aadhaar Card", "Land Documents", "Bank Account Details"],
                "contact_info": {"phone": "1800-180-1551", "email": "digitalagri@gov.in"},
                "website_url": "https://digitalagriculture.gov.in",
                "official_apply_url": "https://digitalagriculture.gov.in/apply",
                "is_active": True,
                "expiry_date": datetime.utcnow() + timedelta(days=365)
            },
            {
                "name": "Climate Smart Agriculture Initiative",
                "description": "Supporting farmers in adopting climate-resilient agricultural practices",
                "eligibility_criteria": "Farmers in climate-vulnerable regions",
                "benefits": "Up to ₹50,000 per hectare for climate adaptation measures",
                "subsidy_percentage": "80%",
                "category": "Sustainable Agriculture",
                "applicable_states": ["Maharashtra", "Karnataka", "Tamil Nadu", "Rajasthan"],
                "applicable_crops": ["Millets", "Pulses", "Oilseeds"],
                "application_process": "Through state agriculture departments",
                "required_documents": ["Aadhaar Card", "Land Documents", "Climate Risk Assessment"],
                "contact_info": {"phone": "1800-180-1552", "email": "climateagri@gov.in"},
                "website_url": "https://climateagriculture.gov.in",
                "official_apply_url": "https://climateagriculture.gov.in/apply",
                "is_active": True,
                "expiry_date": datetime.utcnow() + timedelta(days=730)
            }
        ]
        
        return sample_schemes
    
    def _create_scheme(self, scheme_data: Dict) -> GovernmentScheme:
        """Create a new government scheme from data"""
        return GovernmentScheme(
            name=scheme_data["name"],
            description=scheme_data["description"],
            eligibility_criteria=scheme_data["eligibility_criteria"],
            benefits=scheme_data["benefits"],
            subsidy_percentage=scheme_data["subsidy_percentage"],
            category=scheme_data["category"],
            applicable_states=json.dumps(scheme_data["applicable_states"]),
            applicable_crops=json.dumps(scheme_data["applicable_crops"]),
            application_process=scheme_data["application_process"],
            required_documents=json.dumps(scheme_data["required_documents"]),
            contact_info=json.dumps(scheme_data["contact_info"]),
            website_url=scheme_data["website_url"],
            official_apply_url=scheme_data["official_apply_url"],
            is_active=scheme_data["is_active"],
            expiry_date=scheme_data["expiry_date"],
            last_refreshed=datetime.utcnow()
        )
    
    def _update_scheme(self, scheme: GovernmentScheme, scheme_data: Dict):
        """Update existing scheme with new data"""
        scheme.description = scheme_data["description"]
        scheme.eligibility_criteria = scheme_data["eligibility_criteria"]
        scheme.benefits = scheme_data["benefits"]
        scheme.subsidy_percentage = scheme_data["subsidy_percentage"]
        scheme.category = scheme_data["category"]
        scheme.applicable_states = json.dumps(scheme_data["applicable_states"])
        scheme.applicable_crops = json.dumps(scheme_data["applicable_crops"])
        scheme.application_process = scheme_data["application_process"]
        scheme.required_documents = json.dumps(scheme_data["required_documents"])
        scheme.contact_info = json.dumps(scheme_data["contact_info"])
        scheme.website_url = scheme_data["website_url"]
        scheme.official_apply_url = scheme_data["official_apply_url"]
        scheme.is_active = scheme_data["is_active"]
        scheme.expiry_date = scheme_data["expiry_date"]
        scheme.last_refreshed = datetime.utcnow()
        scheme.updated_at = datetime.utcnow()
    
    def get_refresh_status(self, db: Session) -> Dict:
        """Get the last refresh status and next refresh time"""
        last_refresh = db.query(SchemeRefreshLog).order_by(
            SchemeRefreshLog.refresh_date.desc()
        ).first()
        
        if not last_refresh:
            return {
                "last_refresh": None,
                "next_refresh": None,
                "status": "never_refreshed"
            }
        
        return {
            "last_refresh": last_refresh.refresh_date,
            "next_refresh": last_refresh.next_refresh,
            "status": last_refresh.refresh_status,
            "new_schemes": last_refresh.new_schemes_count,
            "updated_schemes": last_refresh.updated_schemes_count,
            "error_message": last_refresh.error_message
        }
    
    def mark_new_schemes_as_old(self, db: Session):
        """Mark all new schemes as not new after user has seen them"""
        db.query(GovernmentScheme).filter(GovernmentScheme.is_new == True).update(
            {"is_new": False}
        )
        db.commit()

# Global service instance
scheme_service = GovernmentSchemeService()
