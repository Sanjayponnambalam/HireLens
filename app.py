import os
import logging
from flask import Flask, render_template, request, jsonify
import spacy
from werkzeug.utils import secure_filename
import tempfile
import uuid

from resume_parser import extract_text, extract_info
from analyzer import extract_skills
from job_matcher import match_job_description, predict_job_role

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except Exception as e:
    logger.error(f"Error loading spaCy model: {str(e)}")
    # Fallback to downloading the model if not present
    logger.info("Attempting to download spaCy model...")
    import subprocess
    try:
        subprocess.run([
            "python", "-m", "spacy", "download", "en_core_web_sm"
        ], check=True)
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model downloaded and loaded successfully")
    except Exception as download_error:
        logger.error(f"Failed to download spaCy model: {str(download_error)}")
        nlp = None


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not supported. Please upload a PDF or DOCX file.'}), 400
    
    try:
        # Save file temporarily with unique name
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        temp_filename = f"{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(filepath)
        logger.debug(f"Saved file to {filepath}")
        
        # Get job description if provided
        job_description = request.form.get('job_description', '')
        
        # Extract text from resume
        text = extract_text(filepath, file_extension)
        if not text:
            return jsonify({'error': 'Could not extract text from the resume'}), 400
        
        # Process the text with spaCy
        doc = nlp(text)
        
        # Extract structured information
        info = extract_info(doc, text)
        
        # Extract skills
        skills_data = extract_skills(doc, text)
        
        # Match against job description
        job_match = {}
        job_role_prediction = {}
        if job_description:
            job_match = match_job_description(text, job_description, skills_data['skills'])
            job_role_prediction = predict_job_role(text, skills_data['skills'])
        else:
            job_role_prediction = predict_job_role(text, skills_data['skills'])
        
        # Clean up the temporary file
        os.remove(filepath)
        
        # Prepare response
        response = {
            'personal_info': info,
            'skills': skills_data,
            'job_match': job_match,
            'job_role_prediction': job_role_prediction
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error during resume analysis: {str(e)}", exc_info=True)
        return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
