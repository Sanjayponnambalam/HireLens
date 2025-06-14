import logging
import re
import PyPDF2
import docx2txt
from spacy.tokens import Doc

logger = logging.getLogger(__name__)

def extract_text(file_path, file_extension):
    """
    Extract text content from resume files
    
    Args:
        file_path (str): Path to the resume file
        file_extension (str): File extension (pdf or docx)
        
    Returns:
        str: Extracted text from the resume
    """
    try:
        if file_extension == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension == 'docx':
            return extract_text_from_docx(file_path)
        else:
            logger.error(f"Unsupported file extension: {file_extension}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return None


def extract_text_from_pdf(file_path):
    """Extract text from PDF files"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        # If PyPDF2 fails, try with pdfminer as fallback
        try:
            from pdfminer.high_level import extract_text as extract_text_pdfminer
            text = extract_text_pdfminer(file_path)
            return text
        except Exception as e2:
            logger.error(f"Fallback extraction also failed: {str(e2)}")
            return None


def extract_text_from_docx(file_path):
    """Extract text from DOCX files"""
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return None


def extract_info(doc, text):
    """
    Extract structured information from resume
    
    Args:
        doc (spacy.tokens.Doc): spaCy Doc object of resume text
        text (str): Raw text of the resume
        
    Returns:
        dict: Structured information from resume
    """
    info = {
        'name': extract_name(doc),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'education': extract_education(doc, text),
        'experience': extract_experience(doc, text)
    }
    return info


def extract_name(doc):
    """Extract the name from the resume"""
    # Look for PERSON entities at the beginning of the document
    for ent in doc.ents:
        if ent.label_ == "PERSON" and ent.start < 50:  # Consider entities at the beginning of the doc
            return ent.text
    
    # If no name found, return the first 2-3 tokens if they're proper nouns
    potential_name_tokens = []
    for token in doc[:10]:  # Check first 10 tokens
        if token.pos_ == "PROPN":
            potential_name_tokens.append(token.text)
            if len(potential_name_tokens) >= 2:
                return " ".join(potential_name_tokens)
    
    return "Name not detected"


def extract_email(text):
    """Extract email address from resume text"""
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "Email not detected"


def extract_phone(text):
    """Extract phone number from resume text"""
    # Pattern to match various phone number formats
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    return phones[0] if phones else "Phone not detected"


def extract_education(doc, text):
    """Extract education information from resume"""
    education_keywords = ["education", "university", "college", "degree", "bachelor", "master", "phd", "diploma"]
    education_info = []
    
    # Look for education section
    lines = text.split('\n')
    is_education_section = False
    education_section_text = ""
    
    for line in lines:
        line_lower = line.lower()
        # Check if this line is an education section header
        if any(keyword in line_lower for keyword in ["education", "qualification"]) and len(line) < 50:
            is_education_section = True
            continue
            
        # End of education section if we hit another section header
        if is_education_section and line.strip() and line[0].isupper() and len(line) < 50 and all(keyword not in line_lower for keyword in education_keywords):
            next_word = line.split()[0].lower() if line.split() else ""
            if next_word in ["experience", "work", "employment", "skills", "projects"]:
                is_education_section = False
                
        if is_education_section and line.strip():
            education_section_text += line + " "
    
    # If we found an education section, extract details
    if education_section_text:
        # Look for degree names and institutions
        degree_keywords = ["bachelor", "master", "phd", "b.tech", "m.tech", "bsc", "msc", "diploma"]
        for sentence in education_section_text.split('. '):
            # Check if sentence likely contains education info
            if any(keyword in sentence.lower() for keyword in education_keywords):
                # Extract the year if present
                years = re.findall(r'\b(19|20)\d{2}\b', sentence)
                year = years[0] if years else ""
                
                # Find educational institutions (ORG entities)
                orgs = []
                doc_sentence = doc(sentence)
                for ent in doc_sentence.ents:
                    if ent.label_ == "ORG":
                        orgs.append(ent.text)
                
                institution = orgs[0] if orgs else ""
                
                # Clean and add the education entry
                entry = sentence.strip()
                if entry:
                    if institution and institution in entry:
                        education_info.append({
                            "degree": entry,
                            "institution": institution,
                            "year": year
                        })
                    else:
                        education_info.append({
                            "degree": entry,
                            "institution": institution,
                            "year": year
                        })
    
    # If no structured education info found, just return potential education text
    if not education_info and education_section_text:
        education_info.append({"description": education_section_text.strip()})
        
    return education_info


def extract_experience(doc, text):
    """Extract work experience information from resume"""
    experience_keywords = ["experience", "work", "employment", "career"]
    experience_info = []
    
    # Look for experience section
    lines = text.split('\n')
    is_experience_section = False
    current_entry = ""
    
    for line in lines:
        line_lower = line.lower()
        # Check if this line is an experience section header
        if any(keyword in line_lower for keyword in experience_keywords) and len(line) < 50:
            is_experience_section = True
            continue
            
        # End of experience section if we hit another section header
        if is_experience_section and line.strip() and line[0].isupper() and len(line) < 50:
            next_word = line.split()[0].lower() if line.split() else ""
            if next_word in ["education", "skills", "projects", "achievements"]:
                if current_entry.strip():
                    experience_info.append({"description": current_entry.strip()})
                    current_entry = ""
                is_experience_section = False
                
        # Process experience section content
        if is_experience_section:
            # Check if this line starts a new entry (company or position)
            if line.strip() and (line[0].isupper() or re.match(r'^\d{4}', line)):
                if current_entry.strip():
                    experience_info.append({"description": current_entry.strip()})
                    current_entry = ""
                current_entry = line + " "
            elif line.strip():
                current_entry += line + " "
    
    # Add the last entry if exists
    if is_experience_section and current_entry.strip():
        experience_info.append({"description": current_entry.strip()})
        
    # If no structured info found, extract sentences with work-related terms
    if not experience_info:
        work_sentences = []
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if any(keyword in sent_text.lower() for keyword in ["work", "company", "position", "job", "role"]):
                work_sentences.append(sent_text)
        
        if work_sentences:
            experience_info.append({"description": " ".join(work_sentences)})
    
    return experience_info
