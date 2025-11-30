import Link from "next/link";
import SearchBar from "../components/SearchBar";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">MTG Rule Engine</h1>

      {/* Search Bar */}
      <SearchBar className="mb-8" />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/cards"
          className="card variant-filled-primary p-6 hover:scale-105 transition-transform"
        >
          <h2 className="text-2xl font-bold mb-2">Card Explorer</h2>
          <p className="text-sm opacity-80">
            Search and browse Magic: The Gathering cards with intelligent
            filtering
          </p>
        </Link>

        <Link
          href="/rules"
          className="card variant-filled-secondary p-6 hover:scale-105 transition-transform"
        >
          <h2 className="text-2xl font-bold mb-2">Rules Browser</h2>
          <p className="text-sm opacity-80">
            Explore MTG rules and find cards that match specific mechanics
          </p>
        </Link>

        <Link
          href="/deck"
          className="card variant-filled-tertiary p-6 hover:scale-105 transition-transform"
        >
          <h2 className="text-2xl font-bold mb-2">Deck Analyzer</h2>
          <p className="text-sm opacity-80">
            Analyze deck compositions and discover rule interactions
          </p>
        </Link>
      </div>

      <div className="mt-12">
        <h3 className="text-2xl font-bold mb-4">Features</h3>
        <ul className="list-disc list-inside space-y-2">
          <li>Vector-powered semantic search across 500K+ cards</li>
          <li>Intelligent rule extraction and matching</li>
          <li>Latest printing focus with playability filtering</li>
          <li>Card image optimization via Scryfall</li>
          <li>Real-time API integration</li>
        </ul>
      </div>
    </div>
  );
}
