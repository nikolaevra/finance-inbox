import logging
import yaml
from typing import Dict, Optional
from datetime import datetime, timezone
from database import get_supabase
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserPromptService:
    """Service for managing user-specific email categorization prompts"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    def get_default_prompt_template(self) -> str:
        """Get the default prompt template from YAML file"""
        try:
            config_path = Path(__file__).parent.parent / "prompts" / "email_categorization.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('template', '')
        except Exception as e:
            logger.warning(f"⚠️ Could not load default template: {str(e)}")
            raise e
    
    def get_user_prompt_config(self, user_id: str) -> Dict:
        """Get the active prompt configuration for a user"""
        
        try:
            # Don't use .single() as it throws error when no rows found
            result = self.supabase.table("user_prompts").select("*").eq("user_id", user_id).eq("is_active", True).eq("name", "email_categorization").execute()
            
            if result.data and len(result.data) > 0:
                prompt_data = result.data[0]
                return {
                    'id': prompt_data['id'],
                    'name': prompt_data['name'],
                    'model': prompt_data['model'],
                    'temperature': float(prompt_data['temperature']),
                    'max_tokens': prompt_data['max_tokens'],
                    'timeout': prompt_data['timeout'],
                    'prompt_version': prompt_data['prompt_version'],
                    'template': prompt_data['template'],
                    'created_at': prompt_data['created_at'],
                    'updated_at': prompt_data['updated_at']
                }
            else:
                # No custom prompt found, create default prompt for user
                logger.info(f"📝 Creating default prompt for user {user_id}")
                return self.create_default_prompt_for_user(user_id)
                
        except Exception as e:
            logger.error(f"❌ Error getting user prompt config: {str(e)}")
            # Check if it's the "no rows" error and try to create default
            if "PGRST116" in str(e) or "0 rows" in str(e):
                logger.info(f"📝 No prompt found, creating default for user {user_id}")
                try:
                    return self.create_default_prompt_for_user(user_id)
                except Exception as create_error:
                    logger.error(f"❌ Failed to create default prompt: {str(create_error)}")
                    return self.get_fallback_config()
            # Return fallback configuration
            return self.get_fallback_config()
    
    def create_default_prompt_for_user(self, user_id: str) -> Dict:
        """Create a default prompt configuration for a new user"""
        try:
            default_template = self.get_default_prompt_template()
            
            prompt_data = {
                "user_id": user_id,
                "name": "email_categorization",
                "model": "gpt-3.5-turbo",
                "temperature": 0.1,
                "max_tokens": 200,
                "timeout": 10,
                "prompt_version": "1.0",
                "template": default_template,
                "is_active": True
            }
            
            result = self.supabase.table("user_prompts").insert(prompt_data).execute()
            
            if result.data:
                created_prompt = result.data[0]
                logger.info(f"✅ Created default prompt for user {user_id}")
                return {
                    'id': created_prompt['id'],
                    'name': created_prompt['name'],
                    'model': created_prompt['model'],
                    'temperature': float(created_prompt['temperature']),
                    'max_tokens': created_prompt['max_tokens'],
                    'timeout': created_prompt['timeout'],
                    'prompt_version': created_prompt['prompt_version'],
                    'template': created_prompt['template'],
                    'created_at': created_prompt['created_at'],
                    'updated_at': created_prompt['updated_at']
                }
            else:
                raise Exception("Failed to create default prompt")
                
        except Exception as e:
            logger.error(f"❌ Error creating default prompt for user {user_id}: {str(e)}")
            return self.get_fallback_config()
    
    def update_user_prompt(self, user_id: str, prompt_data: Dict) -> Dict:
        """Update user's prompt configuration"""
        try:
            # Get current prompt
            current_result = self.supabase.table("user_prompts").select("id").eq("user_id", user_id).eq("is_active", True).eq("name", "email_categorization").single().execute()
            
            update_data = {
                "model": prompt_data.get("model", "gpt-3.5-turbo"),
                "temperature": prompt_data.get("temperature", 0.1),
                "max_tokens": prompt_data.get("max_tokens", 200),
                "timeout": prompt_data.get("timeout", 10),
                "template": prompt_data.get("template"),
                "prompt_version": str(float(prompt_data.get("prompt_version", "1.0")) + 0.1),  # Increment version
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if current_result.data:
                # Update existing prompt
                prompt_id = current_result.data['id']
                result = self.supabase.table("user_prompts").update(update_data).eq("id", prompt_id).execute()
                
                if result.data:
                    logger.info(f"✅ Updated prompt for user {user_id}")
                    return {"success": True, "message": "Prompt updated successfully"}
                else:
                    raise Exception("Failed to update prompt")
            else:
                # Create new prompt
                update_data.update({
                    "user_id": user_id,
                    "name": "email_categorization",
                    "is_active": True
                })
                result = self.supabase.table("user_prompts").insert(update_data).execute()
                
                if result.data:
                    logger.info(f"✅ Created new prompt for user {user_id}")
                    return {"success": True, "message": "Prompt created successfully"}
                else:
                    raise Exception("Failed to create prompt")
                    
        except Exception as e:
            logger.error(f"❌ Error updating user prompt: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_fallback_config(self) -> Dict:
        """Get fallback configuration when database fails"""
        return {
            'id': None,
            'name': 'email_categorization',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.1,
            'max_tokens': 200,
            'timeout': 10,
            'prompt_version': '1.0',
            'template': self.get_default_prompt_template(),
            'created_at': None,
            'updated_at': None
        }

# Global service instance
user_prompt_service = UserPromptService() 