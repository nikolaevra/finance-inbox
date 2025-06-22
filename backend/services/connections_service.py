"""Connections service for managing user integrations."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import get_supabase
from models import ConnectionStatus, ConnectionProvider
import logging

logger = logging.getLogger(__name__)

class ConnectionsService:
    def __init__(self):
        self.supabase = get_supabase()
    
    def create_or_update_connection(
        self, 
        user_id: str, 
        provider: ConnectionProvider, 
        status: ConnectionStatus,
        oauth_token_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create or update a user connection"""
        try:
            connection_data = {
                "user_id": user_id,
                "connection_provider": provider.value,
                "status": status.value,
                "oauth_token_id": oauth_token_id,
                "metadata": metadata,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values
            connection_data = {k: v for k, v in connection_data.items() if v is not None}
            
            logger.info(f"🔗 Creating/updating {provider.value} connection for user {user_id}")
            
            # Use upsert to create or update
            result = self.supabase.table("connections").upsert(
                connection_data,
                on_conflict="user_id,connection_provider"
            ).execute()
            
            if result.data:
                logger.info(f"✅ Successfully created/updated {provider.value} connection")
                return result.data[0]
            else:
                logger.error(f"❌ Failed to create/update {provider.value} connection")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating/updating connection: {str(e)}")
            return None
    
    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connections for a user"""
        try:
            logger.info(f"🔍 Retrieving connections for user {user_id}")
            
            result = self.supabase.table("connections").select(
                "*, oauth_tokens(*)"
            ).eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"✅ Found {len(result.data)} connections for user {user_id}")
                return result.data
            else:
                logger.info(f"📭 No connections found for user {user_id}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error retrieving connections for user {user_id}: {str(e)}")
            return []
    
    def update_last_sync(
        self, 
        user_id: str, 
        provider: ConnectionProvider
    ) -> bool:
        """Update last sync timestamp"""
        try:
            logger.info(f"📅 Updating last sync time for {provider.value} connection")
            
            update_data = {
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("connections").update(update_data).eq(
                "user_id", user_id
            ).eq("connection_provider", provider.value).execute()
            
            if result.data:
                logger.info(f"✅ Successfully updated last sync time")
                return True
            else:
                logger.warning(f"⚠️ No connection found to update sync time")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating last sync time: {str(e)}")
            return False
    
    def disconnect_provider(
        self, 
        user_id: str, 
        provider: ConnectionProvider
    ) -> bool:
        """Disconnect a provider (set status to disconnected and clear oauth_token_id)"""
        try:
            logger.info(f"🔌 Disconnecting {provider.value} for user {user_id}")
            
            update_data = {
                "status": ConnectionStatus.DISCONNECTED.value,
                "oauth_token_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("connections").update(update_data).eq(
                "user_id", user_id
            ).eq("connection_provider", provider.value).execute()
            
            if result.data:
                logger.info(f"✅ Successfully disconnected {provider.value}")
                return True
            else:
                logger.warning(f"⚠️ No connection found to disconnect for {provider.value}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error disconnecting {provider.value}: {str(e)}")
            return False

    def create_gmail_connection_after_oauth(
        self, 
        user_id: str, 
        oauth_token_id: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ) -> bool:
        """Create Gmail connection record after successful OAuth"""
        try:
            logger.info(f"🔗 Creating Gmail connection record for user {user_id}")
            
            # Create/update connection record
            connection = self.create_or_update_connection(
                user_id=user_id,
                provider=ConnectionProvider.GMAIL,
                status=ConnectionStatus.CONNECTED,
                oauth_token_id=oauth_token_id,
                metadata={
                    "scopes": scopes or [],
                    "connected_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            if connection:
                logger.info(f"✅ Successfully created Gmail connection record")
                return True
            else:
                logger.error(f"❌ Failed to create Gmail connection record")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating Gmail connection record: {str(e)}")
            return False

    def disconnect_gmail_connection(self, user_id: str) -> bool:
        """Disconnect Gmail connection and clear oauth token reference"""
        try:
            logger.info(f"🔌 Disconnecting Gmail connection for user {user_id}")
            
            success = self.disconnect_provider(
                user_id=user_id,
                provider=ConnectionProvider.GMAIL
            )
            
            if success:
                logger.info(f"✅ Successfully disconnected Gmail connection")
            else:
                logger.warning(f"⚠️ No Gmail connection found to disconnect")
                
            return success
                
        except Exception as e:
            logger.error(f"❌ Error disconnecting Gmail connection: {str(e)}")
            return False

# Initialize connections service
connections_service = ConnectionsService() 