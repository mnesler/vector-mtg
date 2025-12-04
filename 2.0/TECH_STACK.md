# Technology Stack - MTG Planeswalker AI 2.0

## Backend (Agent Service)

### Core Framework
- **FastAPI** (Python 3.11+)
  - Async/await support
  - WebSocket support
  - OpenAPI docs auto-generation
  - High performance

### LLM Integration
- **LangChain** (0.1.0+)
  - Agent framework
  - Tool calling
  - Memory management
  - OR **LiteLLM** (simpler, provider-agnostic)

### LLM Providers (Choose One or Hybrid)
- **OpenAI** - GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic** - Claude 3 (Opus, Sonnet, Haiku)
- **Local** - Llama 3.1, Phi-3.5 (already loaded)
- **Hybrid** - Mix of above

### Authentication
- **Authlib** (OAuth 2.0 client library)
- **PyJWT** (JWT token handling)
- **Passlib** (password hashing, if needed)

### Database
- **PostgreSQL** 14+ (existing)
- **pgvector** (existing - for embeddings)
- **psycopg2** / **asyncpg** (database drivers)
- **Alembic** (database migrations)

### Caching
- **Redis** (optional - session caching, rate limiting)
- OR in-memory caching with **functools.lru_cache**

### WebSocket
- **FastAPI WebSockets** (built-in)
- **python-socketio** (alternative)

## Frontend (UI)

### Framework
- **Next.js** 16+ (existing)
- **React** 19+ (existing)
- **TypeScript** 5+ (existing)

### Styling
- **Tailwind CSS** 4+ (existing)
- **Skeleton UI** (existing component library)

### State Management
- **React Context** (for simple state)
- **Zustand** (lightweight state management)
- OR **Redux Toolkit** (if complex state needed)

### WebSocket Client
- **native WebSocket API**
- **Socket.IO client** (if using socket.io backend)
- **react-use-websocket** (React hooks)

### Forms & Validation
- **React Hook Form**
- **Zod** (schema validation)

## Database Schema

### Tables (New for 2.0)
```
users
oauth_credentials
conversation_sessions
conversation_messages
user_decks
deck_cards
known_combos
public_deck_links
deck_analytics
```

### Existing Tables (Reuse)
```
cards (509K rows)
rules
rule_categories
card_rules
rule_interactions
```

## Development Tools

### Testing
- **pytest** (backend unit tests)
- **pytest-asyncio** (async tests)
- **Jest** (frontend unit tests)
- **React Testing Library**
- **Playwright** (e2e tests)

### Code Quality
- **Black** (Python formatting)
- **Ruff** (Python linting)
- **ESLint** (TypeScript/React linting)
- **Prettier** (frontend formatting)

### Development
- **Docker** & **Docker Compose** (existing)
- **VSCode** / **Cursor** (IDE)
- **Git** (version control)

## Deployment

### Backend Options
1. **Local Development** (current)
2. **VPS** (DigitalOcean, Linode, Hetzner)
3. **Cloud** (AWS, GCP, Azure)
4. **PaaS** (Railway, Render, Fly.io)

### Frontend Options
1. **Vercel** (Next.js recommended)
2. **Netlify**
3. **Self-hosted** (Nginx + PM2)

### Database
- **PostgreSQL** (same as 1.0)
- **Managed** (AWS RDS, DigitalOcean, etc.)
- **Self-hosted** (existing setup)

## Monitoring & Observability

### Logging
- **structlog** (structured logging)
- **Python logging** (standard library)

### Monitoring (Optional for MVP)
- **Sentry** (error tracking)
- **DataDog** / **New Relic** (APM)
- **Grafana** + **Prometheus** (metrics)

### Analytics (Optional)
- **PostHog** (product analytics)
- **Plausible** (website analytics)

## Security

### Dependencies
- **python-decouple** (environment variables)
- **cryptography** (encryption utilities)
- **oauthlib** (OAuth helpers)

### Best Practices
- Environment variables for secrets
- HTTPS only in production
- CORS configuration
- Rate limiting (per user, per IP)
- Input validation
- SQL injection prevention (parameterized queries)
- XSS prevention (React auto-escaping)

## External Services

### Required
- **OAuth Providers** (Google, Discord, Steam)

### Optional
- **CDN** (CloudFlare)
- **Email** (SendGrid, Mailgun) - for notifications
- **File Storage** (S3) - for deck images, avatars

## Cost Estimates

### Development
- All free / open-source

### Production (Monthly, 1000 active users)
- **VPS**: $20-50/month
- **Database**: $0 (included) or $25/month (managed)
- **LLM API**: $50-200/month (depends on usage & provider)
- **Redis**: $0 (included) or $10/month (managed)
- **Monitoring**: $0-50/month (optional)
- **Total**: $70-335/month

## Performance Targets

### Backend
- Response time: <2s (non-streaming)
- First token: <500ms (streaming)
- Tool execution: <1s per tool
- Database queries: <100ms

### Frontend
- Initial page load: <2s
- Time to interactive: <3s
- WebSocket latency: <100ms
- Lighthouse score: >90

## Scalability Considerations

### Horizontal Scaling
- Stateless API (can run multiple instances)
- WebSocket sessions (sticky sessions or Redis pub/sub)
- Database connection pooling

### Vertical Scaling
- Current PostgreSQL can handle 100K+ users
- Agent service can handle 100+ concurrent chats per instance

### Caching Strategy
- Card data (99% cache hit rate)
- Combo database (100% cache hit)
- User sessions (Redis or in-memory)
- LLM responses (optional, privacy concerns)

---

**Document Status:** Complete - Ready for Review  
**Last Updated:** December 3, 2024
