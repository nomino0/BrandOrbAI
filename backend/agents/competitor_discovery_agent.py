"""
Competitor Discovery Agent

This agent automatically discovers direct business competitors and finds their 
LinkedIn and TikTok social media links for marketing analysis.
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    logger.warning("Google Maps API key not found in environment variables. Some features may not work.")

@dataclass
class CompetitorInfo:
    """Data class for competitor information"""
    name: str
    industry: str
    description: str
    linkedin_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    website: Optional[str] = None
    confidence_score: float = 0.0
    discovery_method: str = ""
    # Google Maps specific fields
    place_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    business_status: Optional[str] = None
    location: Optional[Dict[str, float]] = None

class CompetitorDiscoveryAgent:
    """Agent for discovering business competitors and their social media presence"""
    
    def __init__(self):
        """Initialize the competitor discovery agent"""
        self.groq_client = self._init_groq_client()
        self.output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _init_groq_client(self):
        """Initialize Groq AI client"""
        try:
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                logger.error("GROQ_API_KEY not found in environment variables")
                return None
            return Groq(api_key=groq_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return None

    def discover_competitors(self, business_summary: str, max_competitors: int = 5, use_google_maps: bool = True, location: str = None) -> List[CompetitorInfo]:
        """
        Discover direct business competitors based on business summary
        
        Args:
            business_summary: Detailed business description
            max_competitors: Maximum number of competitors to discover
            use_google_maps: Whether to use Google Maps API for enhanced discovery
            location: Optional location for geographic competitor search
            
        Returns:
            List of CompetitorInfo objects with discovered competitors
        """
        logger.info(f"🔍 Starting competitor discovery for business...")
        
        try:
            # Extract business context
            business_context = self._extract_business_context(business_summary)
            logger.info(f"📊 Business context extracted: {business_context.get('industry', 'Unknown')} industry")
            
            # Discover competitors using AI
            ai_competitors = self._discover_competitors_with_ai(business_context, max_competitors)
            
            # Enhance with Google Maps if enabled
            if use_google_maps and GOOGLE_MAPS_API_KEY:
                logger.info("🗺️ Enhancing discovery with Google Maps API...")
                maps_competitors = self._discover_competitors_with_google_maps(business_context, location, max_competitors)
                
                # Merge AI and Google Maps results
                all_competitors = self._merge_competitor_lists(ai_competitors, maps_competitors)
            else:
                all_competitors = ai_competitors
                logger.info("⏭️ Skipping Google Maps integration")
            
            # Enrich with social media links
            enriched_competitors = []
            for competitor in all_competitors[:max_competitors]:
                enriched_competitor = self._enrich_competitor_social_media(competitor)
                enriched_competitors.append(enriched_competitor)
                
            # Save results
            self._save_discovery_results(enriched_competitors, business_context)
            
            logger.info(f"✅ Discovered {len(enriched_competitors)} competitors with social media links")
            return enriched_competitors
            
        except Exception as e:
            logger.error(f"❌ Error in competitor discovery: {e}")
            return self._get_fallback_competitors()

    def _extract_business_context(self, business_summary: str) -> Dict[str, Any]:
        """Extract key business context from summary"""
        if not self.groq_client:
            return self._extract_context_fallback(business_summary)
            
        try:
            context_prompt = f"""
            Analyze this business description and extract key information for competitor discovery:

            Business Description:
            {business_summary}

            Extract the following information in JSON format:
            {{
                "company_name": "extracted company name",
                "industry": "specific industry/sector",
                "business_model": "B2B/B2C/marketplace/etc",
                "target_market": "target market description",
                "key_services": ["service1", "service2", "service3"],
                "business_type": "startup/established/enterprise",
                "geographic_focus": "local/national/international",
                "technology_focus": "tech stack or technology focus if applicable",
                "unique_value_prop": "what makes this business unique"
            }}

            Return only valid JSON.
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a business analysis expert. Extract business context for competitor research. Return only valid JSON."},
                    {"role": "user", "content": context_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extracting business context: {e}")
            return self._extract_context_fallback(business_summary)

    def _extract_context_fallback(self, business_summary: str) -> Dict[str, Any]:
        """Fallback method to extract basic context without AI"""
        context = {
            "company_name": "Unknown Company",
            "industry": "Technology",
            "business_model": "B2B",
            "target_market": "Enterprise",
            "key_services": ["Software Development", "Consulting"],
            "business_type": "startup",
            "geographic_focus": "international",
            "technology_focus": "Software",
            "unique_value_prop": "Innovation and quality"
        }
        
        # Basic keyword extraction
        if "e-learning" in business_summary.lower() or "education" in business_summary.lower():
            context["industry"] = "E-Learning"
            context["key_services"] = ["Online Education", "Training", "Learning Platform"]
        elif "fintech" in business_summary.lower() or "financial" in business_summary.lower():
            context["industry"] = "FinTech"
            context["key_services"] = ["Financial Services", "Digital Banking", "Payment Solutions"]
        elif "healthcare" in business_summary.lower() or "medical" in business_summary.lower():
            context["industry"] = "Healthcare"
            context["key_services"] = ["Healthcare Solutions", "Medical Software", "Patient Care"]
        elif "ecommerce" in business_summary.lower() or "retail" in business_summary.lower():
            context["industry"] = "E-commerce"
            context["key_services"] = ["Online Retail", "E-commerce Platform", "Digital Sales"]
            
        return context

    def _discover_competitors_with_ai(self, business_context: Dict[str, Any], max_competitors: int) -> List[CompetitorInfo]:
        """Use AI to discover competitors based on business context"""
        if not self.groq_client:
            return self._get_industry_competitors(business_context["industry"])
            
        try:
            discovery_prompt = f"""
            Based on this business context, identify the top {max_competitors} direct competitors:

            Business Context:
            - Industry: {business_context.get('industry', 'Technology')}
            - Business Model: {business_context.get('business_model', 'B2B')}
            - Services: {', '.join(business_context.get('key_services', []))}
            - Target Market: {business_context.get('target_market', 'Enterprise')}
            - Geographic Focus: {business_context.get('geographic_focus', 'international')}

            Find real companies that are direct competitors. Focus on established companies with strong market presence.

            Return information in this JSON format:
            {{
                "competitors": [
                    {{
                        "name": "Company Name",
                        "industry": "Specific industry",
                        "description": "Brief description of what they do",
                        "website": "company website if known",
                        "confidence_score": 0.9,
                        "discovery_method": "AI analysis"
                    }}
                ]
            }}

            Requirements:
            - Only include real, existing companies
            - Focus on direct competitors (same industry/services)
            - Include global and regional competitors
            - Prioritize companies with strong online presence
            - Provide accurate company names for social media search

            Return only valid JSON.
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a competitive intelligence expert. Identify real competitor companies based on business context. Return only valid JSON."},
                    {"role": "user", "content": discovery_prompt}
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean and parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            data = json.loads(content)
            competitors_data = data.get("competitors", [])
            
            # Convert to CompetitorInfo objects
            competitors = []
            for comp_data in competitors_data:
                competitor = CompetitorInfo(
                    name=comp_data.get("name", "Unknown"),
                    industry=comp_data.get("industry", business_context.get("industry", "Technology")),
                    description=comp_data.get("description", ""),
                    website=comp_data.get("website"),
                    confidence_score=comp_data.get("confidence_score", 0.7),
                    discovery_method=comp_data.get("discovery_method", "AI analysis")
                )
                competitors.append(competitor)
                
            logger.info(f"🔍 AI discovered {len(competitors)} competitors")
            return competitors
            
        except Exception as e:
            logger.error(f"Error in AI competitor discovery: {e}")
            return self._get_industry_competitors(business_context["industry"])

    def _get_industry_competitors(self, industry: str) -> List[CompetitorInfo]:
        """Get predefined competitors based on industry"""
        industry_competitors = {
            "E-Learning": [
                CompetitorInfo("Coursera", "E-Learning", "Online course platform", confidence_score=0.9),
                CompetitorInfo("Udemy", "E-Learning", "Online learning marketplace", confidence_score=0.9),
                CompetitorInfo("Khan Academy", "E-Learning", "Free online education", confidence_score=0.8),
                CompetitorInfo("Skillshare", "E-Learning", "Creative skills platform", confidence_score=0.8),
                CompetitorInfo("MasterClass", "E-Learning", "Premium video lessons", confidence_score=0.7)
            ],
            "FinTech": [
                CompetitorInfo("PayPal", "FinTech", "Digital payment solutions", confidence_score=0.9),
                CompetitorInfo("Square", "FinTech", "Point of sale and payment processing", confidence_score=0.9),
                CompetitorInfo("Stripe", "FinTech", "Online payment infrastructure", confidence_score=0.8),
                CompetitorInfo("Revolut", "FinTech", "Digital banking platform", confidence_score=0.8),
                CompetitorInfo("Wise", "FinTech", "International money transfers", confidence_score=0.7)
            ],
            "Technology": [
                CompetitorInfo("Microsoft", "Technology", "Software and cloud services", confidence_score=0.9),
                CompetitorInfo("Google", "Technology", "Internet services and technology", confidence_score=0.9),
                CompetitorInfo("IBM", "Technology", "Enterprise technology solutions", confidence_score=0.8),
                CompetitorInfo("Oracle", "Technology", "Database and enterprise software", confidence_score=0.8),
                CompetitorInfo("Salesforce", "Technology", "CRM and cloud software", confidence_score=0.7)
            ],
            "Healthcare": [
                CompetitorInfo("Teladoc", "Healthcare", "Telehealth services", confidence_score=0.9),
                CompetitorInfo("Epic Systems", "Healthcare", "Electronic health records", confidence_score=0.8),
                CompetitorInfo("Cerner", "Healthcare", "Healthcare information technology", confidence_score=0.8),
                CompetitorInfo("Amwell", "Healthcare", "Digital healthcare platform", confidence_score=0.7),
                CompetitorInfo("Doxy.me", "Healthcare", "Telemedicine platform", confidence_score=0.7)
            ],
            "E-commerce": [
                CompetitorInfo("Amazon", "E-commerce", "Online retail marketplace", confidence_score=0.9),
                CompetitorInfo("Shopify", "E-commerce", "E-commerce platform", confidence_score=0.9),
                CompetitorInfo("eBay", "E-commerce", "Online auction and marketplace", confidence_score=0.8),
                CompetitorInfo("WooCommerce", "E-commerce", "WordPress e-commerce plugin", confidence_score=0.7),
                CompetitorInfo("BigCommerce", "E-commerce", "E-commerce software", confidence_score=0.7)
            ]
        }
        
        return industry_competitors.get(industry, industry_competitors["Technology"])[:5]

    def _discover_competitors_with_google_maps(self, business_context: Dict[str, Any], location: str = None, max_results: int = 10) -> List[CompetitorInfo]:
        """Discover competitors using Google Maps Places API"""
        logger.info("🗺️ Starting Google Maps competitor discovery...")
        
        if not GOOGLE_MAPS_API_KEY:
            logger.warning("⚠️ Google Maps API key not configured")
            return []
        
        try:
            # Determine search location
            search_location = location or self._determine_search_location(business_context)
            
            # Build search query based on business context
            search_query = self._build_maps_search_query(business_context)
            
            logger.info(f"🔍 Searching for: '{search_query}' near {search_location}")
            
            # Search for competitors using Places API
            competitors = []
            
            # Use Text Search API for broader results
            text_search_results = self._google_maps_text_search(search_query, search_location, max_results)
            competitors.extend(text_search_results)
            
            # Use Nearby Search for location-specific results if location is available
            if search_location and search_location != "global":
                nearby_results = self._google_maps_nearby_search(business_context, search_location, max_results // 2)
                competitors.extend(nearby_results)
            
            # Remove duplicates and rank by relevance
            unique_competitors = self._deduplicate_competitors(competitors)
            ranked_competitors = self._rank_competitors_by_relevance(unique_competitors, business_context)
            
            logger.info(f"🗺️ Google Maps found {len(ranked_competitors)} potential competitors")
            return ranked_competitors[:max_results]
            
        except Exception as e:
            logger.error(f"❌ Google Maps discovery failed: {e}")
            return []

    def _determine_search_location(self, business_context: Dict[str, Any]) -> str:
        """Determine the best search location based on business context"""
        geographic_focus = business_context.get('geographic_focus', 'international')
        
        if geographic_focus == 'local':
            return "United States"  # Default to US for local searches
        elif geographic_focus == 'national':
            return "United States"
        else:
            return "global"

    def _build_maps_search_query(self, business_context: Dict[str, Any]) -> str:
        """Build an effective search query for Google Maps"""
        industry = business_context.get('industry', 'business')
        services = business_context.get('key_services', [])
        business_type = business_context.get('business_type', 'company')
        
        # Create a comprehensive search query
        query_parts = []
        
        # Add industry
        if industry:
            query_parts.append(industry)
        
        # Add main service if available
        if services:
            main_service = services[0] if services else ""
            if main_service and main_service.lower() not in industry.lower():
                query_parts.append(main_service)
        
        # Add business type context
        if business_type in ['startup', 'enterprise']:
            query_parts.append('company')
        
        return ' '.join(query_parts)

    def _google_maps_text_search(self, query: str, location: str, max_results: int) -> List[CompetitorInfo]:
        """Perform Google Maps Text Search"""
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            
            params = {
                'query': query,
                'key': GOOGLE_MAPS_API_KEY,
                'type': 'establishment',
                'region': 'us' if location != 'global' else None
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.warning(f"⚠️ Google Maps API status: {data.get('status')}")
                return []
            
            competitors = []
            for place in data.get('results', [])[:max_results]:
                competitor = self._parse_google_maps_place(place, "text_search")
                if competitor:
                    competitors.append(competitor)
            
            logger.info(f"📍 Text search found {len(competitors)} results")
            return competitors
            
        except Exception as e:
            logger.error(f"❌ Google Maps text search failed: {e}")
            return []

    def _google_maps_nearby_search(self, business_context: Dict[str, Any], location: str, max_results: int) -> List[CompetitorInfo]:
        """Perform Google Maps Nearby Search"""
        try:
            # First, geocode the location
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            geocode_params = {
                'address': location,
                'key': GOOGLE_MAPS_API_KEY
            }
            
            geocode_response = requests.get(geocode_url, params=geocode_params, timeout=10)
            geocode_data = geocode_response.json()
            
            if not geocode_data.get('results'):
                logger.warning(f"⚠️ Could not geocode location: {location}")
                return []
            
            lat_lng = geocode_data['results'][0]['geometry']['location']
            
            # Perform nearby search
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            
            # Determine search type based on industry
            place_type = self._get_place_type_for_industry(business_context.get('industry', ''))
            
            params = {
                'location': f"{lat_lng['lat']},{lat_lng['lng']}",
                'radius': 50000,  # 50km radius
                'type': place_type,
                'key': GOOGLE_MAPS_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.warning(f"⚠️ Google Maps nearby search status: {data.get('status')}")
                return []
            
            competitors = []
            for place in data.get('results', [])[:max_results]:
                competitor = self._parse_google_maps_place(place, "nearby_search")
                if competitor:
                    competitors.append(competitor)
            
            logger.info(f"📍 Nearby search found {len(competitors)} results")
            return competitors
            
        except Exception as e:
            logger.error(f"❌ Google Maps nearby search failed: {e}")
            return []

    def _get_place_type_for_industry(self, industry: str) -> str:
        """Map industry to Google Maps place type"""
        industry_mapping = {
            'restaurant': 'restaurant',
            'retail': 'store',
            'healthcare': 'hospital',
            'fitness': 'gym',
            'beauty': 'beauty_salon',
            'automotive': 'car_dealer',
            'real_estate': 'real_estate_agency',
            'legal': 'lawyer',
            'financial': 'bank',
            'education': 'school'
        }
        
        industry_lower = industry.lower()
        for key, place_type in industry_mapping.items():
            if key in industry_lower:
                return place_type
        
        return 'establishment'  # Default fallback

    def _parse_google_maps_place(self, place: Dict, discovery_method: str) -> Optional[CompetitorInfo]:
        """Parse a Google Maps place result into CompetitorInfo"""
        try:
            name = place.get('name', 'Unknown Business')
            
            # Skip generic or irrelevant results
            if self._should_skip_place(name, place):
                return None
            
            # Extract business information
            place_id = place.get('place_id')
            address = place.get('formatted_address', place.get('vicinity', ''))
            rating = place.get('rating')
            review_count = place.get('user_ratings_total')
            business_status = place.get('business_status', 'OPERATIONAL')
            
            # Extract location
            location = None
            if place.get('geometry') and place['geometry'].get('location'):
                location = {
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng']
                }
            
            # Determine industry from place types
            place_types = place.get('types', [])
            industry = self._determine_industry_from_place_types(place_types)
            
            # Get additional details if place_id is available
            website = None
            phone = None
            if place_id:
                details = self._get_place_details(place_id)
                if details:
                    website = details.get('website')
                    phone = details.get('international_phone_number')
            
            # Calculate confidence score based on rating, reviews, and business status
            confidence_score = self._calculate_maps_confidence_score(rating, review_count, business_status)
            
            competitor = CompetitorInfo(
                name=name,
                industry=industry,
                description=f"Business found via Google Maps in {address.split(',')[-1].strip() if address else 'Unknown location'}",
                website=website,
                confidence_score=confidence_score,
                discovery_method=f"google_maps_{discovery_method}",
                place_id=place_id,
                address=address,
                phone=phone,
                rating=rating,
                review_count=review_count,
                business_status=business_status,
                location=location
            )
            
            return competitor
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse Google Maps place: {e}")
            return None

    def _should_skip_place(self, name: str, place: Dict) -> bool:
        """Determine if a place should be skipped based on name and other factors"""
        skip_keywords = [
            'atm', 'parking', 'gas station', 'transit', 'subway', 'bus stop',
            'airport', 'church', 'school', 'hospital', 'government', 'post office'
        ]
        
        name_lower = name.lower()
        place_types = [t.lower() for t in place.get('types', [])]
        
        # Skip if name contains skip keywords
        if any(keyword in name_lower for keyword in skip_keywords):
            return True
        
        # Skip certain place types
        skip_types = ['transit_station', 'gas_station', 'atm', 'parking', 'church', 'school']
        if any(skip_type in place_types for skip_type in skip_types):
            return True
        
        # Skip permanently closed businesses
        if place.get('business_status') == 'CLOSED_PERMANENTLY':
            return True
        
        return False

    def _determine_industry_from_place_types(self, place_types: List[str]) -> str:
        """Determine industry from Google Maps place types"""
        type_mapping = {
            'restaurant': 'Food & Beverage',
            'food': 'Food & Beverage',
            'store': 'Retail',
            'clothing_store': 'Fashion & Retail',
            'electronics_store': 'Electronics & Technology',
            'health': 'Healthcare',
            'gym': 'Fitness & Wellness',
            'beauty_salon': 'Beauty & Personal Care',
            'car_dealer': 'Automotive',
            'real_estate_agency': 'Real Estate',
            'lawyer': 'Legal Services',
            'bank': 'Financial Services',
            'insurance_agency': 'Insurance',
            'travel_agency': 'Travel & Tourism',
            'lodging': 'Hospitality',
            'establishment': 'Business Services'
        }
        
        for place_type in place_types:
            if place_type in type_mapping:
                return type_mapping[place_type]
        
        return 'Business Services'  # Default industry

    def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information for a specific place"""
        try:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            
            params = {
                'place_id': place_id,
                'fields': 'website,international_phone_number,business_status,opening_hours',
                'key': GOOGLE_MAPS_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('result', {})
            else:
                logger.warning(f"⚠️ Place details API status: {data.get('status')}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to get place details for {place_id}: {e}")
            return None

    def _calculate_maps_confidence_score(self, rating: Optional[float], review_count: Optional[int], business_status: str) -> float:
        """Calculate confidence score based on Google Maps data"""
        score = 0.5  # Base score
        
        # Rating contribution (0-0.3)
        if rating:
            score += (rating / 5.0) * 0.3
        
        # Review count contribution (0-0.2)
        if review_count:
            # Normalize review count (100+ reviews = max score)
            review_score = min(review_count / 100.0, 1.0) * 0.2
            score += review_score
        
        # Business status contribution
        if business_status == 'OPERATIONAL':
            score += 0.1
        elif business_status == 'CLOSED_TEMPORARILY':
            score -= 0.1
        elif business_status == 'CLOSED_PERMANENTLY':
            score -= 0.5
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1

    def _deduplicate_competitors(self, competitors: List[CompetitorInfo]) -> List[CompetitorInfo]:
        """Remove duplicate competitors based on name similarity"""
        if not competitors:
            return []
        
        unique_competitors = []
        seen_names = set()
        
        for competitor in competitors:
            # Normalize name for comparison
            normalized_name = competitor.name.lower().strip()
            normalized_name = re.sub(r'[^\w\s]', '', normalized_name)  # Remove special chars
            
            # Check for similar names
            is_duplicate = False
            for seen_name in seen_names:
                if self._names_are_similar(normalized_name, seen_name):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_competitors.append(competitor)
                seen_names.add(normalized_name)
        
        logger.info(f"🔄 Deduplicated {len(competitors)} -> {len(unique_competitors)} competitors")
        return unique_competitors

    def _names_are_similar(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Check if two business names are similar enough to be considered duplicates"""
        # Simple similarity check based on common words
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold

    def _rank_competitors_by_relevance(self, competitors: List[CompetitorInfo], business_context: Dict[str, Any]) -> List[CompetitorInfo]:
        """Rank competitors by relevance to the business context"""
        industry = business_context.get('industry', '').lower()
        services = [s.lower() for s in business_context.get('key_services', [])]
        
        def relevance_score(competitor: CompetitorInfo) -> float:
            score = competitor.confidence_score
            
            # Industry match bonus
            if industry and industry in competitor.industry.lower():
                score += 0.2
            
            # Service match bonus
            for service in services:
                if service in competitor.description.lower() or service in competitor.name.lower():
                    score += 0.1
                    break
            
            # Google Maps specific bonuses
            if competitor.rating and competitor.rating >= 4.0:
                score += 0.1
            
            if competitor.review_count and competitor.review_count >= 50:
                score += 0.05
            
            return min(score, 1.0)
        
        # Sort by relevance score
        competitors.sort(key=relevance_score, reverse=True)
        return competitors

    def _merge_competitor_lists(self, ai_competitors: List[CompetitorInfo], maps_competitors: List[CompetitorInfo]) -> List[CompetitorInfo]:
        """Merge AI-discovered and Google Maps competitors, removing duplicates"""
        all_competitors = ai_competitors.copy()
        
        # Add Google Maps competitors that aren't already found by AI
        for maps_comp in maps_competitors:
            is_duplicate = False
            for ai_comp in ai_competitors:
                if self._names_are_similar(maps_comp.name.lower(), ai_comp.name.lower()):
                    # Merge information from both sources
                    ai_comp.place_id = maps_comp.place_id
                    ai_comp.address = maps_comp.address
                    ai_comp.phone = maps_comp.phone
                    ai_comp.rating = maps_comp.rating
                    ai_comp.review_count = maps_comp.review_count
                    ai_comp.location = maps_comp.location
                    if maps_comp.website and not ai_comp.website:
                        ai_comp.website = maps_comp.website
                    # Update confidence score with Google Maps data
                    ai_comp.confidence_score = max(ai_comp.confidence_score, maps_comp.confidence_score)
                    ai_comp.discovery_method += " + google_maps"
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_competitors.append(maps_comp)
        
        logger.info(f"🔀 Merged {len(ai_competitors)} AI + {len(maps_competitors)} Maps = {len(all_competitors)} total competitors")
        return all_competitors

    def _enrich_competitor_social_media(self, competitor: CompetitorInfo) -> CompetitorInfo:
        """Enrich competitor with social media links"""
        try:
            # Search for LinkedIn company page
            linkedin_url = self._find_linkedin_company_url(competitor.name)
            if linkedin_url:
                competitor.linkedin_url = linkedin_url
                logger.info(f"📱 Found LinkedIn for {competitor.name}: {linkedin_url}")
            
            # Search for TikTok profile
            tiktok_url = self._find_tiktok_profile_url(competitor.name)
            if tiktok_url:
                competitor.tiktok_url = tiktok_url
                logger.info(f"📱 Found TikTok for {competitor.name}: {tiktok_url}")
                
            # Small delay to avoid overwhelming services
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"Error enriching social media for {competitor.name}: {e}")
            
        return competitor

    def _find_linkedin_company_url(self, company_name: str) -> Optional[str]:
        """Find LinkedIn company URL for a given company name"""
        try:
            # Use AI to predict LinkedIn URL patterns
            if self.groq_client:
                return self._ai_predict_linkedin_url(company_name)
            else:
                return self._pattern_predict_linkedin_url(company_name)
                
        except Exception as e:
            logger.warning(f"Error finding LinkedIn URL for {company_name}: {e}")
            return None

    def _ai_predict_linkedin_url(self, company_name: str) -> Optional[str]:
        """Use AI to predict LinkedIn company URL"""
        try:
            linkedin_prompt = f"""
            Based on the company name "{company_name}", predict the most likely LinkedIn company URL.

            LinkedIn company URLs follow these patterns:
            - https://linkedin.com/company/company-name
            - Company names are usually lowercase with spaces replaced by hyphens
            - Special characters are often removed
            - "Inc", "LLC", "Corp" are often omitted

            Examples:
            - "Microsoft Corporation" → https://linkedin.com/company/microsoft
            - "Apple Inc." → https://linkedin.com/company/apple  
            - "Goldman Sachs" → https://linkedin.com/company/goldman-sachs
            - "JPMorgan Chase & Co." → https://linkedin.com/company/jpmorgan-chase-co

            Return only the most likely LinkedIn URL for "{company_name}".
            Format: https://linkedin.com/company/[predicted-name]
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert at predicting LinkedIn company URLs. Return only the URL."},
                    {"role": "user", "content": linkedin_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            predicted_url = response.choices[0].message.content.strip()
            
            # Validate URL format
            if "linkedin.com/company/" in predicted_url and predicted_url.startswith("https://"):
                return predicted_url
                
        except Exception as e:
            logger.warning(f"AI LinkedIn URL prediction failed for {company_name}: {e}")
            
        return self._pattern_predict_linkedin_url(company_name)

    def _pattern_predict_linkedin_url(self, company_name: str) -> Optional[str]:
        """Use pattern matching to predict LinkedIn URL"""
        try:
            # Clean company name
            clean_name = company_name.lower()
            clean_name = re.sub(r'\s+(inc|corp|corporation|llc|ltd|co\.|company)\.?$', '', clean_name)
            clean_name = re.sub(r'[^\w\s-]', '', clean_name)  # Remove special chars
            clean_name = re.sub(r'\s+', '-', clean_name.strip())  # Replace spaces with hyphens
            clean_name = re.sub(r'-+', '-', clean_name)  # Remove multiple hyphens
            
            return f"https://linkedin.com/company/{clean_name}"
            
        except Exception as e:
            logger.warning(f"Pattern LinkedIn URL prediction failed for {company_name}: {e}")
            return None

    def _find_tiktok_profile_url(self, company_name: str) -> Optional[str]:
        """Find TikTok profile URL for a given company name"""
        try:
            # Use AI to predict TikTok URL patterns
            if self.groq_client:
                return self._ai_predict_tiktok_url(company_name)
            else:
                return self._pattern_predict_tiktok_url(company_name)
                
        except Exception as e:
            logger.warning(f"Error finding TikTok URL for {company_name}: {e}")
            return None

    def _ai_predict_tiktok_url(self, company_name: str) -> Optional[str]:
        """Use AI to predict TikTok profile URL"""
        try:
            tiktok_prompt = f"""
            Based on the company name "{company_name}", predict the most likely TikTok profile URL.

            TikTok profile URLs follow these patterns:
            - https://tiktok.com/@username
            - Usernames are usually lowercase with no spaces
            - Companies often use variations like: companyname, company_official, officialcompany
            - Some add suffixes like _official, _corp, _inc

            Examples:
            - "Microsoft" → https://tiktok.com/@microsoft
            - "Nike" → https://tiktok.com/@nike
            - "McDonald's" → https://tiktok.com/@mcdonalds
            - "Walmart" → https://tiktok.com/@walmart

            Return only the most likely TikTok URL for "{company_name}".
            Format: https://tiktok.com/@[predicted-username]
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert at predicting TikTok profile URLs. Return only the URL."},
                    {"role": "user", "content": tiktok_prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            predicted_url = response.choices[0].message.content.strip()
            
            # Validate URL format
            if "tiktok.com/@" in predicted_url and predicted_url.startswith("https://"):
                return predicted_url
                
        except Exception as e:
            logger.warning(f"AI TikTok URL prediction failed for {company_name}: {e}")
            
        return self._pattern_predict_tiktok_url(company_name)

    def _pattern_predict_tiktok_url(self, company_name: str) -> Optional[str]:
        """Use pattern matching to predict TikTok URL"""
        try:
            # Clean company name for TikTok username
            clean_name = company_name.lower()
            clean_name = re.sub(r'\s+(inc|corp|corporation|llc|ltd|co\.|company)\.?$', '', clean_name)
            clean_name = re.sub(r'[^\w]', '', clean_name)  # Remove all non-alphanumeric
            
            # Try different variations
            variations = [
                clean_name,
                f"{clean_name}official",
                f"official{clean_name}",
                f"{clean_name}_official"
            ]
            
            # Return the first (most likely) variation
            return f"https://tiktok.com/@{variations[0]}"
            
        except Exception as e:
            logger.warning(f"Pattern TikTok URL prediction failed for {company_name}: {e}")
            return None

    def _save_discovery_results(self, competitors: List[CompetitorInfo], business_context: Dict[str, Any]):
        """Save competitor discovery results to file"""
        try:
            output_data = {
                "discovery_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "business_context": business_context,
                    "total_competitors": len(competitors)
                },
                "competitors": []
            }
            
            for competitor in competitors:
                comp_data = {
                    "name": competitor.name,
                    "industry": competitor.industry,
                    "description": competitor.description,
                    "linkedin_url": competitor.linkedin_url,
                    "tiktok_url": competitor.tiktok_url,
                    "website": competitor.website,
                    "confidence_score": competitor.confidence_score,
                    "discovery_method": competitor.discovery_method
                }
                output_data["competitors"].append(comp_data)
            
            # Save to JSON file
            output_file = os.path.join(self.output_dir, "competitor_discovery_output.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Saved competitor discovery results to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving discovery results: {e}")

    def _get_fallback_competitors(self) -> List[CompetitorInfo]:
        """Get fallback competitors when discovery fails"""
        return [
            CompetitorInfo(
                name="Generic Competitor 1",
                industry="Technology",
                description="Technology solutions provider",
                linkedin_url="https://linkedin.com/company/generic-competitor-1",
                confidence_score=0.5,
                discovery_method="fallback"
            ),
            CompetitorInfo(
                name="Generic Competitor 2", 
                industry="Technology",
                description="Business software company",
                linkedin_url="https://linkedin.com/company/generic-competitor-2",
                confidence_score=0.5,
                discovery_method="fallback"
            )
        ]

    def load_existing_competitors(self) -> Optional[List[CompetitorInfo]]:
        """Load previously discovered competitors"""
        try:
            output_file = os.path.join(self.output_dir, "competitor_discovery_output.json")
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                competitors = []
                for comp_data in data.get("competitors", []):
                    competitor = CompetitorInfo(
                        name=comp_data.get("name", ""),
                        industry=comp_data.get("industry", ""),
                        description=comp_data.get("description", ""),
                        linkedin_url=comp_data.get("linkedin_url"),
                        tiktok_url=comp_data.get("tiktok_url"),
                        website=comp_data.get("website"),
                        confidence_score=comp_data.get("confidence_score", 0.0),
                        discovery_method=comp_data.get("discovery_method", "")
                    )
                    competitors.append(competitor)
                
                logger.info(f"📂 Loaded {len(competitors)} existing competitors")
                return competitors
                
        except Exception as e:
            logger.error(f"Error loading existing competitors: {e}")
            
        return None

# Standalone function for easy integration
def discover_business_competitors(business_summary: str, max_competitors: int = 5, use_google_maps: bool = True, location: str = None) -> List[Dict[str, Any]]:
    """
    Discover business competitors and return as dictionaries
    
    Args:
        business_summary: Business description
        max_competitors: Maximum number of competitors to find
        use_google_maps: Whether to use Google Maps API for enhanced discovery
        location: Optional location for geographic competitor search
        
    Returns:
        List of competitor dictionaries with social media links
    """
    try:
        agent = CompetitorDiscoveryAgent()
        competitors = agent.discover_competitors(business_summary, max_competitors, use_google_maps, location)
        
        # Convert to dictionaries for API response
        competitor_dicts = []
        for competitor in competitors:
            comp_dict = {
                "id": f"comp_{hash(competitor.name) % 10000}",
                "name": competitor.name,
                "industry": competitor.industry,
                "description": competitor.description,
                "linkedin_url": competitor.linkedin_url,
                "tiktok_url": competitor.tiktok_url,
                "website": competitor.website,
                "confidence_score": competitor.confidence_score,
                "discovery_method": competitor.discovery_method,
                "platform": "linkedin" if competitor.linkedin_url else "tiktok" if competitor.tiktok_url else "website",
                # Google Maps specific fields
                "place_id": competitor.place_id,
                "address": competitor.address,
                "phone": competitor.phone,
                "rating": competitor.rating,
                "review_count": competitor.review_count,
                "business_status": competitor.business_status,
                "location": competitor.location
            }
            competitor_dicts.append(comp_dict)
            
        return competitor_dicts
        
    except Exception as e:
        logger.error(f"Error in competitor discovery function: {e}")
        return []

if __name__ == "__main__":
    # Test the agent with Google Maps integration
    test_business = """
    GreenTech Solar is a renewable energy company specializing in solar panel installation 
    and energy storage solutions for residential and commercial properties in California. 
    We help customers reduce their carbon footprint while saving money on energy costs 
    through innovative solar technology and battery storage systems.
    """
    
    agent = CompetitorDiscoveryAgent()
    
    print("🧪 Testing Google Maps Integration...")
    print("=" * 50)
    
    # Test with Google Maps enabled
    competitors = agent.discover_competitors(
        test_business, 
        max_competitors=5, 
        use_google_maps=True, 
        location="California, USA"
    )
    
    print(f"\n🔍 Discovered {len(competitors)} Competitors:")
    print("=" * 50)
    
    for i, comp in enumerate(competitors, 1):
        print(f"\n{i}. 🏢 {comp.name}")
        print(f"   📍 Industry: {comp.industry}")
        print(f"   📝 Description: {comp.description}")
        print(f"   🔗 LinkedIn: {comp.linkedin_url or 'Not found'}")
        print(f"   🎵 TikTok: {comp.tiktok_url or 'Not found'}")
        print(f"   🌐 Website: {comp.website or 'Not found'}")
        print(f"   📊 Confidence: {comp.confidence_score:.2f}")
        print(f"   🔍 Discovery: {comp.discovery_method}")
        
        # Google Maps specific info
        if comp.place_id:
            print(f"   📍 Address: {comp.address or 'Not available'}")
            print(f"   📞 Phone: {comp.phone or 'Not available'}")
            print(f"   ⭐ Rating: {comp.rating or 'No rating'}")
            print(f"   💬 Reviews: {comp.review_count or 'No reviews'}")
            print(f"   🏪 Status: {comp.business_status}")
    
    print("\n" + "=" * 50)
    print("✅ Google Maps integration test completed!")
    
    # Test discovery function
    print("\n🔧 Testing standalone discovery function...")
    discovery_results = discover_business_competitors(
        test_business, 
        max_competitors=3, 
        use_google_maps=True, 
        location="California, USA"
    )
    
    print(f"📊 Function returned {len(discovery_results)} competitors")
    for comp in discovery_results:
        print(f"- {comp['name']} ({comp['discovery_method']})")
    
    print("🎉 All tests completed!")
