import os
import json
from models.embedder import get_embedding, get_similarity_score
from extractor.pdf_parser import extract_chunks_from_pdf
from extractor.section_grouper import group_chunks_into_sections
from processor.summarizer import summarize_with_ollama, build_prompt
from utils.json_output import build_output_json, save_json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Use absolute paths based on current script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON_PATH = os.path.join(SCRIPT_DIR, "input", "input.json")
PDF_FOLDER = os.path.join(SCRIPT_DIR, "assets", "Testing PDFs", "PDF Set 1")
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "output")
OUTPUT_FILE_PATH = os.path.join(OUTPUT_FOLDER, "final_output.json")

def run_pipeline_from_json(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    persona = input_data["persona"]["role"]
    job = input_data["job_to_be_done"]["task"]
    query_embedding = get_embedding(persona + " " + job)

    all_chunks = []
    for doc in input_data["documents"]:
        filename = doc["filename"]
        path = os.path.join(PDF_FOLDER, filename)
        chunks = extract_chunks_from_pdf(path)
        for chunk in chunks:
            chunk["document"] = filename
        all_chunks.extend(chunks)

    sections = group_chunks_into_sections(all_chunks)

    for section in sections:
        section_embedding = get_embedding(section["title"] + " " + section["content"])
        section["score"] = get_similarity_score(query_embedding, section_embedding)

    # Top 5 most relevant sections
    ranked = sorted(sections, key=lambda x: x["score"], reverse=True)[:5]

    # Generate summary for each
    for sec in ranked:
        prompt = build_prompt(sec, persona, job)
        summary = summarize_with_ollama(prompt)
        sec["summary"] = summary

    # Build final output with summaries included
    final_json = build_output_json(input_data, ranked)

    # Save output JSON
    save_json(final_json, OUTPUT_FILE_PATH)
    print(f"\n Final output saved to: {OUTPUT_FILE_PATH}")

if __name__ == "__main__":
    run_pipeline_from_json(INPUT_JSON_PATH)
