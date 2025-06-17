# 🚕 FastAPI Taxi Data Application

A production-ready FastAPI application for accessing taxi trip data stored in Databricks SQL Warehouses. Features scalable architecture, automatic token refresh, and optimized database connection management.

## 🌟 Features

- **FastAPI REST API** with async/await support
- **Databricks SQL Warehouse Integration** with OAuth token management
- **Automatic Token Refresh** with configurable intervals
- **Production-Ready Architecture** with domain-driven design
- **Connection Pooling** with optimized settings for high-traffic scenarios
- **Environment-Based Configuration** for different deployment environments
- **Comprehensive Error Handling** and logging

## 📋 Prerequisites

- **Databricks Workspace** with SQL Warehouse access
- **Database Instance** configured in Databricks
- **Python 3.11+** and uv package manager
- **Environment Variables** configured (see Configuration section)

## 🚀 Quick Start

### Local Development

1. **Clone and install dependencies:**
   ```bash
   uv sync
   uv pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Databricks configuration
   ```

3. **Run the application:**
   ```bash
   uv run uvicorn src.main:app --reload
   ```

4. **Access the API:**
   - API: `http://localhost:8000`
   - Interactive docs: `http://localhost:8000/docs`

### Databricks Apps Deployment

1. **Deploy using Databricks CLI:**
   ```bash
   databricks bundle deploy
   ```

2. **Configure environment variables in app.yaml:**
   ```yaml
   env:
     - name: 'DATABRICKS_DATABASE_INSTANCE'
       value: 'your-database-instance-name'
     - name: 'DATABRICKS_DATABASE_NAME'  
       value: 'your-database-name'
   ```

## ⚙️ Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_DATABASE_INSTANCE` | Database instance name | `my-warehouse-instance` |
| `DATABRICKS_DATABASE_NAME` | Database name | `taxi_data` |
| `DATABRICKS_HOST` | Workspace URL (for apps) | `https://workspace.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Access token (for apps) | `dapi...` |
| `DATABRICKS_CLIENT_ID` | OAuth client ID | `token` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Max overflow connections |
| `DB_POOL_TIMEOUT` | `30` | Pool checkout timeout (seconds) |
| `DB_COMMAND_TIMEOUT` | `10` | Query timeout (seconds) |

## 🏗️ Architecture

### Project Structure
```
src/
├── core/
│   └── database.py          # Database connection with automatic token refresh
├── models/
│   ├── base.py             # SQLAlchemy base model
│   └── taxi.py             # Taxi trip model
├── routers/
│   └── taxi.py             # API endpoints
├── schemas/
│   └── taxi.py             # Pydantic schemas
├── services/
│   └── taxi_service.py     # Business logic (optional)
└── main.py                 # FastAPI application
```

### Database Connection Strategy

**Automatic Token Refresh:**
- 55-minute connection recycling with `pool_recycle=3300`
- Fresh token generation for each new connection
- Guaranteed token refresh before expiry (safe for 1-hour token lifespans)
- Optimized for high-traffic production applications

## 📚 API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trips/count` | GET | Get total trip count |
| `/trips/sample` | GET | Get 5 random trip IDs |
| `/trips/{trip_id}` | GET | Get trip by ID |

### Example Requests

```bash
# Get trip count
curl http://localhost:8000/trips/count

# Get specific trip
curl http://localhost:8000/trips/123

# Test alternative database connection
curl http://localhost:8000/trips/simple/123
```

### Response Format

```json
{
  "id": 123,
  "vendor_id": "2",
  "pickup_datetime": "2023-01-01T10:30:00",
  "dropoff_datetime": "2023-01-01T10:45:00"
}
```

## 🔧 Performance Tuning

### High-Traffic Applications

For applications handling thousands of requests per minute:

1. **Increase pool size:**
   ```env
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=50
   ```

2. **Use simple database approach** for predictable token refresh
3. **Monitor connection pool metrics** in application logs

### Token Refresh Optimization

- **Standard approach**: Best for low-medium traffic
- **Simple approach**: Best for high-traffic with predictable refresh needs
- **Custom intervals**: Adjust `pool_recycle` based on token lifespan

## 🛡️ Security

- **OAuth token rotation** prevents credential staleness
- **SSL/TLS enforcement** for all database connections
- **Environment variable isolation** for sensitive configuration
- **No credential logging** in production builds

## 📊 Monitoring

### Key Metrics to Monitor

- **Request latency** (`X-Process-Time` header)
- **Token refresh frequency** (log analysis)
- **Connection pool utilization**
- **Database query performance**

### Log Messages

```
# Token refresh events
"Refreshing PostgreSQL OAuth token via event handler"
"Simple DB: Generating fresh PostgreSQL OAuth token"

# Performance tracking
"Request: GET /trips/123 - 12.3ms"
```

## 🧪 Testing

```bash
# Run local tests
uv run pytest

# Load testing
for i in {1..100}; do curl http://localhost:8000/trips/sample; done
```

## 🚨 Troubleshooting

### Common Issues

**"Resource not found" on startup:**
- Verify `DATABRICKS_DATABASE_INSTANCE` exists in workspace
- Check database instance permissions

**High latency on first requests:**
- Expected behavior during token generation
- Monitor for "Generating fresh PostgreSQL OAuth token" logs

**Connection timeouts:**
- Increase `DB_COMMAND_TIMEOUT` for slow queries
- Check database instance performance

## 📄 License

&copy; 2025 Databricks, Inc. All rights reserved. The source in this notebook is provided subject to the [Databricks License](https://databricks.com/db-license-source).

| Library | Description | License | Source |
|---------|-------------|---------|---------|
| FastAPI | High-performance API framework | MIT | [GitHub](https://github.com/tiangolo/fastapi) |
| SQLAlchemy | SQL toolkit and ORM | MIT | [GitHub](https://github.com/sqlalchemy/sqlalchemy) |
| Databricks SDK | Official Databricks SDK | Apache 2.0 | [GitHub](https://github.com/databricks/databricks-sdk-py) |
| asyncpg | Async PostgreSQL driver | Apache 2.0 | [GitHub](https://github.com/MagicStack/asyncpg) |
| Pydantic | Data validation using Python type hints | MIT | [GitHub](https://github.com/pydantic/pydantic) |