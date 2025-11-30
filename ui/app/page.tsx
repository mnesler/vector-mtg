import SearchBar from "../components/SearchBar";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8"></h1>

      {/* Search Bar */}
      <SearchBar className="mb-8" />

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
