# Security Guidelines for BrandOrbAI

## Environment Variables and API Keys

### IMPORTANT: Never commit API keys to version control!

This project uses several external APIs that require authentication keys. All sensitive information should be stored in environment variables.

### Setup Instructions

1. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Fill in your actual API keys in the `.env` file:
   ```bash
   # Required API Keys
   GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key
   OPENROUTER_API_KEY=your_actual_openrouter_api_key
   
   # Optional Social Media API Keys
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   # ... etc
   ```

### Required API Keys

#### Google Maps API
- **Purpose**: Used for competitor discovery and location-based business search
- **How to get**: [Google Cloud Console](https://console.cloud.google.com/)
- **Required APIs**: Places API, Maps JavaScript API
- **Environment Variable**: `GOOGLE_MAPS_API_KEY`

#### OpenRouter API  
- **Purpose**: Used for AI-powered competitor analysis and content generation
- **How to get**: [OpenRouter](https://openrouter.ai/)
- **Environment Variable**: `OPENROUTER_API_KEY`

#### Groq API
- **Purpose**: Used for fast AI processing and image generation prompts
- **How to get**: [Groq Console](https://console.groq.com/)
- **Environment Variable**: `GROQ_API_KEY`

#### Apify API
- **Purpose**: Used for social media scraping (LinkedIn and TikTok data)
- **How to get**: [Apify Console](https://console.apify.com/)
- **Environment Variable**: `APIFY_API_TOKEN`

#### Together AI API
- **Purpose**: Used for investor analysis and recommendation generation
- **How to get**: [Together AI](https://api.together.xyz/)
- **Environment Variable**: `TOGETHER_API_KEY`

#### Pexels API
- **Purpose**: Used for stock image search and retrieval
- **How to get**: [Pexels API](https://www.pexels.com/api/)
- **Environment Variable**: `PEXELS_API_KEY`

#### Tavily API (Optional)
- **Purpose**: Used for web search and content discovery
- **How to get**: [Tavily](https://tavily.com/)
- **Environment Variable**: `TAVILY_API_KEY`

#### LangSmith API (Optional)
- **Purpose**: Used for AI model monitoring and debugging
- **How to get**: [LangSmith](https://smith.langchain.com/)
- **Environment Variable**: `LANGSMITH_API_KEY`

#### LinkedIn API (Optional)
- **Purpose**: Social media posting and competitor analysis
- **How to get**: [LinkedIn Developer Portal](https://developer.linkedin.com/)
- **Environment Variables**: 
  - `LINKEDIN_CLIENT_ID`
  - `LINKEDIN_CLIENT_SECRET`
  - `LINKEDIN_ACCESS_TOKEN`

### Security Checklist

- [ ] `.env` files are listed in `.gitignore`
- [ ] No hardcoded API keys in source code
- [ ] All API keys use environment variables
- [ ] `.env.example` contains placeholder values only
- [ ] Team members have their own API keys
- [ ] API keys are rotated regularly

### Files That Should NEVER Be Committed

- `backend/.env` - Contains actual API keys
- Any file with real API keys or secrets
- Private key files (`.pem`, `.key`, etc.)

### Safe Files to Commit

- `backend/.env.example` - Template with placeholder values
- Configuration files that reference environment variables
- Documentation about required API keys

### If You Accidentally Commit API Keys

1. **Immediately revoke/regenerate** the exposed API keys
2. Remove the commit from git history:
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch path/to/file/with/keys' \
   --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push to update remote repository
4. Update all team members
5. Update `.env` with new API keys

### Environment Variable Loading

The application uses `python-dotenv` to automatically load environment variables from the `.env` file. Make sure this package is installed:

```bash
pip install python-dotenv
```

### Production Deployment

For production deployments, set environment variables directly in your hosting platform (Heroku, AWS, etc.) rather than using `.env` files.
