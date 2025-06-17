# 🌊 Lakebase FastAPI Databricks App.

A production-ready FastAPI application for accessing Databricks Lakebase data. Features scalable architecture, automatic token refresh, and optimized database connection management.

## ❓ Why do you need an api? 
- **Database Abstraction & Security**:  APIs prevent direct database access and provide controlled access through authenticated apps. 
- **Standardized Access Patterns**: APIs create consistent ways to interact with data across different teams and applications. 
- **Development Velocity**:   APIs reduce duplicate code in applications. Write your api logic once and let applications leverage your endpoint.
- **Performance Optimization & Caching**:  APIs leverage connection pooling, query optimization, and results caching for high performance workloads.
- **Cross Platform Capability**: Any programming language can leverage the REST protocol. 
- **Audit Trails & Monitoring**: Custom logging, request tracking, and usage analytics give visibility into data access.
- **Future Proof**:  APIs simplify switching between databases, adding new data sources, or changing infrastructure.

## 🌟 Features
- **FastAPI REST API** with async/await support
- **Databricks Lakebase Integration** with OAuth token management
- **Automatic Token Refresh** with configurable intervals
- **Production-Ready Architecture** with domain-driven design
- **Connection Pooling** with optimized settings for high-traffic scenarios
- **Environment-Based Configuration** for different deployment environments
- **Comprehensive Error Handling** and logging

## 📋 Prerequisites
- **Databricks Workspace**: Permissions to create apps and database instances
- **Database Instance** configured in Databricks
- **Python 3.11+** and uv package manager
- **Environment Variables** configured (see Configuration section)

## 🚀 Quick Start

### Local Development

1. **Clone and install dependencies:**
   ```bash
   git clone https://github.com/DoyleDev/lakebase-fastapi-app.git
   uv pip install -r requirements.txt
   uv add -r requirements.txt
   uv venv
   source .venv/bin/activate
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

1. **Databricks UI: Create Custom App:**

2. **Databricks UI: App Database Instance Permissions:**
   - Copy App Service Principal Id from App -> Authorization
   - Compute -> Database Instances -> Your Instance -> Permissions
   - Grant App Service Principal the proper permissions on your instance.
   - Grant App Service Principal permissions to the Postgres Catalog.

3. **Configure environment variables in app.yaml:**

   #### ⚙️ Configuration

   ### Required Environment Variables

   | Variable | Description | Example |
   |----------|-------------|---------|
   | `DATABRICKS_DATABASE_INSTANCE` | Database instance name | `my-database-instance` |
   | `DATABRICKS_DATABASE_NAME` | Database name | `database` |
   | `DATABRICKS_HOST` | Workspace URL (for apps) | `https://workspace.cloud.databricks.com` |
   | `DATABRICKS_TOKEN` | Access token (for local apps) | `dapi...` |
   | `DATABRICKS_CLIENT_ID` | OAuth client ID (for apps) | `app_client_id` |
   | `DEFAULT_POSTGRES_SCHEMA` | Database schema | `public` |
   | `DEFAULT_POSTGRES_TABLE` | Table name | `nyc_train_synced` |

   ### Optional Configuration

   | Variable | Default | Description |
   |----------|---------|-------------|
   | `DB_POOL_SIZE` | `5` | Connection pool size |
   | `DB_MAX_OVERFLOW` | `10` | Max overflow connections |
   | `DB_POOL_TIMEOUT` | `30` | Pool checkout timeout (seconds) |
   | `DB_COMMAND_TIMEOUT` | `10` | Query timeout (seconds) |

4. **Deploy app files using Databricks CLI:**
   ```bash
   databricks sync --watch . /Workspace/Users/<your_username>/<project_folder>
   ```
5. **Databricks UI: Deploy Application:**
   - App -> Deploy
   - Source code path = /Workspace/Users/<your_username>/<project_folder> - source code path is at the project root where app.yaml lives. 
   - View logs for successful deploy: src.main - INFO - Application startup initiated
   - View your API docs: <your_app_url>/docs


## 🏗️ Architecture

### Project Structure
```
src/
├── core/
│   └── database.py          # Database connection with automatic token refresh
├── models/
│   └── taxi.py             # Taxi trip model using sqlModel
├── routers/
│   └── taxi.py             # API endpoints
├── services/
│   └── taxi_service.py     # Business logic (optional)
└── main.py                 # FastAPI application
```

### Database Connection Strategy
**Important Note:** OAuth tokens expire after one hour, but expiration is enforced only at login. Open connections remain active even if the token expires. However, any PostgreSQL command that requires authentication fails if the token has expired.  Read More: https://docs.databricks.com/aws/en/oltp/oauth

**Automatic Token Refresh:**
- 50 Minute token refresh with background async task that does not impact requests.
- Guaranteed token refresh before expiry (safe for 1-hour token lifespans)
- Optimized for high-traffic production applications

## 📚 API Documentation

### Example Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trips/count` | GET | Get total trip count |
| `/trips/sample` | GET | Get 5 random trip IDs |
| `/trips/{trip_id}` | GET | Get trip by ID |
| `/trips/analytics` | GET | Get high level stats using services |
| `/trips/pages` | GET | Page-based pagination (traditional) |
| `/trips/stream` | GET | Cursor-based pagination (high performance) |

### Example Requests

```bash
# Get trip count
curl http://localhost:8000/trips/count

# Get specific trip
curl http://localhost:8000/trips/123

# Get paginated trips
curl "http://localhost:8000/trips/pages?page=1&page_size=10"

# Get cursor-based trips
curl "http://localhost:8000/trips/stream?cursor=0&page_size=10"
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

2. **Monitor connection pool metrics** in application logs

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
"Background token refresh: Generating fresh PostgreSQL OAuth token"
"Background token refresh: Token updated successfully"

# Performance tracking
"Request: GET /trips/123 - 8.3ms"
```

## 🚨 Troubleshooting

### Common Issues

**"Resource not found" on startup:**
- Verify `DATABRICKS_DATABASE_INSTANCE` exists in workspace
- Check database instance permissions

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