from pathlib import Path
def search_docs(query):
    results = []
    for p in Path("data/sample_docs").glob("*.txt"):
        text = p.read_text(encoding="utf-8")
        if query.lower() in text.lower():
            results.append(p.name)
    return results
