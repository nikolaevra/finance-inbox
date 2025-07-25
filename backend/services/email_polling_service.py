import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from supabase import Client
from services.google_service import GoogleService
from database import get_supabase

logger = logging.getLogger(__name__)

class EmailPollingService:
    """Service to automatically poll Gmail for new emails"""
    
    def __init__(self, polling_interval_seconds: int = 60):  # Default 1 minute
        self.polling_interval = polling_interval_seconds
        self.is_running = False
        self.supabase: Client = get_supabase()
        self._polling_tasks = {}
        
    async def start_polling_for_user(self, user_id: str):
        """Start polling emails for a specific user"""
        if user_id in self._polling_tasks:
            logger.warning(f"⚠️ Polling already active for user {user_id}")
            return
            
        logger.info(f"🚀 Starting email polling for user {user_id}")
        task = asyncio.create_task(self._poll_user_emails(user_id))
        self._polling_tasks[user_id] = task
        
    async def stop_polling_for_user(self, user_id: str):
        """Stop polling emails for a specific user"""
        if user_id in self._polling_tasks:
            logger.info(f"🛑 Stopping email polling for user {user_id}")
            self._polling_tasks[user_id].cancel()
            del self._polling_tasks[user_id]
            
    async def _poll_user_emails(self, user_id: str):
        """Poll emails for a specific user"""
        while True:
            try:
                logger.info(f"📧 Polling emails for user {user_id}")
                
                # Create GoogleService instance for this user
                google_service = GoogleService(internal_user_id=user_id)
                
                # Fetch only new emails
                new_emails = google_service.fetch_gmail_emails(max_results=50, only_new=True)
                
                if new_emails:
                    logger.info(f"✅ Found {len(new_emails)} new emails for user {user_id}")
                    # Notify connected clients about new emails
                    await self._notify_new_emails(user_id, len(new_emails))
                else:
                    logger.debug(f"📭 No new emails for user {user_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error polling emails for user {user_id}: {str(e)}")
                
            # Wait for the next polling interval
            await asyncio.sleep(self.polling_interval)
            
    async def _notify_new_emails(self, user_id: str, count: int):
        """Notify about new emails (placeholder for WebSocket/SSE implementation)"""
        # This is where you would send notifications to connected clients
        # For now, just log it
        logger.info(f"📢 User {user_id} has {count} new emails")
        
    def get_active_users(self) -> list:
        """Get list of users who have active Gmail connections"""
        try:
            # Get users who have Gmail connections with 'connected' status
            result = self.supabase.table("connections").select("user_id").eq("connection_provider", "gmail").eq("status", "connected").execute()
            
            if result.data:
                return [conn['user_id'] for conn in result.data]
            return []
        except Exception as e:
            logger.error(f"❌ Error getting active users: {str(e)}")
            return []
            
    async def start_polling_all_users(self):
        """Start polling for all users with active Gmail connections"""
        self.is_running = True
        
        while self.is_running:
            try:
                # Get all active users
                active_users = self.get_active_users()
                logger.info(f"🔍 Found {len(active_users)} active users")
                
                # Start polling for users who aren't already being polled
                for user_id in active_users:
                    if user_id not in self._polling_tasks:
                        await self.start_polling_for_user(user_id)
                        
                # Stop polling for users who are no longer active
                inactive_users = set(self._polling_tasks.keys()) - set(active_users)
                for user_id in inactive_users:
                    await self.stop_polling_for_user(user_id)
                    
                # Check for new users every minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Error in polling loop: {str(e)}")
                await asyncio.sleep(60)
                
    def stop(self):
        """Stop all polling tasks"""
        self.is_running = False
        for user_id in list(self._polling_tasks.keys()):
            asyncio.create_task(self.stop_polling_for_user(user_id))

# Global instance
email_polling_service = EmailPollingService() 