import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from models.embedder import get_embedding, get_similarity_score
from extractor.pdf_parser import extract_chunks_from_pdf
from extractor.section_grouper import group_chunks_into_sections
from processor.summarizer import summarize_with_ollama, build_prompt
from utils.json_output import build_output_json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    # Check if files were uploaded
    if 'documents' not in request.files:
        flash('No files uploaded')
        return redirect(url_for('index'))
    
    files = request.files.getlist('documents')
    persona = request.form.get('persona', '').strip()
    job_task = request.form.get('job_task', '').strip()
    
    if not persona or not job_task:
        flash('Please provide both persona and job specification')
        return redirect(url_for('index'))
    
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(url_for('index'))
    
    # Clear previous uploads
    for old_file in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_file))
    
    # Save uploaded files
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append({'filename': filename, 'title': filename.rsplit('.', 1)[0]})
    
    if not uploaded_files:
        flash('No valid PDF files uploaded')
        return redirect(url_for('index'))
    
    # Process the documents
    try:
        results = process_documents(uploaded_files, persona, job_task)
        return render_template('results.html', 
                             results=results, 
                             persona=persona, 
                             job_task=job_task,
                             documents=[f['filename'] for f in uploaded_files])
    except Exception as e:
        flash(f'Error processing documents: {str(e)}')
        return redirect(url_for('index'))

def process_documents(documents, persona, job_task):
    """Process uploaded documents and return results"""
    
    # Create query embedding
    query_embedding = get_embedding(persona + " " + job_task)
    
    # Extract chunks from all documents
    all_chunks = []
    for doc in documents:
        filename = doc["filename"]
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        chunks = extract_chunks_from_pdf(path)
        for chunk in chunks:
            chunk["document"] = filename
        all_chunks.extend(chunks)
    
    if not all_chunks:
        raise Exception("No content could be extracted from the PDFs")
    
    # Group chunks into sections
    sections = group_chunks_into_sections(all_chunks)
    
    if not sections:
        raise Exception("No sections could be identified in the documents")
    
    # Score sections by relevance
    for section in sections:
        section_embedding = get_embedding(section["title"] + " " + section["content"])
        section["score"] = get_similarity_score(query_embedding, section_embedding)
    
    # Get top 5 most relevant sections
    ranked = sorted(sections, key=lambda x: x["score"], reverse=True)[:5]
    
    # Generate summaries for top sections
    for sec in ranked:
        prompt = build_prompt(sec, persona, job_task)
        summary = summarize_with_ollama(prompt)
        sec["summary"] = summary
    
    return ranked

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8000, use_reloader=False)
