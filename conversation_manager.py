import json
import asyncio
from typing import Dict, List, Optional
from collections import defaultdict
import logging
import time

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, max_history: int = 20, context_window: int = 4096):
        self.conversations: Dict[int, List[Dict]] = defaultdict(list)
        self.max_history = max_history
        self.context_window = context_window
        self.last_activity: Dict[int, float] = defaultdict(float)
        self._lock = asyncio.Lock()
    
    async def add_message(self, channel_id: int, role: str, content: str):
        """Add a message to the conversation history"""
        async with self._lock:
            message = {
                "role": role,
                "content": content,
                "timestamp": time.time()
            }
            
            self.conversations[channel_id].append(message)
            self.last_activity[channel_id] = time.time()
            
            # Trim history if too long
            if len(self.conversations[channel_id]) > self.max_history:
                self.conversations[channel_id] = self.conversations[channel_id][-self.max_history:]
            
            logger.debug(f"Added message to channel {channel_id}: {role}")
    
    async def get_conversation_history(self, channel_id: int, max_messages: int = None) -> List[Dict]:
        """Get conversation history for a channel"""
        async with self._lock:
            history = self.conversations[channel_id]
            if max_messages:
                history = history[-max_messages:]
            return history.copy()
    
    async def clear_conversation(self, channel_id: int):
        """Clear conversation history for a channel"""
        async with self._lock:
            if channel_id in self.conversations:
                self.conversations[channel_id].clear()
                logger.info(f"Cleared conversation history for channel {channel_id}")
    
    async def get_context_for_model(self, channel_id: int, max_tokens: int = None) -> List[Dict[str, str]]:
        """Get conversation context formatted for the model"""
        max_tokens = max_tokens or self.context_window
        
        async with self._lock:
            history = self.conversations[channel_id]
            if not history:
                return []
            
            # Start with most recent messages and work backwards
            context = []
            current_tokens = 0
            
            for message in reversed(history):
                # Rough token estimation (4 chars = 1 token)
                message_tokens = len(message['content']) // 4
                
                if current_tokens + message_tokens > max_tokens and context:
                    break
                
                context.insert(0, {
                    "role": message['role'],
                    "content": message['content']
                })
                current_tokens += message_tokens
            
            return context
    
    async def get_stats(self) -> Dict:
        """Get conversation manager statistics"""
        async with self._lock:
            total_conversations = len(self.conversations)
            total_messages = sum(len(conv) for conv in self.conversations.values())
            active_conversations = sum(1 for last_time in self.last_activity.values() 
                                    if time.time() - last_time < 3600)  # Active in last hour
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'active_conversations': active_conversations,
                'max_history': self.max_history,
                'context_window': self.context_window
            }
    
    async def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversations to save memory"""
        async with self._lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            channels_to_remove = []
            for channel_id, last_time in self.last_activity.items():
                if current_time - last_time > max_age_seconds:
                    channels_to_remove.append(channel_id)
            
            for channel_id in channels_to_remove:
                if channel_id in self.conversations:
                    del self.conversations[channel_id]
                if channel_id in self.last_activity:
                    del self.last_activity[channel_id]
            
            if channels_to_remove:
                logger.info(f"Cleaned up {len(channels_to_remove)} old conversations")
    
    async def export_conversation(self, channel_id: int) -> str:
        """Export conversation as JSON"""
        async with self._lock:
            if channel_id not in self.conversations:
                return json.dumps({"error": "No conversation found"})
            
            return json.dumps({
                "channel_id": channel_id,
                "messages": self.conversations[channel_id],
                "exported_at": time.time()
            }, indent=2)
    
    async def import_conversation(self, channel_id: int, data: str):
        """Import conversation from JSON"""
        try:
            conversation_data = json.loads(data)
            messages = conversation_data.get('messages', [])
            
            async with self._lock:
                self.conversations[channel_id] = messages
                self.last_activity[channel_id] = time.time()
                
            logger.info(f"Imported {len(messages)} messages to channel {channel_id}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to import conversation: {e}")
            raise

# Global conversation manager instance
conversation_manager = ConversationManager()
