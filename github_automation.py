#!/usr/bin/env python3
"""
Automated GitHub Workflow System for PhD Research
Handles automatic commits, documentation generation, and research backup
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json
import git
from git import Repo, GitCommandError
import subprocess
import hashlib
import shutil
from dataclasses import dataclass, asdict
import tempfile
import requests

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ResearchSession:
    """Represents a research session for tracking"""
    id: str
    topic: str
    start_time: str
    end_time: Optional[str] = None
    files_modified: List[str] = None
    key_findings: List[str] = None
    commit_hash: Optional[str] = None
    branch_name: Optional[str] = None
    
    def __post_init__(self):
        if self.files_modified is None:
            self.files_modified = []
        if self.key_findings is None:
            self.key_findings = []

class GitHubAutomation:
    """Automated GitHub workflow system for research"""
    
    def __init__(self, repo_path: str = None, github_token: str = None):
        self.repo_path = repo_path or os.getcwd()
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
        # Initialize repository
        try:
            self.repo = Repo(self.repo_path)
        except:
            logger.warning("Not in a git repository, will initialize when needed")
            self.repo = None
        
        # Session tracking
        self.sessions_dir = Path(self.repo_path) / ".research_sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        
        self.current_session: Optional[ResearchSession] = None
        self.auto_commit_enabled = False
        self.auto_push_enabled = False
        
        # Configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load automation configuration"""
        config_file = Path(self.repo_path) / ".github_automation.json"
        default_config = {
            "auto_commit_interval": 300,  # 5 minutes
            "auto_push_interval": 1800,   # 30 minutes
            "research_branches": True,
            "generate_documentation": True,
            "backup_frequency": "daily",
            "commit_message_template": "[AUTO] Research update: {topic}",
            "excluded_files": [".env", "*.log", "*.cache", "__pycache__"],
            "research_file_patterns": ["*.py", "*.md", "*.txt", "*.json", "*.pdf"],
            "auto_tag_releases": True
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            default_config.update(config)
        else:
            self._save_config(default_config)
        
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration"""
        config_file = Path(self.repo_path) / ".github_automation.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    async def initialize_repository(self, remote_url: str = None):
        """Initialize git repository if needed"""
        if not self.repo:
            logger.info("Initializing git repository")
            self.repo = Repo.init(self.repo_path)
            
            if remote_url:
                self.repo.create_remote('origin', remote_url)
        
        # Ensure .gitignore exists
        await self._ensure_gitignore()
        
        # Create initial commit if needed
        if not list(self.repo.iter_commits()):
            await self._create_initial_commit()
    
    async def _ensure_gitignore(self):
        """Ensure proper .gitignore exists"""
        gitignore_path = Path(self.repo_path) / ".gitignore"
        
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Research specific
*.log
*.cache
.research_sessions/temp/
rag_data/cache/
*.tmp

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Large files
*.pdf
*.zip
*.tar.gz
models/
data/large_datasets/
""".strip()
        
        if not gitignore_path.exists():
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
            logger.info("Created .gitignore file")
    
    async def _create_initial_commit(self):
        """Create initial commit"""
        self.repo.index.add(['.'])
        self.repo.index.commit("Initial commit - PhD Research Repository")
        logger.info("Created initial commit")
    
    def start_research_session(self, topic: str) -> str:
        """Start a new research session"""
        session_id = hashlib.sha256(
            f"{topic}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        self.current_session = ResearchSession(
            id=session_id,
            topic=topic,
            start_time=datetime.now().isoformat()
        )
        
        # Create research branch if enabled
        if self.config['research_branches']:
            branch_name = f"research/{topic.replace(' ', '-').lower()}"
            try:
                self.repo.git.checkout('-b', branch_name)
                self.current_session.branch_name = branch_name
                logger.info(f"Created research branch: {branch_name}")
            except GitCommandError as e:
                if "already exists" in str(e):
                    self.repo.git.checkout(branch_name)
                    logger.info(f"Switched to existing branch: {branch_name}")
                else:
                    logger.warning(f"Failed to create branch: {e}")
        
        # Save session
        self._save_session()
        
        logger.info(f"Started research session: {topic} ({session_id})")
        return session_id
    
    def end_research_session(self, key_findings: List[str] = None):
        """End current research session"""
        if not self.current_session:
            logger.warning("No active research session")
            return
        
        self.current_session.end_time = datetime.now().isoformat()
        if key_findings:
            self.current_session.key_findings = key_findings
        
        # Create final commit for session
        if self.repo.is_dirty():
            commit_msg = f"[RESEARCH] End session: {self.current_session.topic}\n\nKey findings:\n" + \
                        "\n".join([f"- {finding}" for finding in (key_findings or [])])
            
            commit_hash = self.commit_changes(commit_msg)
            self.current_session.commit_hash = commit_hash
        
        # Generate session summary
        self._generate_session_summary()
        
        # Save and clear session
        self._save_session()
        logger.info(f"Ended research session: {self.current_session.topic}")
        self.current_session = None
    
    def _save_session(self):
        """Save current session to file"""
        if not self.current_session:
            return
        
        session_file = self.sessions_dir / f"{self.current_session.id}.json"
        with open(session_file, 'w') as f:
            json.dump(asdict(self.current_session), f, indent=2)
    
    def _generate_session_summary(self):
        """Generate markdown summary of research session"""
        if not self.current_session:
            return
        
        summary_dir = Path(self.repo_path) / "research_summaries"
        summary_dir.mkdir(exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        summary_file = summary_dir / f"{date_str}_{self.current_session.topic.replace(' ', '_')}.md"
        
        summary_content = f"""# Research Session: {self.current_session.topic}

**Date:** {self.current_session.start_time.split('T')[0]}
**Duration:** {self.current_session.start_time} to {self.current_session.end_time}
**Session ID:** {self.current_session.id}
**Branch:** {self.current_session.branch_name or 'main'}

## Key Findings

{chr(10).join([f'- {finding}' for finding in self.current_session.key_findings])}

## Files Modified

{chr(10).join([f'- {file}' for file in self.current_session.files_modified])}

## Commit Hash

{self.current_session.commit_hash or 'No commits made'}

---
*Generated automatically by GitHub Automation System*
"""
        
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        logger.info(f"Generated session summary: {summary_file}")
    
    def track_file_modification(self, file_path: str):
        """Track file modification in current session"""
        if self.current_session and file_path not in self.current_session.files_modified:
            self.current_session.files_modified.append(file_path)
            self._save_session()
    
    def commit_changes(self, message: str = None, files: List[str] = None) -> Optional[str]:
        """Commit changes to repository"""
        if not self.repo:
            logger.error("No repository initialized")
            return None
        
        try:
            if not self.repo.is_dirty():
                logger.info("No changes to commit")
                return None
            
            # Add files
            if files:
                self.repo.index.add(files)
            else:
                # Add all tracked files and new files matching patterns
                self.repo.git.add('.')
            
            # Generate commit message if not provided
            if not message:
                if self.current_session:
                    message = self.config['commit_message_template'].format(
                        topic=self.current_session.topic
                    )
                else:
                    message = f"Auto-commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Commit
            commit = self.repo.index.commit(message)
            commit_hash = commit.hexsha[:8]
            
            logger.info(f"Committed changes: {commit_hash} - {message}")
            return commit_hash
            
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return None
    
    async def auto_commit_loop(self):
        """Auto-commit loop for continuous backup"""
        if not self.auto_commit_enabled:
            return
        
        while self.auto_commit_enabled:
            try:
                if self.repo and self.repo.is_dirty():
                    self.commit_changes()
                
                await asyncio.sleep(self.config['auto_commit_interval'])
                
            except Exception as e:
                logger.error(f"Auto-commit failed: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def push_changes(self, branch: str = None) -> bool:
        """Push changes to remote repository"""
        if not self.repo:
            logger.error("No repository initialized")
            return False
        
        try:
            if not branch:
                branch = self.repo.active_branch.name
            
            origin = self.repo.remotes.origin
            origin.push(branch)
            
            logger.info(f"Pushed changes to {branch}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push changes: {e}")
            return False
    
    async def auto_push_loop(self):
        """Auto-push loop for remote backup"""
        if not self.auto_push_enabled:
            return
        
        while self.auto_push_enabled:
            try:
                # Check if there are unpushed commits
                if self.repo and self._has_unpushed_commits():
                    self.push_changes()
                
                await asyncio.sleep(self.config['auto_push_interval'])
                
            except Exception as e:
                logger.error(f"Auto-push failed: {e}")
                await asyncio.sleep(300)  # Wait before retry
    
    def _has_unpushed_commits(self) -> bool:
        """Check if there are unpushed commits"""
        try:
            local_commit = self.repo.head.commit.hexsha
            remote_commit = self.repo.remotes.origin.refs[self.repo.active_branch.name].commit.hexsha
            return local_commit != remote_commit
        except:
            return False
    
    async def generate_research_documentation(self):
        """Generate comprehensive research documentation"""
        if not self.config['generate_documentation']:
            return
        
        docs_dir = Path(self.repo_path) / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Generate README
        await self._generate_readme()
        
        # Generate research index
        await self._generate_research_index()
        
        # Generate API documentation
        await self._generate_api_docs()
        
        logger.info("Generated research documentation")
    
    async def _generate_readme(self):
        """Generate comprehensive README"""
        readme_path = Path(self.repo_path) / "README.md"
        
        # Get repository stats
        commit_count = len(list(self.repo.iter_commits()))
        branch_count = len(list(self.repo.branches))
        
        # Get research sessions
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                sessions.append(session_data)
            except:
                continue
        
        readme_content = f"""# PhD Research Repository - Academic Research

**Automated Research Management System**

## 🎓 Research Overview

This repository contains comprehensive PhD research in academic research, focusing on digital criminal methodologies and defensive strategies.

### 📊 Repository Statistics

- **Commits:** {commit_count}
- **Branches:** {branch_count}
- **Research Sessions:** {len(sessions)}
- **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔬 Research Areas

- Digital forensics and incident response
- Cybercrime behavior analysis
- Dark web marketplace dynamics
- Cryptocurrency transaction analysis
- Social engineering psychology
- Threat intelligence gathering
- Malware reverse engineering

## 🤖 Automation Features

- **Auto-commit:** Every {self.config['auto_commit_interval']} seconds
- **Auto-push:** Every {self.config['auto_push_interval']} seconds
- **Research Sessions:** Automatic tracking and documentation
- **RAG Integration:** Advanced knowledge management
- **Documentation Generation:** Automated research summaries

## 📁 Repository Structure

```
├── docs/                   # Generated documentation
├── research_summaries/     # Session summaries
├── rag_data/              # RAG knowledge base
├── src/                   # Source code
├── papers/                # Research papers (PDFs)
└── .research_sessions/    # Session tracking
```

## 🚀 Recent Research Sessions

{self._format_recent_sessions(sessions[:5])}

## 📚 Key Publications & References

*Automatically generated from RAG system*

## 🛠 Tools & Technologies

- Python 3.13+
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Git automation with GitPython
- Discord bot integration
- Ollama for local LLM inference

---

*This README is automatically updated by the GitHub Automation System*
*Last update: {datetime.now().isoformat()}*
"""
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    def _format_recent_sessions(self, sessions: List[Dict]) -> str:
        """Format recent research sessions for README"""
        if not sessions:
            return "No recent sessions"
        
        formatted = []
        for session in sessions:
            date = session.get('start_time', '').split('T')[0]
            topic = session.get('topic', 'Unknown')
            findings_count = len(session.get('key_findings', []))
            
            formatted.append(f"- **{date}** - {topic} ({findings_count} findings)")
        
        return "\n".join(formatted)
    
    async def _generate_research_index(self):
        """Generate research index page"""
        docs_dir = Path(self.repo_path) / "docs"
        index_path = docs_dir / "research_index.md"
        
        # Collect all research sessions
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    sessions.append(json.load(f))
            except:
                continue
        
        # Sort by date
        sessions.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        index_content = f"""# Research Index

## All Research Sessions

{self._generate_sessions_table(sessions)}

## Topics Overview

{self._generate_topics_overview(sessions)}

## Timeline

{self._generate_research_timeline(sessions)}

---
*Generated: {datetime.now().isoformat()}*
"""
        
        with open(index_path, 'w') as f:
            f.write(index_content)
    
    def _generate_sessions_table(self, sessions: List[Dict]) -> str:
        """Generate table of all research sessions"""
        if not sessions:
            return "No sessions recorded"
        
        table = "| Date | Topic | Duration | Findings | Commit |\n"
        table += "|------|-------|----------|----------|--------|\n"
        
        for session in sessions:
            date = session.get('start_time', '').split('T')[0]
            topic = session.get('topic', 'Unknown')[:30]
            
            start = session.get('start_time', '')
            end = session.get('end_time', '')
            duration = "Ongoing" if not end else self._calculate_duration(start, end)
            
            findings = len(session.get('key_findings', []))
            commit = session.get('commit_hash', 'N/A')[:8]
            
            table += f"| {date} | {topic} | {duration} | {findings} | {commit} |\n"
        
        return table
    
    def _calculate_duration(self, start: str, end: str) -> str:
        """Calculate session duration"""
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            duration = end_dt - start_dt
            
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"
    
    def _generate_topics_overview(self, sessions: List[Dict]) -> str:
        """Generate topics overview"""
        topics = {}
        for session in sessions:
            topic = session.get('topic', 'Unknown')
            if topic not in topics:
                topics[topic] = 0
            topics[topic] += 1
        
        if not topics:
            return "No topics recorded"
        
        overview = "### Most Researched Topics\n\n"
        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]:
            overview += f"- **{topic}** ({count} sessions)\n"
        
        return overview
    
    def _generate_research_timeline(self, sessions: List[Dict]) -> str:
        """Generate research timeline"""
        if not sessions:
            return "No timeline data"
        
        timeline = "### Recent Research Activity\n\n"
        for session in sessions[:10]:
            date = session.get('start_time', '').split('T')[0]
            topic = session.get('topic', 'Unknown')
            findings = len(session.get('key_findings', []))
            
            timeline += f"**{date}** - {topic}"
            if findings > 0:
                timeline += f" ({findings} findings)"
            timeline += "\n"
        
        return timeline
    
    async def _generate_api_docs(self):
        """Generate API documentation for research tools"""
        docs_dir = Path(self.repo_path) / "docs"
        api_path = docs_dir / "api_reference.md"
        
        api_content = f"""# API Reference

## GitHub Automation

### ResearchSession

Methods for managing research sessions.

### GitHubAutomation

Main automation class for repository management.

## RAG System

### AdvancedRAGSystem

Advanced retrieval-augmented generation for research.

---
*Generated: {datetime.now().isoformat()}*
"""
        
        with open(api_path, 'w') as f:
            f.write(api_content)
    
    async def create_release(self, version: str, notes: str = ""):
        """Create a GitHub release"""
        if not self.github_token:
            logger.error("GitHub token not configured")
            return False
        
        try:
            # Get repository info
            remote_url = self.repo.remotes.origin.url
            
            # Extract owner/repo from URL
            if 'github.com' in remote_url:
                parts = remote_url.split('/')
                owner = parts[-2]
                repo = parts[-1].replace('.git', '')
                
                # Create release via API
                url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                
                headers = {
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                data = {
                    'tag_name': version,
                    'name': f'Research Release {version}',
                    'body': notes,
                    'draft': False,
                    'prerelease': False
                }
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 201:
                    logger.info(f"Created release {version}")
                    return True
                else:
                    logger.error(f"Failed to create release: {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to create release: {e}")
            return False
    
    def enable_automation(self, auto_commit: bool = True, auto_push: bool = True):
        """Enable automated workflows"""
        self.auto_commit_enabled = auto_commit
        self.auto_push_enabled = auto_push
        
        if auto_commit:
            asyncio.create_task(self.auto_commit_loop())
        
        if auto_push:
            asyncio.create_task(self.auto_push_loop())
        
        logger.info(f"Enabled automation - Commit: {auto_commit}, Push: {auto_push}")
    
    def disable_automation(self):
        """Disable automated workflows"""
        self.auto_commit_enabled = False
        self.auto_push_enabled = False
        logger.info("Disabled automation")

# Global automation instance
github_automation = GitHubAutomation()

async def main():
    """Test the GitHub automation system"""
    await github_automation.initialize_repository()
    
    # Start a test session
    session_id = github_automation.start_research_session("Test RAG Integration")
    
    # Simulate some work
    github_automation.track_file_modification("test_file.py")
    
    # End session
    github_automation.end_research_session([
        "Successfully integrated RAG system",
        "Automated GitHub workflows working",
        "Documentation generation complete"
    ])
    
    # Generate documentation
    await github_automation.generate_research_documentation()

if __name__ == "__main__":
    asyncio.run(main())
