#!/usr/bin/env python3
"""
Gemini API connections module
"""

import google.generativeai as genai
from config.secrets import gemini_api_key

def gemini_create_client():
    """Create Gemini client"""
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')
        return model
    except Exception as e:
        print_lg(f"Failed to create Gemini client: {e}")
        return None

def gemini_extract_skills(client, job_description: str) -> list:
    """Extract skills from job description using Gemini"""
    try:
        prompt = f"Extract the technical skills from this job description and return them as a comma-separated list: {job_description}"
        response = client.generate_content(prompt)
        skills = response.text.strip()
        return skills.split(', ')
    except Exception as e:
        print_lg(f"Failed to extract skills with Gemini: {e}")
        return []

def gemini_answer_question(client, question: str, options: list = None, question_type: str = "text", job_description: str = None, about_company: str = None, user_information_all: dict = None) -> str:
    """Answer application questions using Gemini"""
    try:
        context = f"Job Description: {job_description}\n" if job_description else ""
        context += f"About Company: {about_company}\n" if about_company else ""
        context += f"User Information: {user_information_all}\n" if user_information_all else ""
        
        if options:
            context += f"Available Options: {', '.join(options)}\n"
        
        prompt = f"{context}Question: {question}\nQuestion Type: {question_type}\n\nPlease provide a professional and appropriate answer."
        response = client.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print_lg(f"Failed to answer question with Gemini: {e}")
        return ""