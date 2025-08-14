#!/usr/bin/env python3
"""
LinkedIn Posting Agent - Simplified integration for BrandOrbAI
Handles LinkedIn authentication and posting functionality
"""

import os
import base64
import urllib.parse
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class LinkedInAgent:
    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8001/social/linkedin/callback')
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        
    def get_person_id(self, access_token: str = None) -> str | None:
        """Get LinkedIn person ID from access token"""
        token = access_token or self.access_token
        if not token:
            return None
            
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("sub")
        except Exception as e:
            logger.error(f"Error getting person ID: {e}")
            return None

    def post_to_linkedin(self, message: str, access_token: str = None, image_data: str = None):
        """Post content to LinkedIn with optional image"""
        token = access_token or self.access_token
        if not token:
            raise Exception("Missing LinkedIn access token")

        person_id = self.get_person_id(token)
        if not person_id:
            raise Exception("Unable to fetch LinkedIn person ID")

        asset_urn = None
        if image_data:
            # Register upload for image
            reg_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            reg_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{person_id}",
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            }
            reg_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            reg_resp = requests.post(reg_url, json=reg_payload, headers=reg_headers)
            reg_resp.raise_for_status()
            reg_data = reg_resp.json()
            
            asset_urn = reg_data["value"]["asset"]
            upload_url = reg_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]

            # Upload image binary data
            img_bytes = base64.b64decode(image_data)
            up_resp = requests.put(upload_url, data=img_bytes, headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream"
            })
            up_resp.raise_for_status()

        # Create post
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        payload = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": message},
                    "shareMediaCategory": "IMAGE" if asset_urn else "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        
        if asset_urn:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "media": asset_urn
            }]

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return {
            "post_id": response.json().get("id"),
            "status": "success",
            "posted_at": datetime.now().isoformat()
        }

    def get_auth_url(self) -> str:
        """Generate LinkedIn OAuth authorization URL"""
        if not self.client_id:
            raise Exception("LinkedIn Client ID not configured")
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "w_member_social profile openid email",
            "state": "brandorb_auth_state"
        }
        
        return f"https://www.linkedin.com/oauth/v2/authorization?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if not self.client_id or not self.client_secret:
            raise Exception("LinkedIn credentials not configured")

        token_resp = requests.post("https://www.linkedin.com/oauth/v2/accessToken", data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        
        if token_resp.status_code != 200:
            raise Exception(f"Token exchange failed: {token_resp.text}")

        return token_resp.json()

# Initialize LinkedIn agent
linkedin_agent = LinkedInAgent()
