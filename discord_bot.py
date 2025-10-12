import discord
from discord.ext import commands, tasks
import asyncio
import aiohttp
import json
import logging
import time
import os
import sys
from typing import Optional, Dict, Any
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ollama_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OllamaDiscordBot:
    def __init__(self, token: str, ollama_host: str = "http://localhost:11434"):
        # Discord setup
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.token = token
        
        # Ollama setup
        self.ollama_host = ollama_host
        self.session: Optional[aiohttp.ClientSession] = None
        self.default_model = "llama3.2:3b"
        
        # Rate limiting
        self.user_requests = {}
        self.rate_limit = 5  # requests per minute
        
        # Conversation context
        self.conversations = {}
        self.max_history = 10
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'errors': 0,
            'uptime_start': time.time()
        }
        
        self.setup_bot_events()
        self.setup_commands()
    
    async def start_session(self):
        """Initialize aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def setup_bot_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'{self.bot.user} has connected to Discord!')
            await self.start_session()
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name="!ask <question> | !help"
            )
            await self.bot.change_presence(activity=activity)
            
            # Start cleanup task
            if not self.cleanup_task.is_running():
                self.cleanup_task.start()
        
        @self.bot.event
        async def on_message(message):
            # Ignore bot messages
            if message.author == self.bot.user:
                return
            
            # Process commands
            await self.bot.process_commands(message)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            logger.error(f"Command error: {error}")
            self.stats['errors'] += 1
            
            if isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f}s")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send("❌ Missing required argument. Use `!help` for command info.")
            else:
                await ctx.send(f"❌ An error occurred: {str(error)[:100]}...")
    
    def setup_commands(self):
        @self.bot.command(name='ask', help='Ask the AI a question')
        @commands.cooldown(1, 10, commands.BucketType.user)
        async def ask(ctx, *, question: str):
            """Ask the AI a question"""
            if not await self.check_rate_limit(ctx.author.id):
                await ctx.send("⏰ You're sending too many requests. Please slow down!")
                return
            
            # Add typing indicator
            async with ctx.typing():
                try:
                    # Get conversation context
                    context = self.get_conversation_context(ctx.channel.id)
                    
                    # Add user message to context
                    context.append({"role": "user", "content": question})
                    
                    # Generate response
                    response = await self.generate_response(context)
                    
                    if response:
                        # Update conversation history
                        self.update_conversation(ctx.channel.id, "user", question)
                        self.update_conversation(ctx.channel.id, "assistant", response)
                        
                        # Send response (split if too long)
                        await self.send_long_message(ctx, response)
                        
                        self.stats['messages_processed'] += 1
                    else:
                        await ctx.send("❌ Failed to generate response. Please try again.")
                        self.stats['errors'] += 1
                        
                except Exception as e:
                    logger.error(f"Error in ask command: {e}")
                    await ctx.send(f"❌ Error: {str(e)[:100]}...")
                    self.stats['errors'] += 1
        
        @self.bot.command(name='chat', help='Continue conversation with AI')
        @commands.cooldown(1, 5, commands.BucketType.user)
        async def chat(ctx, *, message: str):
            """Continue conversation with context"""
            await self.bot.get_command('ask')(ctx, question=message)
        
        @self.bot.command(name='clear', help='Clear conversation history')
        async def clear_conversation(ctx):
            """Clear conversation history for this channel"""
            if ctx.channel.id in self.conversations:
                del self.conversations[ctx.channel.id]
            await ctx.send("🗑️ Conversation history cleared!")
        
        @self.bot.command(name='models', help='List available AI models')
        async def list_models(ctx):
            """List available Ollama models"""
            try:
                models = await self.get_available_models()
                if models:
                    model_list = "\n".join([f"• **{model['name']}** ({model['size']//1e9:.1f}GB)" for model in models])
                    embed = discord.Embed(
                        title="📚 Available AI Models",
                        description=model_list,
                        color=0x00ff00
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ No models available or connection error.")
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                await ctx.send("❌ Failed to fetch model list.")
        
        @self.bot.command(name='stats', help='Show bot statistics')
        async def show_stats(ctx):
            """Show bot statistics"""
            uptime = time.time() - self.stats['uptime_start']
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=0x0099ff
            )
            embed.add_field(name="Messages Processed", value=self.stats['messages_processed'], inline=True)
            embed.add_field(name="Errors", value=self.stats['errors'], inline=True)
            embed.add_field(name="Uptime", value=f"{uptime/3600:.1f} hours", inline=True)
            embed.add_field(name="Active Conversations", value=len(self.conversations), inline=True)
            embed.add_field(name="Model", value=self.default_model, inline=True)
            embed.add_field(name="Host", value=self.ollama_host, inline=True)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='ping', help='Check bot latency')
        async def ping(ctx):
            """Check bot latency"""
            latency = round(self.bot.latency * 1000)
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Latency: {latency}ms",
                color=0x00ff00 if latency < 100 else 0xff9900 if latency < 300 else 0xff0000
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name='system', help='Send a system message to AI')
        @commands.has_permissions(administrator=True)
        async def system_message(ctx, *, message: str):
            """Send a system message (admin only)"""
            self.update_conversation(ctx.channel.id, "system", message)
            await ctx.send(f"✅ System message added: `{message[:50]}...`")
        
        @self.bot.command(name='help_ai', help='Get help about AI commands')
        async def help_ai(ctx):
            """Custom help for AI commands"""
            embed = discord.Embed(
                title="🤖 AI Bot Commands",
                description="Here are all available commands:",
                color=0x0099ff
            )
            
            commands_info = [
                ("!ask <question>", "Ask the AI a question"),
                ("!chat <message>", "Continue conversation with AI"),
                ("!clear", "Clear conversation history"),
                ("!models", "List available AI models"),
                ("!stats", "Show bot statistics"),
                ("!ping", "Check bot latency"),
                ("!system <msg>", "Send system message (admin only)")
            ]
            
            for cmd, desc in commands_info:
                embed.add_field(name=cmd, value=desc, inline=False)
            
            embed.set_footer(text="Made with ❤️ using Ollama")
            await ctx.send(embed=embed)
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < 60  # 1 minute window
        ]
        
        # Check limit
        if len(self.user_requests[user_id]) >= self.rate_limit:
            return False
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True
    
    def get_conversation_context(self, channel_id: int) -> list:
        """Get conversation context for a channel"""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        return self.conversations[channel_id].copy()
    
    def update_conversation(self, channel_id: int, role: str, content: str):
        """Update conversation history"""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        self.conversations[channel_id].append({
            "role": role,
            "content": content
        })
        
        # Trim history
        if len(self.conversations[channel_id]) > self.max_history * 2:
            self.conversations[channel_id] = self.conversations[channel_id][-self.max_history:]
    
    async def generate_response(self, messages: list) -> Optional[str]:
        """Generate response from Ollama"""
        await self.start_session()
        
        payload = {
            "model": self.default_model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with self.session.post(
                f"{self.ollama_host}/api/chat",
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return data.get('message', {}).get('content', '')
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    return f"API Error: {response.status}"
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    async def get_available_models(self) -> list:
        """Get list of available models"""
        await self.start_session()
        
        try:
            async with self.session.get(f"{self.ollama_host}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('models', [])
                return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []
    
    async def send_long_message(self, ctx, message: str, max_length: int = 2000):
        """Send a long message by splitting it into chunks"""
        if len(message) <= max_length:
            await ctx.send(message)
            return
        
        # Split message into chunks
        chunks = []
        current_chunk = ""
        
        for line in message.split('\n'):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await ctx.send(chunk)
            else:
                await ctx.send(f"**(continued {i+1}/{len(chunks)})**\n{chunk}")
    
    @tasks.loop(minutes=30)
    async def cleanup_task(self):
        """Periodic cleanup task"""
        try:
            # Clean old rate limit entries
            current_time = time.time()
            for user_id in list(self.user_requests.keys()):
                self.user_requests[user_id] = [
                    req_time for req_time in self.user_requests[user_id]
                    if current_time - req_time < 60
                ]
                if not self.user_requests[user_id]:
                    del self.user_requests[user_id]
            
            # Clean old conversations (older than 2 hours)
            for channel_id in list(self.conversations.keys()):
                if len(self.conversations[channel_id]) == 0:
                    del self.conversations[channel_id]
            
            logger.info("Cleanup task completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    async def run(self):
        """Start the bot"""
        try:
            await self.bot.start(self.token)
        except Exception as e:
            logger.error(f"Bot failed to start: {e}")
        finally:
            await self.close_session()

def main():
    # Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN environment variable is required!")
        print("Set it with: export DISCORD_TOKEN='your_bot_token_here'")
        return
    
    # Create and run bot
    bot = OllamaDiscordBot(DISCORD_TOKEN, OLLAMA_HOST)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
