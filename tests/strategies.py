"""
Hypothesis strategies for property-based testing.

This module provides custom Hypothesis strategies for generating
test data for the AI Legal Aid System components.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from ai_legal_aid.types import (
    SessionId,
    LegalIssueType,
    UrgencyLevel,
    ComplexityLevel,
    ContactMethod,
    DocumentType,
    IncomeRange,
    Location,
    UserContext,
    LegalIssue,
    Address,
    OperatingHours,
    ContactInfo,
    GeographicArea,
    LegalAidOrganization,
    Session,
)


# Basic type strategies
@st.composite
def session_ids(draw) -> SessionId:
    """Generate valid session IDs."""
    prefix = draw(st.sampled_from(["session", "sess", "s"]))
    suffix = draw(st.integers(min_value=1, max_value=999999))
    return SessionId(f"{prefix}-{suffix}")


@st.composite
def coordinates(draw) -> dict:
    """Generate valid latitude/longitude coordinates."""
    latitude = draw(st.floats(min_value=-90.0, max_value=90.0))
    longitude = draw(st.floats(min_value=-180.0, max_value=180.0))
    return {"latitude": latitude, "longitude": longitude}


@st.composite
def locations(draw) -> Location:
    """Generate valid Location objects."""
    state = draw(
        st.sampled_from(["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"])
    )
    county = draw(st.one_of(st.none(), st.text(min_size=3, max_size=20)))
    zip_code = draw(
        st.one_of(
            st.none(),
            st.text(
                min_size=5,
                max_size=10,
                alphabet=st.characters(whitelist_categories=("Nd",)),
            ),
        )
    )
    coords = draw(st.one_of(st.none(), coordinates()))

    return Location(state=state, county=county, zip_code=zip_code, coordinates=coords)


@st.composite
def user_contexts(draw) -> UserContext:
    """Generate valid UserContext objects."""
    location = draw(st.one_of(st.none(), locations()))
    preferred_language = draw(st.sampled_from(["en", "es", "fr", "de"]))
    legal_issue_type = draw(st.one_of(st.none(), st.sampled_from(LegalIssueType)))
    urgency_level = draw(st.one_of(st.none(), st.sampled_from(UrgencyLevel)))
    has_minor_children = draw(st.one_of(st.none(), st.booleans()))
    household_income = draw(st.one_of(st.none(), st.sampled_from(IncomeRange)))

    return UserContext(
        location=location,
        preferred_language=preferred_language,
        legal_issue_type=legal_issue_type,
        urgency_level=urgency_level,
        has_minor_children=has_minor_children,
        household_income=household_income,
    )


@st.composite
def legal_issues(draw) -> LegalIssue:
    """Generate valid LegalIssue objects."""
    issue_type = draw(st.sampled_from(LegalIssueType))
    description = draw(st.text(min_size=10, max_size=500))
    urgency = draw(st.sampled_from(UrgencyLevel))
    complexity = draw(st.sampled_from(ComplexityLevel))
    involved_parties = draw(
        st.lists(st.text(min_size=3, max_size=50), min_size=0, max_size=5)
    )
    timeframe = draw(
        st.one_of(
            st.none(),
            st.sampled_from(
                [
                    "yesterday",
                    "last week",
                    "last month",
                    "last year",
                    "ongoing",
                    "recently",
                    "a few days ago",
                ]
            ),
        )
    )
    documents = draw(st.lists(st.sampled_from(DocumentType), min_size=0, max_size=3))

    return LegalIssue(
        type=issue_type,
        description=description,
        urgency=urgency,
        complexity=complexity,
        involved_parties=involved_parties,
        timeframe=timeframe,
        documents=documents,
    )


@st.composite
def addresses(draw) -> Address:
    """Generate valid Address objects."""
    street = draw(st.text(min_size=5, max_size=100))
    city = draw(st.text(min_size=3, max_size=50))
    state = draw(
        st.sampled_from(["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"])
    )
    zip_code = draw(
        st.text(
            min_size=5,
            max_size=10,
            alphabet=st.characters(whitelist_categories=("Nd",)),
        )
    )
    country = draw(st.sampled_from(["US", "CA", "MX"]))

    return Address(
        street=street, city=city, state=state, zip_code=zip_code, country=country
    )


@st.composite
def operating_hours(draw) -> OperatingHours:
    """Generate valid OperatingHours objects."""
    days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    hours_dict = {}

    for day in days:
        # Randomly include or exclude each day
        if draw(st.booleans()):
            open_hour = draw(st.integers(min_value=6, max_value=11))
            close_hour = draw(st.integers(min_value=15, max_value=20))
            hours_dict[day] = {
                "open": f"{open_hour:02d}:00",
                "close": f"{close_hour:02d}:00",
            }

    notes = draw(
        st.one_of(
            st.none(),
            st.sampled_from(
                [
                    "Closed on holidays",
                    "By appointment only",
                    "Limited weekend hours",
                    "Call ahead",
                ]
            ),
        )
    )

    return OperatingHours(notes=notes, **hours_dict)


@st.composite
def contact_infos(draw) -> ContactInfo:
    """Generate valid ContactInfo objects."""
    phone = draw(
        st.text(
            min_size=10,
            max_size=15,
            alphabet=st.characters(whitelist_categories=("Nd", "Pd")),
        )
    )
    email = draw(st.one_of(st.none(), st.emails()))
    address = draw(addresses())
    website = draw(
        st.one_of(
            st.none(),
            st.text(min_size=10, max_size=50).map(lambda x: f"https://www.{x}.org"),
        )
    )
    intake_hours = draw(operating_hours())

    return ContactInfo(
        phone=phone,
        email=email,
        address=address,
        website=website,
        intake_hours=intake_hours,
    )


@st.composite
def geographic_areas(draw) -> GeographicArea:
    """Generate valid GeographicArea objects."""
    states = draw(
        st.lists(
            st.sampled_from(
                ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
            ),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    counties = draw(
        st.one_of(
            st.none(),
            st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=5),
        )
    )
    zip_codes = draw(
        st.one_of(
            st.none(),
            st.lists(
                st.text(
                    min_size=5,
                    max_size=5,
                    alphabet=st.characters(whitelist_categories=("Nd",)),
                ),
                min_size=1,
                max_size=10,
            ),
        )
    )
    radius = draw(st.one_of(st.none(), st.floats(min_value=1.0, max_value=100.0)))

    return GeographicArea(
        states=states, counties=counties, zip_codes=zip_codes, radius=radius
    )


@st.composite
def legal_aid_organizations(draw) -> LegalAidOrganization:
    """Generate valid LegalAidOrganization objects."""
    org_id = draw(
        st.text(
            min_size=5,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd")),
        )
    )
    name = draw(st.text(min_size=10, max_size=100))
    contact_info = draw(contact_infos())
    specializations = draw(
        st.lists(st.sampled_from(LegalIssueType), min_size=1, max_size=3, unique=True)
    )
    service_area = draw(geographic_areas())
    languages = draw(
        st.lists(
            st.sampled_from(["en", "es", "fr", "de", "zh", "ar"]),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    availability = draw(operating_hours())
    eligibility_requirements = draw(
        st.lists(st.text(min_size=10, max_size=100), min_size=0, max_size=3)
    )

    return LegalAidOrganization(
        id=org_id,
        name=name,
        contact_info=contact_info,
        specializations=specializations,
        service_area=service_area,
        languages=languages,
        availability=availability,
        eligibility_requirements=eligibility_requirements,
    )


@st.composite
def sessions(draw) -> Session:
    """Generate valid Session objects."""
    session_id = draw(session_ids())
    # Use fixed base time to avoid flaky datetime generation
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    start_time = draw(
        st.datetimes(
            min_value=base_time,
            max_value=base_time + timedelta(hours=1),
            timezones=st.none(),  # Use naive datetimes to avoid timezone issues
        )
    )
    last_activity = draw(
        st.datetimes(
            min_value=start_time,
            max_value=start_time + timedelta(hours=2),
            timezones=st.none(),  # Use naive datetimes to avoid timezone issues
        )
    )

    # Generate user context first, then match session language to it
    user_context = draw(user_contexts())
    language = user_context.preferred_language  # Ensure consistency

    disclaimer_acknowledged = draw(st.booleans())

    return Session(
        id=session_id,
        start_time=start_time,
        last_activity=last_activity,
        language=language,
        conversation_history=[],  # Keep empty for simplicity
        user_context=user_context,
        disclaimer_acknowledged=disclaimer_acknowledged,
    )


# Voice interface strategies
@st.composite
def speech_inputs(draw) -> str:
    """Generate realistic speech input text."""
    templates = [
        "I have a problem with my {subject}",
        "My {subject} is {action} and I need help",
        "Can you help me with {subject}?",
        "I'm having trouble with my {subject}",
        "What should I do about my {subject}?",
    ]

    subjects = [
        "landlord",
        "employer",
        "neighbor",
        "lease",
        "wages",
        "eviction notice",
        "work contract",
        "property dispute",
    ]

    actions = [
        "not paying me",
        "threatening me",
        "refusing to fix things",
        "violating our agreement",
        "being unfair",
        "discriminating",
    ]

    template = draw(st.sampled_from(templates))
    subject = draw(st.sampled_from(subjects))
    action = draw(st.sampled_from(actions))

    return template.format(subject=subject, action=action)


@st.composite
def audio_quality_levels(draw) -> float:
    """Generate audio quality confidence scores."""
    return draw(st.floats(min_value=0.0, max_value=1.0))


@st.composite
def language_codes(draw) -> str:
    """Generate supported language codes."""
    return draw(st.sampled_from(["en", "es", "en-US", "es-MX", "es-ES"]))


# Legal processing strategies
@st.composite
def legal_queries(draw) -> str:
    """Generate realistic legal queries."""
    issue_templates = {
        LegalIssueType.TENANT_RIGHTS: [
            "My landlord won't fix the {problem}",
            "I received an eviction notice for {reason}",
            "My rent was increased by {amount}",
            "The landlord is entering my apartment without permission",
        ],
        LegalIssueType.WAGE_THEFT: [
            "My employer hasn't paid me for {timeframe}",
            "I'm not getting overtime pay",
            "My boss is deducting money from my paycheck for {reason}",
            "I was fired after asking for my wages",
        ],
        LegalIssueType.DOMESTIC_VIOLENCE: [
            "I need help getting away from an abusive {relationship}",
            "Someone is threatening me and my {family}",
            "I need a restraining order",
            "I'm afraid for my safety",
        ],
        LegalIssueType.LAND_DISPUTE: [
            "My neighbor is building on my property",
            "There's a dispute about property boundaries",
            "Someone is claiming ownership of my land",
            "I have a problem with an easement",
        ],
    }

    issue_type = draw(st.sampled_from(list(LegalIssueType)))
    if issue_type in issue_templates:
        template = draw(st.sampled_from(issue_templates[issue_type]))

        # Fill in template variables
        replacements = {
            "problem": draw(
                st.sampled_from(["heating", "plumbing", "roof", "windows"])
            ),
            "reason": draw(
                st.sampled_from(["no reason", "late rent", "noise complaints"])
            ),
            "amount": draw(st.sampled_from(["$100", "$200", "$500", "50%"])),
            "timeframe": draw(
                st.sampled_from(["two weeks", "a month", "three months"])
            ),
            "relationship": draw(
                st.sampled_from(["partner", "spouse", "ex-boyfriend"])
            ),
            "family": draw(st.sampled_from(["children", "family", "kids"])),
        }

        for key, value in replacements.items():
            template = template.replace(f"{{{key}}}", value)

        return template
    else:
        # Generate a basic legal query for OTHER type
        return draw(
            st.sampled_from(
                [
                    "I need legal help with my situation",
                    "Can you help me understand my rights",
                    "I have a legal problem and need advice",
                    "What should I do about this legal issue",
                    "I need to know my legal options",
                ]
            )
        )


# Export commonly used strategies
common_strategies = {
    "session_ids": session_ids,
    "locations": locations,
    "user_contexts": user_contexts,
    "legal_issues": legal_issues,
    "legal_aid_organizations": legal_aid_organizations,
    "sessions": sessions,
    "speech_inputs": speech_inputs,
    "legal_queries": legal_queries,
}
