from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio
import feedparser
import requests
from urllib.parse import urljoin
import json
import csv
from io import StringIO
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat
emergent_key = os.environ.get('EMERGENT_LLM_KEY')
if not emergent_key:
    logging.warning("EMERGENT_LLM_KEY not found in environment variables")

# Models
class ContentItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    summary: str = ""
    source: str
    source_url: str = ""
    published_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # AI Analysis Scores
    knowledge_density_score: float = 0.0  # 0-10 scale
    credibility_score: float = 0.0        # 0-10 scale
    distraction_score: float = 0.0        # 0-10 scale (higher = more distracting)
    cognitive_utility_score: float = 0.0  # Final score = knowledge + credibility - distraction
    
    # Metadata
    content_type: str = "article"  # article, transcript, manual
    tags: List[str] = []
    evidence_links: List[str] = []
    
    # User Interaction
    expand_count: int = 0
    helpful_votes: int = 0
    unhelpful_votes: int = 0
    flagged_count: int = 0

class RSSSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    enabled: bool = True
    last_fetched: Optional[datetime] = None
    reputation_score: float = 5.0  # 0-10 scale
    fetch_frequency: int = 15  # minutes

class UserFeedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    action: str  # expand, helpful, unhelpful, flag
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class ManualUpload(BaseModel):
    title: str
    content: str
    source: str = "Manual Upload"

class ContentAnalysisRequest(BaseModel):
    title: str
    content: str
    source: str

# RSS Feed Processing
async def fetch_rss_feed(source: RSSSource) -> List[Dict[str, Any]]:
    """Fetch and parse RSS feed"""
    try:
        response = requests.get(source.url, timeout=10)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        articles = []
        
        for entry in feed.entries[:10]:  # Limit to 10 most recent
            # Extract content
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else entry.content.value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Clean HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            
            # Extract publication date
            pub_date = datetime.now(timezone.utc)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            
            articles.append({
                'title': entry.title if hasattr(entry, 'title') else 'No Title',
                'content': content,
                'source': source.name,
                'source_url': entry.link if hasattr(entry, 'link') else source.url,
                'published_date': pub_date
            })
            
        return articles
    
    except Exception as e:
        logging.error(f"Error fetching RSS feed {source.name}: {str(e)}")
        return []

async def analyze_content_with_ai(title: str, content: str, source: str) -> Dict[str, Any]:
    """Analyze content using LLM for cognitive utility scoring"""
    if not emergent_key:
        # Return default scores if no AI key
        return {
            'knowledge_density_score': 5.0,
            'credibility_score': 5.0,
            'distraction_score': 5.0,
            'summary': title,
            'tags': [],
            'evidence_links': []
        }
    
    try:
        # Initialize LLM Chat for content analysis
        analyzer = LlmChat(
            api_key=emergent_key,
            session_id=f"analysis-{uuid.uuid4()}",
            system_message="""You are an expert content analyst. Analyze content for knowledge value, credibility, and potential for distraction.

Provide scores (0-10) and analysis in this exact JSON format:
{
    "knowledge_density_score": 7.5,
    "credibility_score": 8.0,
    "distraction_score": 3.0,
    "summary": "Brief 1-2 sentence summary focusing on key insights",
    "tags": ["tag1", "tag2", "tag3"],
    "evidence_links": ["url1", "url2"]
}

Scoring Guide:
- Knowledge Density: How much useful information per word? Technical depth? Novel insights?
- Credibility: Source reliability? Factual accuracy? Evidence provided?
- Distraction: Clickbait? Emotional manipulation? Sensationalism? (higher = more distracting)"""
        ).with_model("openai", "gpt-4o-mini")
        
        analysis_prompt = f"""
Analyze this content:

Title: {title}
Source: {source}
Content: {content[:2000]}...

Provide detailed scoring and analysis."""

        response = await analyzer.send_message(UserMessage(text=analysis_prompt))
        
        # Parse JSON response
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback to extract scores from text response
            knowledge_score = extract_score_from_text(response, "knowledge_density_score")
            credibility_score = extract_score_from_text(response, "credibility_score")
            distraction_score = extract_score_from_text(response, "distraction_score")
            
            return {
                'knowledge_density_score': knowledge_score or 5.0,
                'credibility_score': credibility_score or 5.0,
                'distraction_score': distraction_score or 5.0,
                'summary': title,
                'tags': [],
                'evidence_links': []
            }
            
    except Exception as e:
        logging.error(f"AI analysis error: {str(e)}")
        return {
            'knowledge_density_score': 5.0,
            'credibility_score': 5.0,
            'distraction_score': 5.0,
            'summary': title,
            'tags': [],
            'evidence_links': []
        }

def extract_score_from_text(text: str, score_name: str) -> Optional[float]:
    """Extract numeric score from text response"""
    pattern = rf'{score_name}["\']?\s*:\s*([0-9.]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None

def calculate_cognitive_utility(knowledge: float, credibility: float, distraction: float) -> float:
    """Calculate final cognitive utility score"""
    return max(0, knowledge + credibility - distraction)

# API Routes

@api_router.get("/")
async def root():
    return {"message": "Knowledge Aggregator API"}

@api_router.get("/content", response_model=List[ContentItem])
async def get_content(
    limit: int = 50,
    min_score: float = 0.0,
    serendipity: bool = False,
    diversity: bool = False
):
    """Get content feed with cognitive utility ranking"""
    try:
        # Build query
        query = {"cognitive_utility_score": {"$gte": min_score}}
        
        # Get content from database
        cursor = db.content.find(query)
        
        if serendipity:
            # Add some randomness for discovery
            cursor = cursor.limit(limit * 2)
            content_list = await cursor.to_list(length=None)
            # Randomly sample from top content
            import random
            if len(content_list) > limit:
                # Keep top 50% by score, randomly sample the rest
                sorted_content = sorted(content_list, key=lambda x: x['cognitive_utility_score'], reverse=True)
                top_half = sorted_content[:len(sorted_content)//2]
                bottom_half = sorted_content[len(sorted_content)//2:]
                random.shuffle(bottom_half)
                content_list = top_half + bottom_half[:limit - len(top_half)]
            else:
                content_list = content_list[:limit]
        else:
            # Standard sorting by cognitive utility score
            cursor = cursor.sort("cognitive_utility_score", -1).limit(limit)
            content_list = await cursor.to_list(length=None)
        
        return [ContentItem(**item) for item in content_list]
        
    except Exception as e:
        logging.error(f"Error fetching content: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching content")

@api_router.post("/content/analyze", response_model=Dict[str, Any])
async def analyze_content(request: ContentAnalysisRequest):
    """Analyze content with AI scoring"""
    try:
        analysis = await analyze_content_with_ai(request.title, request.content, request.source)
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing content: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing content")

@api_router.post("/content/manual")
async def upload_manual_content(upload: ManualUpload):
    """Upload content manually"""
    try:
        # Analyze the content
        analysis = await analyze_content_with_ai(upload.title, upload.content, upload.source)
        
        # Create content item
        content_item = ContentItem(
            title=upload.title,
            content=upload.content,
            source=upload.source,
            content_type="manual",
            **analysis
        )
        
        # Calculate cognitive utility
        content_item.cognitive_utility_score = calculate_cognitive_utility(
            content_item.knowledge_density_score,
            content_item.credibility_score,
            content_item.distraction_score
        )
        
        # Save to database
        await db.content.insert_one(content_item.dict())
        
        return {"status": "success", "content_id": content_item.id}
        
    except Exception as e:
        logging.error(f"Error uploading manual content: {str(e)}")
        raise HTTPException(status_code=500, detail="Error uploading content")

@api_router.post("/rss-sources")
async def add_rss_source(source: RSSSource):
    """Add new RSS source"""
    try:
        await db.rss_sources.insert_one(source.dict())
        return {"status": "success", "source_id": source.id}
    except Exception as e:
        logging.error(f"Error adding RSS source: {str(e)}")
        raise HTTPException(status_code=500, detail="Error adding RSS source")

@api_router.get("/rss-sources", response_model=List[RSSSource])
async def get_rss_sources():
    """Get all RSS sources"""
    try:
        sources = await db.rss_sources.find().to_list(length=None)
        return [RSSSource(**source) for source in sources]
    except Exception as e:
        logging.error(f"Error fetching RSS sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching RSS sources")

@api_router.post("/rss-sources/{source_id}/fetch")
async def fetch_rss_source(source_id: str):
    """Manually fetch content from specific RSS source"""
    try:
        # Get the source
        source_doc = await db.rss_sources.find_one({"id": source_id})
        if not source_doc:
            raise HTTPException(status_code=404, detail="RSS source not found")
        
        source = RSSSource(**source_doc)
        
        # Fetch articles
        articles = await fetch_rss_feed(source)
        
        # Process each article
        processed_count = 0
        for article_data in articles:
            # Check if already exists
            existing = await db.content.find_one({
                "title": article_data['title'],
                "source": article_data['source']
            })
            
            if existing:
                continue
                
            # Analyze with AI
            analysis = await analyze_content_with_ai(
                article_data['title'],
                article_data['content'],
                article_data['source']
            )
            
            # Create content item
            content_item = ContentItem(**article_data, **analysis)
            content_item.cognitive_utility_score = calculate_cognitive_utility(
                content_item.knowledge_density_score,
                content_item.credibility_score,
                content_item.distraction_score
            )
            
            # Save to database
            await db.content.insert_one(content_item.dict())
            processed_count += 1
        
        # Update last fetched time
        await db.rss_sources.update_one(
            {"id": source_id},
            {"$set": {"last_fetched": datetime.now(timezone.utc)}}
        )
        
        return {"status": "success", "processed_count": processed_count}
        
    except Exception as e:
        logging.error(f"Error fetching RSS source: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching RSS source")

@api_router.post("/feedback")
async def log_feedback(feedback: UserFeedback):
    """Log user feedback for content"""
    try:
        await db.user_feedback.insert_one(feedback.dict())
        
        # Update content item counters
        update_data = {}
        if feedback.action == "expand":
            update_data["$inc"] = {"expand_count": 1}
        elif feedback.action == "helpful":
            update_data["$inc"] = {"helpful_votes": 1}
        elif feedback.action == "unhelpful":
            update_data["$inc"] = {"unhelpful_votes": 1}
        elif feedback.action == "flag":
            update_data["$inc"] = {"flagged_count": 1}
            
        if update_data:
            await db.content.update_one({"id": feedback.content_id}, update_data)
        
        return {"status": "success"}
        
    except Exception as e:
        logging.error(f"Error logging feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Error logging feedback")

# Default RSS sources
DEFAULT_RSS_SOURCES = [
    {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/rss.xml", "reputation_score": 8.5},
    {"name": "Reuters", "url": "http://feeds.reuters.com/reuters/topNews", "reputation_score": 8.0},
    {"name": "NPR", "url": "https://feeds.npr.org/1001/rss.xml", "reputation_score": 8.0},
    {"name": "The Guardian", "url": "https://www.theguardian.com/international/rss", "reputation_score": 7.5},
    {"name": "Associated Press", "url": "https://feeds.apnews.com/apnews/topnews", "reputation_score": 8.0},
]

@api_router.post("/setup/default-sources")
async def setup_default_sources():
    """Set up default RSS sources"""
    try:
        for source_data in DEFAULT_RSS_SOURCES:
            # Check if already exists
            existing = await db.rss_sources.find_one({"url": source_data["url"]})
            if not existing:
                source = RSSSource(**source_data)
                await db.rss_sources.insert_one(source.dict())
        
        return {"status": "success", "message": "Default sources added"}
    except Exception as e:
        logging.error(f"Error setting up default sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Error setting up default sources")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()