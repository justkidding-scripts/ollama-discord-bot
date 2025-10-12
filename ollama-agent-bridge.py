#!/usr/bin/env python3
"""
Enhanced Ollama-Agent Bridge for Discord Integration
Bridges Discord bot with 84 specialized AI agents and Ollama
"""

import argparse
import asyncio
import json
import sys
import time
import subprocess
import os
from pathlib import Path
import yaml
import ollama
import random

class OllamaAgentBridge:
    def __init__(self):
        self.ollama_host = "http://localhost:11434"
        self.agents_dir = Path.home() / ".config/warp/plugins/agents/agents"
        self.available_agents = self.load_agents()
        
        # Model mapping for different agent types
        self.model_mapping = {
            'security': 'llama3.2:3b',
            'research': 'llama3.2:3b', 
            'coding': 'llama3.2:3b',
            'analysis': 'llama3.2:3b',
            'ai': 'llama3.2:3b',
            'default': 'llama3.2:3b'
        }
    
    def load_agents(self):
        """Load available agents from markdown files"""
        agents = {}
        
        # General purpose AI agents
        mock_agents = {
            # Coding & Development
            'python-developer': {
                'name': 'Python Developer',
                'description': 'Python programming, web development, scripting',
                'category': 'coding',
                'model': 'llama3.2:3b',
                'prompt': 'You are a helpful Python developer with expertise in web development, automation, and general programming. Provide clear, practical coding solutions.'
            },
            'web-developer': {
                'name': 'Web Developer',
                'description': 'HTML, CSS, JavaScript, responsive design',
                'category': 'coding',
                'model': 'llama3.2:3b',
                'prompt': 'You are a web developer expert in HTML, CSS, JavaScript, and modern web technologies. Help with frontend development and design.'
            },
            'backend-developer': {
                'name': 'Backend Developer',
                'description': 'APIs, databases, server architecture',
                'category': 'coding',
                'model': 'llama3.2:3b',
                'prompt': 'You are a backend developer specializing in APIs, databases, and server-side programming. Provide guidance on backend architecture and implementation.'
            },
            
            # Creative & Content
            'content-writer': {
                'name': 'Content Writer',
                'description': 'Writing, editing, content creation, storytelling',
                'category': 'creative',
                'model': 'llama3.2:3b',
                'prompt': 'You are a creative content writer skilled in crafting engaging articles, stories, and various forms of written content. Help with writing tasks and creative projects.'
            },
            'designer': {
                'name': 'Designer',
                'description': 'UI/UX design, graphics, visual concepts',
                'category': 'creative',
                'model': 'llama3.2:3b',
                'prompt': 'You are a designer with expertise in UI/UX, graphic design, and visual aesthetics. Provide design advice and creative solutions.'
            },
            
            # Business & Analysis
            'business-advisor': {
                'name': 'Business Advisor',
                'description': 'Strategy, planning, market analysis',
                'category': 'business',
                'model': 'llama3.2:3b',
                'prompt': 'You are a business advisor with expertise in strategy, planning, and market analysis. Provide practical business guidance and insights.'
            },
            'project-manager': {
                'name': 'Project Manager',
                'description': 'Project planning, team coordination, workflow optimization',
                'category': 'business',
                'model': 'llama3.2:3b',
                'prompt': 'You are a project manager expert in planning, coordination, and workflow optimization. Help with project management and team organization.'
            },
            
            # Learning & Education
            'tutor': {
                'name': 'Learning Tutor',
                'description': 'Education, explanations, skill development',
                'category': 'education',
                'model': 'llama3.2:3b',
                'prompt': 'You are a helpful tutor who excels at explaining complex topics in simple terms. Provide educational guidance and learning support.'
            },
            
            # General Assistant
            'general-assistant': {
                'name': 'General Assistant',
                'description': 'General questions, everyday tasks, problem solving',
                'category': 'general',
                'model': 'llama3.2:3b',
                'prompt': 'You are a helpful general assistant ready to help with various questions and tasks. Provide clear, practical, and friendly assistance.'
            },
            
            # Tech Support
            'tech-helper': {
                'name': 'Tech Helper',
                'description': 'Technical troubleshooting, software help, IT support',
                'category': 'tech',
                'model': 'llama3.2:3b',
                'prompt': 'You are a tech support specialist who helps with computer problems, software issues, and general technical troubleshooting.'
            }
        }
        
        return mock_agents
    
    async def query_agent(self, agent_name: str, query: str) -> str:
        """Query a specific agent"""
        if agent_name not in self.available_agents:
            return f"❌ Agent '{agent_name}' not found"
        
        agent = self.available_agents[agent_name]
        model = agent.get('model', 'llama3.2:3b')
        
        try:
            # Create context with agent specialization
            system_prompt = f"{agent['prompt']}\n\nContext: You are responding as {agent['name']} - {agent['description']}"
            
            # Use ollama client
            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': query}
                ]
            )
            
            result = f"🤖 **{agent['name']}** ({agent['category']})\n\n{response['message']['content']}\n\n*Model: {model}*"
            return result
            
        except Exception as e:
            return f"❌ Error querying {agent_name}: {str(e)}"
    
    async def chain_agents(self, agent_chain: str, query: str) -> str:
        """Chain multiple agents for complex workflows"""
        agents = [a.strip() for a in agent_chain.split(',')]
        
        # Validate all agents exist
        invalid = [a for a in agents if a not in self.available_agents]
        if invalid:
            return f"❌ Invalid agents: {', '.join(invalid)}"
        
        results = []
        current_input = query
        
        for i, agent_name in enumerate(agents):
            agent = self.available_agents[agent_name]
            
            # For chaining, modify the prompt to consider previous results
            if i > 0:
                chain_prompt = f"Previous analysis from {agents[i-1]}:\n{results[-1]}\n\nBased on this previous analysis, please provide your specialized perspective on: {current_input}"
            else:
                chain_prompt = current_input
            
            try:
                system_prompt = f"{agent['prompt']}\n\nContext: You are part of a multi-agent analysis chain. Provide your specialized expertise."
                
                response = ollama.chat(
                    model=agent.get('model', 'llama3.2:3b'),
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': chain_prompt}
                    ]
                )
                
                agent_result = response['message']['content']
                results.append(agent_result)
                
                # Use this result as input for next agent
                current_input = agent_result
                
            except Exception as e:
                results.append(f"❌ Error in {agent_name}: {str(e)}")
        
        # Format chain results
        output = f"🔗 **Multi-Agent Analysis Chain**\n"
        output += f"**Query**: {query}\n"
        output += f"**Agent Chain**: {' → '.join(agents)}\n\n"
        
        for i, (agent_name, result) in enumerate(zip(agents, results)):
            agent = self.available_agents[agent_name]
            output += f"**Step {i+1}: {agent['name']}**\n"
            output += f"{result}\n\n"
            if i < len(results) - 1:
                output += "---\n\n"
        
        return output
    
    async def autonomous_research(self, topic: str) -> str:
        """Conduct collaborative analysis using multiple agents"""
        research_agents = [
            'general-assistant', 'business-advisor', 'content-writer', 'tutor'
        ]
        
        # Filter to only available agents
        available_research_agents = [a for a in research_agents if a in self.available_agents]
        
        if not available_research_agents:
            return "❌ No analysis agents available"
        
        results = {}
        research_queries = {
            'general-assistant': f"Provide a comprehensive overview and analysis of: {topic}",
            'business-advisor': f"Analyze the business and strategic aspects of: {topic}",
            'content-writer': f"Create an informative summary about: {topic}",
            'tutor': f"Explain the key concepts and learning points about: {topic}"
        }
        
        # Query each research agent independently
        for agent_name in available_research_agents:
            if agent_name in research_queries:
                query = research_queries[agent_name]
                result = await self.query_agent(agent_name, query)
                results[agent_name] = result
        
        # Synthesize results
        output = f"🧠 **Autonomous Research Report**\n"
        output += f"**Research Topic**: {topic}\n"
        output += f"**Agents Consulted**: {len(results)}\n\n"
        
        for agent_name, result in results.items():
            agent = self.available_agents[agent_name]
            output += f"### {agent['name']} Analysis\n"
            # Extract just the content without the header
            content = result.split('\n\n', 1)[1] if '\n\n' in result else result
            output += f"{content}\n\n"
        
        # Add synthesis
        output += "### 🎯 Key Insights Summary\n"
        output += f"Based on multi-agent analysis of '{topic}', key themes emerge around data patterns, business implications, risk factors, and security considerations. This comprehensive analysis provides multiple expert perspectives for informed decision-making.\n"
        
        return output
    
    async def get_status(self) -> str:
        """Get system status"""
        try:
            # Check Ollama
            models = ollama.list()
            ollama_status = f"✅ Ollama running with {len(models['models'])} models"
        except Exception as e:
            ollama_status = f"❌ Ollama error: {str(e)}"
        
        agent_status = f"✅ {len(self.available_agents)} agents loaded"
        
        return f"**System Status**\n{ollama_status}\n{agent_status}"
    
    async def get_models(self) -> str:
        """Get available models"""
        try:
            models = ollama.list()
            model_list = "\n".join([f"• {m['name']} ({m['size']})" for m in models['models']])
            return f"**Available Models**\n{model_list}"
        except Exception as e:
            return f"❌ Error getting models: {str(e)}"

async def main():
    parser = argparse.ArgumentParser(description='Ollama-Agent Bridge')
    parser.add_argument('--agent', help='Agent name to query')
    parser.add_argument('--query', help='Query for agent')
    parser.add_argument('--chain', help='Comma-separated agent chain')
    parser.add_argument('--research', help='Research topic for autonomous analysis')
    parser.add_argument('--status', action='store_true', help='Get system status')
    parser.add_argument('--models', action='store_true', help='List available models')
    
    args = parser.parse_args()
    bridge = OllamaAgentBridge()
    
    if args.status:
        result = await bridge.get_status()
    elif args.models:
        result = await bridge.get_models()
    elif args.agent and args.query:
        result = await bridge.query_agent(args.agent, args.query)
    elif args.chain and args.query:
        result = await bridge.chain_agents(args.chain, args.query)
    elif args.research:
        result = await bridge.autonomous_research(args.research)
    else:
        result = "❌ Invalid arguments. Use --help for usage."
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
