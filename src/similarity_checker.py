"""
Similarity Checker — TF-IDF cosine similarity between channel scripts.
Ensures scripts across channels are different enough to avoid YouTube detection.
Max similarity threshold: 40% (0.4).
"""
import re
from typing import Dict, List, Tuple


def _simple_tokenize(text: str) -> List[str]:
    """Simple word tokenizer without external dependencies."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    words = text.split()
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
        'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'neither',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
        'their', 'we', 'our', 'you', 'your', 'he', 'she', 'his', 'her',
    }
    return [w for w in words if w not in stop_words and len(w) > 2]


def _word_overlap_similarity(text_a: str, text_b: str) -> float:
    """Calculate similarity based on word overlap ratio (simpler fallback)."""
    words_a = set(_simple_tokenize(text_a))
    words_b = set(_simple_tokenize(text_b))
    
    if not words_a or not words_b:
        return 0.0
    
    intersection = words_a & words_b
    union = words_a | words_b
    
    return len(intersection) / len(union) if union else 0.0


def check_script_similarity(scripts: Dict[str, str], threshold: float = 0.4) -> Tuple[bool, List[Tuple[str, str, float]]]:
    """
    Check similarity between all pairs of channel scripts.
    
    Args:
        scripts: dict {channel_name: script_text}
        threshold: max allowed similarity (default 0.4 = 40%)
    
    Returns:
        (all_ok, violations) where violations is list of (ch1, ch2, similarity)
    """
    violations = []
    channels = list(scripts.keys())
    
    # Try scikit-learn TF-IDF first, fall back to simple method
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        texts = [scripts[ch] for ch in channels]
        vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)
        
        for i in range(len(channels)):
            for j in range(i + 1, len(channels)):
                sim = sim_matrix[i][j]
                if sim > threshold:
                    violations.append((channels[i], channels[j], round(sim, 3)))
                    print(f"[SIMILARITY] {channels[i]} vs {channels[j]}: {sim:.1%} (OVER {threshold:.0%} threshold)")
                else:
                    print(f"[SIMILARITY] {channels[i]} vs {channels[j]}: {sim:.1%} OK")
        
    except ImportError:
        # Fallback: simple word overlap
        print("[SIMILARITY] scikit-learn not available, using word overlap method")
        for i in range(len(channels)):
            for j in range(i + 1, len(channels)):
                sim = _word_overlap_similarity(scripts[channels[i]], scripts[channels[j]])
                if sim > threshold:
                    violations.append((channels[i], channels[j], round(sim, 3)))
                    print(f"[SIMILARITY] {channels[i]} vs {channels[j]}: {sim:.1%} (OVER {threshold:.0%} threshold)")
                else:
                    print(f"[SIMILARITY] {channels[i]} vs {channels[j]}: {sim:.1%} OK")
    
    all_ok = len(violations) == 0
    if all_ok:
        print("[SIMILARITY] All scripts are sufficiently different!")
    else:
        print(f"[SIMILARITY] {len(violations)} pair(s) too similar. Need regeneration.")
    
    return all_ok, violations


def get_most_similar_channel(scripts: Dict[str, str]) -> str:
    """
    Returns the channel key whose script is most similar to others (the one to regenerate).
    """
    channels = list(scripts.keys())
    similarity_scores = {ch: 0.0 for ch in channels}
    
    for i in range(len(channels)):
        for j in range(i + 1, len(channels)):
            sim = _word_overlap_similarity(scripts[channels[i]], scripts[channels[j]])
            similarity_scores[channels[i]] += sim
            similarity_scores[channels[j]] += sim
    
    # Return channel with highest total similarity
    return max(similarity_scores, key=similarity_scores.get)
