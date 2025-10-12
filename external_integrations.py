#!/usr/bin/env python3
"""
External API Integrations - GitHub, VirusTotal, OSINT tools, Security scanners
"""

import aiohttp
import asyncio
import json
import base64
import hashlib
import hmac
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class GitHubIntegration:
    """GitHub API integration for repository management and analysis"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = None
        
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            self.session = aiohttp.ClientSession(headers=headers)
            
    async def search_repositories(self, query: str, language: str = None, stars: int = None) -> List[Dict]:
        """Search GitHub repositories"""
        await self.init_session()
        
        search_query = query
        if language:
            search_query += f" language:{language}"
        if stars:
            search_query += f" stars:>={stars}"
            
        url = f"{self.base_url}/search/repositories"
        params = {'q': search_query, 'sort': 'stars', 'order': 'desc'}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data['items'][:10]  # Top 10 results
            else:
                raise Exception(f"GitHub API error: {response.status}")
                
    async def analyze_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Analyze a GitHub repository for security and metrics"""
        await self.init_session()
        
        # Get repository info
        repo_url = f"{self.base_url}/repos/{owner}/{repo}"
        languages_url = f"{repo_url}/languages"
        contents_url = f"{repo_url}/contents"
        
        results = {}
        
        try:
            # Repository metadata
            async with self.session.get(repo_url) as response:
                if response.status == 200:
                    repo_data = await response.json()
                    results['metadata'] = {
                        'name': repo_data['name'],
                        'full_name': repo_data['full_name'],
                        'description': repo_data.get('description', ''),
                        'stars': repo_data['stargazers_count'],
                        'forks': repo_data['forks_count'],
                        'language': repo_data.get('language'),
                        'created_at': repo_data['created_at'],
                        'updated_at': repo_data['updated_at'],
                        'size': repo_data['size']
                    }
                    
            # Language breakdown
            async with self.session.get(languages_url) as response:
                if response.status == 200:
                    results['languages'] = await response.json()
                    
            # Security analysis (check for common security files)
            security_files = ['SECURITY.md', 'security.md', '.github/SECURITY.md']
            results['security_files'] = []
            
            for file in security_files:
                check_url = f"{contents_url}/{file}"
                async with self.session.get(check_url) as response:
                    if response.status == 200:
                        results['security_files'].append(file)
                        
            # Check for dependency files
            dependency_files = ['requirements.txt', 'package.json', 'Pipfile', 'Gemfile', 'pom.xml']
            results['dependency_files'] = []
            
            for file in dependency_files:
                check_url = f"{contents_url}/{file}"
                async with self.session.get(check_url) as response:
                    if response.status == 200:
                        results['dependency_files'].append(file)
                        
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get GitHub user profile and activity analysis"""
        await self.init_session()
        
        user_url = f"{self.base_url}/users/{username}"
        repos_url = f"{user_url}/repos"
        
        results = {}
        
        try:
            # User info
            async with self.session.get(user_url) as response:
                if response.status == 200:
                    user_data = await response.json()
                    results['profile'] = {
                        'login': user_data['login'],
                        'name': user_data.get('name'),
                        'bio': user_data.get('bio'),
                        'company': user_data.get('company'),
                        'location': user_data.get('location'),
                        'public_repos': user_data['public_repos'],
                        'followers': user_data['followers'],
                        'following': user_data['following'],
                        'created_at': user_data['created_at']
                    }
                    
            # Repository analysis
            async with self.session.get(repos_url) as response:
                if response.status == 200:
                    repos = await response.json()
                    
                    # Analyze language preferences and activity
                    languages = {}
                    total_stars = 0
                    
                    for repo in repos[:20]:  # Top 20 repos
                        if repo['language']:
                            languages[repo['language']] = languages.get(repo['language'], 0) + 1
                        total_stars += repo['stargazers_count']
                        
                    results['activity'] = {
                        'languages': languages,
                        'total_stars': total_stars,
                        'recent_repos': [r['name'] for r in repos[:5]]
                    }
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results

class VirusTotalIntegration:
    """VirusTotal API integration for malware and URL analysis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
        self.session = None
        
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            headers = {'x-apikey': self.api_key}
            self.session = aiohttp.ClientSession(headers=headers)
            
    async def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan URL with VirusTotal"""
        await self.init_session()
        
        # Submit URL for scanning
        submit_url = f"{self.base_url}/urls"
        data = aiohttp.FormData()
        data.add_field('url', url)
        
        async with self.session.post(submit_url, data=data) as response:
            if response.status == 200:
                result = await response.json()
                analysis_id = result['data']['id']
                
                # Wait a bit then get results
                await asyncio.sleep(5)
                
                analysis_url = f"{self.base_url}/analyses/{analysis_id}"
                async with self.session.get(analysis_url) as analysis_response:
                    if analysis_response.status == 200:
                        analysis_data = await analysis_response.json()
                        return self._parse_analysis_results(analysis_data, 'url')
                        
        return {'error': 'Failed to scan URL'}
        
    async def scan_file_hash(self, file_hash: str) -> Dict[str, Any]:
        """Scan file hash with VirusTotal"""
        await self.init_session()
        
        url = f"{self.base_url}/files/{file_hash}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_analysis_results(data, 'file')
            else:
                return {'error': f'File hash not found: {file_hash}'}
                
    def _parse_analysis_results(self, data: Dict, scan_type: str) -> Dict[str, Any]:
        """Parse VirusTotal analysis results"""
        attributes = data.get('data', {}).get('attributes', {})
        stats = attributes.get('stats', {})
        
        return {
            'scan_type': scan_type,
            'scan_date': attributes.get('date'),
            'stats': {
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'clean': stats.get('undetected', 0),
                'timeout': stats.get('timeout', 0)
            },
            'total_scans': sum(stats.values()) if stats else 0,
            'threat_detected': stats.get('malicious', 0) > 0,
            'engines_flagged': [
                engine for engine, result in attributes.get('scans', {}).items()
                if result.get('category') == 'malicious'
            ][:5]  # Top 5 engines that flagged it
        }

class OSINTTools:
    """OSINT (Open Source Intelligence) tools integration"""
    
    def __init__(self):
        self.session = None
        
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def whois_lookup(self, domain: str) -> Dict[str, Any]:
        """Perform WHOIS lookup"""
        try:
            result = subprocess.run(
                ['whois', domain],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                whois_data = result.stdout
                return {
                    'domain': domain,
                    'raw_data': whois_data,
                    'parsed': self._parse_whois(whois_data)
                }
            else:
                return {'error': f'WHOIS lookup failed for {domain}'}
                
        except Exception as e:
            return {'error': str(e)}
            
    def _parse_whois(self, whois_data: str) -> Dict[str, Any]:
        """Parse WHOIS data for key information"""
        parsed = {}
        
        # Common patterns
        patterns = {
            'registrar': r'Registrar:\s*(.+)',
            'creation_date': r'Creation Date:\s*(.+)',
            'expiry_date': r'Registry Expiry Date:\s*(.+)',
            'name_servers': r'Name Server:\s*(.+)'
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, whois_data, re.IGNORECASE)
            if matches:
                parsed[key] = matches[0].strip() if len(matches) == 1 else [m.strip() for m in matches]
                
        return parsed
        
    async def dns_lookup(self, domain: str, record_type: str = 'A') -> Dict[str, Any]:
        """Perform DNS lookup"""
        try:
            result = subprocess.run(
                ['dig', '+short', domain, record_type],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                records = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return {
                    'domain': domain,
                    'record_type': record_type,
                    'records': records
                }
            else:
                return {'error': f'DNS lookup failed for {domain}'}
                
        except Exception as e:
            return {'error': str(e)}
            
    async def shodan_ip_lookup(self, ip: str, api_key: str) -> Dict[str, Any]:
        """Lookup IP information via Shodan (if API key provided)"""
        if not api_key:
            return {'error': 'Shodan API key required'}
            
        await self.init_session()
        
        url = f"https://api.shodan.io/shodan/host/{ip}"
        params = {'key': api_key}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'ip': ip,
                        'country': data.get('country_name'),
                        'city': data.get('city'),
                        'isp': data.get('isp'),
                        'organization': data.get('org'),
                        'ports': data.get('ports', []),
                        'hostnames': data.get('hostnames', []),
                        'last_update': data.get('last_update')
                    }
                else:
                    return {'error': f'Shodan lookup failed: {response.status}'}
                    
        except Exception as e:
            return {'error': str(e)}
            
    async def check_reputation(self, indicator: str) -> Dict[str, Any]:
        """Check indicator reputation using multiple sources"""
        results = {}
        
        # Determine indicator type
        if self._is_ip(indicator):
            results['type'] = 'ip'
            # Would integrate with threat intelligence feeds
            results['reputation'] = 'unknown'
        elif self._is_domain(indicator):
            results['type'] = 'domain'
            # Would check domain reputation
            results['reputation'] = 'unknown'
        elif self._is_hash(indicator):
            results['type'] = 'hash'
            # Would check hash reputation
            results['reputation'] = 'unknown'
        else:
            results['error'] = 'Unknown indicator type'
            
        return results
        
    def _is_ip(self, indicator: str) -> bool:
        """Check if indicator is an IP address"""
        import ipaddress
        try:
            ipaddress.ip_address(indicator)
            return True
        except ValueError:
            return False
            
    def _is_domain(self, indicator: str) -> bool:
        """Check if indicator is a domain"""
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-._]*[a-zA-Z0-9]$'
        return re.match(domain_pattern, indicator) is not None
        
    def _is_hash(self, indicator: str) -> bool:
        """Check if indicator is a hash"""
        hash_patterns = {
            32: 'MD5',
            40: 'SHA1', 
            64: 'SHA256'
        }
        return len(indicator) in hash_patterns and all(c in '0123456789abcdefABCDEF' for c in indicator)

class SecurityScanners:
    """Security scanning tools integration"""
    
    def __init__(self):
        pass
        
    async def nmap_scan(self, target: str, scan_type: str = 'quick') -> Dict[str, Any]:
        """Perform nmap scan (requires nmap to be installed)"""
        scan_options = {
            'quick': ['-T4', '-F'],
            'tcp': ['-sS', '-T4'],
            'udp': ['-sU', '--top-ports', '100'],
            'service': ['-sV', '-T4'],
            'os': ['-O', '-T4']
        }
        
        if scan_type not in scan_options:
            return {'error': f'Unknown scan type: {scan_type}'}
            
        try:
            cmd = ['nmap'] + scan_options[scan_type] + [target]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return {
                    'target': target,
                    'scan_type': scan_type,
                    'raw_output': result.stdout,
                    'parsed': self._parse_nmap_output(result.stdout)
                }
            else:
                return {'error': f'Nmap scan failed: {result.stderr}'}
                
        except subprocess.TimeoutExpired:
            return {'error': 'Nmap scan timed out'}
        except FileNotFoundError:
            return {'error': 'Nmap not installed'}
        except Exception as e:
            return {'error': str(e)}
            
    def _parse_nmap_output(self, output: str) -> Dict[str, Any]:
        """Parse nmap output for key information"""
        parsed = {
            'open_ports': [],
            'host_status': 'unknown',
            'os_guess': None
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Host status
            if 'Host is up' in line:
                parsed['host_status'] = 'up'
            elif 'host down' in line.lower():
                parsed['host_status'] = 'down'
                
            # Open ports
            if '/tcp' in line and 'open' in line:
                port_info = line.split()
                if len(port_info) >= 3:
                    parsed['open_ports'].append({
                        'port': port_info[0],
                        'state': port_info[1],
                        'service': port_info[2] if len(port_info) > 2 else 'unknown'
                    })
                    
            # OS detection
            if 'OS details:' in line:
                parsed['os_guess'] = line.split('OS details:')[1].strip()
                
        return parsed
        
    async def ssl_scan(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Perform SSL/TLS scan using openssl"""
        try:
            # Get certificate info
            cert_cmd = [
                'openssl', 's_client', '-connect', f'{hostname}:{port}',
                '-servername', hostname, '-showcerts'
            ]
            
            result = subprocess.run(
                cert_cmd,
                input='',
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'hostname': hostname,
                    'port': port,
                    'certificate_info': self._parse_ssl_output(result.stdout),
                    'connection_successful': True
                }
            else:
                return {
                    'hostname': hostname,
                    'port': port,
                    'error': result.stderr,
                    'connection_successful': False
                }
                
        except Exception as e:
            return {'error': str(e)}
            
    def _parse_ssl_output(self, output: str) -> Dict[str, Any]:
        """Parse SSL certificate information"""
        cert_info = {}
        
        # Extract certificate details
        if '-----BEGIN CERTIFICATE-----' in output:
            cert_start = output.find('-----BEGIN CERTIFICATE-----')
            cert_end = output.find('-----END CERTIFICATE-----', cert_start)
            
            if cert_end != -1:
                cert_data = output[cert_start:cert_end + 25]
                
                # Parse certificate with openssl
                try:
                    parse_result = subprocess.run(
                        ['openssl', 'x509', '-text', '-noout'],
                        input=cert_data,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if parse_result.returncode == 0:
                        cert_text = parse_result.stdout
                        
                        # Extract key information
                        for line in cert_text.split('\n'):
                            line = line.strip()
                            
                            if 'Subject:' in line:
                                cert_info['subject'] = line.split('Subject:')[1].strip()
                            elif 'Issuer:' in line:
                                cert_info['issuer'] = line.split('Issuer:')[1].strip()
                            elif 'Not Before:' in line:
                                cert_info['not_before'] = line.split('Not Before:')[1].strip()
                            elif 'Not After :' in line:
                                cert_info['not_after'] = line.split('Not After :')[1].strip()
                                
                except Exception:
                    cert_info['parse_error'] = 'Failed to parse certificate'
                    
        return cert_info