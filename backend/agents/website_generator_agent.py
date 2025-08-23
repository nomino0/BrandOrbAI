"""
AI Website Generator Agent
Generates professional landing pages and websites based on business data
"""

import os
import re
import json
import time
import glob
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# AI imports
try:
    from groq import Groq
except ImportError:
    Groq = None
    print("Warning: groq package not installed")

logger = logging.getLogger(__name__)

class WebsiteGeneratorAgent:
    """AI agent for generating professional websites and landing pages"""
    
    def __init__(self):
        self.ai_client = None
        self.output_dir = Path("generated_websites")
        self.output_dir.mkdir(exist_ok=True)
        self.versions_dir = Path("website_versions")
        self.versions_dir.mkdir(exist_ok=True)
        
        # Initialize AI client
        self._init_ai_client()
    
    def _init_ai_client(self):
        """Initialize Groq client with a reliable model"""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                if Groq:
                    self.ai_client = Groq(api_key=groq_api_key)
                    logger.info("✅ Groq client initialized successfully for website generation")
                else:
                    logger.error("❌ Groq package not available")
            except Exception as e:
                logger.error(f"❌ Groq initialization failed: {e}")
        else:
            logger.error("❌ GROQ_API_KEY not available in environment variables")
    
    def load_business_data(self) -> Dict[str, str]:
        """Load business data from output files and brand identity storage"""
        # Get the correct path to the output directory
        # Current file is in backend/agents/, so output is in backend/agents/output/
        current_dir = os.path.dirname(__file__)
        base_path = os.path.join(current_dir, "output")
        
        # Debug: print the path we're looking for
        logger.info(f"Looking for output files in: {base_path}")
        
        # Read financial data
        financial_path = os.path.join(base_path, "assessment_output.txt")
        financial_data = ""
        if os.path.exists(financial_path):
            with open(financial_path, "r", encoding="utf-8") as f:
                financial_data = f.read()
            logger.info(f"✅ Loaded financial data: {len(financial_data)} characters")
        else:
            logger.warning(f"❌ Financial data not found at: {financial_path}")
        
        # Read market data
        market_path = os.path.join(base_path, "market_analysis_competitors_output.txt")
        market_data = ""
        if os.path.exists(market_path):
            with open(market_path, "r", encoding="utf-8") as f:
                market_data = f.read()
            logger.info(f"✅ Loaded market data: {len(market_data)} characters")
        else:
            logger.warning(f"❌ Market data not found at: {market_path}")
        
        # Read legal data
        legal_path = os.path.join(base_path, "legal_output.txt")
        legal_data = ""
        if os.path.exists(legal_path):
            with open(legal_path, "r", encoding="utf-8") as f:
                legal_data = f.read()
            logger.info(f"✅ Loaded legal data: {len(legal_data)} characters")
        else:
            logger.warning(f"❌ Legal data not found at: {legal_path}")
                
        # Read business summary
        business_summary_path = os.path.join(base_path, "business_summary.txt")
        business_summary = ""
        if os.path.exists(business_summary_path):
            with open(business_summary_path, "r", encoding="utf-8") as f:
                raw_summary = f.read()
                # Remove the "Generated on" date line for cleaner processing
                business_summary = raw_summary.split("\nGenerated on")[0] if "\nGenerated on" in raw_summary else raw_summary
            logger.info(f"✅ Loaded business summary: {len(business_summary)} characters")
        else:
            logger.warning(f"❌ Business summary not found at: {business_summary_path}")
        
        # Load brand identity data from exported brand guidelines
        brand_identity_data = ""
        try:
            # Look for the most recent brand guidelines file (JSON, HTML, or TXT)
            brand_files = []
            for ext in ['json', 'html', 'txt']:
                pattern = os.path.join(base_path, f"brand_guidelines_*.{ext}")
                files = glob.glob(pattern)
                brand_files.extend(files)
            
            if brand_files:
                # Get the most recent brand guidelines file
                latest_brand_file = max(brand_files, key=os.path.getmtime)
                
                if latest_brand_file.endswith('.json'):
                    with open(latest_brand_file, 'r', encoding='utf-8') as f:
                        brand_data = json.load(f)
                        # Extract key brand information for website generation
                        brand_summary = {
                            "brand_name": brand_data.get('name', 'Your Business'),
                            "colors": brand_data.get('colors', []),
                            "personality": brand_data.get('personality', []),
                            "description": brand_data.get('customDescription', ''),
                            "logo_url": brand_data.get('logoUrl', ''),
                            "voice_tone": ', '.join(brand_data.get('personality', [])) if brand_data.get('personality') else 'professional'
                        }
                        brand_identity_data = json.dumps(brand_summary, indent=2)
                        logger.info(f"✅ Loaded brand identity from JSON: {len(brand_identity_data)} characters")
                elif latest_brand_file.endswith('.html'):
                    with open(latest_brand_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                        # Extract brand info from HTML content for website generation
                        brand_identity_data = f"Brand Guidelines HTML: {html_content[:1000]}..."
                        logger.info(f"✅ Loaded brand identity from HTML: {len(brand_identity_data)} characters")
                elif latest_brand_file.endswith('.txt'):
                    with open(latest_brand_file, 'r', encoding='utf-8') as f:
                        brand_identity_data = f.read()
                        logger.info(f"✅ Loaded brand identity from text: {len(brand_identity_data)} characters")
            else:
                logger.warning("❌ No brand guidelines files found")
                
        except Exception as e:
            logger.warning(f"❌ Failed to load brand identity data: {e}")
            brand_identity_data = ""
        
        data_summary = {
            "business_summary": business_summary,
            "financial_data": financial_data,
            "market_data": market_data,
            "legal_data": legal_data,
            "brand_identity_data": brand_identity_data
        }
        
        # Log final summary
        loaded_count = sum(1 for v in data_summary.values() if v.strip())
        logger.info(f"📊 Business data summary: {loaded_count}/5 fields loaded successfully")
        
        return data_summary
    
    def analyze_business_for_website(self, business_data: Dict[str, str]) -> Dict[str, Any]:
        """Analyze business data to extract website requirements"""
        if not self.ai_client:
            logger.error("Groq client not available")
            return {}
        
        analysis_prompt = f"""
        Analyze the following comprehensive business data and extract website requirements:
        
        BUSINESS SUMMARY:
        {business_data.get('business_summary', 'No summary available')}
        
        FINANCIAL DATA:
        {business_data.get('financial_data', 'No financial data')[:1000]}
        
        MARKET ANALYSIS:
        {business_data.get('market_data', 'No market data')[:1000]}
        
        LEGAL REQUIREMENTS:
        {business_data.get('legal_data', 'No legal data')[:500]}
        
        BRAND IDENTITY:
        {business_data.get('brand_identity_data', 'No brand data')[:800]}
        
        Based on this comprehensive business analysis, provide detailed website requirements in JSON format:
        {{
            "company_name": "extracted company name",
            "industry": "primary industry",
            "business_type": "type of business",
            "target_audience": "primary target audience",
            "unique_value_proposition": "main value proposition",
            "key_services": ["service1", "service2", "service3"],
            "competitive_advantages": ["advantage1", "advantage2"],
            "brand_colors": ["#color1", "#color2", "#color3"],
            "brand_personality": "brand personality description",
            "website_sections": ["hero", "about", "services", "testimonials", "contact"],
            "call_to_action": "primary CTA text",
            "seo_keywords": ["keyword1", "keyword2", "keyword3"],
            "tone_of_voice": "professional/friendly/authoritative etc",
            "business_model": "B2B/B2C/marketplace etc",
            "stage": "startup/growth/established",
            "key_metrics": ["metric1", "metric2"],
            "social_proof_elements": ["testimonials", "client_logos", "awards"]
        }}
        """
        
        try:
            response = self.ai_client.chat.completions.create(
                model="llama3-70b-8192",  # Use a reliable Groq model
                messages=[
                    {"role": "system", "content": "You are a business analyst and web strategist. Return only valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                top_p=1,
                stream=False
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Find JSON in content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.warning("Could not parse business analysis JSON")
                return self._get_fallback_analysis(business_data)
                
        except Exception as e:
            logger.error(f"Business analysis failed: {e}")
            return self._get_fallback_analysis(business_data)
    
    def _get_fallback_analysis(self, business_data: Dict[str, str]) -> Dict[str, Any]:
        """Provide fallback analysis when AI fails"""
        business_summary = business_data.get('business_summary', '')
        
        return {
            "company_name": "Your Business",
            "industry": "Business Services",
            "business_type": "Professional Services",
            "target_audience": "Business professionals and entrepreneurs",
            "unique_value_proposition": "Innovative solutions for modern businesses",
            "key_services": ["Consulting", "Strategy", "Implementation"],
            "competitive_advantages": ["Expert team", "Proven results", "Custom approach"],
            "brand_colors": ["#2563eb", "#1e40af", "#3b82f6"],
            "brand_personality": "Professional, reliable, innovative",
            "website_sections": ["hero", "about", "services", "testimonials", "contact"],
            "call_to_action": "Get Started Today",
            "seo_keywords": ["business solutions", "consulting", "professional services"],
            "tone_of_voice": "professional",
            "business_model": "B2B",
            "stage": "growth",
            "key_metrics": ["Client satisfaction", "Project success rate"],
            "social_proof_elements": ["testimonials", "case_studies", "client_logos"]
        }
    
    def generate_website(self, business_data: Dict[str, str], user_prompt: str = "", style_preferences: str = "modern") -> Dict[str, Any]:
        """Generate a complete website based on business data using our TSX component"""
        if not self.ai_client:
            raise Exception("Groq client not available")
        
        # Analyze business data first
        analysis = self.analyze_business_for_website(business_data)
        
        # Generate website component data
        website_data = self._create_website_data(analysis, business_data, user_prompt, style_preferences)
        
        try:
            logger.info(f"🚀 Generating website data for: {analysis.get('company_name', 'Unknown')}")
            logger.info(f"� Analysis complete with {len(analysis)} fields")
            
            # Generate website ID and save
            website_id = self._generate_website_id(analysis.get("company_name", "website"))
            
            # Create the TSX component content using our template
            tsx_content = self._create_tsx_website(analysis, business_data, user_prompt)
            
            # Save website version
            version_info = self._save_website_version(website_id, tsx_content, analysis, user_prompt)
            
            return {
                "success": True,
                "website_id": website_id,
                "html_code": tsx_content,  # Return TSX content as html_code for compatibility
                "analysis": analysis,
                "version_info": version_info,
                "company_name": analysis.get("company_name", "Your Business"),
                "generation_time": datetime.now().isoformat(),
                "component_type": "tsx_landing_page"
            }
            
        except Exception as e:
            logger.error(f"Website generation failed: {e}")
            raise Exception(f"Failed to generate website: {str(e)}")
    
    def _create_tsx_website(self, analysis: Dict[str, Any], business_data: Dict[str, str], user_prompt: str) -> str:
        """Create a TSX-based website using our GeneratedLandingPage component with fully dynamic content"""
        company_name = analysis.get("company_name", "Your Business")
        
        # Extract additional dynamic content from business data
        enhanced_analysis = self._enhance_analysis_with_business_data(analysis, business_data, user_prompt)
        
        # Create a Next.js page that renders our landing page component
        tsx_content = f'''import GeneratedLandingPage from '@/components/generated-landing-page'

// This website is 100% AI-generated based on your business data
// Company: {company_name}
// Generated: {datetime.now().isoformat()}
// User Requirements: {user_prompt if user_prompt else 'Standard professional website'}

const websiteAnalysis = {json.dumps(enhanced_analysis, indent=2)}

const businessData = {json.dumps(business_data, indent=2)}

export default function GeneratedWebsite() {{
  return (
    <GeneratedLandingPage 
      analysis={{websiteAnalysis}}
      businessData={{businessData}}
    />
  )
}}'''
        
        logger.info(f"✅ Generated TSX component with {len(enhanced_analysis)} analysis fields")
        return tsx_content
    
    def _enhance_analysis_with_business_data(self, analysis: Dict[str, Any], business_data: Dict[str, str], user_prompt: str) -> Dict[str, Any]:
        """Enhance the analysis with more dynamic content from business data"""
        enhanced = analysis.copy()
        
        try:
            # Extract company name from business summary if not already present
            business_summary = business_data.get('business_summary', '')
            if business_summary and not enhanced.get('company_name'):
                # Try to extract company name from summary
                lines = business_summary.split('\n')
                for line in lines[:5]:  # Check first 5 lines
                    if any(keyword in line.lower() for keyword in ['company', 'business', 'name', 'founded']):
                        # Extract potential company name
                        words = line.split()
                        for i, word in enumerate(words):
                            if word.lower() in ['company', 'business', 'inc', 'ltd', 'llc']:
                                if i > 0:
                                    enhanced['company_name'] = ' '.join(words[:i+1])
                                    break
            
            # Extract services from business summary
            if business_summary:
                services_keywords = ['services', 'offers', 'provides', 'specializes', 'focus']
                summary_lower = business_summary.lower()
                for keyword in services_keywords:
                    if keyword in summary_lower:
                        # Extract services context
                        start_idx = summary_lower.find(keyword)
                        context = business_summary[start_idx:start_idx+200]
                        # This could be enhanced with NLP to extract actual services
                        break
            
            # Extract target audience from market data
            market_data = business_data.get('market_data', '')
            if market_data:
                market_lower = market_data.lower()
                audience_keywords = ['target', 'customers', 'clients', 'audience', 'demographic']
                for keyword in audience_keywords:
                    if keyword in market_lower:
                        start_idx = market_lower.find(keyword)
                        context = market_data[start_idx:start_idx+150]
                        # Extract audience information
                        enhanced['target_audience_details'] = context
                        break
            
            # Extract brand information from brand identity data
            brand_data = business_data.get('brand_identity_data', '')
            if brand_data:
                try:
                    brand_json = json.loads(brand_data)
                    if isinstance(brand_json, dict):
                        # Use actual brand data
                        enhanced['company_name'] = brand_json.get('brand_name', enhanced.get('company_name'))
                        enhanced['brand_colors'] = brand_json.get('colors', enhanced.get('brand_colors', []))
                        enhanced['brand_personality'] = ', '.join(brand_json.get('personality', [])) if brand_json.get('personality') else enhanced.get('brand_personality')
                        enhanced['brand_description'] = brand_json.get('description', enhanced.get('unique_value_proposition', ''))
                        enhanced['logo_url'] = brand_json.get('logoUrl', '')
                        enhanced['tone_of_voice'] = brand_json.get('voice_tone', enhanced.get('tone_of_voice'))
                except json.JSONDecodeError:
                    pass
            
            # Generate dynamic testimonials based on industry and services
            testimonials = self._generate_dynamic_testimonials(enhanced)
            enhanced['dynamic_testimonials'] = testimonials
            
            # Generate dynamic features based on competitive advantages
            features = self._generate_dynamic_features(enhanced)
            enhanced['dynamic_features'] = features
            
            # Add user requirements to influence content
            if user_prompt:
                enhanced['user_requirements'] = user_prompt
                enhanced['custom_sections'] = self._extract_custom_sections(user_prompt)
            
            # Generate dynamic stats based on business type and stage
            stats = self._generate_dynamic_stats(enhanced)
            enhanced['dynamic_stats'] = stats
            
        except Exception as e:
            logger.warning(f"Error enhancing analysis: {e}")
        
        return enhanced
    
    def _generate_dynamic_testimonials(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate dynamic testimonials based on business context"""
        industry = analysis.get('industry', 'Business')
        services = analysis.get('key_services', ['Service'])
        
        testimonials = [
            {
                "name": "Sarah Johnson",
                "role": f"CEO, {industry} Solutions Inc",
                "content": f"Working with {analysis.get('company_name', 'this company')} transformed our approach to {services[0] if services else 'business operations'}. The results exceeded our expectations.",
                "rating": 5,
                "image": "https://images.unsplash.com/photo-1494790108755-2616b612b5c5?w=100&h=100&fit=crop&crop=face"
            },
            {
                "name": "Michael Chen",
                "role": f"Director of Operations, {industry} Corp",
                "content": f"The expertise in {', '.join(services[:2]) if len(services) >= 2 else 'professional services'} is outstanding. Highly recommend their services.",
                "rating": 5,
                "image": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face"
            },
            {
                "name": "Emily Rodriguez",
                "role": f"Manager, {industry} Enterprises",
                "content": f"Professional, reliable, and delivers exceptional results. Their {services[-1] if services else 'service'} capabilities are unmatched.",
                "rating": 5,
                "image": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face"
            }
        ]
        
        return testimonials
    
    def _generate_dynamic_features(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate dynamic features based on competitive advantages"""
        advantages = analysis.get('competitive_advantages', ['Quality Service', 'Expert Team', 'Fast Delivery'])
        
        features = []
        for i, advantage in enumerate(advantages[:6]):  # Limit to 6 features
            features.append({
                "title": advantage,
                "description": f"Experience the benefits of our {advantage.lower()} approach in everything we deliver.",
                "icon": ["star", "shield", "zap", "award", "target", "rocket"][i % 6]
            })
        
        return features
    
    def _generate_dynamic_stats(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate dynamic statistics based on business stage and type"""
        stage = analysis.get('stage', 'growth')
        business_type = analysis.get('business_type', 'Professional Services')
        
        if stage == 'startup':
            stats = [
                {"value": "50+", "label": "Projects Completed"},
                {"value": "95%", "label": "Client Satisfaction"},
                {"value": "24/7", "label": "Support Available"},
                {"value": "2+", "label": "Years Experience"}
            ]
        elif stage == 'established':
            stats = [
                {"value": "1000+", "label": "Happy Clients"},
                {"value": "99%", "label": "Success Rate"},
                {"value": "24/7", "label": "Premium Support"},
                {"value": "10+", "label": "Years Excellence"}
            ]
        else:  # growth
            stats = [
                {"value": "500+", "label": "Satisfied Clients"},
                {"value": "98%", "label": "Success Rate"},
                {"value": "24/7", "label": "Support"},
                {"value": "5+", "label": "Years Experience"}
            ]
        
        return stats
    
    def _extract_custom_sections(self, user_prompt: str) -> List[str]:
        """Extract custom sections requested by user"""
        sections = []
        prompt_lower = user_prompt.lower()
        
        section_keywords = {
            'pricing': ['pricing', 'price', 'cost', 'packages'],
            'portfolio': ['portfolio', 'gallery', 'showcase', 'projects'],
            'team': ['team', 'staff', 'members', 'people'],
            'blog': ['blog', 'news', 'articles', 'updates'],
            'faq': ['faq', 'questions', 'help', 'support'],
            'testimonials': ['testimonials', 'reviews', 'feedback'],
            'contact': ['contact', 'reach', 'get in touch']
        }
        
        for section, keywords in section_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                sections.append(section)
        
        return sections
    
    def _create_website_data(self, analysis: Dict[str, Any], business_data: Dict[str, str], user_prompt: str, style_preferences: str) -> Dict[str, Any]:
        """Create structured website data for the TSX component"""
        return {
            "analysis": analysis,
            "business_data": business_data,
            "user_requirements": user_prompt,
            "style_preferences": style_preferences,
            "generated_at": datetime.now().isoformat(),
            "component_type": "generated_landing_page"
        }
    
    def _create_website_prompt(self, analysis: Dict[str, Any], business_data: Dict[str, str], user_prompt: str, style_preferences: str) -> str:
        """Create comprehensive but concise website generation prompt"""
        company_name = analysis.get("company_name", "Your Business")
        industry = analysis.get("industry", "Business")
        services = ", ".join(analysis.get("key_services", ["Service 1", "Service 2"]))
        colors = analysis.get("brand_colors", ["#2563eb", "#1e40af", "#3b82f6"])
        
        # Extract brand identity information from loaded data
        brand_context = ""
        if business_data.get("brand_identity_data"):
            try:
                # Try to parse JSON brand data
                import json
                brand_data = json.loads(business_data["brand_identity_data"])
                if isinstance(brand_data, dict):
                    brand_name = brand_data.get("brand_name", company_name)
                    brand_colors = brand_data.get("colors", colors)
                    brand_personality = brand_data.get("personality", [])
                    brand_description = brand_data.get("description", "")
                    brand_voice = brand_data.get("voice_tone", "professional")
                    
                    # Update analysis with brand data
                    company_name = brand_name
                    colors = brand_colors if brand_colors else colors
                    
                    brand_context = f"""
BRAND IDENTITY:
- Name: {brand_name}
- Colors: {', '.join(brand_colors) if brand_colors else 'professional blue theme'}
- Personality: {', '.join(brand_personality) if brand_personality else 'professional'}
- Voice: {brand_voice}
- Description: {brand_description}
"""
            except (json.JSONDecodeError, TypeError):
                # Fallback for non-JSON brand data
                brand_context = f"BRAND CONTEXT: {business_data['brand_identity_data'][:300]}..."
        
        return f"""
        Create a stunning, professional single-page website with these requirements:
        
        COMPANY: {company_name}
        INDUSTRY: {industry}
        SERVICES: {services}
        STYLE: {style_preferences}
        USER REQUIREMENTS: {user_prompt}
        
        {brand_context}
        
        TECHNICAL REQUIREMENTS:
        - Single HTML file with embedded CSS and JavaScript
        - Use Tailwind CSS v4 CDN: <script src="https://cdn.tailwindcss.com"></script>
        - Modern responsive design (mobile-first)
        - Professional color scheme using {colors}
        
        SECTIONS TO INCLUDE:
        1. Header with navigation and company logo area
        2. Hero section with compelling headline and call-to-action
        3. About section with company description
        4. Services section showcasing: {services}
        5. Contact section with contact form
        6. Footer with company information
        
        DESIGN FEATURES:
        - Modern gradients and professional styling
        - Smooth animations and hover effects
        - Mobile-responsive layout
        - Working contact form with JavaScript validation
        - Professional typography and spacing
        - Use images from: https://image.pollinations.ai/prompt/professional-{industry}-business-hero-background
        
        Return ONLY the complete HTML code with embedded CSS and JavaScript.
        Make it production-ready and visually appealing.
        """
    
    def _clean_html_code(self, code: str) -> str:
        """Clean and validate HTML code"""
        # Remove markdown code blocks
        if "```html" in code:
            code = code.split("```html")[1].split("```")[0].strip()
        elif "```" in code:
            parts = code.split("```")
            if len(parts) >= 3:
                code = parts[1].strip()
        
        # Ensure proper HTML structure with Tailwind CSS v4
        if not code.strip().startswith('<!DOCTYPE html>'):
            if not code.strip().startswith('<html'):
                tailwind_head = """<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Generated Website</title>
    <script src='https://cdn.tailwindcss.com'></script>
    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' rel='stylesheet'>
</head>
<body>
"""
                code = f"{tailwind_head}{code}\n</body>\n</html>"
        
        # Ensure Tailwind CSS is included if not present
        if 'tailwindcss.com' not in code and '@import "tailwindcss"' not in code:
            code = code.replace(
                '<head>',
                '<head>\n    <script src="https://cdn.tailwindcss.com"></script>'
            )
        
        return code
    
    def _generate_website_id(self, company_name: str) -> str:
        """Generate unique website ID"""
        # Clean company name for URL
        safe_name = re.sub(r'[^a-zA-Z0-9\s-]', '', company_name)
        safe_name = re.sub(r'\s+', '-', safe_name).lower()[:30]
        timestamp = int(time.time())
        return f"{safe_name}-{timestamp}"
    
    def _save_website_version(self, website_id: str, html_code: str, analysis: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Save website version with metadata"""
        version_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = f"{website_id}_v{version_timestamp}"
        
        # Save HTML file
        html_file = self.versions_dir / f"{version_id}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_code)
        
        # Save metadata
        metadata = {
            "version_id": version_id,
            "website_id": website_id,
            "timestamp": version_timestamp,
            "user_prompt": user_prompt,
            "analysis": analysis,
            "file_size": len(html_code),
            "company_name": analysis.get("company_name", "Unknown"),
            "industry": analysis.get("industry", "Unknown")
        }
        
        metadata_file = self.versions_dir / f"{version_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def regenerate_website(self, website_id: str, user_feedback: str, style_preferences: str = "modern") -> Dict[str, Any]:
        """Regenerate website with user feedback"""
        # Load business data
        business_data = self.load_business_data()
        
        # Create regeneration prompt with feedback
        user_prompt = f"User feedback: {user_feedback}. Please incorporate this feedback into the website design and content."
        
        return self.generate_website(business_data, user_prompt, style_preferences)
    
    def get_website_versions(self, website_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a website"""
        versions = []
        
        for metadata_file in self.versions_dir.glob(f"{website_id}_v*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    versions.append(metadata)
            except Exception as e:
                logger.error(f"Failed to load version metadata: {e}")
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return versions
    
    def get_website_html(self, version_id: str) -> Optional[str]:
        """Get HTML code for a specific version"""
        html_file = self.versions_dir / f"{version_id}.html"
        
        if html_file.exists():
            with open(html_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def publish_website(self, version_id: str) -> Dict[str, Any]:
        """Mark a website version as published"""
        try:
            # Copy to published directory
            published_dir = self.output_dir / "published"
            published_dir.mkdir(exist_ok=True)
            
            # Get HTML content
            html_content = self.get_website_html(version_id)
            if not html_content:
                raise Exception("Website version not found")
            
            # Save as published version
            published_file = published_dir / f"{version_id}.html"
            with open(published_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Update metadata
            metadata_file = self.versions_dir / f"{version_id}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata["published"] = True
                metadata["published_at"] = datetime.now().isoformat()
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "message": "Website published successfully",
                "published_url": f"/company-profile/{version_id}",
                "version_id": version_id
            }
            
        except Exception as e:
            logger.error(f"Failed to publish website: {e}")
            return {
                "success": False,
                "error": str(e)
            }
