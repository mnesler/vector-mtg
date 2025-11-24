# MTG Rule Engine - UI Prototype

Simple HTML/JavaScript frontend for the MTG Rule Engine API.

## Features

- **Dashboard**: View overall statistics and top rules
- **Card Explorer**: Search cards by name or filter by rule
- **Rule Browser**: Browse all 45 rules with category filtering
- **Deck Analyzer**: Analyze deck composition and rule distribution

## Requirements

- MTG Rule Engine API running on `http://localhost:8000`
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Running the UI

### Option 1: Python HTTP Server

```bash
cd ui-proto
python3 -m http.server 3000
```

Then visit: http://localhost:3000

### Option 2: Node.js HTTP Server

```bash
cd ui-proto
npx http-server -p 3000
```

Then visit: http://localhost:3000

### Option 3: PHP Server

```bash
cd ui-proto
php -S localhost:3000
```

Then visit: http://localhost:3000

## File Structure

```
ui-proto/
├── index.html          # Dashboard
├── cards.html          # Card Explorer
├── rules.html          # Rule Browser
├── deck.html           # Deck Analyzer
├── css/
│   └── styles.css      # Custom styles
├── js/
│   ├── api.js          # API client
│   ├── dashboard.js    # Dashboard logic
│   ├── cards.js        # Card page logic
│   ├── rules.js        # Rules page logic
│   └── deck.js         # Deck analyzer logic
└── README.md           # This file
```

## API Configuration

The API base URL is set in `js/api.js`:

```javascript
const api = new MTGRuleEngineAPI('http://localhost:8000');
```

Change this if your API is running on a different host/port.

## Browser Support

- Chrome/Edge: Latest
- Firefox: Latest
- Safari: Latest

## Technologies Used

- **Tailwind CSS**: Utility-first CSS framework (CDN)
- **Chart.js**: Data visualization (CDN)
- **Vanilla JavaScript**: No framework dependencies

## Features by Page

### Dashboard
- Real-time statistics
- Top 10 rules bar chart
- Category distribution pie chart
- Popular rules table
- Quick card search

### Card Explorer
- Search by exact card name
- Filter by rule category
- View matched rules for each card
- Display keywords and oracle text

### Rule Browser
- Browse all 45 rules
- Filter by category
- Search rules by name/template
- Click to view matching cards
- Modal detail view

### Deck Analyzer
- Paste deck list (MTGO format)
- Rule distribution analysis
- Category pie chart
- Top rules breakdown
- Example decks (Aggro, Control, Ramp)

## Development

No build step required! Just edit the HTML/CSS/JS files and refresh your browser.

## Troubleshooting

**"Failed to load data"**
- Make sure the API server is running (`python api_server_rules.py`)
- Check console for CORS errors
- Verify API URL in `js/api.js`

**Charts not showing**
- Check browser console for Chart.js errors
- Ensure CDN is accessible

**Slow loading**
- Large datasets may take time to render
- Consider pagination for large result sets (future enhancement)

## Future Enhancements

- Card image display
- Advanced search filters
- Deck export to MTGO/Arena format
- Saved searches
- Dark/Light mode toggle
- Mobile responsive improvements
