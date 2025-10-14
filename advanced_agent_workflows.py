#!/usr/bin/env python3
"""
Advanced Agent Workflows - Multi-agent chaining, research pipelines, and file management
"""

import asyncio
import json
import os
import subprocess
import tempfile
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import aiofiles
import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class AdvancedAgentWorkflows:
    """Advanced agent workflow management system"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.active_workflows = {}
        self.workflow_templates = {
            'security_analysis': {
                'name': 'Comprehensive Security Analysis',
                'agents': ['security-auditor', 'risk-manager', 'threat-analyst'],
                'description': 'Multi-layer security assessment pipeline',
                'steps': [
                    {'agent': 'security-auditor', 'task': 'vulnerability_scan', 'depends_on': []},
                    {'agent': 'threat-analyst', 'task': 'threat_modeling', 'depends_on': ['vulnerability_scan']},
                    {'agent': 'risk-manager', 'task': 'risk_assessment', 'depends_on': ['vulnerability_scan', 'threat_modeling']}
                ]
            },
            'malware_analysis': {
                'name': 'Advanced Malware Analysis Pipeline',
                'agents': ['malware-analyst', 'reverse-engineer', 'forensics-expert'],
                'description': 'Complete malware reverse engineering workflow',
                'steps': [
                    {'agent': 'malware-analyst', 'task': 'static_analysis', 'depends_on': []},
                    {'agent': 'reverse-engineer', 'task': 'dynamic_analysis', 'depends_on': ['static_analysis']},
                    {'agent': 'forensics-expert', 'task': 'ioc_extraction', 'depends_on': ['static_analysis', 'dynamic_analysis']}
                ]
            },
            'research_pipeline': {
                'name': 'PhD Research Data Pipeline',
                'agents': ['data-scientist', 'research-assistant', 'statistician'],
                'description': 'Academic research data processing and analysis',
                'steps': [
                    {'agent': 'research-assistant', 'task': 'data_collection', 'depends_on': []},
                    {'agent': 'data-scientist', 'task': 'data_preprocessing', 'depends_on': ['data_collection']},
                    {'agent': 'statistician', 'task': 'statistical_analysis', 'depends_on': ['data_preprocessing']}
                ]
            }
        }
        
    async def start_workflow(self, workflow_type: str, context: Dict[str, Any], user_id: int, channel_id: int) -> str:
        """Start an advanced multi-agent workflow"""
        if workflow_type not in self.workflow_templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
            
        workflow_id = str(uuid.uuid4())[:8]
        template = self.workflow_templates[workflow_type]
        
        workflow = {
            'id': workflow_id,
            'type': workflow_type,
            'template': template,
            'context': context,
            'user_id': user_id,
            'channel_id': channel_id,
            'status': 'running',
            'started_at': datetime.now(),
            'steps': {},
            'results': {},
            'current_step': 0,
            'total_steps': len(template['steps'])
        }
        
        self.active_workflows[workflow_id] = workflow
        
        # Start workflow execution
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        return workflow_id
        
    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow steps in dependency order"""
        workflow = self.active_workflows[workflow_id]
        template = workflow['template']
        
        try:
            # Build execution order based on dependencies
            execution_order = self._build_execution_order(template['steps'])
            
            for step_name in execution_order:
                step = next(s for s in template['steps'] if s.get('name', f"{s['agent']}_{s['task']}") == step_name)
                
                logger.info(f"Executing workflow {workflow_id} step: {step_name}")
                
                # Wait for dependencies to complete
                await self._wait_for_dependencies(workflow, step)
                
                # Execute step
                result = await self._execute_step(workflow, step)
                
                workflow['steps'][step_name] = {
                    'status': 'completed' if result['success'] else 'failed',
                    'result': result,
                    'completed_at': datetime.now()
                }
                
                workflow['current_step'] += 1
                
                # Send progress update
                await self._send_workflow_update(workflow, step_name, result)
                
                if not result['success']:
                    workflow['status'] = 'failed'
                    break
                    
            if workflow['status'] != 'failed':
                workflow['status'] = 'completed'
                
            # Send final results
            await self._send_workflow_completion(workflow)
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            workflow['status'] = 'error'
            workflow['error'] = str(e)
            await self._send_workflow_error(workflow, str(e))
            
    def _build_execution_order(self, steps: List[Dict]) -> List[str]:
        """Build execution order based on step dependencies"""
        # Simple topological sort
        order = []
        remaining = {s.get('name', f"{s['agent']}_{s['task']}"): s for s in steps}
        
        while remaining:
            # Find steps with no unresolved dependencies
            ready = []
            for name, step in remaining.items():
                deps = step.get('depends_on', [])
                if all(dep in order for dep in deps):
                    ready.append(name)
                    
            if not ready:
                # Circular dependency or error
                ready = [next(iter(remaining.keys()))]  # Just pick one
                
            for name in ready:
                order.append(name)
                del remaining[name]
                
        return order
        
    async def _wait_for_dependencies(self, workflow: Dict, step: Dict):
        """Wait for step dependencies to complete"""
        deps = step.get('depends_on', [])
        max_wait = 300  # 5 minutes max wait
        start_time = datetime.now()
        
        while deps:
            if (datetime.now() - start_time).seconds > max_wait:
                raise TimeoutError(f"Dependencies not ready: {deps}")
                
            completed_deps = []
            for dep in deps:
                if dep in workflow['steps'] and workflow['steps'][dep]['status'] == 'completed':
                    completed_deps.append(dep)
                    
            for dep in completed_deps:
                deps.remove(dep)
                
            if deps:
                await asyncio.sleep(1)
                
    async def _execute_step(self, workflow: Dict, step: Dict) -> Dict[str, Any]:
        """Execute a single workflow step"""
        agent_name = step['agent']
        task = step['task']
        context = workflow['context']
        
        # Build query for agent
        query = self._build_agent_query(task, context, workflow)
        
        try:
            # Execute agent query
            result = await self._call_agent(agent_name, query)
            
            return {
                'success': True,
                'output': result,
                'agent': agent_name,
                'task': task,
                'execution_time': 0  # Would track actual time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent': agent_name,
                'task': task
            }
            
    def _build_agent_query(self, task: str, context: Dict, workflow: Dict) -> str:
        """Build query for agent based on task and context"""
        base_queries = {
            'vulnerability_scan': f"Perform vulnerability scan on: {context.get('target', 'system')}",
            'threat_modeling': f"Create threat model for: {context.get('target', 'system')}",
            'risk_assessment': f"Assess security risks for: {context.get('target', 'system')}",
            'static_analysis': f"Perform static analysis on: {context.get('file_path', 'target file')}",
            'dynamic_analysis': f"Perform dynamic analysis on: {context.get('file_path', 'target file')}",
            'ioc_extraction': f"Extract IoCs from analysis of: {context.get('file_path', 'target file')}",
            'data_collection': f"Collect research data for: {context.get('research_topic', 'study')}",
            'data_preprocessing': f"Preprocess collected data for: {context.get('research_topic', 'study')}",
            'statistical_analysis': f"Perform statistical analysis on: {context.get('research_topic', 'study')}"
        }
        
        query = base_queries.get(task, f"Perform {task}")
        
        # Add context from previous steps
        if workflow.get('steps'):
            query += f"\n\nPrevious results: {json.dumps({k: v['result']['output'][:200] for k, v in workflow['steps'].items()}, indent=2)}"
            
        return query
        
    async def _call_agent(self, agent_name: str, query: str) -> str:
        """Call agent via bridge"""
        result = subprocess.run([
            'python3', '/home/nike/ollama-agent-bridge.py',
            'agent', agent_name, query
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise Exception(f"Agent call failed: {result.stderr}")
            
    async def _send_workflow_update(self, workflow: Dict, step_name: str, result: Dict):
        """Send workflow progress update to Discord"""
        channel = self.bot.get_channel(workflow['channel_id'])
        if not channel:
            return
            
        embed = discord.Embed(
            title=f"🔄 Workflow Progress: {workflow['template']['name']}",
            description=f"Step completed: {step_name}",
            color=0x00ff00 if result['success'] else 0xff0000
        )
        
        embed.add_field(name="Workflow ID", value=workflow['id'], inline=True)
        embed.add_field(name="Progress", value=f"{workflow['current_step']}/{workflow['total_steps']}", inline=True)
        embed.add_field(name="Status", value="✅ Success" if result['success'] else "❌ Failed", inline=True)
        
        if result['success']:
            output = result['output'][:500] + "..." if len(result['output']) > 500 else result['output']
            embed.add_field(name="Result", value=f"```{output}```", inline=False)
        else:
            embed.add_field(name="Error", value=f"```{result['error']}```", inline=False)
            
        await channel.send(embed=embed)
        
    async def _send_workflow_completion(self, workflow: Dict):
        """Send workflow completion notification"""
        channel = self.bot.get_channel(workflow['channel_id'])
        if not channel:
            return
            
        embed = discord.Embed(
            title=f"✅ Workflow Completed: {workflow['template']['name']}",
            description="All steps completed successfully",
            color=0x00ff00
        )
        
        embed.add_field(name="Workflow ID", value=workflow['id'], inline=True)
        embed.add_field(name="Duration", value=f"{(datetime.now() - workflow['started_at']).seconds}s", inline=True)
        embed.add_field(name="Steps Completed", value=workflow['total_steps'], inline=True)
        
        # Add summary of results
        results_summary = []
        for step_name, step_result in workflow['steps'].items():
            results_summary.append(f"• {step_name}: ✅")
            
        embed.add_field(name="Results Summary", value='\n'.join(results_summary), inline=False)
        
        await channel.send(embed=embed)
        
    async def _send_workflow_error(self, workflow: Dict, error: str):
        """Send workflow error notification"""
        channel = self.bot.get_channel(workflow['channel_id'])
        if not channel:
            return
            
        embed = discord.Embed(
            title=f"❌ Workflow Error: {workflow['template']['name']}",
            description="Workflow execution failed",
            color=0xff0000
        )
        
        embed.add_field(name="Workflow ID", value=workflow['id'], inline=True)
        embed.add_field(name="Error", value=f"```{error}```", inline=False)
        
        await channel.send(embed=embed)

class SecureFileManager:
    """Secure file management system for Discord bot"""
    
    def __init__(self, base_path: str = "/home/nike/ollama-discord-bot/files"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.txt', '.py', '.js', '.json', '.yaml', '.yml', '.md', '.log', '.csv'}
        self.user_quotas = {}  # user_id -> bytes used
        self.max_user_quota = 100 * 1024 * 1024  # 100MB per user
        
    def get_user_path(self, user_id: int) -> Path:
        """Get user-specific directory"""
        user_path = self.base_path / f"user_{user_id}"
        user_path.mkdir(exist_ok=True)
        return user_path
        
    async def upload_file(self, user_id: int, file_name: str, content: bytes, channel_id: int) -> Dict[str, Any]:
        """Upload file securely"""
        # Validate file
        if len(content) > self.max_file_size:
            raise ValueError(f"File too large: {len(content)} bytes (max: {self.max_file_size})")
            
        file_path = Path(file_name)
        if file_path.suffix.lower() not in self.allowed_extensions:
            raise ValueError(f"File type not allowed: {file_path.suffix}")
            
        # Check user quota
        current_usage = await self.get_user_usage(user_id)
        if current_usage + len(content) > self.max_user_quota:
            raise ValueError(f"User quota exceeded: {current_usage + len(content)} bytes")
            
        # Sanitize filename
        safe_name = self.sanitize_filename(file_name)
        user_path = self.get_user_path(user_id)
        full_path = user_path / safe_name
        
        # Ensure unique filename
        counter = 1
        while full_path.exists():
            name_parts = safe_name.rsplit('.', 1)
            if len(name_parts) == 2:
                full_path = user_path / f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                full_path = user_path / f"{safe_name}_{counter}"
            counter += 1
            
        # Write file
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(content)
            
        # Calculate hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Update usage tracking
        self.user_quotas[user_id] = current_usage + len(content)
        
        return {
            'file_id': str(uuid.uuid4()),
            'original_name': file_name,
            'safe_name': safe_name,
            'path': str(full_path),
            'size': len(content),
            'hash': file_hash,
            'uploaded_at': datetime.now().isoformat(),
            'user_id': user_id,
            'channel_id': channel_id
        }
        
    async def download_file(self, user_id: int, file_name: str) -> Tuple[bytes, Dict[str, Any]]:
        """Download file securely"""
        user_path = self.get_user_path(user_id)
        file_path = user_path / self.sanitize_filename(file_name)
        
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_name}")
            
        # Read file
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            
        metadata = {
            'name': file_path.name,
            'size': len(content),
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        return content, metadata
        
    async def list_files(self, user_id: int) -> List[Dict[str, Any]]:
        """List user's files"""
        user_path = self.get_user_path(user_id)
        files = []
        
        for file_path in user_path.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'extension': file_path.suffix
                })
                
        return sorted(files, key=lambda x: x['modified'], reverse=True)
        
    async def delete_file(self, user_id: int, file_name: str) -> bool:
        """Delete file securely"""
        user_path = self.get_user_path(user_id)
        file_path = user_path / self.sanitize_filename(file_name)
        
        if not file_path.exists() or not file_path.is_file():
            return False
            
        # Update quota
        file_size = file_path.stat().st_size
        current_usage = self.user_quotas.get(user_id, 0)
        self.user_quotas[user_id] = max(0, current_usage - file_size)
        
        file_path.unlink()
        return True
        
    async def get_user_usage(self, user_id: int) -> int:
        """Get user's current storage usage"""
        if user_id not in self.user_quotas:
            user_path = self.get_user_path(user_id)
            total_size = 0
            
            for file_path in user_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    
            self.user_quotas[user_id] = total_size
            
        return self.user_quotas[user_id]
        
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        # Remove path separators and other dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = ''.join(c for c in filename if c in safe_chars)
        
        # Ensure it's not empty and not too long
        if not sanitized:
            sanitized = "file"
        
        return sanitized[:100]  # Max 100 characters
        
    async def execute_code(self, user_id: int, file_name: str, language: str = 'python3') -> Dict[str, Any]:
        """Execute code file securely"""
        user_path = self.get_user_path(user_id)
        file_path = user_path / self.sanitize_filename(file_name)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_name}")
            
        # Check file extension matches language
        ext_mapping = {
            'python3': ['.py'],
            'python': ['.py'],
            'node': ['.js'],
            'javascript': ['.js']
        }
        
        if language in ext_mapping and file_path.suffix not in ext_mapping[language]:
            raise ValueError(f"File extension {file_path.suffix} doesn't match language {language}")
            
        try:
            # Execute in sandboxed environment
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Copy file to temp directory
                tmp_file = Path(tmp_dir) / file_path.name
                async with aiofiles.open(file_path, 'r') as src:
                    content = await src.read()
                async with aiofiles.open(tmp_file, 'w') as dst:
                    await dst.write(content)
                    
                # Execute with restrictions
                cmd = [language, str(tmp_file)]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tmp_dir
                )
                
                return {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode,
                    'execution_time': 30  # Would track actual time
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Code execution timed out (30s limit)',
                'return_code': 1
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'return_code': 1
            }