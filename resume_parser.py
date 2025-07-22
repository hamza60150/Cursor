#!/usr/bin/env python3
"""
Resume Parser for Adaptive Job Application Bot
Parses resume data from various formats (text, PDF, HTML, etc.)
"""

import os
import json
import logging
import re
import base64
import tempfile
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import asyncio

# PDF parsing
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

# Document parsing
try:
    import docx2txt
except ImportError:
    docx2txt = None

from bs4 import BeautifulSoup
from llm_integration import LLMIntegration, load_llm_config

@dataclass
class ParsedResume:
    """Structured resume data"""
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    linkedin: str = ""
    website: str = ""
    summary: str = ""
    skills: List[str] = None
    experience: List[Dict] = None
    education: List[Dict] = None
    certifications: List[str] = None
    languages: List[str] = None
    raw_text: str = ""
    confidence_score: float = 0.0

class ResumeParser:
    """Main resume parser class"""
    
    def __init__(self, llm_integration: Optional[LLMIntegration] = None):
        self.logger = logging.getLogger(__name__)
        self.llm = llm_integration or LLMIntegration(load_llm_config())
        
        # Regex patterns for common fields
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        self.linkedin_pattern = re.compile(r'linkedin\.com/in/[\w-]+')
        self.url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?')
    
    async def parse_resume(self, resume_input: Union[str, bytes, Dict]) -> Dict[str, Any]:
        """Main method to parse resume from various input formats"""
        try:
            # Determine input type and extract text
            raw_text = await self._extract_text_from_input(resume_input)
            
            if not raw_text:
                raise ValueError("Could not extract text from resume input")
            
            # Parse with regex patterns first
            regex_parsed = self._parse_with_regex(raw_text)
            
            # Enhance with LLM analysis
            llm_parsed = await self._parse_with_llm(raw_text)
            
            # Combine results
            final_parsed = self._combine_parsing_results(regex_parsed, llm_parsed, raw_text)
            
            self.logger.info(f"Resume parsed successfully with confidence: {final_parsed.get('confidence_score', 0)}")
            
            return final_parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing resume: {e}")
            return self._create_fallback_resume(str(resume_input)[:500])
    
    async def _extract_text_from_input(self, resume_input: Union[str, bytes, Dict]) -> str:
        """Extract text from various input formats"""
        try:
            if isinstance(resume_input, str):
                # Check if it's a file path
                if os.path.isfile(resume_input):
                    return await self._extract_from_file(resume_input)
                # Check if it's base64 encoded
                elif self._is_base64(resume_input):
                    return await self._extract_from_base64(resume_input)
                # Treat as plain text
                else:
                    return resume_input
            
            elif isinstance(resume_input, bytes):
                # Try to decode as text first
                try:
                    return resume_input.decode('utf-8')
                except UnicodeDecodeError:
                    # Save to temp file and process
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(resume_input)
                        tmp.flush()
                        text = await self._extract_from_file(tmp.name)
                        os.unlink(tmp.name)
                        return text
            
            elif isinstance(resume_input, dict):
                # Handle structured input
                if 'content' in resume_input:
                    return await self._extract_text_from_input(resume_input['content'])
                elif 'text' in resume_input:
                    return resume_input['text']
                elif 'file_path' in resume_input:
                    return await self._extract_from_file(resume_input['file_path'])
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting text from input: {e}")
            return ""
    
    async def _extract_from_file(self, file_path: str) -> str:
        """Extract text from file based on extension"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                return await self._extract_from_pdf(file_path)
            elif file_ext in ['.doc', '.docx']:
                return await self._extract_from_docx(file_path)
            elif file_ext in ['.txt']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_ext in ['.html', '.htm']:
                return await self._extract_from_html(file_path)
            else:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        except Exception as e:
            self.logger.error(f"Error extracting from file {file_path}: {e}")
            return ""
    
    async def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            
            # Try pdfplumber first (better for complex layouts)
            if pdfplumber:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            
            # Fallback to PyPDF2
            elif PyPDF2:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    async def _extract_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            if docx2txt:
                return docx2txt.process(docx_path)
            else:
                self.logger.warning("docx2txt not available, cannot parse DOCX files")
                return ""
        except Exception as e:
            self.logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    async def _extract_from_html(self, html_path: str) -> str:
        """Extract text from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator='\n').strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting HTML text: {e}")
            return ""
    
    async def _extract_from_base64(self, base64_string: str) -> str:
        """Extract text from base64 encoded data"""
        try:
            decoded_data = base64.b64decode(base64_string)
            
            # Try to decode as text first
            try:
                return decoded_data.decode('utf-8')
            except UnicodeDecodeError:
                # Save to temp file and process as PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(decoded_data)
                    tmp.flush()
                    text = await self._extract_from_pdf(tmp.name)
                    os.unlink(tmp.name)
                    return text
        
        except Exception as e:
            self.logger.error(f"Error extracting from base64: {e}")
            return ""
    
    def _is_base64(self, s: str) -> bool:
        """Check if string is base64 encoded"""
        try:
            if isinstance(s, str):
                sb_bytes = bytes(s, 'ascii')
            elif isinstance(s, bytes):
                sb_bytes = s
            else:
                return False
            return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
        except Exception:
            return False
    
    def _parse_with_regex(self, text: str) -> Dict[str, Any]:
        """Parse resume using regex patterns"""
        try:
            parsed = {}
            
            # Extract email
            email_match = self.email_pattern.search(text)
            if email_match:
                parsed['email'] = email_match.group()
            
            # Extract phone
            phone_match = self.phone_pattern.search(text)
            if phone_match:
                parsed['phone'] = phone_match.group()
            
            # Extract LinkedIn
            linkedin_match = self.linkedin_pattern.search(text)
            if linkedin_match:
                parsed['linkedin'] = f"https://{linkedin_match.group()}"
            
            # Extract URLs (potential websites)
            urls = self.url_pattern.findall(text)
            websites = [url for url in urls if 'linkedin.com' not in url]
            if websites:
                parsed['website'] = websites[0]
            
            # Extract name (heuristic: first line that looks like a name)
            lines = text.split('\n')
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if len(line.split()) in [2, 3] and not any(char in line for char in '@.()'):
                    if not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum']):
                        parsed['name'] = line
                        break
            
            # Extract skills (look for skills section)
            skills = self._extract_skills_section(text)
            if skills:
                parsed['skills'] = skills
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error in regex parsing: {e}")
            return {}
    
    async def _parse_with_llm(self, text: str) -> Dict[str, Any]:
        """Parse resume using LLM intelligence"""
        try:
            prompt = self._create_resume_parsing_prompt(text)
            response = await self.llm._call_llm(prompt)
            
            # Parse LLM response
            parsed = self._parse_llm_response(response)
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error in LLM parsing: {e}")
            return {}
    
    def _create_resume_parsing_prompt(self, text: str) -> str:
        """Create prompt for LLM resume parsing"""
        return f"""
Parse the following resume text and extract structured information:

RESUME TEXT:
{text[:3000]}  # Limit text size for LLM

Extract the following information in JSON format:
1. Personal Information:
   - name (full name)
   - email
   - phone
   - address, city, state, zip_code
   - linkedin (full URL)
   - website (personal website URL)

2. Professional Information:
   - summary (professional summary/objective)
   - skills (array of technical and soft skills)
   - experience (array of work experience with company, position, duration, description)
   - education (array of education with school, degree, year)
   - certifications (array of certifications)
   - languages (array of languages spoken)

3. Analysis:
   - confidence_score (0-100 based on how well you could extract information)

RESPONSE FORMAT (JSON):
{{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94105",
    "linkedin": "https://linkedin.com/in/johndoe",
    "website": "https://johndoe.com",
    "summary": "Experienced software engineer...",
    "skills": ["Python", "JavaScript", "React"],
    "experience": [
        {{
            "company": "Tech Corp",
            "position": "Software Engineer",
            "duration": "2020-2023",
            "description": "Developed web applications..."
        }}
    ],
    "education": [
        {{
            "school": "University of California",
            "degree": "BS Computer Science",
            "year": "2020"
        }}
    ],
    "certifications": ["AWS Certified Developer"],
    "languages": ["English", "Spanish"],
    "confidence_score": 85
}}

Focus on accuracy and provide empty arrays/strings for missing information.
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return {}
    
    def _combine_parsing_results(self, regex_result: Dict, llm_result: Dict, raw_text: str) -> Dict[str, Any]:
        """Combine regex and LLM parsing results"""
        try:
            combined = {}
            
            # Start with LLM result as base (more comprehensive)
            combined.update(llm_result)
            
            # Override with regex results where they exist (more accurate for specific patterns)
            for key, value in regex_result.items():
                if value and value.strip():  # Only use non-empty values
                    combined[key] = value
            
            # Ensure required fields exist
            required_fields = ['name', 'email', 'phone', 'skills', 'experience', 'education']
            for field in required_fields:
                if field not in combined:
                    combined[field] = [] if field in ['skills', 'experience', 'education'] else ""
            
            # Add raw text
            combined['raw_text'] = raw_text
            
            # Calculate overall confidence
            regex_confidence = len([v for v in regex_result.values() if v]) * 10
            llm_confidence = llm_result.get('confidence_score', 50)
            combined['confidence_score'] = min(100, (regex_confidence + llm_confidence) / 2)
            
            return combined
            
        except Exception as e:
            self.logger.error(f"Error combining parsing results: {e}")
            return self._create_fallback_resume(raw_text)
    
    def _extract_skills_section(self, text: str) -> List[str]:
        """Extract skills from skills section using heuristics"""
        try:
            skills = []
            lines = text.split('\n')
            
            # Look for skills section
            skills_section_started = False
            for line in lines:
                line = line.strip()
                
                # Check if this is a skills section header
                if any(keyword in line.lower() for keyword in ['skills', 'technologies', 'technical skills']):
                    skills_section_started = True
                    continue
                
                # If we're in skills section, extract skills
                if skills_section_started:
                    # Stop if we hit another section
                    if any(keyword in line.lower() for keyword in ['experience', 'education', 'work', 'employment']):
                        break
                    
                    # Extract skills from line
                    if line and not line.startswith(('•', '-', '*')):
                        # Split by common separators
                        line_skills = re.split(r'[,;|]', line)
                        for skill in line_skills:
                            skill = skill.strip()
                            if skill and len(skill) < 30:  # Reasonable skill name length
                                skills.append(skill)
            
            return skills[:20]  # Limit to 20 skills
            
        except Exception as e:
            self.logger.error(f"Error extracting skills: {e}")
            return []
    
    def _create_fallback_resume(self, text: str) -> Dict[str, Any]:
        """Create fallback resume when parsing fails"""
        return {
            'name': '',
            'email': '',
            'phone': '',
            'address': '',
            'city': '',
            'state': '',
            'zip_code': '',
            'linkedin': '',
            'website': '',
            'summary': '',
            'skills': [],
            'experience': [],
            'education': [],
            'certifications': [],
            'languages': [],
            'raw_text': text,
            'confidence_score': 10.0
        }

async def main():
    """Test function"""
    parser = ResumeParser()
    
    # Test with sample text
    sample_resume = """
    John Doe
    john.doe@example.com
    (555) 123-4567
    123 Main St, San Francisco, CA 94105
    https://linkedin.com/in/johndoe
    
    SUMMARY
    Experienced software engineer with 5 years of experience in web development.
    
    SKILLS
    Python, JavaScript, React, Node.js, SQL, AWS, Docker
    
    EXPERIENCE
    Software Engineer - Tech Corp (2020-2023)
    - Developed web applications using React and Node.js
    - Managed AWS infrastructure
    
    EDUCATION
    BS Computer Science - UC Berkeley (2020)
    """
    
    result = await parser.parse_resume(sample_resume)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
