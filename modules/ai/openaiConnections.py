#!/usr/bin/env python3
"""
OpenAI API connections module
"""

import openai
from config.secrets import openai_api_key

def ai_create_openai_client():
    """Create OpenAI client"""
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        return client
    except Exception as e:
        print_lg(f"Failed to create OpenAI client: {e}")
        return None

def ai_extract_skills(client, job_description: str) -> list:
    """Extract skills from job description using OpenAI"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts technical skills from job descriptions."},
                {"role": "user", "content": f"Extract the technical skills from this job description and return them as a comma-separated list: {job_description}"}
            ],
            max_tokens=200
        )
        skills = response.choices[0].message.content.strip()
        return skills.split(', ')
    except Exception as e:
        print_lg(f"Failed to extract skills with OpenAI: {e}")
        return []

def ai_answer_question(client, question: str, question_type: str = "text", job_description: str = None, user_information_all: dict = None) -> str:
    """Answer application questions using OpenAI"""
    try:
        context = f"Job Description: {job_description}\n" if job_description else ""
        context += f"User Information: {user_information_all}\n" if user_information_all else ""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers job application questions professionally and concisely."},
                {"role": "user", "content": f"{context}Question: {question}\nQuestion Type: {question_type}\n\nPlease provide a professional and appropriate answer."}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print_lg(f"Failed to answer question with OpenAI: {e}")
        return ""

def ai_close_openai_client(client):
    """Close OpenAI client"""
    try:
        # OpenAI client doesn't need explicit closing
        pass
    except Exception as e:
        print_lg(f"Error closing OpenAI client: {e}")