import React from 'react';
import { Zap } from 'lucide-react';

export default function SearchBar({
  searchTerm,
  setSearchTerm,
  onSearch,
  loading,
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      onSearch(searchTerm.trim());
    }
  };

  return (
    <section className="docket-search-panel">
      <form onSubmit={handleSubmit} className="docket-search-form">
        <span className="docket-label">TRANSACTION ID</span>
        <div className="docket-input-wrapper">
          <input
            type="text"
            className="docket-input"
            placeholder="e.g. TXN10087..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="btn-docket-investigate"
          disabled={loading || !searchTerm.trim()}
        >
          <Zap size={14} />
          {loading ? 'GENERATING RECEIPT...' : 'INVESTIGATE'}
        </button>
      </form>
    </section>
  );
}
