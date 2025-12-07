# Shared Infrastructure

## Purpose
Common code, configurations, and infrastructure used across all projects.

## Components

### Database (`/database`)
- **Schemas**: PostgreSQL table definitions
- **Migrations**: Database migration scripts
- **Seeds**: Initial data loading
- **Models**: Shared data models/types

### Docker (`/docker`)
- **docker-compose.yml**: PostgreSQL + pgVector + pgAdmin
- **Dockerfiles**: Container definitions for services
- **Configuration**: Database connection configs

### Utils (`/utils`)
- **Common Functions**: Shared utility code
- **API Clients**: Scryfall, EDHREC API wrappers
- **Data Processing**: Common data transformation functions
- **Logging**: Shared logging configuration

### Docs (`/docs`)
- Overall architecture documentation
- Database schema documentation
- Development setup guides
- Contribution guidelines

## What Goes Here
- Code used by 2+ projects
- Database schemas (used by all projects)
- Docker infrastructure (runs for all projects)
- Common utilities (API clients, parsers, validators)

## What Doesn't Go Here
- Project-specific logic
- Project-specific tests
- Application code

## Current Files to Migrate
- `/docker-compose.yml` → `/shared/docker/`
- `/sql/schemas/*` → `/shared/database/schemas/`
- `/sql/migrations/*` → `/shared/database/migrations/`
- Common utils from `/scripts/` → `/shared/utils/`
