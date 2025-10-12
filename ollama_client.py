import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
from config import config

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, host: str = None):
        self.host = host or config.OLLAMA_HOST
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            )
    
    async def list_models(self) -> List[Dict]:
        """List available models"""
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.host}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('models', [])
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def check_model_exists(self, model_name: str) -> bool:
        """Check if a model exists"""
        models = await self.list_models()
        return any(model['name'] == model_name for model in models)
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = None, 
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate response from Ollama model"""
        await self._ensure_session()
        
        model = model or config.DEFAULT_MODEL
        temperature = temperature or config.TEMPERATURE
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or config.MAX_TOKENS
            }
        }
        
        try:
            async with self.session.post(
                f"{self.host}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    yield f"❌ Error: {response.status} - {error_text}"
                    return
                
                if stream:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk:
                                    yield chunk['response']
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    data = await response.json()
                    if 'response' in data:
                        yield data['response']
                        
        except asyncio.TimeoutError:
            logger.error("Timeout while generating response")
            yield "❌ Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"❌ Error: {str(e)}"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Chat with context using messages"""
        await self._ensure_session()
        
        model = model or config.DEFAULT_MODEL
        temperature = temperature or config.TEMPERATURE
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": config.MAX_TOKENS
            }
        }
        
        try:
            async with self.session.post(
                f"{self.host}/api/chat",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    yield f"❌ Chat API error: {response.status} - {error_text}"
                    return
                
                if stream:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'message' in chunk and 'content' in chunk['message']:
                                    yield chunk['message']['content']
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    data = await response.json()
                    if 'message' in data and 'content' in data['message']:
                        yield data['message']['content']
                        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            yield f"❌ Chat error: {str(e)}"
    
    async def pull_model(self, model_name: str) -> AsyncGenerator[str, None]:
        """Pull/download a model"""
        await self._ensure_session()
        
        payload = {"name": model_name, "stream": True}
        
        try:
            async with self.session.post(
                f"{self.host}/api/pull",
                json=payload
            ) as response:
                
                if response.status != 200:
                    yield f"❌ Failed to pull model: {response.status}"
                    return
                
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            status = chunk.get('status', '')
                            if status:
                                yield f"📥 {status}"
                            if chunk.get('completed'):
                                yield f"✅ Model {model_name} downloaded successfully!"
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            yield f"❌ Pull error: {str(e)}"

# Global client instance
ollama_client = OllamaClient()
