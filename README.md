# AI Legal Aid System

A voice-enabled legal guidance system for underserved populations, providing first-level legal guidance through accessible voice interfaces while maintaining clear boundaries about professional legal counsel requirements.

## Overview

The AI Legal Aid System combines speech recognition, natural language processing, legal knowledge bases, and resource directories to deliver accessible legal information to users who may have limited literacy or visual impairments. The system prioritizes accessibility, privacy, and reliability while ensuring users understand the distinction between AI guidance and professional legal counsel.

## Features

- **Voice Interface**: Speech-to-text and text-to-speech capabilities with multi-language support
- **Legal Guidance**: AI-powered guidance for common legal issues (tenant rights, wage theft, domestic violence, land disputes)
- **Resource Directory**: Comprehensive database of legal aid organizations with geographic and specialization-based matching
- **Privacy-First**: End-to-end encryption, data anonymization, and secure session management
- **Compliance**: Built-in disclaimer management and legal advice boundary enforcement
- **Accessibility**: Designed for users with varying literacy levels and disabilities

## Architecture

The system follows a microservices architecture with distinct components:

- **Voice Interface Layer**: Speech recognition and synthesis
- **Session Management Layer**: User sessions and conversation state
- **Legal Processing Layer**: Legal guidance and reasoning
- **Resource Management Layer**: Legal aid organization data
- **Data Layer**: Encrypted storage with privacy compliance

## Technology Stack

- **Language**: Python 3.9+
- **Framework**: FastAPI for API services
- **Voice Services**: Google Cloud Speech-to-Text and Text-to-Speech
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session management
- **Testing**: pytest with Hypothesis for property-based testing
- **Code Quality**: Black, flake8, mypy, isort
- **Security**: Cryptography library for encryption

## Quick Start

### Prerequisites

- Python 3.9 or higher
- PostgreSQL (for production)
- Redis (for session management)
- Google Cloud account (for voice services)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ai-legal-aid/ai-legal-aid.git
cd ai-legal-aid
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make install-dev
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run tests to verify installation:
```bash
make test
```

6. Start the application:
```bash
make run
```

## Development

### Project Structure

```
src/ai_legal_aid/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── types/                   # Data models and type definitions
│   ├── __init__.py
│   ├── base.py             # Enums and basic types
│   └── models.py           # Pydantic data models
└── interfaces/             # Protocol definitions
    ├── __init__.py
    ├── voice.py            # Voice interface protocols
    ├── session.py          # Session management protocols
    ├── legal.py            # Legal processing protocols
    ├── resources.py        # Resource management protocols
    └── compliance.py       # Compliance protocols

tests/
├── __init__.py
├── conftest.py             # Test configuration and fixtures
├── strategies.py           # Hypothesis strategies for property testing
├── test_types.py           # Unit tests for data models
└── test_properties.py      # Property-based tests
```

### Development Workflow

1. **Setup development environment**:
```bash
make dev-setup
```

2. **Run tests**:
```bash
make test                   # All tests
make test-unit             # Unit tests only
make test-property         # Property-based tests only
make test-coverage         # Tests with coverage report
```

3. **Code quality checks**:
```bash
make format                # Format code with black and isort
make lint                  # Run flake8 linting
make type-check           # Run mypy type checking
make quality              # Run all quality checks
```

4. **Pre-commit hooks**:
```bash
pre-commit install         # Install git hooks
pre-commit run --all-files # Run hooks on all files
```

### Testing Strategy

The project uses a dual testing approach:

- **Unit Tests**: Test specific examples, edge cases, and component integration
- **Property-Based Tests**: Use Hypothesis to verify universal properties across all possible inputs

Property tests validate correctness properties from the design document:
- Data integrity and serialization
- Privacy compliance
- Multi-language support consistency
- Legal guidance appropriateness
- Resource referral completeness

### Code Quality Standards

- **Formatting**: Black with 88-character line length
- **Import Sorting**: isort with Black profile
- **Linting**: flake8 with docstring conventions
- **Type Checking**: mypy with strict settings
- **Test Coverage**: Minimum 90% coverage for core components

## Configuration

The system uses environment variables for configuration. Key settings include:

- `DEBUG`: Enable debug mode
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud service account key
- `ENCRYPTION_KEY`: 32-character key for data encryption
- `SESSION_TIMEOUT`: Session timeout in seconds

See `.env.example` for a complete list of configuration options.

## Legal and Compliance

This system is designed to provide **informational guidance only** and explicitly:

- Does not provide legal advice
- Requires clear disclaimers for all interactions
- Maintains strict boundaries about professional legal counsel
- Implements privacy-first data handling
- Provides audit trails for compliance

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code quality standards
4. Add tests for new functionality
5. Run the full test suite (`make ci-test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation at [docs/](docs/)
- Review the design document at [.kiro/specs/ai-legal-aid/design.md](.kiro/specs/ai-legal-aid/design.md)

## Acknowledgments

- Legal aid organizations providing guidance on requirements
- Open source community for foundational tools
- Accessibility advocates for inclusive design principles