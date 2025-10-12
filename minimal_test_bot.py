#!/usr/bin/env python3
"""
Minimal Discord bot to test server connection and basic functionality
"""
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ DISCORD_TOKEN not found in environment")
    exit(1)

# Create bot with minimal intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'📊 Connected to {len(bot.guilds)} server(s)')
    for guild in bot.guilds:
        print(f'  - {guild.name} (id: {guild.id})')
    
    # Set status
    await bot.change_presence(activity=discord.Game(name="Testing Connection"))

@bot.event
async def on_guild_join(guild):
    print(f'🎉 Bot joined server: {guild.name} (id: {guild.id})')

@bot.event
async def on_guild_remove(guild):
    print(f'👋 Bot left server: {guild.name} (id: {guild.id})')

@bot.command(name='ping')
async def ping(ctx):
    """Simple ping command"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='test')
async def test(ctx):
    """Test command"""
    await ctx.send('✅ Bot is working correctly!')

@bot.command(name='info')
async def info(ctx):
    """Bot info command"""
    embed = discord.Embed(title="Bot Information", color=0x00ff00)
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    await ctx.send(embed=embed)

if __name__ == '__main__':
    print("🚀 Starting minimal test bot...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")