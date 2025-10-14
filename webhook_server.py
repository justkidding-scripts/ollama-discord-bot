#!/usr/bin/env python3
"""
Advanced Webhook Server for Discord Bot Integration
Handles GitHub, monitoring, and CI/CD webhooks
"""

import asyncio
import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from aiohttp import web, ClientSession
import discord
import os
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookServer:
    """Advanced webhook server with Discord integration"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = web.Application()
        self.discord_webhook_url = None
        self.github_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_post('/webhook/github', self.handle_github_webhook)
        self.app.router.add_post('/webhook/monitoring', self.handle_monitoring_webhook)
        self.app.router.add_post('/webhook/cicd', self.handle_cicd_webhook)
        self.app.router.add_get('/webhook/health', self.health_check)
        self.app.router.add_get('/', self.index)
    
    async def index(self, request):
        """Index page"""
        return web.Response(text="🤖 Discord Bot Webhook Server Online", content_type='text/plain')
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'server': 'Discord Bot Webhook Server'
        })
    
    def verify_github_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not self.github_secret:
            return True  # Skip verification if no secret
            
        expected_signature = hmac.new(
            self.github_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def handle_github_webhook(self, request):
        """Handle GitHub webhook events"""
        try:
            # Get headers
            event_type = request.headers.get('X-GitHub-Event', 'unknown')
            signature = request.headers.get('X-Hub-Signature-256', '')
            
            # Get payload
            payload_bytes = await request.read()
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Verify signature
            if not self.verify_github_signature(payload_bytes, signature):
                logger.warning("Invalid GitHub webhook signature")
                return web.Response(status=401, text="Invalid signature")
            
            logger.info(f"Received GitHub {event_type} event")
            
            # Process different event types
            embed = await self.process_github_event(event_type, payload)
            
            if embed:
                await self.send_to_discord(embed)
            
            return web.json_response({'status': 'processed', 'event': event_type})
            
        except Exception as e:
            logger.error(f"GitHub webhook processing failed: {e}")
            return web.Response(status=500, text=f"Processing failed: {str(e)}")
    
    async def process_github_event(self, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process GitHub webhook events and create Discord embeds"""
        
        if event_type == 'push':
            return await self._create_push_embed(payload)
        elif event_type == 'pull_request':
            return await self._create_pr_embed(payload)
        elif event_type == 'issues':
            return await self._create_issue_embed(payload)
        elif event_type == 'release':
            return await self._create_release_embed(payload)
        elif event_type == 'workflow_run':
            return await self._create_workflow_embed(payload)
        
        return None
    
    async def _create_push_embed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create embed for GitHub push events"""
        repo = payload.get('repository', {})
        pusher = payload.get('pusher', {})
        commits = payload.get('commits', [])
        
        embed = {
            'title': '🔄 New Push to Repository',
            'description': f"**{len(commits)}** commits pushed to **{repo.get('full_name', 'Unknown')}**",
            'color': 0x28a745,
            'timestamp': datetime.now().isoformat(),
            'fields': [
                {
                    'name': 'Pusher',
                    'value': pusher.get('name', 'Unknown'),
                    'inline': True
                },
                {
                    'name': 'Branch',
                    'value': payload.get('ref', 'unknown').replace('refs/heads/', ''),
                    'inline': True
                },
                {
                    'name': 'Commits',
                    'value': str(len(commits)),
                    'inline': True
                }
            ]
        }
        
        if commits:
            commit_list = []
            for commit in commits[:5]:  # Show max 5 commits
                commit_list.append(f"• [`{commit.get('id', '')[:7]}`]({commit.get('url', '')}) {commit.get('message', '')[:50]}...")
            
            embed['fields'].append({
                'name': 'Recent Commits',
                'value': '\n'.join(commit_list),
                'inline': False
            })
        
        return embed
    
    async def _create_pr_embed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create embed for GitHub pull request events"""
        action = payload.get('action', 'unknown')
        pr = payload.get('pull_request', {})
        
        color_map = {
            'opened': 0x28a745,
            'closed': 0xdc3545,
            'merged': 0x6f42c1,
            'reopened': 0xffc107
        }
        
        embed = {
            'title': f'📋 Pull Request {action.title()}',
            'description': pr.get('title', 'No title'),
            'url': pr.get('html_url', ''),
            'color': color_map.get(action, 0x17a2b8),
            'timestamp': datetime.now().isoformat(),
            'fields': [
                {
                    'name': 'Author',
                    'value': pr.get('user', {}).get('login', 'Unknown'),
                    'inline': True
                },
                {
                    'name': 'Base → Head',
                    'value': f"{pr.get('base', {}).get('ref', 'unknown')} ← {pr.get('head', {}).get('ref', 'unknown')}",
                    'inline': True
                }
            ]
        }
        
        if pr.get('body'):
            embed['fields'].append({
                'name': 'Description',
                'value': pr.get('body', '')[:200] + ('...' if len(pr.get('body', '')) > 200 else ''),
                'inline': False
            })
        
        return embed
    
    async def _create_issue_embed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create embed for GitHub issue events"""
        action = payload.get('action', 'unknown')
        issue = payload.get('issue', {})
        
        color_map = {
            'opened': 0xdc3545,
            'closed': 0x28a745,
            'reopened': 0xffc107
        }
        
        embed = {
            'title': f'🐛 Issue {action.title()}',
            'description': issue.get('title', 'No title'),
            'url': issue.get('html_url', ''),
            'color': color_map.get(action, 0x17a2b8),
            'timestamp': datetime.now().isoformat(),
            'fields': [
                {
                    'name': 'Author',
                    'value': issue.get('user', {}).get('login', 'Unknown'),
                    'inline': True
                },
                {
                    'name': 'Issue #',
                    'value': str(issue.get('number', 'Unknown')),
                    'inline': True
                }
            ]
        }
        
        if issue.get('labels'):
            labels = [label['name'] for label in issue['labels']]
            embed['fields'].append({
                'name': 'Labels',
                'value': ', '.join(labels),
                'inline': True
            })
        
        return embed
    
    async def _create_release_embed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create embed for GitHub release events"""
        action = payload.get('action', 'unknown')
        release = payload.get('release', {})
        
        embed = {
            'title': f'🚀 Release {action.title()}',
            'description': release.get('name', 'No name'),
            'url': release.get('html_url', ''),
            'color': 0x6f42c1,
            'timestamp': datetime.now().isoformat(),
            'fields': [
                {
                    'name': 'Tag',
                    'value': release.get('tag_name', 'Unknown'),
                    'inline': True
                },
                {
                    'name': 'Author',
                    'value': release.get('author', {}).get('login', 'Unknown'),
                    'inline': True
                }
            ]
        }
        
        if release.get('body'):
            embed['fields'].append({
                'name': 'Release Notes',
                'value': release.get('body', '')[:300] + ('...' if len(release.get('body', '')) > 300 else ''),
                'inline': False
            })
        
        return embed
    
    async def _create_workflow_embed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create embed for GitHub workflow events"""
        workflow = payload.get('workflow_run', {})
        conclusion = workflow.get('conclusion', 'unknown')
        
        color_map = {
            'success': 0x28a745,
            'failure': 0xdc3545,
            'cancelled': 0x6c757d,
            'skipped': 0xffc107
        }
        
        embed = {
            'title': f'⚙️ Workflow {conclusion.title()}',
            'description': workflow.get('name', 'Unknown workflow'),
            'url': workflow.get('html_url', ''),
            'color': color_map.get(conclusion, 0x17a2b8),
            'timestamp': datetime.now().isoformat(),
            'fields': [
                {
                    'name': 'Branch',
                    'value': workflow.get('head_branch', 'Unknown'),
                    'inline': True
                },
                {
                    'name': 'Commit',
                    'value': workflow.get('head_sha', 'Unknown')[:7],
                    'inline': True
                },
                {
                    'name': 'Actor',
                    'value': workflow.get('actor', {}).get('login', 'Unknown'),
                    'inline': True
                }
            ]
        }
        
        return embed
    
    async def handle_monitoring_webhook(self, request):
        """Handle monitoring system webhooks (Grafana, Prometheus, etc.)"""
        try:
            payload = await request.json()
            logger.info("Received monitoring webhook")
            
            # Create monitoring alert embed
            embed = {
                'title': '⚠️ Monitoring Alert',
                'description': payload.get('message', 'No message provided'),
                'color': 0xffc107 if payload.get('status') == 'warning' else 0xdc3545,
                'timestamp': datetime.now().isoformat(),
                'fields': [
                    {
                        'name': 'Status',
                        'value': payload.get('status', 'unknown'),
                        'inline': True
                    },
                    {
                        'name': 'Source',
                        'value': payload.get('source', 'unknown'),
                        'inline': True
                    }
                ]
            }
            
            await self.send_to_discord(embed)
            
            return web.json_response({'status': 'processed'})
            
        except Exception as e:
            logger.error(f"Monitoring webhook processing failed: {e}")
            return web.Response(status=500, text=f"Processing failed: {str(e)}")
    
    async def handle_cicd_webhook(self, request):
        """Handle CI/CD pipeline webhooks"""
        try:
            payload = await request.json()
            logger.info("Received CI/CD webhook")
            
            # Create CI/CD embed
            embed = {
                'title': '🚀 CI/CD Pipeline Update',
                'description': f"Pipeline **{payload.get('pipeline', 'unknown')}** {payload.get('status', 'unknown')}",
                'color': 0x28a745 if payload.get('status') == 'success' else 0xdc3545,
                'timestamp': datetime.now().isoformat(),
                'fields': [
                    {
                        'name': 'Status',
                        'value': payload.get('status', 'unknown'),
                        'inline': True
                    },
                    {
                        'name': 'Branch',
                        'value': payload.get('branch', 'unknown'),
                        'inline': True
                    },
                    {
                        'name': 'Duration',
                        'value': payload.get('duration', 'unknown'),
                        'inline': True
                    }
                ]
            }
            
            await self.send_to_discord(embed)
            
            return web.json_response({'status': 'processed'})
            
        except Exception as e:
            logger.error(f"CI/CD webhook processing failed: {e}")
            return web.Response(status=500, text=f"Processing failed: {str(e)}")
    
    async def send_to_discord(self, embed: Dict[str, Any]):
        """Send embed to Discord via webhook or bot"""
        # This would integrate with your Discord bot
        # For now, just log the embed
        logger.info(f"Discord embed: {json.dumps(embed, indent=2)}")
    
    def set_discord_webhook(self, webhook_url: str):
        """Set Discord webhook URL"""
        self.discord_webhook_url = webhook_url
        logger.info("Discord webhook URL configured")
    
    async def start_server(self):
        """Start the webhook server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🚀 Webhook server started on port {self.port}")
        logger.info(f"📡 GitHub webhook: http://localhost:{self.port}/webhook/github")
        logger.info(f"📊 Monitoring webhook: http://localhost:{self.port}/webhook/monitoring")
        logger.info(f"🔧 CI/CD webhook: http://localhost:{self.port}/webhook/cicd")

async def main():
    """Main server execution"""
    port = int(os.getenv('WEBHOOK_PORT', '8181'))
    server = WebhookServer(port=port)
    
    # Start the server
    await server.start_server()
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server...")

if __name__ == "__main__":
    asyncio.run(main())
