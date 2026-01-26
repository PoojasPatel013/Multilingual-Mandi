#!/usr/bin/env python3
"""
Debug script to understand conversation flow and resource generation.
"""

import asyncio
from ai_legal_aid.conversation_engine import BasicConversationEngine
from ai_legal_aid.legal_guidance_engine import BasicLegalGuidanceEngine
from ai_legal_aid.resource_directory import BasicResourceDirectory
from ai_legal_aid.disclaimer_service import BasicDisclaimerService
from ai_legal_aid.session_manager import InMemorySessionManager
from ai_legal_aid.types import UserContext, Location

async def debug_conversation_flow():
    """Debug the full conversation flow."""
    
    # Create components
    session_manager = InMemorySessionManager()
    legal_engine = BasicLegalGuidanceEngine()
    resource_directory = BasicResourceDirectory()
    disclaimer_service = BasicDisclaimerService()
    
    conversation_engine = BasicConversationEngine(
        session_manager=session_manager,
        legal_guidance_engine=legal_engine,
        resource_directory=resource_directory,
        disclaimer_service=disclaimer_service
    )
    
    # Create a session
    session_id = await session_manager.create_session()
    session = await session_manager.get_session(session_id)
    
    # Set user context with location
    session.user_context = UserContext(
        location=Location(state="CA", county="Los Angeles", zip_code="90012"),
        preferred_language="en"
    )
    await session_manager.update_session(session_id, {"user_context": session.user_context})
    
    # Acknowledge disclaimer
    print("Acknowledging initial disclaimer...")
    await disclaimer_service.record_disclaimer_acknowledgment(session_id, "initial")
    
    print("Acknowledging high-risk disclaimer...")
    await disclaimer_service.record_disclaimer_acknowledgment(session_id, "high_risk")
    
    # Check if acknowledgment was recorded
    has_acknowledged_initial = disclaimer_service._has_acknowledged_disclaimer(session_id, "initial")
    has_acknowledged_high_risk = disclaimer_service._has_acknowledged_disclaimer(session_id, "high_risk")
    print(f"Initial disclaimer acknowledged: {has_acknowledged_initial}")
    print(f"High-risk disclaimer acknowledged: {has_acknowledged_high_risk}")
    
    # Also check the session state
    session = await session_manager.get_session(session_id)
    print(f"Session disclaimer_acknowledged: {session.disclaimer_acknowledged}")
    
    print("Processing user input: 'I am in immediate danger from my partner'")
    
    # Check disclaimer state before processing
    session = await session_manager.get_session(session_id)
    from ai_legal_aid.types import ConversationContext
    context = ConversationContext(
        session=session,
        current_turn=len(session.conversation_history) + 1,
        last_user_input="I am in immediate danger from my partner",
        pending_questions=[],
        conversation_length=len(session.conversation_history)
    )
    should_show = disclaimer_service.should_show_disclaimer(context)
    print(f"Should show disclaimer: {should_show}")
    print(f"Conversation length: {context.conversation_length}")
    print(f"Legal issue type: {context.session.user_context.legal_issue_type}")
    
    # Check high-risk situation
    is_high_risk = disclaimer_service._is_high_risk_situation(context)
    print(f"Is high risk situation: {is_high_risk}")
    
    # Process the input
    response = await conversation_engine.process_user_input(
        session_id, "I am in immediate danger from my partner"
    )
    
    print(f"Response text: {response.text[:200]}...")
    print(f"Requires disclaimer: {response.requires_disclaimer}")
    print(f"Number of resources: {len(response.resources)}")
    print(f"Number of suggested actions: {len(response.suggested_actions)}")
    print(f"Follow-up questions: {response.follow_up_questions}")
    
    if response.resources:
        print("\nResources:")
        for i, resource in enumerate(response.resources, 1):
            print(f"  {i}. {resource.organization.name}")
            print(f"     Phone: {resource.organization.contact_info.phone}")
            print(f"     Relevance: {resource.relevance_score:.2f}")
    else:
        print("\nNo resources generated - debugging...")
        
        # Let's manually check what should happen
        query = "I need to sue my landlord for not returning my deposit"
        issue_type = await legal_engine.classify_legal_issue(query)
        print(f"Issue type: {issue_type}")
        
        # Create a legal issue manually
        from ai_legal_aid.types import LegalIssue, UrgencyLevel, ComplexityLevel
        issue = LegalIssue(
            type=issue_type,
            description=query,
            urgency=UrgencyLevel.MEDIUM,
            complexity=await legal_engine.assess_complexity(LegalIssue(
                type=issue_type,
                description=query,
                urgency=UrgencyLevel.MEDIUM,
                complexity=ComplexityLevel.SIMPLE,
                involved_parties=[],
                documents=[]
            )),
            involved_parties=[],
            documents=[]
        )
        
        guidance = await legal_engine.generate_guidance(issue, session.user_context)
        print(f"Recommends professional help: {guidance.recommends_professional_help}")
        
        if guidance.recommends_professional_help:
            from ai_legal_aid.types import SearchCriteria
            search_criteria = SearchCriteria(
                location=session.user_context.location,
                issue_type=issue.type,
                language=session.user_context.preferred_language,
                urgency=issue.urgency
            )
            
            resources = await resource_directory.generate_referrals(search_criteria, max_referrals=3)
            print(f"Manual resource generation found {len(resources)} resources")
            for resource in resources:
                print(f"  - {resource.organization.name}")

if __name__ == "__main__":
    asyncio.run(debug_conversation_flow())