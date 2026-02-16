import os
import json
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models.embedder import get_embedding, get_similarity_score
from extractor.pdf_parser import extract_chunks_from_pdf
from extractor.section_grouper import group_chunks_into_sections
from processor.summarizer import summarize_with_ollama, build_prompt
from utils.json_output import build_output_json
from database import db, User, Document, AnalysisResult
import pyttsx3
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///document_analyzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create database tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Authentication routes
@app.route('/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    remember = data.get('remember', False)
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    login_user(user, remember=remember)
    return jsonify({'success': True, 'redirect': '/dashboard'})

@app.route('/signup', methods=['GET'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Create new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html')

@app.route('/settings', methods=['POST'])
@login_required
def settings_post():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    # Check if username or email is taken by another user
    if username != current_user.username:
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 400
    
    if email != current_user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
    
    # Update basic info
    current_user.username = username
    current_user.email = email
    
    # Update password if provided
    if current_password and new_password:
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        current_user.set_password(new_password)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/user')
@login_required
def get_user_data():
    # Get user documents
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).limit(10).all()
    
    # Calculate stats
    total_docs = Document.query.filter_by(user_id=current_user.id).count()
    this_month = Document.query.filter_by(user_id=current_user.id).filter(
        Document.uploaded_at >= datetime.now().replace(day=1)
    ).count()
    total_pages = db.session.query(db.func.sum(Document.page_count)).filter_by(user_id=current_user.id).scalar() or 0
    
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'stats': {
            'total_documents': total_docs,
            'this_month': this_month,
            'total_pages': total_pages
        },
        'history': [doc.to_dict() for doc in documents]
    })

@app.route('/api/document/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    
    # Delete file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except:
        pass
    
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/analyze', methods=['GET'])
@login_required
def analyze():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@login_required
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
    
    # Save uploaded files and create database records
    uploaded_files = []
    saved_documents = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
            file.save(filepath)
            uploaded_files.append({'filename': filename, 'title': filename.rsplit('.', 1)[0]})
            
            # Create document record
            doc = Document(
                user_id=current_user.id,
                filename=f"{current_user.id}_{filename}",
                original_filename=filename,
                file_path=filepath,
                persona=persona,
                job_task=job_task
            )
            db.session.add(doc)
            saved_documents.append(doc)
    
    if not uploaded_files:
        flash('No valid PDF files uploaded')
        return redirect(url_for('index'))
    
    # Commit documents to database
    db.session.commit()
    
    # Process the documents
    try:
        results = process_documents(uploaded_files, persona, job_task, current_user.id)
        
        # Save analysis results to database
        for idx, result in enumerate(results):
            analysis = AnalysisResult(
                document_id=saved_documents[0].id,  # Associate with first document
                section_title=result.get('title', f'Section {idx+1}'),
                section_text=result.get('content', ''),
                relevance_score=result.get('score', 0.0),
                summary=result.get('summary', '')
            )
            db.session.add(analysis)
        
        # Update page count with actual section count
        total_sections = len(results)
        for doc in saved_documents:
            doc.page_count = total_sections
        
        db.session.commit()
        
        return render_template('results.html', 
                             results=results, 
                             persona=persona, 
                             job_task=job_task,
                             documents=[f['filename'] for f in uploaded_files])
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing documents: {str(e)}')
        return redirect(url_for('index'))

def process_documents(documents, persona, job_task, user_id):
    """Process uploaded documents and return results"""
    
    # Create query embedding
    query_embedding = get_embedding(persona + " " + job_task)
    
    # Extract chunks from all documents
    all_chunks = []
    for doc in documents:
        filename = doc["filename"]
        # Use the user-specific filename
        path = os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_{filename}")
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

@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    """Generate speech from text using pyttsx3"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 150)  # Speed
        engine.setProperty('volume', 0.9)  # Volume
        
        # Create temporary file for audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        audio_path = temp_file.name
        temp_file.close()
        
        # Save speech to file
        engine.save_to_file(text, audio_path)
        engine.runAndWait()
        
        # Send audio file
        return send_file(audio_path, mimetype='audio/wav', as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8000, use_reloader=False)
