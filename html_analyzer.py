#!/usr/bin/env python3
"""
HTML Analyzer for Adaptive Job Application Bot
Analyzes website HTML structure to identify job application elements and navigation paths.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
import asyncio
from urllib.parse import urljoin, urlparse

from llm_integration import LLMIntegration

@dataclass
class ElementInfo:
    """Information about a detected HTML element"""
    tag: str
    selector: str
    text: str
    attributes: Dict[str, str]
    element_type: str  # button, input, link, form, etc.
    confidence: float
    action_potential: str  # apply, navigate, form_field, etc.

@dataclass
class NavigationPath:
    """Represents a potential navigation path"""
    steps: List[ElementInfo]
    confidence: float
    description: str
    obstacles: List[str]

@dataclass
class HTMLAnalysisResult:
    """Complete analysis result of HTML structure"""
    page_type: str  # job_listing, application_form, company_page, etc.
    apply_buttons: List[ElementInfo]
    form_fields: List[ElementInfo]
    navigation_links: List[ElementInfo]
    potential_paths: List[NavigationPath]
    obstacles: List[str]
    confidence_score: float
    recommendations: List[str]

class HTMLAnalyzer:
    """Main HTML analysis class"""
    
    def __init__(self, llm_integration: Optional[LLMIntegration] = None):
        self.logger = logging.getLogger(__name__)
        self.llm = llm_integration
        
        # Patterns for different element types
        self.apply_button_patterns = [
            r'apply\s*(now|for|to)?',
            r'submit\s*application',
            r'quick\s*apply',
            r'easy\s*apply',
            r'one\s*click\s*apply',
            r'apply\s*online'
        ]
        
        self.form_field_patterns = {
            'name': [r'name', r'full.?name', r'first.?name', r'last.?name'],
            'email': [r'email', r'e.?mail'],
            'phone': [r'phone', r'telephone', r'mobile', r'contact'],
            'resume': [r'resume', r'cv', r'upload', r'file'],
            'cover_letter': [r'cover.?letter', r'message', r'additional.?info'],
            'experience': [r'experience', r'years', r'background'],
            'salary': [r'salary', r'compensation', r'pay', r'wage']
        }
        
        self.navigation_patterns = [
            r'careers?',
            r'jobs?',
            r'employment',
            r'opportunities',
            r'work\s*with\s*us',
            r'join\s*(us|our\s*team)',
            r'hiring'
        ]
    
    async def analyze_html(self, html_content: str, base_url: str = "") -> HTMLAnalysisResult:
        """Main method to analyze HTML content"""
        try:
            self.logger.info("Starting HTML analysis")
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Basic analysis with heuristics
            heuristic_result = await self._analyze_with_heuristics(soup, base_url)
            
            # Enhanced analysis with LLM if available
            if self.llm:
                llm_result = await self._analyze_with_llm(html_content, base_url)
                final_result = self._combine_analysis_results(heuristic_result, llm_result)
            else:
                final_result = heuristic_result
            
            self.logger.info(f"HTML analysis completed with confidence: {final_result.confidence_score}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing HTML: {e}")
            return self._create_fallback_result()
    
    async def _analyze_with_heuristics(self, soup: BeautifulSoup, base_url: str) -> HTMLAnalysisResult:
        """Analyze HTML using rule-based heuristics"""
        try:
            # Detect page type
            page_type = self._detect_page_type(soup)
            
            # Find apply buttons
            apply_buttons = self._find_apply_buttons(soup)
            
            # Find form fields
            form_fields = self._find_form_fields(soup)
            
            # Find navigation links
            nav_links = self._find_navigation_links(soup, base_url)
            
            # Generate potential navigation paths
            potential_paths = self._generate_navigation_paths(apply_buttons, form_fields, nav_links)
            
            # Detect obstacles
            obstacles = self._detect_obstacles(soup)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(apply_buttons, form_fields, obstacles)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(apply_buttons, form_fields, page_type)
            
            return HTMLAnalysisResult(
                page_type=page_type,
                apply_buttons=apply_buttons,
                form_fields=form_fields,
                navigation_links=nav_links,
                potential_paths=potential_paths,
                obstacles=obstacles,
                confidence_score=confidence,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error in heuristic analysis: {e}")
            return self._create_fallback_result()
    
    def _detect_page_type(self, soup: BeautifulSoup) -> str:
        """Detect the type of page based on content"""
        try:
            # Check for forms (likely application page)
            forms = soup.find_all('form')
            if forms:
                # Check if forms contain job application fields
                for form in forms:
                    form_text = form.get_text().lower()
                    if any(pattern in form_text for pattern in ['resume', 'apply', 'application', 'cv']):
                        return 'application_form'
            
            # Check for job listing indicators
            page_text = soup.get_text().lower()
            
            if any(pattern in page_text for pattern in ['job description', 'responsibilities', 'requirements', 'qualifications']):
                return 'job_listing'
            
            if any(pattern in page_text for pattern in ['careers', 'jobs', 'employment opportunities']):
                return 'careers_page'
            
            if any(pattern in page_text for pattern in ['about us', 'company', 'our team']):
                return 'company_page'
            
            if any(pattern in page_text for pattern in ['login', 'sign in', 'account']):
                return 'login_page'
            
            if any(pattern in page_text for pattern in ['thank you', 'application submitted', 'success']):
                return 'success_page'
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error detecting page type: {e}")
            return 'unknown'
    
    def _find_apply_buttons(self, soup: BeautifulSoup) -> List[ElementInfo]:
        """Find all potential apply buttons"""
        apply_buttons = []
        
        try:
            # Search in buttons and links
            elements = soup.find_all(['button', 'a', 'input'])
            
            for element in elements:
                element_text = element.get_text().lower().strip()
                element_attrs = element.attrs
                
                # Check text content
                is_apply_button = any(
                    re.search(pattern, element_text, re.IGNORECASE)
                    for pattern in self.apply_button_patterns
                )
                
                # Check attributes
                if not is_apply_button:
                    attr_text = ' '.join([
                        str(element_attrs.get('class', '')),
                        str(element_attrs.get('id', '')),
                        str(element_attrs.get('data-testid', '')),
                        str(element_attrs.get('aria-label', ''))
                    ]).lower()
                    
                    is_apply_button = any(
                        re.search(pattern, attr_text, re.IGNORECASE)
                        for pattern in self.apply_button_patterns
                    )
                
                if is_apply_button:
                    selector = self._generate_selector(element)
                    confidence = self._calculate_element_confidence(element, 'apply_button')
                    
                    apply_buttons.append(ElementInfo(
                        tag=element.name,
                        selector=selector,
                        text=element_text,
                        attributes=element_attrs,
                        element_type='apply_button',
                        confidence=confidence,
                        action_potential='apply'
                    ))
            
            # Sort by confidence
            apply_buttons.sort(key=lambda x: x.confidence, reverse=True)
            return apply_buttons[:10]  # Return top 10
            
        except Exception as e:
            self.logger.error(f"Error finding apply buttons: {e}")
            return []
    
    def _find_form_fields(self, soup: BeautifulSoup) -> List[ElementInfo]:
        """Find all form fields that might be relevant for job applications"""
        form_fields = []
        
        try:
            # Find all input elements
            inputs = soup.find_all(['input', 'textarea', 'select'])
            
            for input_elem in inputs:
                input_attrs = input_elem.attrs
                input_type = input_attrs.get('type', 'text').lower()
                
                # Skip hidden and submit inputs
                if input_type in ['hidden', 'submit', 'button']:
                    continue
                
                # Determine field type
                field_type = self._classify_form_field(input_elem)
                
                if field_type != 'unknown':
                    selector = self._generate_selector(input_elem)
                    confidence = self._calculate_element_confidence(input_elem, 'form_field')
                    
                    form_fields.append(ElementInfo(
                        tag=input_elem.name,
                        selector=selector,
                        text=input_elem.get_text().strip(),
                        attributes=input_attrs,
                        element_type=field_type,
                        confidence=confidence,
                        action_potential='form_field'
                    ))
            
            return form_fields
            
        except Exception as e:
            self.logger.error(f"Error finding form fields: {e}")
            return []
    
    def _classify_form_field(self, element: Tag) -> str:
        """Classify the type of form field"""
        try:
            attrs = element.attrs
            
            # Check attributes for field type hints
            attr_text = ' '.join([
                str(attrs.get('name', '')),
                str(attrs.get('id', '')),
                str(attrs.get('placeholder', '')),
                str(attrs.get('aria-label', '')),
                str(attrs.get('class', ''))
            ]).lower()
            
            # Check surrounding text (labels)
            label_text = ""
            if element.parent:
                label_text = element.parent.get_text().lower()
            
            combined_text = f"{attr_text} {label_text}"
            
            # Classify based on patterns
            for field_type, patterns in self.form_field_patterns.items():
                if any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in patterns):
                    return field_type
            
            # Check input type
            input_type = attrs.get('type', '').lower()
            if input_type == 'email':
                return 'email'
            elif input_type == 'tel':
                return 'phone'
            elif input_type == 'file':
                return 'resume'
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error classifying form field: {e}")
            return 'unknown'
    
    def _find_navigation_links(self, soup: BeautifulSoup, base_url: str) -> List[ElementInfo]:
        """Find navigation links that might lead to job applications"""
        nav_links = []
        
        try:
            links = soup.find_all('a', href=True)
            
            for link in links:
                link_text = link.get_text().lower().strip()
                href = link['href']
                
                # Check if link text matches navigation patterns
                is_nav_link = any(
                    re.search(pattern, link_text, re.IGNORECASE)
                    for pattern in self.navigation_patterns
                )
                
                if is_nav_link:
                    # Convert relative URLs to absolute
                    if base_url and not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    
                    selector = self._generate_selector(link)
                    confidence = self._calculate_element_confidence(link, 'navigation')
                    
                    nav_links.append(ElementInfo(
                        tag=link.name,
                        selector=selector,
                        text=link_text,
                        attributes={'href': href},
                        element_type='navigation_link',
                        confidence=confidence,
                        action_potential='navigate'
                    ))
            
            return nav_links
            
        except Exception as e:
            self.logger.error(f"Error finding navigation links: {e}")
            return []
    
    def _generate_selector(self, element: Tag) -> str:
        """Generate CSS selector for an element"""
        try:
            # Try ID first
            if element.get('id'):
                return f"#{element['id']}"
            
            # Try class
            if element.get('class'):
                classes = ' '.join(element['class'])
                return f".{classes.replace(' ', '.')}"
            
            # Try data attributes
            for attr in element.attrs:
                if attr.startswith('data-testid'):
                    return f"[{attr}='{element[attr]}']"
            
            # Fallback to tag with attributes
            attrs = []
            for key, value in element.attrs.items():
                if key in ['name', 'type']:
                    attrs.append(f"[{key}='{value}']")
            
            selector = element.name
            if attrs:
                selector += ''.join(attrs)
            
            return selector
            
        except Exception as e:
            self.logger.error(f"Error generating selector: {e}")
            return element.name
    
    def _calculate_element_confidence(self, element: Tag, element_type: str) -> float:
        """Calculate confidence score for an element"""
        try:
            confidence = 50.0  # Base confidence
            
            # Boost for specific attributes
            if element.get('id'):
                confidence += 20
            if element.get('class'):
                confidence += 15
            if element.get('data-testid'):
                confidence += 25
            
            # Boost for relevant text content
            text = element.get_text().lower()
            if element_type == 'apply_button':
                if 'apply' in text:
                    confidence += 30
                if 'now' in text or 'quick' in text:
                    confidence += 10
            
            # Boost for form fields with proper labels
            if element_type == 'form_field':
                if element.get('required'):
                    confidence += 15
                if element.get('placeholder'):
                    confidence += 10
            
            return min(100.0, confidence)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 50.0
    
    def _generate_navigation_paths(self, apply_buttons: List[ElementInfo], 
                                 form_fields: List[ElementInfo], 
                                 nav_links: List[ElementInfo]) -> List[NavigationPath]:
        """Generate potential navigation paths to complete job application"""
        paths = []
        
        try:
            # Path 1: Direct apply button
            if apply_buttons:
                for button in apply_buttons[:3]:  # Top 3 buttons
                    steps = [button]
                    if form_fields:
                        steps.extend(form_fields[:5])  # Add top 5 form fields
                    
                    paths.append(NavigationPath(
                        steps=steps,
                        confidence=button.confidence,
                        description=f"Direct application via {button.text}",
                        obstacles=[]
                    ))
            
            # Path 2: Navigate then apply
            if nav_links and apply_buttons:
                for nav_link in nav_links[:2]:  # Top 2 nav links
                    for button in apply_buttons[:2]:  # Top 2 buttons
                        steps = [nav_link, button]
                        if form_fields:
                            steps.extend(form_fields[:3])
                        
                        paths.append(NavigationPath(
                            steps=steps,
                            confidence=(nav_link.confidence + button.confidence) / 2,
                            description=f"Navigate via {nav_link.text} then apply",
                            obstacles=['page_navigation_required']
                        ))
            
            # Sort by confidence
            paths.sort(key=lambda x: x.confidence, reverse=True)
            return paths[:5]  # Return top 5 paths
            
        except Exception as e:
            self.logger.error(f"Error generating navigation paths: {e}")
            return []
    
    def _detect_obstacles(self, soup: BeautifulSoup) -> List[str]:
        """Detect potential obstacles in the HTML"""
        obstacles = []
        
        try:
            page_text = soup.get_text().lower()
            
            # Check for login requirements
            if any(keyword in page_text for keyword in ['sign in', 'login', 'account required']):
                obstacles.append('login_required')
            
            # Check for CAPTCHA
            if any(keyword in page_text for keyword in ['captcha', 'recaptcha', 'verify you are human']):
                obstacles.append('captcha')
            
            # Check for bot detection
            if any(keyword in page_text for keyword in ['access denied', 'blocked', 'suspicious activity']):
                obstacles.append('bot_detection')
            
            # Check for premium/paid requirements
            if any(keyword in page_text for keyword in ['premium', 'subscription', 'upgrade required']):
                obstacles.append('premium_required')
            
            # Check for complex forms
            forms = soup.find_all('form')
            for form in forms:
                inputs = form.find_all(['input', 'textarea', 'select'])
                if len(inputs) > 10:
                    obstacles.append('complex_form')
                    break
            
            return obstacles
            
        except Exception as e:
            self.logger.error(f"Error detecting obstacles: {e}")
            return []
    
    def _generate_recommendations(self, apply_buttons: List[ElementInfo], 
                                form_fields: List[ElementInfo], 
                                obstacles: List[str]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        try:
            if not apply_buttons:
                recommendations.append("No apply buttons found - may need to navigate to different page")
            elif len(apply_buttons) > 1:
                recommendations.append(f"Multiple apply options found - prioritize highest confidence button")
            
            if form_fields:
                recommendations.append(f"Found {len(form_fields)} form fields - prepare resume data for auto-fill")
            
            if 'login_required' in obstacles:
                recommendations.append("Login required - ensure credentials are available")
            
            if 'captcha' in obstacles:
                recommendations.append("CAPTCHA detected - may require manual intervention")
            
            if 'complex_form' in obstacles:
                recommendations.append("Complex form detected - allow extra time for completion")
            
            if not obstacles:
                recommendations.append("No major obstacles detected - straightforward application process expected")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _calculate_confidence_score(self, apply_buttons: List[ElementInfo], 
                                  form_fields: List[ElementInfo], 
                                  page_type: str) -> float:
        """Calculate overall confidence score for the analysis"""
        try:
            base_score = 30.0
            
            # Page type bonus
            if page_type in ['application_form', 'job_listing']:
                base_score += 30
            elif page_type in ['careers_page']:
                base_score += 20
            
            # Apply buttons bonus
            if apply_buttons:
                avg_button_confidence = sum(btn.confidence for btn in apply_buttons) / len(apply_buttons)
                base_score += avg_button_confidence * 0.3
            
            # Form fields bonus
            if form_fields:
                base_score += min(20, len(form_fields) * 2)
            
            return min(100.0, base_score)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {e}")
            return 50.0
    
    async def _analyze_with_llm(self, html_content: str, base_url: str) -> HTMLAnalysisResult:
        """Analyze HTML using LLM intelligence"""
        try:
            # Create analysis prompt
            prompt = self._create_html_analysis_prompt(html_content)
            
            # Get LLM response
            response = await self.llm._call_llm(prompt)
            
            # Parse response
            return self._parse_llm_html_analysis(response)
            
        except Exception as e:
            self.logger.error(f"Error in LLM HTML analysis: {e}")
            return self._create_fallback_result()
    
    def _create_html_analysis_prompt(self, html_content: str) -> str:
        """Create prompt for LLM HTML analysis"""
        # Clean and truncate HTML for LLM
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        clean_html = str(soup)[:4000]  # Limit size
        
        return f"""
Analyze this HTML content for job application automation:

HTML CONTENT:
{clean_html}

Identify and analyze:
1. Page type (job_listing, application_form, careers_page, etc.)
2. Apply buttons (text, selectors, confidence)
3. Form fields for job applications (name, email, resume upload, etc.)
4. Navigation links to job application pages
5. Potential obstacles (login required, CAPTCHA, etc.)
6. Recommended automation approach

Provide response in JSON format:
{{
    "page_type": "application_form",
    "apply_buttons": [
        {{
            "selector": "#apply-btn",
            "text": "Apply Now",
            "confidence": 90
        }}
    ],
    "form_fields": [
        {{
            "selector": "#email",
            "field_type": "email",
            "required": true
        }}
    ],
    "obstacles": ["login_required"],
    "confidence_score": 85,
    "recommendations": ["Prepare login credentials", "Have resume file ready"]
}}
"""
    
    def _parse_llm_html_analysis(self, response: str) -> HTMLAnalysisResult:
        """Parse LLM response into HTMLAnalysisResult"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Convert to ElementInfo objects
                apply_buttons = []
                for btn_data in data.get('apply_buttons', []):
                    apply_buttons.append(ElementInfo(
                        tag='button',
                        selector=btn_data.get('selector', ''),
                        text=btn_data.get('text', ''),
                        attributes={},
                        element_type='apply_button',
                        confidence=btn_data.get('confidence', 50),
                        action_potential='apply'
                    ))
                
                form_fields = []
                for field_data in data.get('form_fields', []):
                    form_fields.append(ElementInfo(
                        tag='input',
                        selector=field_data.get('selector', ''),
                        text='',
                        attributes={'required': field_data.get('required', False)},
                        element_type=field_data.get('field_type', 'unknown'),
                        confidence=70,
                        action_potential='form_field'
                    ))
                
                return HTMLAnalysisResult(
                    page_type=data.get('page_type', 'unknown'),
                    apply_buttons=apply_buttons,
                    form_fields=form_fields,
                    navigation_links=[],
                    potential_paths=[],
                    obstacles=data.get('obstacles', []),
                    confidence_score=data.get('confidence_score', 50),
                    recommendations=data.get('recommendations', [])
                )
            
            return self._create_fallback_result()
            
        except Exception as e:
            self.logger.error(f"Error parsing LLM HTML analysis: {e}")
            return self._create_fallback_result()
    
    def _combine_analysis_results(self, heuristic: HTMLAnalysisResult, llm: HTMLAnalysisResult) -> HTMLAnalysisResult:
        """Combine heuristic and LLM analysis results"""
        try:
            # Use heuristic as base and enhance with LLM insights
            combined = heuristic
            
            # Merge apply buttons (prioritize higher confidence)
            all_buttons = heuristic.apply_buttons + llm.apply_buttons
            combined.apply_buttons = sorted(all_buttons, key=lambda x: x.confidence, reverse=True)[:5]
            
            # Merge form fields
            all_fields = heuristic.form_fields + llm.form_fields
            combined.form_fields = all_fields[:10]
            
            # Merge obstacles
            combined.obstacles = list(set(heuristic.obstacles + llm.obstacles))
            
            # Merge recommendations
            combined.recommendations = list(set(heuristic.recommendations + llm.recommendations))
            
            # Average confidence scores
            combined.confidence_score = (heuristic.confidence_score + llm.confidence_score) / 2
            
            return combined
            
        except Exception as e:
            self.logger.error(f"Error combining analysis results: {e}")
            return heuristic
    
    def _create_fallback_result(self) -> HTMLAnalysisResult:
        """Create fallback result when analysis fails"""
        return HTMLAnalysisResult(
            page_type='unknown',
            apply_buttons=[],
            form_fields=[],
            navigation_links=[],
            potential_paths=[],
            obstacles=['analysis_failed'],
            confidence_score=10.0,
            recommendations=['Manual inspection required']
        )

async def main():
    """Test function"""
    analyzer = HTMLAnalyzer()
    
    # Test HTML
    test_html = """
    <html>
        <body>
            <h1>Software Engineer Position</h1>
            <div class="job-description">
                <p>We are looking for a talented software engineer...</p>
            </div>
            <form id="application-form">
                <input type="text" name="full_name" placeholder="Full Name" required>
                <input type="email" name="email" placeholder="Email Address" required>
                <input type="tel" name="phone" placeholder="Phone Number">
                <input type="file" name="resume" accept=".pdf,.doc,.docx">
                <textarea name="cover_letter" placeholder="Cover Letter"></textarea>
                <button type="submit" class="apply-btn">Apply Now</button>
            </form>
        </body>
    </html>
    """
    
    result = await analyzer.analyze_html(test_html)
    print(f"Page Type: {result.page_type}")
    print(f"Apply Buttons: {len(result.apply_buttons)}")
    print(f"Form Fields: {len(result.form_fields)}")
    print(f"Confidence: {result.confidence_score}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
