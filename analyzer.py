import re
import logging
import json
import os

logger = logging.getLogger(__name__)

# Load skills data
SKILLS_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'data', 'skills.json')

def load_skills_data():
    try:
        if os.path.exists(SKILLS_DATA_PATH):
            with open(SKILLS_DATA_PATH, 'r') as f:
                return json.load(f)
        else:
            # If file doesn't exist, return default skills categorization
            return {
                "technical_skills": [
                    "python", "java", "javascript", "html", "css", "react", "angular", "vue", 
                    "node.js", "express", "flask", "django", "spring", "hibernate", "sql", 
                    "mysql", "postgresql", "mongodb", "redis", "aws", "azure", "gcp", 
                    "docker", "kubernetes", "jenkins", "git", "jira", "agile", "scrum",
                    "c++", "c#", "php", "ruby", "swift", "kotlin", "rust", "golang", "scala",
                    "machine learning", "deep learning", "artificial intelligence", "data science",
                    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "hadoop", "spark",
                    "tableau", "power bi", "excel", "word", "powerpoint", "photoshop", "illustrator",
                    "figma", "sketch", "adobe xd", "ui/ux", "seo", "digital marketing"
                ],
                "soft_skills": [
                    "communication", "teamwork", "problem solving", "critical thinking", 
                    "creativity", "leadership", "time management", "adaptability", "flexibility",
                    "organization", "planning", "decision making", "conflict resolution",
                    "attention to detail", "interpersonal skills", "emotional intelligence",
                    "negotiation", "persuasion", "presentation", "public speaking", "writing",
                    "customer service", "project management", "prioritization", "self-motivated",
                    "analytical", "logical", "innovative", "patient", "reliable", "responsible"
                ],
                "certifications": [
                    "aws certified", "microsoft certified", "google certified", "comptia", 
                    "cisco certified", "pmp", "six sigma", "itil", "scrum master", "agile certified",
                    "cpa", "cfa", "ceh", "cissp", "ccna", "ccnp", "mcsa", "mcse", "rhce", "salesforce"
                ],
                "languages": [
                    "english", "spanish", "french", "german", "italian", "portuguese", "russian",
                    "chinese", "japanese", "korean", "arabic", "hindi", "dutch", "swedish", "norwegian"
                ]
            }
    except Exception as e:
        logger.error(f"Error loading skills data: {str(e)}")
        return {
            "technical_skills": [],
            "soft_skills": [],
            "certifications": [],
            "languages": []
        }

def extract_skills(doc, text):
    """
    Extract and categorize skills from resume text
    
    Args:
        doc (spacy.tokens.Doc): spaCy Doc object of resume text
        text (str): Raw text of the resume
        
    Returns:
        dict: Skills information categorized by type
    """
    skills_data = load_skills_data()
    
    # Initialize results
    extracted_skills = {
        "skills": [],
        "technical": [],
        "soft": [],
        "certifications": [],
        "languages": []
    }
    
    # Normalize text for better matching
    text_lower = text.lower()
    
    # Extract skills by category
    for skill in skills_data.get("technical_skills", []):
        skill_pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(skill_pattern, text_lower):
            extracted_skills["technical"].append(skill)
            extracted_skills["skills"].append(skill)
    
    for skill in skills_data.get("soft_skills", []):
        skill_pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(skill_pattern, text_lower):
            extracted_skills["soft"].append(skill)
            extracted_skills["skills"].append(skill)
    
    for cert in skills_data.get("certifications", []):
        cert_pattern = r'\b' + re.escape(cert) + r'\b'
        if re.search(cert_pattern, text_lower):
            extracted_skills["certifications"].append(cert)
    
    for lang in skills_data.get("languages", []):
        lang_pattern = r'\b' + re.escape(lang) + r'\b'
        if re.search(lang_pattern, text_lower):
            extracted_skills["languages"].append(lang)
    
    # Extract potential skills mentioned in skills section
    skills_section = extract_skills_section(text)
    if skills_section:
        # Split by common delimiters and clean up
        potential_skills = re.split(r'[,;•\n]', skills_section)
        for skill in potential_skills:
            skill = skill.strip().lower()
            if skill and len(skill) > 2 and skill not in extracted_skills["skills"]:
                # Only add if it's not already found and looks like a valid skill (not just a word)
                if not any(common_word == skill for common_word in ["and", "or", "the", "a", "an", "in", "on", "at", "to", "for"]):
                    extracted_skills["skills"].append(skill)
    
    # Add skills count and percentages
    total_skills = len(extracted_skills["skills"])
    extracted_skills["total_count"] = total_skills
    extracted_skills["technical_count"] = len(extracted_skills["technical"])
    extracted_skills["soft_count"] = len(extracted_skills["soft"])
    
    # Calculate percentages for visualization
    extracted_skills["technical_percentage"] = round((len(extracted_skills["technical"]) / max(1, total_skills)) * 100)
    extracted_skills["soft_percentage"] = round((len(extracted_skills["soft"]) / max(1, total_skills)) * 100)
    
    return extracted_skills


def extract_skills_section(text):
    """Extract the skills section from resume text"""
    lines = text.split('\n')
    skills_section = ""
    in_skills_section = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Check if this line indicates the start of skills section
        if (line_lower == "skills" or 
            line_lower == "technical skills" or 
            line_lower.startswith("skills:") or 
            line_lower.startswith("technical skills:") or
            "core skills" in line_lower) and len(line) < 50:
            in_skills_section = True
            continue
        
        # End skills section if we reach a new section
        if in_skills_section and line.strip() and line[0].isupper() and len(line) < 50:
            next_word = line.split()[0].lower() if line.split() else ""
            if next_word in ["experience", "education", "projects", "certifications", "languages"]:
                break
        
        # Add line to skills section if we're in it
        if in_skills_section and line.strip():
            skills_section += line + "\n"
    
    return skills_section


# Grammar & Spelling check function removed

# Readability analysis function removed
