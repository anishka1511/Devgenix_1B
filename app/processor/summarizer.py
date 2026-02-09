import ollama

def summarize_with_ollama(prompt, model="llama3.2:1b"):
    """
    Uses the lightweight llama3.2:1b model from Ollama for local summarization.
    Returns a summary generated from the given prompt.
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.7}
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"[SUMMARY ERROR: {str(e)}]"

def build_prompt(section, persona, job):
    """
    Builds a focused summarization prompt using persona and job-to-be-done context.
    """
    return f"""You are helping a {persona} whose task is: {job}

Here is a relevant section from a document:

Title: {section['title']}
Page: {section['page']}

Content:
{section['content']}

Give a concise, relevant summary (3-5 sentences) focused on what helps accomplish the task.
"""
