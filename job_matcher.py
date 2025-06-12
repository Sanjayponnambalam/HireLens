import logging
import json
import os
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Load job roles data
JOB_ROLES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'data', 'job_roles.json')

def load_job_roles():
    try:
        if os.path.exists(JOB_ROLES_PATH):
            with open(JOB_ROLES_PATH, 'r') as f:
                return json.load(f)
        else:
            # Return default job roles data if file doesn't exist
            return {
                "job_roles": [
                    {
                        "title": "Software Engineer",
                        "keywords": ["software", "developer", "programming", "coding", "java", "python", "javascript", "c++", "algorithms", "data structures"]
                    },
                    {
                        "title": "Data Scientist",
                        "keywords": ["data science", "machine learning", "statistics", "python", "r", "ai", "deep learning", "analytics", "data mining", "big data"]
                    },
                    {
                        "title": "Web Developer",
                        "keywords": ["web", "frontend", "backend", "full-stack", "html", "css", "javascript", "react", "angular", "vue", "node.js", "php"]
                    },
                    {
                        "title": "Product Manager",
                        "keywords": ["product", "management", "agile", "scrum", "roadmap", "strategy", "user stories", "prioritization", "requirements", "stakeholders"]
                    },
                    {
                        "title": "UX/UI Designer",
                        "keywords": ["ux", "ui", "user experience", "user interface", "design", "wireframes", "prototypes", "usability", "figma", "sketch", "adobe xd"]
                    },
                    {
                        "title": "DevOps Engineer",
                        "keywords": ["devops", "ci/cd", "continuous integration", "deployment", "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform"]
                    },
                    {
                        "title": "Business Analyst",
                        "keywords": ["business analysis", "requirements", "stakeholders", "process", "documentation", "sql", "data analysis", "reporting", "visualization"]
                    },
                    {
                        "title": "Project Manager",
                        "keywords": ["project management", "pmp", "agile", "scrum", "waterfall", "budget", "timeline", "resources", "risk management", "planning"]
                    },
                    {
                        "title": "Marketing Specialist",
                        "keywords": ["marketing", "digital marketing", "seo", "sem", "social media", "content", "campaigns", "analytics", "brand", "strategy"]
                    },
                    {
                        "title": "Sales Representative",
                        "keywords": ["sales", "business development", "account management", "negotiation", "client", "customer", "crm", "pipeline", "quota", "closing"]
                    }
                ]
            }
    except Exception as e:
        logger.error(f"Error loading job roles data: {str(e)}")
        return {"job_roles": []}


def extract_keywords_from_job_description(job_description):
    """
    Extract key requirements and skills from job description
    
    Args:
        job_description (str): Job description text
        
    Returns:
        list: List of extracted keywords
    """
    # Normalize text
    job_description = job_description.lower()
    
    # Define patterns to identify requirement sections
    requirement_patterns = [
        r'requirements:.*?(?=\n\n|\Z)',
        r'qualifications:.*?(?=\n\n|\Z)',
        r'skills:.*?(?=\n\n|\Z)',
        r'what you need:.*?(?=\n\n|\Z)',
        r'what you\'ll need:.*?(?=\n\n|\Z)',
        r'required skills:.*?(?=\n\n|\Z)'
    ]
    
    # Try to extract requirement sections
    requirement_sections = []
    for pattern in requirement_patterns:
        matches = re.findall(pattern, job_description, re.DOTALL)
        requirement_sections.extend(matches)
    
    # If no specific sections found, use entire job description
    if not requirement_sections:
        requirement_sections = [job_description]
    
    # Extract potential keywords
    keywords = []
    combined_text = ' '.join(requirement_sections)
    
    # Extract skills mentioned with bullets or numbers
    bullet_skills = re.findall(r'(?:•|\*|\-|\d+\.)\s*([\w\s/+#]+)', combined_text)
    keywords.extend([skill.strip().lower() for skill in bullet_skills if skill.strip()])
    
    # Extract technical terms, programming languages, tools, etc.
    tech_terms = [
        'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'vue', 
        'node', 'express', 'django', 'flask', 'sql', 'nosql', 'aws', 'azure', 'gcp',
        'docker', 'kubernetes', 'devops', 'ci/cd', 'git', 'agile', 'scrum', 'jira',
        'machine learning', 'deep learning', 'ai', 'data science', 'tensorflow', 'pytorch',
        'ux', 'ui', 'design', 'product', 'management', 'analytics', 'marketing', 'sales'
    ]
    
    for term in tech_terms:
        if term in combined_text:
            keywords.append(term)
    
    # Extract phrases with "experience with/in"
    experience_phrases = re.findall(r'experience (?:with|in) ([\w\s/+#]+)', combined_text)
    keywords.extend([phrase.strip().lower() for phrase in experience_phrases if phrase.strip()])
    
    # Extract "familiarity with" phrases
    familiarity_phrases = re.findall(r'familiarity with ([\w\s/+#]+)', combined_text)
    keywords.extend([phrase.strip().lower() for phrase in familiarity_phrases if phrase.strip()])
    
    # Remove duplicates and very common words
    common_words = ['and', 'or', 'the', 'a', 'an', 'in', 'with', 'to']
    filtered_keywords = []
    seen = set()
    
    for keyword in keywords:
        if keyword not in seen and keyword not in common_words and len(keyword) > 2:
            filtered_keywords.append(keyword)
            seen.add(keyword)
    
    return filtered_keywords


def match_job_description(resume_text, job_description, resume_skills):
    """
    Match resume against job description
    
    Args:
        resume_text (str): Full text of the resume
        job_description (str): Job description text
        resume_skills (list): List of skills extracted from resume
        
    Returns:
        dict: Job matching results
    """
    if not job_description:
        return {
            "match_percentage": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "matched_details": []
        }
    
    # Extract keywords from job description
    job_keywords = extract_keywords_from_job_description(job_description)
    
    # Normalize resume text
    resume_text_lower = resume_text.lower()
    
    # Find matching keywords
    matched_keywords = []
    missing_keywords = []
    matched_details = []
    
    for keyword in job_keywords:
        # Check if keyword is in resume text or resume skills
        if keyword in resume_text_lower or keyword in resume_skills:
            matched_keywords.append(keyword)
            matched_details.append({
                "keyword": keyword,
                "found": True,
                "context": get_keyword_context(resume_text_lower, keyword)
            })
        else:
            missing_keywords.append(keyword)
            matched_details.append({
                "keyword": keyword,
                "found": False,
                "context": None
            })
    
    # Calculate match percentage
    total_keywords = len(job_keywords) if job_keywords else 1
    match_percentage = round((len(matched_keywords) / total_keywords) * 100)
    
    return {
        "match_percentage": match_percentage,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "matched_details": matched_details
    }


def get_keyword_context(text, keyword):
    """Get surrounding context for a keyword in text"""
    try:
        keyword_index = text.find(keyword)
        if keyword_index >= 0:
            start = max(0, keyword_index - 50)
            end = min(len(text), keyword_index + len(keyword) + 50)
            context = text[start:end]
            # Bold the keyword
            highlighted_context = context.replace(keyword, f"**{keyword}**")
            return highlighted_context
        return None
    except:
        return None


def predict_job_role(resume_text, skills):
    """
    Predict suitable job roles based on resume content
    
    Args:
        resume_text (str): Full text of the resume
        skills (list): Extracted skills from resume
        
    Returns:
        dict: Job role prediction results
    """
    job_roles = load_job_roles()["job_roles"]
    
    # Normalize text
    resume_text_lower = resume_text.lower()
    
    # Count keyword matches for each job role
    role_scores = []
    
    for role in job_roles:
        title = role["title"]
        keywords = role["keywords"]
        
        # Count matches
        matches = sum(1 for keyword in keywords if keyword in resume_text_lower or keyword in skills)
        match_percentage = round((matches / len(keywords)) * 100) if keywords else 0
        
        role_scores.append({
            "title": title,
            "score": match_percentage,
            "matched_keywords": [keyword for keyword in keywords if keyword in resume_text_lower or keyword in skills]
        })
    
    # Sort roles by score
    role_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Get top 3 roles
    top_roles = role_scores[:3]
    
    # Generate recommendations for top role
    recommendations = []
    if top_roles:
        top_role = top_roles[0]
        missing_keywords = [
            keyword for keyword in job_roles[job_roles.index(next(r for r in job_roles if r["title"] == top_role["title"]))]["keywords"]
            if keyword not in resume_text_lower and keyword not in skills
        ]
        
        if missing_keywords:
            recommendations.append(f"Consider adding skills in: {', '.join(missing_keywords[:5])}")
        
        if top_role["score"] < 50:
            recommendations.append("Your profile seems to differ from common job roles. Consider highlighting your unique skills and experience.")
    
    return {
        "top_roles": top_roles,
        "recommendations": recommendations
    }
