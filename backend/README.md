# Multilingual Mandi Backend

A Python FastAPI backend for the Multilingual Mandi platform - an AI-powered multilingual marketplace with real-time translation, intelligent price discovery, and culturally-aware negotiation assistance.

## Features

- **FastAPI Framework**: High-performance async API with automatic OpenAPI documentation
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **Redis Caching**: Fast caching and session management
- **Real-time Communication**: WebSocket support for instant messaging
- **AI Integration**: Translation services and price discovery algorithms
- **Property-Based Testing**: Comprehensive testing with Hypothesis
- **Docker Support**: Containerized development and deployment
- **Multi-language Support**: Built-in internationalization capabilities

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone and navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development services**:
   ```bash
   chmod +x scripts/start-dev.sh
   ./scripts/start-dev.sh
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Using Docker

1. **Start all services**:
   ```bash
   docker-compose -f ../docker-compose.backend.yml up -d
   ```

2. **View logs**:
   ```bash
   docker-compose -f ../docker-compose.backend.yml logs -f backend-dev
   ```

3. **Stop services**:
   ```bash
   docker-compose -f ../docker-compose.backend.yml down
   ```

## Testing

### Run Tests

```bash
# All tests
chmod +x scripts/run-tests.sh
./scripts/run-tests.sh

# Unit tests only
./scripts/run-tests.sh unit

# Integration tests only
./scripts/run-tests.sh integration

# Property-based tests only
./scripts/run-tests.sh property

# With coverage report
./scripts/run-tests.sh coverage

# Fast tests only (exclude slow tests)
./scripts/run-tests.sh fast
```

### Test Types

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and database operations
- **Property-Based Tests**: Test universal properties using Hypothesis
- **End-to-End Tests**: Test complete user workflows

## API Documentation

The API follows RESTful principles and includes:

- **Authentication**: JWT-based authentication with role-based access
- **User Management**: User registration, profiles, and vendor management
- **Product Management**: CRUD operations for marketplace products
- **Translation Services**: Real-time multilingual translation
- **Negotiation System**: AI-assisted price negotiation
- **Payment Processing**: Secure transaction handling
- **Real-time Communication**: WebSocket-based messaging

### Key Endpoints

- `GET /health` - Health check
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/products` - List products
- `POST /api/v1/negotiations` - Start negotiation
- `POST /api/v1/translations` - Translate text
- `WebSocket /ws/negotiations/{id}` - Real-time negotiation

## Architecture

### Core Components

- **FastAPI Application**: Main API server with async support
- **SQLAlchemy Models**: Database models with relationships
- **Redis Cache**: Session management and caching layer
- **WebSocket Manager**: Real-time communication handling
- **Translation Engine**: AI-powered multilingual translation
- **Price Discovery**: Market analysis and pricing algorithms
- **Negotiation Assistant**: Cultural context and negotiation guidance

### Database Schema

The database includes tables for:
- Users and vendor profiles
- Products and categories
- Negotiations and messages
- Transactions and payments
- Cultural profiles and translations
- Analytics and market data

### External Integrations

- **Translation APIs**: Google Cloud Translation, Azure Translator
- **Payment Gateways**: Stripe, PayPal, local payment methods
- **Market Data**: Price comparison and trend analysis
- **Cultural Context**: Region-specific business etiquette

## Configuration

### Environment Variables

Key configuration options:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_URL=redis://localhost:6379/0

# External Services
TRANSLATION_API_KEY=your-api-key
STRIPE_SECRET_KEY=your-stripe-key

# Features
SUPPORTED_LANGUAGES=en,es,fr,de,zh,hi,ar,pt,ru,ja
RATE_LIMIT_PER_MINUTE=60
```

### Docker Configuration

The application supports multiple deployment modes:
- Development with hot reload
- Production with optimized settings
- Background workers for async tasks
- Scheduled tasks with Celery Beat

## Development

### Code Style

The project uses:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **MyPy**: Type checking

```bash
# Format code
poetry run black app tests
poetry run isort app tests

# Lint code
poetry run flake8 app tests
poetry run mypy app
```

### Database Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

### Adding New Features

1. Create models in `app/models/`
2. Add API endpoints in `app/api/v1/endpoints/`
3. Write tests in `tests/`
4. Update documentation
5. Run tests and ensure coverage

## Deployment

### Production Deployment

1. **Build production image**:
   ```bash
   docker build -f Dockerfile -t multilingual-mandi-backend .
   ```

2. **Deploy with Docker Compose**:
   ```bash
   docker-compose -f ../docker-compose.backend.yml --profile production up -d
   ```

3. **Environment setup**:
   - Set production environment variables
   - Configure external services
   - Set up monitoring and logging
   - Configure SSL/TLS certificates

### Scaling

The application supports horizontal scaling:
- Multiple API server instances
- Separate worker processes for background tasks
- Redis cluster for caching
- PostgreSQL read replicas

## Monitoring

### Health Checks

- `GET /health` - Basic health status
- `GET /api/v1/health/detailed` - Detailed system health

### Metrics

The application exposes metrics for:
- Request/response times
- Database query performance
- Cache hit rates
- Translation API usage
- WebSocket connections

### Logging

Structured logging with:
- Request/response logging
- Error tracking
- Performance metrics
- Security events
- Business metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

### Code Quality

- Write comprehensive tests
- Follow type hints
- Document public APIs
- Use meaningful commit messages
- Ensure backward compatibility

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation
- Review existing issues
- Create a new issue with details
- Contact the development team

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern Python practices.