#!/usr/bin/env python3
"""
Enhanced Research Discord Bot with RAG and GitHub Integration
Advanced PhD research assistant with automated workflows
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
import json
import os
from typing import Optional, List, Dict, Any

# Import our systems
from advanced_rag_system import rag_system
from github_automation import github_automation
from ultra_enhanced_discord_bot import UltraEnhancedBot

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedResearchBot(UltraEnhancedBot):
    """Enhanced research bot with RAG and GitHub integration"""
    
    def __init__(self):
        super().__init__()
        self.rag_system = rag_system
        self.github_automation = github_automation
        self.research_active = False
        self.current_topic = None
    
    async def setup_research_systems(self):
        """Initialize research systems"""
        logger.info("Initializing research systems...")
        
        # Initialize RAG system
        await self.rag_system.initialize()
        
        # Initialize GitHub automation
        await self.github_automation.initialize_repository()
        
        logger.info("Research systems ready!")
    
    @discord.app_commands.command(name="research_start", description="Start a new research session")
    async def start_research_session(self, interaction: discord.Interaction, topic: str):
        """Start a new research session with automatic tracking"""
        await interaction.response.defer()
        
        try:
            # Start GitHub session tracking
            session_id = self.github_automation.start_research_session(topic)
            self.research_active = True
            self.current_topic = topic
            
            embed = discord.Embed(
                title="🔬 Research Session Started",
                description=f"**Topic:** {topic}\n**Session ID:** {session_id}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Automation Active",
                value="✅ Auto-commit enabled\n✅ File tracking enabled\n✅ RAG system ready",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to start session: {str(e)}")
    
    @discord.app_commands.command(name="research_end", description="End current research session")
    async def end_research_session(self, interaction: discord.Interaction, findings: str = ""):
        """End current research session"""
        await interaction.response.defer()
        
        if not self.research_active:
            await interaction.followup.send("❌ No active research session")
            return
        
        try:
            # Parse findings
            key_findings = [f.strip() for f in findings.split('\n') if f.strip()] if findings else []
            
            # End GitHub session
            self.github_automation.end_research_session(key_findings)
            
            # Generate documentation
            await self.github_automation.generate_research_documentation()
            
            self.research_active = False
            self.current_topic = None
            
            embed = discord.Embed(
                title="📋 Research Session Completed",
                description=f"Session ended successfully",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            if key_findings:
                embed.add_field(
                    name="Key Findings",
                    value="\n".join([f"• {finding}" for finding in key_findings[:5]]),
                    inline=False
                )
            
            embed.add_field(
                name="Actions Completed",
                value="✅ Session committed to GitHub\n✅ Documentation generated\n✅ Research summary created",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to end session: {str(e)}")
    
    @discord.app_commands.command(name="rag_search", description="Search the research knowledge base")
    async def rag_search(self, interaction: discord.Interaction, query: str, sources: str = "all"):
        """Search RAG knowledge base"""
        await interaction.response.defer()
        
        try:
            # Parse source filter
            source_filter = None
            if sources.lower() != "all":
                source_filter = [s.strip() for s in sources.split(',')]
            
            # Search RAG system
            results = await self.rag_system.search(query, n_results=10, include_sources=source_filter)
            
            if not results:
                await interaction.followup.send("❌ No results found in knowledge base")
                return
            
            # Create embed with results
            embed = discord.Embed(
                title="📚 Knowledge Base Search Results",
                description=f"**Query:** {query}\n**Results:** {len(results)} documents found",
                color=0x9932cc,
                timestamp=datetime.now()
            )
            
            # Add top results
            for i, result in enumerate(results[:5]):
                embed.add_field(
                    name=f"📄 {result['title'][:50]}{'...' if len(result['title']) > 50 else ''}",
                    value=f"**Source:** {result['source']}\n**Authors:** {', '.join(result['authors'][:2])}\n**Relevance:** {(1-result['distance']):.2%}\n**Content:** {result['content'][:100]}...",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ RAG search failed: {str(e)}")
    
    @discord.app_commands.command(name="rag_research", description="Comprehensive research on a topic")
    async def comprehensive_research(self, interaction: discord.Interaction, topic: str, online: bool = True):
        """Perform comprehensive research using RAG system"""
        await interaction.response.defer()
        
        try:
            # Perform comprehensive research
            research_results = await self.rag_system.research_topic(topic, search_online=online)
            
            embed = discord.Embed(
                title="🔍 Comprehensive Research Results",
                description=f"**Topic:** {topic}",
                color=0xff6600,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Search Summary",
                value=research_results['search_summary'],
                inline=False
            )
            
            embed.add_field(
                name="Total Sources",
                value=f"📚 {research_results['total_sources']} documents in knowledge base",
                inline=True
            )
            
            if research_results['documents_found']:
                docs_text = "\n".join([f"• {doc[:60]}{'...' if len(doc) > 60 else ''}" 
                                     for doc in research_results['documents_found'][:10]])
                embed.add_field(
                    name="New Documents Added",
                    value=docs_text or "None",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
            # Track in research session if active
            if self.research_active:
                self.github_automation.track_file_modification(f"rag_research_{topic.replace(' ', '_')}.md")
            
        except Exception as e:
            await interaction.followup.send(f"❌ Research failed: {str(e)}")
    
    @discord.app_commands.command(name="rag_ask", description="Ask a question with RAG context")
    async def rag_ask(self, interaction: discord.Interaction, question: str):
        """Ask question with RAG-enhanced context"""
        await interaction.response.defer()
        
        try:
            # Get RAG context
            rag_response = await self.rag_system.get_enhanced_response(question, context_chunks=5)
            
            # Build enhanced prompt with context
            enhanced_prompt = f"""Based on the following research context, please answer this question: {question}

Research Context:
{rag_response['context']}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. Incorporates relevant information from the research context
3. Cites specific sources when possible
4. Provides academic-level analysis suitable for PhD research

Question: {question}"""
            
            # Get response from Ollama
            ollama_response = await self.get_ollama_response(enhanced_prompt)
            
            # Create response embed
            embed = discord.Embed(
                title="🤖 RAG-Enhanced Response",
                description=f"**Question:** {question}",
                color=0x00ffff,
                timestamp=datetime.now()
            )
            
            # Add response (truncate if too long)
            response_text = ollama_response[:1800] + "..." if len(ollama_response) > 1800 else ollama_response
            embed.add_field(
                name="Answer",
                value=response_text,
                inline=False
            )
            
            # Add sources
            if rag_response['sources']:
                sources_text = "\n".join([
                    f"• {source['title'][:50]}{'...' if len(source['title']) > 50 else ''} ({source['source']})"
                    for source in rag_response['sources'][:5]
                ])
                embed.add_field(
                    name="Sources Referenced",
                    value=sources_text,
                    inline=False
                )
            
            embed.add_field(
                name="Context Statistics",
                value=f"📊 {rag_response['num_results']} relevant documents\n🔍 {len(rag_response['context'])} characters of context",
                inline=True
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ RAG query failed: {str(e)}")
    
    @discord.app_commands.command(name="git_status", description="Show GitHub repository status")
    async def git_status(self, interaction: discord.Interaction):
        """Show current GitHub repository status"""
        await interaction.response.defer()
        
        try:
            repo = self.github_automation.repo
            if not repo:
                await interaction.followup.send("❌ No Git repository initialized")
                return
            
            # Get repository stats
            commit_count = len(list(repo.iter_commits()))
            branch_count = len(list(repo.branches))
            current_branch = repo.active_branch.name
            is_dirty = repo.is_dirty()
            
            # Get recent commits
            recent_commits = list(repo.iter_commits(max_count=5))
            
            embed = discord.Embed(
                title="📊 Repository Status",
                color=0x28a745,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Repository Info",
                value=f"**Branch:** {current_branch}\n**Total Commits:** {commit_count}\n**Total Branches:** {branch_count}\n**Status:** {'Modified files' if is_dirty else 'Clean'}",
                inline=False
            )
            
            # Recent commits
            commits_text = ""
            for commit in recent_commits:
                short_hash = commit.hexsha[:8]
                message = commit.message.split('\n')[0][:50]
                commits_text += f"`{short_hash}` {message}\n"
            
            embed.add_field(
                name="Recent Commits",
                value=commits_text or "No commits",
                inline=False
            )
            
            # Research session info
            if self.research_active:
                embed.add_field(
                    name="Active Research Session",
                    value=f"🔬 **Topic:** {self.current_topic}\n📝 Auto-tracking enabled",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to get status: {str(e)}")
    
    @discord.app_commands.command(name="git_commit", description="Commit current changes")
    async def git_commit(self, interaction: discord.Interaction, message: str):
        """Commit changes to repository"""
        await interaction.response.defer()
        
        try:
            commit_hash = self.github_automation.commit_changes(message)
            
            if commit_hash:
                embed = discord.Embed(
                    title="✅ Changes Committed",
                    description=f"**Commit:** `{commit_hash}`\n**Message:** {message}",
                    color=0x28a745,
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ No changes to commit")
                
        except Exception as e:
            await interaction.followup.send(f"❌ Commit failed: {str(e)}")
    
    @discord.app_commands.command(name="rag_stats", description="Show RAG system statistics")
    async def rag_stats(self, interaction: discord.Interaction):
        """Show RAG system statistics"""
        await interaction.response.defer()
        
        try:
            stats = await self.rag_system.get_document_stats()
            
            embed = discord.Embed(
                title="📊 Knowledge Base Statistics",
                color=0x9932cc,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Documents",
                value=f"**Total:** {stats['total_documents']}\n**Vector Store:** {stats['collection_size']} chunks",
                inline=True
            )
            
            embed.add_field(
                name="Citations",
                value=f"**Total:** {stats['total_citations']}\n**Average:** {stats['avg_citations']:.1f} per document",
                inline=True
            )
            
            # Sources breakdown
            sources_text = "\n".join([f"**{source}:** {count}" for source, count in stats['sources'].items()])
            embed.add_field(
                name="Sources",
                value=sources_text or "No sources",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to get stats: {str(e)}")
    
    @discord.app_commands.command(name="enable_automation", description="Enable automated research workflows")
    async def enable_automation(self, interaction: discord.Interaction, auto_commit: bool = True, auto_push: bool = False):
        """Enable automated workflows"""
        await interaction.response.defer()
        
        try:
            self.github_automation.enable_automation(auto_commit, auto_push)
            
            embed = discord.Embed(
                title="🤖 Automation Enabled",
                description="Automated research workflows are now active",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Settings",
                value=f"**Auto-commit:** {'✅' if auto_commit else '❌'}\n**Auto-push:** {'✅' if auto_push else '❌'}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to enable automation: {str(e)}")
    
    async def setup_hook(self):
        """Setup hook called when bot is ready"""
        await super().setup_hook()
        await self.setup_research_systems()
        
        # Sync commands
        synced = await self.tree.sync()
        logger.info(f"Synced {len(synced)} research commands")

# Run the enhanced bot
async def main():
    """Main function to run the enhanced research bot"""
    bot = EnhancedResearchBot()
    
    # Get Discord token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
