# Intelligent Document Analyzer  
*Find what matters. Fast.*  

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/Ollama-Phi--2-success?style=flat-square"/>
  <img src="https://img.shields.io/badge/Embeddings-BGE--Small-lightgrey?style=flat-square"/>
  <img src="https://img.shields.io/badge/Offline-Compatible-critical?style=flat-square"/>
</p>

## Overview
Manually skimming through long PDFs is painful. Our solution?  
An intelligent analyzer that extracts the most relevant sections from documents — based on the user's role and goal.

Tailored.  
Fast.  
Fully offline.

Built for hackathons, research teams, and real-world applications where time, resources, and patience are limited.  

## Features
- 🎤 **Speech-to-Text (STT)**: Voice input for persona and task fields using Web Speech API
- 🔊 **Text-to-Speech (TTS)**: Listen to AI-generated summaries with play/pause/resume controls
- 📄 Smart PDF parsing with heading detection (`TITLE`, `H1`, `H2`, `PARAGRAPH`)
- 🔍 Local embeddings via `bge-small` for semantic search
- 🤖 Local summarization with `phi-2` via Ollama
- 📊 Web interface with drag-and-drop PDF upload
- ⚡ Outputs structured `.json` with top-ranked chunks + summaries
- 🔒 Fully offline compatible

## How It Works
1. **Upload PDFs** via drag-and-drop web interface
2. **Voice input** (optional): Use microphone buttons to speak your role and task
3. **PDF Processing**: Parses documents and identifies structure using font & layout heuristics
4. **Semantic Search**: Chunks and embeds content using `bge-small`
5. **Relevance Scoring**: Scores sections based on user's persona and job-to-be-done
6. **AI Summarization**: Generates summaries for top 5 sections using `phi-2`
7. **Voice Output** (optional): Listen to summaries with play/pause/resume controls
8. **Results**: View structured results with relevance scores and metadata

Input example:
```json
{
  "documents": [
    {"filename": "example.pdf", "title": "Example PDF"}
  ],
  "persona": {"role": "Travel Planner"},
  "job_to_be_done": {"task": "Plan a trip to the South of France"}
}
```

Output example:
```json
[
  {
    "document": "example.pdf",
    "page": 3,
    "title": "Cuisine",
    "score": 0.91,
    "summary": "The South of France is known for its seafood..."
  }
]
```

## Setup Instructions

1. Clone the repo  
   ```bash
   git clone https://github.com/your-username/document-analyzer.git
   cd document-analyzer/app
   ```

2. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama and pull the phi model  
   ```bash
   ollama pull phi
   ```

4. Run the web application  
   ```bash
   python app.py
   ```

5. Open your browser to `http://127.0.0.1:8000` and start uploading PDFs

## Using Voice Features

### Speech-to-Text (STT)
- Click the 🎤 microphone button next to any input field
- Grant microphone permission when prompted
- Speak your input (e.g., "History Teacher" or "Tell me about France")
- Text will automatically populate the field

### Text-to-Speech (TTS)
- **Individual summaries**: Click the 🔊 speaker button on any result card
- **Play/Pause**: Click ⏸️ while playing to pause, ▶️ to resume
- **Play all**: Use the "Play All Results" button to hear all summaries in sequence
- Works in Chrome, Edge, and Safari (Web Speech API)

## Tech Stack
| Layer             | Tool              |
|-------------------|-------------------|
| Language          | Python 3.10       |
| Web Framework     | Flask             |
| PDF Parsing       | PyMuPDF           |
| Embedding         | `bge-small`       |
| Summarization     | `phi-2` via Ollama|
| Speech-to-Text    | Web Speech API    |
| Text-to-Speech    | Web Speech API + pyttsx3 |
| Runtime           | Local / Docker    |

## Use Cases
- Travel Planning Assistants
- Education Summarizers
- Business Analysts
- Research Content Extraction
- Legal Document Review
- HR Resume Screening
