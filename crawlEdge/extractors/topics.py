from collections import Counter


STOP_WORDS = {
    "about", "after", "also", "because", "been", "from", "have", "more",
    "that", "their", "there", "these", "this", "were", "when", "with",
    "your", "will", "they", "them", "then", "than", "into", "what",
    "please", "failed", "data",
}


def extract_topics(text: str, title: str, max_topics: int = 8) -> list:
    if not text:
        return [title.lower()] if title else []
    words = [
        word.strip(".,!?;:()[]{}\"'").lower()
        for word in text.split()
        if len(word.strip(".,!?;:()[]{}\"'")) > 3
    ]
    words = [word for word in words if word and word not in STOP_WORDS]
    common = Counter(words).most_common(30)
    return [word for word, _ in common[:max_topics]]
