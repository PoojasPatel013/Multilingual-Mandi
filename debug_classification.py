#!/usr/bin/env python3
"""
Debug legal issue classification.
"""

import asyncio
from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine

async def debug_classification():
    """Debug legal issue classification."""
    engine = BasicLegalGuidanceEngine()
    
    test_inputs = [
        "I have a tenant rights issue",
        "My landlord won't fix the heating",
        "tenant rights",
        "landlord problem"
    ]
    
    for input_text in test_inputs:
        issue_type = await engine.classify_legal_issue(input_text)
        print(f"'{input_text}' -> {issue_type}")

if __name__ == "__main__":
    asyncio.run(debug_classification())