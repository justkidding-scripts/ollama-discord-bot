#!/usr/bin/env python3
"""
Advanced RAG (Retrieval Augmented Generation) System for PhD Research
Integrates with academic databases, PDFs, and knowledge bases
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
import PyPDF2
import arxiv
from scholarly import scholarly, ProxyGenerator
import json
import hashlib
from datetime import datetime, timedelta
import pickle
from pathlib import Path
import aiohttp
import re
from dataclasses import dataclass, asdict

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ResearchDocument:
    """Represents a research document with metadata"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    content: str
    source: str  # 'arxiv', 'pdf', 'manual', 'google_scholar'
    url: Optional[str] = None
    publication_date: Optional[str] = None
    citations: int = 0
    relevance_score: float = 0.0
    embedding: Optional[List[float]] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique document ID"""
        content_hash = hashlib.sha256(
            f"{self.title}{self.authors}{self.abstract}".encode()
        ).hexdigest()[:12]
        return f"{self.source}_{content_hash}"

class AdvancedRAGSystem:
    """Advanced RAG system for academic research"""
    
    def __init__(self, data_dir: str = "./rag_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.client = None
        self.collection = None
        self.encoder = None
        self.documents: Dict[str, ResearchDocument] = {}
        
        # Cache and config
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.config_file = self.data_dir / "config.json"
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load RAG system configuration"""
        default_config = {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "max_documents": 10000,
            "chunk_size": 512,
            "overlap": 50,
            "arxiv_max_results": 50,
            "scholar_max_results": 20,
            "cache_ttl_days": 7
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            default_config.update(config)
        else:
            self._save_config(default_config)
        
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    async def initialize(self):
        """Initialize the RAG system"""
        logger.info("Initializing Advanced RAG System...")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.data_dir / "chroma_db"))
        self.collection = self.client.get_or_create_collection(
            name="phd_research",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize sentence transformer
        logger.info(f"Loading embedding model: {self.config['embedding_model']}")
        self.encoder = SentenceTransformer(self.config['embedding_model'])
        
        # Load existing documents
        await self._load_documents()
        
        logger.info(f"RAG System initialized with {len(self.documents)} documents")
    
    async def _load_documents(self):
        """Load existing documents from storage"""
        docs_file = self.data_dir / "documents.pkl"
        if docs_file.exists():
            with open(docs_file, 'rb') as f:
                self.documents = pickle.load(f)
                logger.info(f"Loaded {len(self.documents)} cached documents")
    
    async def _save_documents(self):
        """Save documents to storage"""
        docs_file = self.data_dir / "documents.pkl"
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding"""
        chunk_size = self.config['chunk_size']
        overlap = self.config['overlap']
        
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Keep overlap
                    words = current_chunk.split()
                    if len(words) > overlap:
                        current_chunk = " ".join(words[-overlap:]) + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def search_arxiv(self, query: str, max_results: int = None) -> List[ResearchDocument]:
        """Search ArXiv for research papers"""
        if max_results is None:
            max_results = self.config['arxiv_max_results']
        
        logger.info(f"Searching ArXiv for: {query}")
        documents = []
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            async for result in search.results():
                doc = ResearchDocument(
                    id="",  # Will be generated
                    title=result.title,
                    authors=[str(author) for author in result.authors],
                    abstract=result.summary,
                    content=result.summary,  # For now, just use abstract
                    source="arxiv",
                    url=result.pdf_url,
                    publication_date=result.published.isoformat(),
                    citations=0  # ArXiv doesn't provide citation count
                )
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
        
        return documents
    
    async def search_google_scholar(self, query: str, max_results: int = None) -> List[ResearchDocument]:
        """Search Google Scholar for research papers"""
        if max_results is None:
            max_results = self.config['scholar_max_results']
        
        logger.info(f"Searching Google Scholar for: {query}")
        documents = []
        
        try:
            # Setup proxy if needed (Scholar blocks frequent requests)
            pg = ProxyGenerator()
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            
            search_query = scholarly.search_pubs(query)
            
            for i, result in enumerate(search_query):
                if i >= max_results:
                    break
                
                try:
                    # Get detailed info
                    pub = scholarly.fill(result)
                    
                    doc = ResearchDocument(
                        id="",
                        title=pub.get('title', ''),
                        authors=pub.get('author', []),
                        abstract=pub.get('abstract', ''),
                        content=pub.get('abstract', ''),
                        source="google_scholar",
                        url=pub.get('url', ''),
                        publication_date=str(pub.get('year', '')),
                        citations=pub.get('num_citations', 0)
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    logger.warning(f"Failed to process Scholar result: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
        
        return documents
    
    async def add_pdf_document(self, pdf_path: str, title: str = None, authors: List[str] = None) -> ResearchDocument:
        """Add PDF document to knowledge base"""
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            # Extract metadata
            if not title:
                title = os.path.basename(pdf_path).replace('.pdf', '')
            
            if not authors:
                authors = []
            
            # Try to extract abstract (first few paragraphs)
            paragraphs = text.split('\n\n')
            abstract = ""
            for para in paragraphs[:5]:
                if len(para.strip()) > 50:
                    abstract = para.strip()
                    break
            
            doc = ResearchDocument(
                id="",
                title=title,
                authors=authors,
                abstract=abstract[:500] + "..." if len(abstract) > 500 else abstract,
                content=text,
                source="pdf",
                url=f"file://{pdf_path}"
            )
            
            await self.add_document(doc)
            return doc
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
            raise
    
    async def add_document(self, document: ResearchDocument):
        """Add document to the knowledge base"""
        logger.info(f"Adding document: {document.title[:50]}...")
        
        # Generate embedding
        text_to_embed = f"{document.title} {document.abstract} {document.content[:1000]}"
        document.embedding = self.encoder.encode(text_to_embed).tolist()
        
        # Chunk the content
        chunks = self._chunk_text(document.content)
        
        # Add to ChromaDB
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document.id}_chunk_{i}"
            chunk_embedding = self.encoder.encode(chunk).tolist()
            
            metadata = {
                "doc_id": document.id,
                "title": document.title,
                "authors": json.dumps(document.authors),
                "source": document.source,
                "url": document.url or "",
                "chunk_index": i,
                "citations": document.citations
            }
            
            self.collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[chunk_embedding],
                metadatas=[metadata]
            )
        
        # Store document
        self.documents[document.id] = document
        await self._save_documents()
        
        logger.info(f"Added document with {len(chunks)} chunks")
    
    async def search(self, query: str, n_results: int = 10, include_sources: List[str] = None) -> List[Dict[str, Any]]:
        """Search the knowledge base"""
        logger.info(f"Searching knowledge base: {query}")
        
        # Generate query embedding
        query_embedding = self.encoder.encode(query).tolist()
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        search_results = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            
            # Filter by source if specified
            if include_sources and metadata['source'] not in include_sources:
                continue
            
            result = {
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "distance": results['distances'][0][i],
                "doc_id": metadata['doc_id'],
                "title": metadata['title'],
                "authors": json.loads(metadata['authors']),
                "source": metadata['source'],
                "url": metadata['url'],
                "chunk_index": metadata['chunk_index'],
                "citations": metadata['citations']
            }
            search_results.append(result)
        
        return search_results
    
    async def get_enhanced_response(self, query: str, context_chunks: int = 5) -> Dict[str, Any]:
        """Get enhanced response with RAG context"""
        # Search for relevant documents
        search_results = await self.search(query, n_results=context_chunks)
        
        # Build context
        context = []
        sources = []
        
        for result in search_results:
            context.append(result['content'])
            source_info = {
                "title": result['title'],
                "authors": result['authors'],
                "source": result['source'],
                "url": result['url'],
                "citations": result['citations']
            }
            if source_info not in sources:
                sources.append(source_info)
        
        return {
            "query": query,
            "context": "\n\n".join(context),
            "sources": sources,
            "num_results": len(search_results)
        }
    
    async def research_topic(self, topic: str, search_online: bool = True) -> Dict[str, Any]:
        """Comprehensive research on a topic"""
        logger.info(f"Researching topic: {topic}")
        
        results = {
            "topic": topic,
            "documents_found": [],
            "total_sources": 0,
            "search_summary": ""
        }
        
        if search_online:
            # Search ArXiv
            arxiv_docs = await self.search_arxiv(topic)
            for doc in arxiv_docs:
                await self.add_document(doc)
            results["documents_found"].extend([doc.title for doc in arxiv_docs])
            
            # Search Google Scholar
            try:
                scholar_docs = await self.search_google_scholar(topic)
                for doc in scholar_docs:
                    await self.add_document(doc)
                results["documents_found"].extend([doc.title for doc in scholar_docs])
            except Exception as e:
                logger.warning(f"Scholar search failed: {e}")
        
        # Search existing knowledge base
        local_results = await self.search(topic, n_results=20)
        
        results["total_sources"] = len(self.documents)
        results["search_summary"] = f"Found {len(local_results)} relevant documents in knowledge base"
        
        return results
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        sources = {}
        total_citations = 0
        
        for doc in self.documents.values():
            if doc.source not in sources:
                sources[doc.source] = 0
            sources[doc.source] += 1
            total_citations += doc.citations
        
        return {
            "total_documents": len(self.documents),
            "sources": sources,
            "total_citations": total_citations,
            "avg_citations": total_citations / len(self.documents) if self.documents else 0,
            "collection_size": self.collection.count()
        }
    
    async def export_bibliography(self, format: str = "bibtex") -> str:
        """Export bibliography in various formats"""
        if format.lower() == "bibtex":
            bib = []
            for doc in self.documents.values():
                entry = f"""@article{{{doc.id},
    title = {{{doc.title}}},
    author = {{{" and ".join(doc.authors)}}},
    abstract = {{{doc.abstract}}},
    url = {{{doc.url or ""}}},
    year = {{{doc.publication_date or ""}}}
}}"""
                bib.append(entry)
            return "\n\n".join(bib)
        else:
            raise ValueError(f"Format {format} not supported")

# Global RAG instance
rag_system = AdvancedRAGSystem()

async def main():
    """Test the RAG system"""
    await rag_system.initialize()
    
    # Test search
    results = await rag_system.research_topic("academic research detection")
    print(json.dumps(results, indent=2))
    
    stats = await rag_system.get_document_stats()
    print("Knowledge base stats:", json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
