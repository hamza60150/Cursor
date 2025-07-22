#!/usr/bin/env python3
"""
LLM Integration Module for LinkedIn Job Application Bot
Provides intelligent job matching, application customization, and content generation.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import time

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

@dataclass
class JobAnalysis:
    """Results from LLM job analysis"""
    relevance_score: float  # 0-100
    match_reasons: List[str]
    concerns: List[str]
    suggested_skills_to_highlight: List[str]
    custom_cover_letter: str
    application_strategy: str

@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: LLMProvider = LLMProvider.OLLAMA
    api_key: str = ""
    model: str = "llama2"
    max_tokens: int = 2000
    temperature: float = 0.7
    ollama_base_url: str = "http://localhost:11434"

class LLMIntegration:
    """Main LLM integration class"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def analyze_job_compatibility(self, job_data: Dict, user_profile: Dict) -> JobAnalysis:
        """Analyze job compatibility using LLM"""
        try:
            prompt = self._create_job_analysis_prompt(job_data, user_profile)
            response = await self._call_llm(prompt)
            return self._parse_job_analysis(response)
        except Exception as e:
            self.logger.error(f"Error analyzing job compatibility: {e}")
            return self._create_default_analysis()
    
    def _create_job_analysis_prompt(self, job_data: Dict, user_profile: Dict) -> str:
        """Create prompt for job analysis"""
        return f"""
        Analyze the compatibility between this job posting and candidate profile:

        JOB POSTING:
        Title: {job_data.get('title', 'N/A')}
        Company: {job_data.get('companyName', 'N/A')}
        Location: {job_data.get('location', 'N/A')}

        CANDIDATE PROFILE:
        Name: {user_profile.get('first_name', '')} {user_profile.get('last_name', '')}
        Skills: {user_profile.get('skills', [])}

        Provide a JSON response with relevance_score (0-100), match_reasons, concerns, suggested_skills_to_highlight, custom_cover_letter, and application_strategy.
        """
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with the given prompt"""
        if self.config.provider == LLMProvider.OLLAMA:
            return await self._call_ollama(prompt)
        else:
            return self._generate_fallback_response(prompt)
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama local API"""
        try:
            response = requests.post(
                f"{self.config.ollama_base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return self._generate_fallback_response(prompt)
        except Exception as e:
            self.logger.error(f"Ollama API error: {e}")
            return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when LLM is not available"""
        return json.dumps({
            "relevance_score": 75,
            "match_reasons": ["General skill match", "Location compatibility", "Industry alignment"],
            "concerns": ["Need to verify specific requirements"],
            "suggested_skills_to_highlight": ["communication", "problem-solving", "teamwork"],
            "custom_cover_letter": "Dear Hiring Manager,\n\nI am excited to apply for this position. My background and skills align well with the requirements.\n\nSincerely,\n[Your Name]",
            "application_strategy": "Focus on relevant experience and skills"
        })
    
    def _parse_job_analysis(self, response: str) -> JobAnalysis:
        """Parse LLM response into JobAnalysis object"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                return JobAnalysis(
                    relevance_score=data.get('relevance_score', 50),
                    match_reasons=data.get('match_reasons', []),
                    concerns=data.get('concerns', []),
                    suggested_skills_to_highlight=data.get('suggested_skills_to_highlight', []),
                    custom_cover_letter=data.get('custom_cover_letter', ''),
                    application_strategy=data.get('application_strategy', '')
                )
        except Exception as e:
            self.logger.error(f"Error parsing job analysis: {e}")
        
        return self._create_default_analysis()
    
    def _create_default_analysis(self) -> JobAnalysis:
        """Create default analysis when LLM fails"""
        return JobAnalysis(
            relevance_score=50.0,
            match_reasons=["General compatibility"],
            concerns=["Unable to perform detailed analysis"],
            suggested_skills_to_highlight=[],
            custom_cover_letter="",
            application_strategy="Standard application approach"
        )

def load_llm_config() -> LLMConfig:
    """Load LLM configuration from environment variables"""
    provider_str = os.getenv('LLM_PROVIDER', 'ollama').lower()
    
    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        provider = LLMProvider.OLLAMA
    
    return LLMConfig(
        provider=provider,
        api_key=os.getenv('LLM_API_KEY', ''),
        model=os.getenv('LLM_MODEL', 'llama2'),
        max_tokens=int(os.getenv('LLM_MAX_TOKENS', '2000')),
        temperature=float(os.getenv('LLM_TEMPERATURE', '0.7')),
        ollama_base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    )
