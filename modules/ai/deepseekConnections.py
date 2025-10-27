#!/usr/bin/env python3
"""
DeepSeek API connections module
"""

import requests
from config.secrets import deepseek_api_key

def deepseek_create_client():
    """Create DeepSeek client"""
    try:
        # DeepSeek uses REST API, so we return the API key
        return deepseek_api_key
    except Exception as e:
        print_lg(f"Failed to create DeepSeek client: {e}")
        return None

def deepseek_extract_skills(client, job_description: str) -> list:
    """Extract skills from job description using DeepSeek"""
    try:
        headers = {
            "Authorization": f"Bearer {client}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that extracts technical skills from job descriptions."},
                {"role": "user", "content": f"Extract the technical skills from this job description and return them as a comma-separated list: {job_description}"}
            ],
            "max_tokens": 200
        }
        
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        skills = result["choices"][0]["message"]["content"].strip()
        return skills.split(', ')
    except Exception as e:
        print_lg(f"Failed to extract skills with DeepSeek: {e}")
        return []

def deepseek_answer_question(client, question: str, options: list = None, question_type: str = "text", job_description: str = None, about_company: str = None, user_information_all: dict = None) -> str:
    """Answer application questions using DeepSeek"""
    try:
        headers = {
            "Authorization": f"Bearer {client}",
            "Content-Type": "application/json"
        }
        
        context = f"Job Description: {job_description}\n" if job_description else ""
        context += f"About Company: {about_company}\n" if about_company else ""
        context += f"User Information: {user_information_all}\n" if user_information_all else ""
        
        if options:
            context += f"Available Options: {', '.join(options)}\n"
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that answers job application questions professionally and concisely."},
                {"role": "user", "content": f"{context}Question: {question}\nQuestion Type: {question_type}\n\nPlease provide a professional and appropriate answer."}
            ],
            "max_tokens": 300
        }
        
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print_lg(f"Failed to answer question with DeepSeek: {e}")
        return ""