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
- Smart PDF parsing with heading detection (`TITLE`, `H1`, `H2`, `PARAGRAPH`)
- Local embeddings via `bge-small` for semantic search
- Local summarization with `phi-2` via Ollama
- Outputs structured `.json` with top-ranked chunks + summaries
- Built to run in CPU-only Docker with `--network none`

## How It Works
1. Parses all PDFs from `/app/input/`
2. Identifies structure using font & layout heuristics
3. Chunks and embeds content using `bge-small`
4. Scores relevance based on user’s persona and job-to-be-done
5. Summarizes top chunks using `phi-2`
6. Saves `.json` results in `/app/output/`

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

## Tech Stack
| Layer        | Tool              |
|--------------|-------------------|
| Language     | Python 3.10       |
| PDF Parsing  | PyMuPDF           |
| Embedding    | `bge-small`       |
| Summarization| `phi-2` via Ollama|
| Runtime      | Docker (CPU-only) |

## Use Cases
- Travel Planning Assistants
- Education Summarizers
- Business Analysts
- Research Content Extraction
- Legal Document Review
- HR Resume Screening
