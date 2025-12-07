# MTG Rule Engine - Next.js + TypeScript + Skeleton UI

Modern web UI for the MTG Rule Engine built with Next.js 14, TypeScript, Tailwind CSS, and Skeleton UI.

## Setup Instructions

1. **Install dependencies:**
   ```bash
   cd ui
   npm install
   ```

2. **Required dependencies** (should be in package.json):
   - next@latest
   - react@latest
   - react-dom@latest
   - typescript
   - @types/react
   - @types/node
   - @types/react-dom
   - tailwindcss
   - postcss
   - autoprefixer
   - @skeletonlabs/skeleton
   - @skeletonlabs/tw-plugin

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   npm start
   ```

## Project Structure

```
ui/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout with Skeleton UI theme
│   ├── page.tsx            # Dashboard home
│   ├── cards/              # Card Explorer pages
│   ├── rules/              # Rules Browser pages
│   └── deck/               # Deck Analyzer pages
├── components/             # React components
│   ├── ui/                 # Skeleton UI components
│   ├── CardGrid.tsx        # Card display grid
│   ├── SearchFilters.tsx   # Search and filter UI
│   └── Navigation.tsx      # App navigation
├── lib/                    # Utilities
│   ├── api.ts              # FastAPI client
│   └── types.ts            # TypeScript interfaces
├── public/                 # Static assets
├── next.config.ts          # Next.js configuration
├── tailwind.config.ts      # Tailwind + Skeleton config
└── tsconfig.json           # TypeScript configuration

```

## Configuration Files Created

- ✅ `tsconfig.json` - TypeScript configuration
- ✅ `next.config.ts` - Next.js configuration with API proxy
- ✅ `tailwind.config.ts` - Tailwind CSS with Skeleton UI themes
- ✅ `postcss.config.mjs` - PostCSS configuration

## API Integration

The Next.js app is configured to proxy API requests to the FastAPI backend:

- **Development**: `http://localhost:3000/api/*` → `http://localhost:8000/api/*`
- **Scryfall Images**: Configured in `next.config.ts` for Next.js Image optimization

## Features

- **Type-safe** API client with TypeScript interfaces
- **Server Components** for fast initial loads
- **Client Components** for interactive features
- **Skeleton UI** components for consistent design
- **Dark mode** support built-in
- **Image optimization** for Scryfall card images
- **API proxy** to avoid CORS issues

## Next Steps

1. Install dependencies: `cd ui && npm install`
2. Create TypeScript types for Card, Rule, etc. in `lib/types.ts`
3. Create API client in `lib/api.ts`
4. Build out pages in `app/` directory
5. Create reusable components in `components/`

## Development

```bash
# Start FastAPI backend first
cd ..
source venv/bin/activate
python api_server_rules.py

# Then start Next.js dev server
cd ui
npm run dev
```

Visit `http://localhost:3000`
