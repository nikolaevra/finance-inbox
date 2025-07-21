from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services.auth_service import get_current_user_profile
from services.user_prompt_service import user_prompt_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["prompt-settings"])

class PromptUpdateRequest(BaseModel):
    template: str
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 200
    timeout: Optional[int] = 10

class PromptValidationRequest(BaseModel):
    template: str

@router.get("/prompt")
async def get_user_prompt(current_user_profile: dict = Depends(get_current_user_profile)):
    """Get user's current prompt configuration"""
    try:
        user_id = current_user_profile["user_id"]
        logger.info(f"🔍 Getting prompt configuration for user {user_id}")
        
        prompt_config = user_prompt_service.get_user_prompt_config(user_id)
        
        return {
            "success": True,
            "prompt": prompt_config
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting prompt configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/prompt")
async def update_user_prompt(request: PromptUpdateRequest, current_user_profile: dict = Depends(get_current_user_profile)):
    """Update user's prompt configuration"""
    try:
        user_id = current_user_profile["user_id"]
        logger.info(f"📝 Updating prompt configuration for user {user_id}")
        
        # Validate template has required variables
        template = request.template
        required_variables = ['{subject}', '{sender}', '{content}']
        missing_variables = [var for var in required_variables if var not in template]
        
        if missing_variables:
            raise HTTPException(
                status_code=400,
                detail=f"Template must contain these variables: {missing_variables}"
            )
        
        # Convert request to dict for the service
        prompt_data = {
            'template': request.template,
            'model': request.model,
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'timeout': request.timeout
        }
        
        # Update the prompt
        result = user_prompt_service.update_user_prompt(user_id, prompt_data)
        
        if result.get('success'):
            logger.info(f"✅ Successfully updated prompt for user {user_id}")
            return result
        else:
            logger.error(f"❌ Failed to update prompt for user {user_id}: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to update prompt'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating prompt configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompt/reset")
async def reset_user_prompt(current_user_profile: dict = Depends(get_current_user_profile)):
    """Reset user's prompt to default"""
    try:
        user_id = current_user_profile["user_id"]
        logger.info(f"🔄 Resetting prompt to default for user {user_id}")
        
        # Get default template
        default_template = user_prompt_service.get_default_prompt_template()
        
        # Reset prompt data
        reset_data = {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.1,
            'max_tokens': 200,
            'timeout': 10,
            'template': default_template
        }
        
        result = user_prompt_service.update_user_prompt(user_id, reset_data)
        
        if result.get('success'):
            logger.info(f"✅ Successfully reset prompt for user {user_id}")
            return {
                "success": True,
                "message": "Prompt reset to default successfully"
            }
        else:
            logger.error(f"❌ Failed to reset prompt for user {user_id}: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to reset prompt'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resetting prompt configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompt/validate")
async def validate_user_prompt(request: PromptValidationRequest, current_user_profile: dict = Depends(get_current_user_profile)):
    """Validate user's prompt template"""
    try:
        user_id = current_user_profile["user_id"]
        logger.info(f"✅ Validating prompt template for user {user_id}")
        
        template = request.template
        
        # Check for required variables
        required_variables = ['{subject}', '{sender}', '{content}']
        missing_variables = [var for var in required_variables if var not in template]
        
        if missing_variables:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Template must contain these variables: {missing_variables}",
                    "missing_variables": missing_variables
                }
            )
        
        # Test template formatting
        try:
            test_result = template.format(
                subject="Test Subject",
                sender="Test Sender",
                content="Test Content"
            )
            
            return {
                "success": True,
                "message": "Template is valid",
                "preview": test_result[:500] + "..." if len(test_result) > 500 else test_result
            }
            
        except Exception as format_error:
            raise HTTPException(
                status_code=400,
                detail=f"Template formatting error: {str(format_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error validating prompt template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 