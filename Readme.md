# Northwoods Housing Security Resource

A comprehensive, multi-layered housing security resource platform for Northern Michigan (The Northwoods), helping people from prevention through crisis with both formal services and alternative housing paths.

## Project Vision

This platform addresses housing insecurity at every stage - from people at risk to those in crisis - with honest, practical information about both traditional resources and unconventional paths to housing security. Built by people with lived experience for people navigating housing challenges.

## Geographic Scope

**The Northwoods Michigan Region:**
- Montmorency County (pilot)
- Alpena, Oscoda, Otsego, Crawford, Roscommon, Ogemaw, Iosco, Alcona, Presque Isle counties

## The Five-Layer Approach

1. **Layer 1: Immediate Survival** - Crisis resources (food, shelter, camping, waste disposal)
2. **Layer 2: Stabilization** - Mail services, healthcare, case management
3. **Layer 3: Cost Reduction** - SNAP, heating assistance, utility help
4. **Layer 4: Alternative Paths** - Vehicle dwelling, land ownership, off-grid living
5. **Layer 5: Prevention** - Early warning signs, risk assessment, planning

## Technology Stack

- **Backend:** Python/FastAPI
- **Database:** PostgreSQL with PostGIS (geospatial queries)
- **Hosting:** Railway
- **Frontend:** TBD (mobile-first responsive design)

## Project Structure

```
northwoods-housing/
├── app/
│   ├── __init__.py
│   ├── database.py          # Database connection and config
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas for validation
│   └── api/
│       ├── __init__.py
│       └── resources.py     # Resources API endpoints
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── database_schema.sql      # PostgreSQL schema
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- pip or poetry for dependency management

### Local Development

1. **Clone the repository**
```bash
git clone [repository-url]
cd northwoods-housing
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up database**
```bash
# Create PostgreSQL database
createdb northwoods_housing

# Enable PostGIS extension
psql northwoods_housing -c "CREATE EXTENSION postgis;"

# Run schema
psql northwoods_housing < database_schema.sql
```

5. **Set environment variables**
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/northwoods_housing"
```

6. **Run the application**
```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload
```

7. **Access the API**
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Resources

- `POST /api/resources/` - Create new resource
- `GET /api/resources/` - List resources with filtering
- `GET /api/resources/{id}` - Get specific resource
- `PUT /api/resources/{id}` - Update resource
- `DELETE /api/resources/{id}` - Soft delete resource
- `GET /api/resources/counties/list` - List all counties
- `GET /api/resources/types/list` - List all resource types

### Search/Filter Parameters

- `resource_type` - Filter by type (food, shelter, etc.)
- `county` - Filter by county
- `latitude` + `longitude` + `radius_miles` - Proximity search
- `seasonal_winter` - Only winter-available resources
- `limit` / `offset` - Pagination

## Database Schema

Key tables:
- `resources` - Core resource data with geospatial location
- `users` - User accounts with tiered access
- `verification_logs` - Tracking data freshness
- `community_reports` - User-submitted status updates
- `assessment_results` - Anonymous risk assessment data

See `database_schema.sql` for complete schema with indexes and constraints.

## Development Roadmap

### Phase 1: Foundation (Weeks 1-4) ✓ IN PROGRESS
- [x] Database schema design
- [x] Basic API structure
- [x] Resources CRUD endpoints
- [ ] Montmorency County data collection
- [ ] Railway deployment

### Phase 2: Expansion (Weeks 5-8)
- [ ] Housing security self-assessment tool
- [ ] "What happens if..." decision trees
- [ ] Winter survival content
- [ ] Expand to Alpena and Oscoda counties
- [ ] Community reporting functionality

### Phase 3: Regional Coverage (Weeks 9-16)
- [ ] All Northwoods counties documented
- [ ] Alternative housing paths content
- [ ] AI-assisted validation system
- [ ] Partnerships with local organizations
- [ ] Mobile optimization

### Phase 4: Refinement (Months 5-6)
- [ ] User feedback integration
- [ ] Offline functionality
- [ ] SMS bridge exploration
- [ ] Success stories section

## Contributing

This project welcomes contributions, especially from people with lived experience of housing insecurity. Ways to help:

- Document resources in your area
- Verify existing resources
- Share your experience (what helped, what didn't)
- Provide feedback on content
- Volunteer as regional coordinator

Contact: [To be added]

## Project Values

1. Meet people where they are - not where we think they should be
2. Dignity and agency - people are experts in their own lives
3. Honesty about barriers - system is broken, not individuals
4. Safety first - protect vulnerable people and locations
5. Community ownership - built with and for people with lived experience

## License

[To be determined]

## Acknowledgments

Built by people who understand housing insecurity isn't a personal failing but a systemic problem. This resource exists because help isn't coming from the government - we have to help each other.

---

*Last updated: November 2025*
