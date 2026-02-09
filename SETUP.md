# Setup Instructions

## Prerequisites
1. **Python 3.10+** installed
2. **Ollama** installed - [Download here](https://ollama.com/download)

## Installation Steps

### 1. Install Python Dependencies
```bash
cd app
pip install -r requirements.txt
```

### 2. Install Ollama Model
```bash
ollama pull phi
```

### 3. Prepare Your Documents
- Place your PDF files in `app/input/` folder
- Update `app/input/input.json` with:
  - List of PDF filenames
  - Persona (role)
  - Job to be done (task)

### 4. Run the Pipeline
```bash
cd app
python main.py
```

### 5. Check Output
Results will be saved in `app/output/final_output.json`

## Example input.json Structure
```json
{
  "documents": [
    {
      "filename": "document1.pdf",
      "title": "Document 1"
    }
  ],
  "persona": {
    "role": "History Teacher"
  },
  "job_to_be_done": {
    "task": "Tell me about France."
  }
}
```

## How It Works
1. Reads job specifications from `input.json`
2. Extracts text and structure from PDFs using PyMuPDF
3. Groups content into sections with headings
4. Ranks sections by relevance using semantic embeddings
5. Summarizes top 5 sections using Phi-2 (via Ollama)
6. Outputs structured JSON with relevant sections
