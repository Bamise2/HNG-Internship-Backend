import hashlib
from collections import Counter
from typing import Dict
import re

def compute_sha256(text: str) -> str:
    """Compute SHA-256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def is_palindrome(text: str) -> bool:
    """Check if string is palindrome (case-insensitive, ignoring spaces)"""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]

def count_unique_characters(text: str) -> int:
    """Count distinct characters in string"""
    return len(set(text))

def count_words(text: str) -> int:
    """Count words separated by whitespace"""
    return len(text.split())

def get_character_frequency(text: str) -> Dict[str, int]:
    """Get frequency map of each character"""
    return dict(Counter(text))

def analyze_string(value: str) -> Dict:
    """Analyze a string and return all computed properties"""
    sha256_hash = compute_sha256(value)
    
    return {
        "id": sha256_hash,
        "value": value,
        "length": len(value),
        "is_palindrome": is_palindrome(value),
        "unique_characters": count_unique_characters(value),
        "word_count": count_words(value),
        "sha256_hash": sha256_hash,
        "character_frequency_map": get_character_frequency(value)
    }

def parse_natural_language_query(query: str) -> Dict:
    """
    Parse natural language query into filter parameters
    Examples:
    - "all single word palindromic strings" -> {word_count: 1, is_palindrome: true}
    - "strings longer than 10 characters" -> {min_length: 11}
    - "strings containing the letter z" -> {contains_character: "z"}
    """
    query = query.lower()
    filters = {}
    
    # Check for palindrome
    if "palindrom" in query:
        filters["is_palindrome"] = True
    
    # Check for single word / one word
    if "single word" in query or "one word" in query:
        filters["word_count"] = 1
    
    # Check for "longer than X characters"
    length_match = re.search(r"longer than (\d+)", query)
    if length_match:
        filters["min_length"] = int(length_match.group(1)) + 1
    
    # Check for "shorter than X characters"
    length_match = re.search(r"shorter than (\d+)", query)
    if length_match:
        filters["max_length"] = int(length_match.group(1)) - 1
    
    # Check for "containing letter X" or "contain the letter X"
    letter_match = re.search(r"contain(?:ing)?(?: the)? letter ([a-z])", query)
    if letter_match:
        filters["contains_character"] = letter_match.group(1)
    
    # Check for "first vowel" -> 'a'
    if "first vowel" in query:
        filters["contains_character"] = "a"
    
    # Check for specific word count
    word_count_match = re.search(r"(\d+) words?", query)
    if word_count_match:
        filters["word_count"] = int(word_count_match.group(1))
    
    return filters