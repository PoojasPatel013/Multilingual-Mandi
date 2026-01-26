#!/usr/bin/env python3
"""
Debug disclaimer acknowledgment.
"""

def test_acknowledgment():
    acknowledgment_phrases = [
        "yes", "i understand", "i acknowledge", "i agree", "understood", "ok", "okay",
        "sí", "entiendo", "reconozco", "estoy de acuerdo", "entendido"
    ]
    
    input_text = "I acknowledge"
    input_lower = input_text.lower().strip()
    print(f"Input: '{input_text}'")
    print(f"Input lower: '{input_lower}'")
    
    # Check for negative responses first (use word boundaries to avoid false positives)
    negative_phrases = ["no", "don't", "not", "disagree", "refuse"]
    has_negative = any(f" {neg} " in f" {input_lower} " or input_lower.startswith(f"{neg} ") or input_lower.endswith(f" {neg}") or input_lower == neg for neg in negative_phrases)
    print(f"Has negative: {has_negative}")
    
    matches = []
    for phrase in acknowledgment_phrases:
        if phrase in input_lower:
            matches.append(phrase)
    
    print(f"Matches: {matches}")
    result = any(phrase in input_lower for phrase in acknowledgment_phrases)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_acknowledgment()