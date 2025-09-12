# Cycle Backend API

A production-ready FastAPI service that powers an offline-first bicycle rental platform. Built with FastAPI, Neon/Postgres, PostGIS, and Redis workers.

## Features

- **Email-based Authentication** with JWT tokens
- **PostGIS Integration** for spatial queries (docks, zones)
- **M-Pesa Integration** for payments (sandbox)
- **Expo Push Notifications** for mobile apps
- **Offline-first Architecture** with client sync
- **Background Workers** with Celery + Redis
- **Analytics & Event Tracking**
- **Admin Dashboard APIs**
- **Comprehensive Testing**

## Tech Stack

- **Python 3.11+**
- **FastAPI + Uvicorn**
- **SQLModel + SQLAlchemy**
- **PostgreSQL + PostGIS** (via Neon)
- **Redis** (Celery broker + caching)
- **Alembic** (database migrations)
- **Celery** (background tasks)
- **Docker** (containerization)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL with PostGIS extension

### Local Development

1. **Clone and setup:**
```bash
git clone <repository>
cd server
cp env.example .env
# Edit .env with your configuration
```

2. **Start services:**
```bash
docker-compose up -d
```

3. **Run migrations:**
```bash
alembic upgrade head
```

4. **Start the API:**
```bash
uvicorn app.main:app --reload
```

5. **Start workers:**
```bash
celery -A app.worker.celery worker --loglevel=info
```

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@192.168.100.6:5432/cycle

# Redis
REDIS_URL=redis://192.168.100.6:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key

# M-Pesa (sandbox)
MPESA_CONSUMER_KEY=your-key
MPESA_CONSUMER_SECRET=your-secret
MPESA_PASSKEY=your-passkey

# Expo Push
EXPO_ACCESS_TOKEN=your-token
```

## API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Current user profile

### Bikes & Rentals
- `GET /bikes` - List available bikes
- `POST /owner/bikes` - Add bike (owner)
- `POST /rides/start` - Start ride
- `POST /rides/end` - End ride

### Payments
- `POST /payments/mpesa/stk` - Initiate M-Pesa payment
- `POST /webhooks/mpesa` - M-Pesa webhook

### Admin
- `GET /admin/analytics/dau` - Daily active users
- `PATCH /admin/users/{id}/policy` - Update user policies
- `POST /admin/payouts/{id}/approve` - Approve payouts

## Database Schema

The API uses PostgreSQL with PostGIS for spatial data:

- **users** - User accounts and verification
- **bikes** - Bike inventory and ownership
- **docks** - Physical dock locations (PostGIS points)
- **zones** - Service areas (PostGIS polygons)
- **rentals** - Ride records with pricing snapshots
- **payments** - Payment tracking
- **events** - Analytics event sink
- **notifications** - Push notification queue

## Key Features

### Offline-First Design
- Clients can start rides offline
- Server accepts client timestamps with validation
- Idempotency keys prevent duplicate records

### Pricing Protection
- `minute_rate_snapshot` captured at ride start
- Admin price changes don't affect active rides
- Policy constraints (min/max hourly rates)

### Spatial Queries
- PostGIS integration for dock proximity
- Zone-based service areas
- GPS path tracking

### Background Processing
- Celery workers for notifications
- M-Pesa webhook processing
- Analytics aggregation

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## Deployment

### Docker
```bash
docker build -t cycle-api .
docker run -p 8000:8000 cycle-api
```

### Production Considerations
- Use environment-specific configs
- Enable Sentry monitoring
- Configure proper CORS origins
- Set up database connection pooling
- Scale workers based on load

## Development

### Code Style
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Endpoints
1. Create schema in `app/schemas/`
2. Add model in `app/models/` (if needed)
3. Create router in `app/routers/`
4. Include router in `app/main.py`
5. Add tests

## Monitoring & Observability

- **Prometheus metrics** at `/metrics`
- **Sentry integration** for error tracking
- **Structured logging** with request IDs
- **Health checks** at `/health`

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

[Your License Here]

## Support

For questions or issues, please open a GitHub issue or contact the development team.
