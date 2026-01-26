#!/usr/bin/env python3
"""
Debug script to understand professional help recommendation.
"""

import asyncio
from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine
from ai_legal_aid.types import LegalIssue, LegalIssueType, UrgencyLevel, ComplexityLevel, UserContext

async def debug_professional_help():
    """Debug professional help recommendation."""
    engine = BasicLegalGuidanceEngine()
    
    # Test the failing case
    query = "I need to sue my landlord for not returning my deposit"
    
    # Classify the issue
    issue_type = await engine.classify_legal_issue(query)
    print(f"Classified issue type: {issue_type}")
    
    # Assess complexity
    issue = LegalIssue(
        type=issue_type,
        description=query,
        urgency=UrgencyLevel.MEDIUM,
        complexity=ComplexityLevel.SIMPLE,  # This will be overridden
        involved_parties=[],
        documents=[]
    )
    
    complexity = await engine.assess_complexity(issue)
    issue.complexity = complexity
    print(f"Assessed complexity: {complexity}")
    
    # Generate guidance
    context = UserContext()
    guidance = await engine.generate_guidance(issue, context)
    
    print(f"Recommends professional help: {guidance.recommends_professional_help}")
    print(f"Summary: {guidance.summary}")
    print("Steps:")
    for i, step in enumerate(guidance.detailed_steps, 1):
        print(f"  {i}. {step}")

if __name__ == "__main__":
    asyncio.run(debug_professional_help())