import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_rate_limited(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user is rate limited.
        Returns: (is_limited, seconds_until_reset)
        """
        async with self._lock:
            current_time = time.time()
            user_queue = self.user_requests[user_id]
            
            # Remove old requests outside the window
            while user_queue and user_queue[0] < current_time - self.window_seconds:
                user_queue.popleft()
            
            # Check if user exceeds rate limit
            if len(user_queue) >= self.max_requests:
                oldest_request = user_queue[0]
                reset_time = oldest_request + self.window_seconds
                seconds_until_reset = max(0, int(reset_time - current_time))
                return True, seconds_until_reset
            
            # Add current request
            user_queue.append(current_time)
            return False, 0
    
    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """Get user's current rate limit stats"""
        async with self._lock:
            current_time = time.time()
            user_queue = self.user_requests[user_id]
            
            # Clean old requests
            while user_queue and user_queue[0] < current_time - self.window_seconds:
                user_queue.popleft()
            
            remaining = max(0, self.max_requests - len(user_queue))
            used = len(user_queue)
            
            # Calculate reset time
            reset_in = 0
            if user_queue:
                oldest_request = user_queue[0]
                reset_in = max(0, int(oldest_request + self.window_seconds - current_time))
            
            return {
                'used': used,
                'remaining': remaining,
                'max_requests': self.max_requests,
                'window_seconds': self.window_seconds,
                'reset_in': reset_in
            }
    
    async def reset_user(self, user_id: int):
        """Reset rate limit for a user (admin function)"""
        async with self._lock:
            if user_id in self.user_requests:
                self.user_requests[user_id].clear()
                logger.info(f"Rate limit reset for user {user_id}")
    
    async def cleanup_old_entries(self):
        """Cleanup old entries to prevent memory leaks"""
        async with self._lock:
            current_time = time.time()
            users_to_remove = []
            
            for user_id, user_queue in self.user_requests.items():
                # Remove old requests
                while user_queue and user_queue[0] < current_time - self.window_seconds:
                    user_queue.popleft()
                
                # Remove users with no recent requests
                if not user_queue:
                    users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                del self.user_requests[user_id]
            
            if users_to_remove:
                logger.debug(f"Cleaned up rate limiter entries for {len(users_to_remove)} users")

# Global rate limiter instance
rate_limiter = RateLimiter()
