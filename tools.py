from agents import function_tool
import ddgs as DDGS


# ---------------- Study Tools ----------------

@function_tool
def generate_flashcards(topic: str, text: str, count: int = 10):
    """Generate study flashcards from text (Q/A style)."""
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    cards = []
    for i in range(min(count, len(sentences))):
        q = f"What is described by: \"{sentences[i][:80]}...\"?"
        a = sentences[i]
        cards.append({"q": q, "a": a})
    return {"flashcards": cards}


@function_tool
def generate_quiz(topic: str, text: str, num_questions: int = 5):
    """Create multiple-choice quiz from text."""
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    if not sentences:
        return {"quiz": []}
    quiz = []
    for i in range(min(num_questions, len(sentences))):
        correct = sentences[i]
        options = list({correct} | set(sentences[max(0, i-2):i+2]))
        quiz.append({"q": f"Question on {topic}", "options": options, "answer": correct})
    return {"quiz": quiz}


@function_tool
def make_notes(title: str, text: str):
    """Summarize text into short bullet notes."""
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    bullets = sentences[:10]
    return {"notes": f"# {title}\n" + "\n- " + "\n- ".join(bullets)}


@function_tool
def explain_in_language(query: str, text: str, language: str = "en"):
    """Explain a topic from text in English or Urdu."""
    if language.startswith("ur"):
        return {"explanation": f"(Urdu) {query} ka jawab yeh hai: ..."}
    else:
        return {"explanation": f"(English) Simple explanation of {query}: ..."}



# ---------------- Study Tools ----------------
@function_tool
def web_search(query: str) -> str:
    """Fetch latest info from DuckDuckGo search."""
    try:
        with DDGS() as ddgs:
            results = [r["body"] for r in ddgs.text(query, max_results=3)]
        return "\n".join(results)
    except Exception as e:
        return f"❌ Web search failed: {e}"
