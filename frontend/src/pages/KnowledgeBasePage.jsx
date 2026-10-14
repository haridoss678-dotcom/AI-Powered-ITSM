import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getArticle, listArticles, searchKnowledge } from '../api/knowledge';

const PRESET_QUERIES = [
  { label: 'Scenario C: Outlook Synchronization', query: 'How do I troubleshoot Outlook synchronization?' },
  { label: 'VPN Connection Issues', query: 'I cannot authenticate or connect to VPN gateway' },
  { label: 'Password Expiry & Unlock', query: 'How do I reset my expired domain password?' },
  { label: 'Scenario E: Unsupported Question', query: 'How do I brew espresso in the office kitchen cafeteria?' },
];

export default function KnowledgeBasePage() {
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'articles'
  const [searchQuery, setSearchQuery] = useState('How do I troubleshoot Outlook synchronization?');
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [articles, setArticles] = useState([]);
  const [loadingArticles, setLoadingArticles] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [loadingArticleDetail, setLoadingArticleDetail] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [error, setError] = useState(null);

  const loadArticles = async () => {
    setLoadingArticles(true);
    setError(null);
    try {
      const data = await listArticles();
      setArticles(data.items || []);
    } catch (err) {
      setError('Failed to load knowledge articles');
    } finally {
      setLoadingArticles(false);
    }
  };

  useEffect(() => {
    loadArticles();
  }, []);

  const handleSearch = async (e, customQuery) => {
    e?.preventDefault();
    const q = customQuery || searchQuery;
    if (!q.trim()) return;

    setSearching(true);
    setError(null);
    setSelectedArticle(null);

    try {
      const res = await searchKnowledge({
        query: q,
        mode: 'answer',
        topK: 4,
        category: selectedCategory !== 'all' ? selectedCategory : null,
      });
      setSearchResult(res);
      setActiveTab('search');
    } catch (err) {
      setError(err.message || 'Knowledge search failed');
      setSearchResult(null);
    } finally {
      setSearching(false);
    }
  };

  const handleViewArticle = async (articleId) => {
    setLoadingArticleDetail(true);
    setError(null);
    try {
      const detail = await getArticle(articleId);
      setSelectedArticle(detail);
      setActiveTab('articles');
    } catch (err) {
      setError(err.message || 'Failed to load article detail');
    } finally {
      setLoadingArticleDetail(false);
    }
  };

  const categories = ['all', ...new Set(articles.map((a) => a.category))];

  return (
    <div className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Screen 4 — Grounded RAG Pipeline</span>
          <h2>Knowledge Base & Retrieval</h2>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="secondary-button"
            onClick={() => setActiveTab('search')}
            style={{
              background: activeTab === 'search' ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
              borderColor: activeTab === 'search' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
            }}
          >
            Semantic Search & RAG
          </button>
          <button
            className="secondary-button"
            onClick={() => setActiveTab('articles')}
            style={{
              background: activeTab === 'articles' ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
              borderColor: activeTab === 'articles' ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
            }}
          >
            Browse Articles ({articles.length})
          </button>
        </div>
      </div>

      <p style={{ color: '#9fb2cc', marginTop: '6px' }}>
        Retrieval-Augmented Generation (RAG) powered by sentence-transformers/all-MiniLM-L6-v2 embeddings, Chroma vector store, and grounded answer synthesis with verifiable citations.
      </p>

      {error && <div className="error-banner">{error}</div>}

      {activeTab === 'search' && (
        <div style={{ marginTop: '20px' }}>
          <h4>Quick Benchmark Scenarios:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
            {PRESET_QUERIES.map((item, idx) => (
              <button
                key={idx}
                className="secondary-button"
                onClick={() => {
                  setSearchQuery(item.query);
                  handleSearch(null, item.query);
                }}
              >
                {item.label}
              </button>
            ))}
          </div>

          <form onSubmit={(e) => handleSearch(e)} className="ticket-form" style={{ marginTop: '18px' }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                placeholder="Ask any technical IT question..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ flex: 1, padding: '12px' }}
                required
              />
              <button type="submit" disabled={searching}>
                {searching ? 'Retrieving Chunks & Generating...' : 'Search & Answer'}
              </button>
            </div>
          </form>

          {searchResult && (
            <div style={{ marginTop: '28px' }}>
              {searchResult.insufficient_knowledge ? (
                <div
                  style={{
                    padding: '18px',
                    borderRadius: '12px',
                    background: 'rgba(127, 29, 29, 0.25)',
                    border: '1px solid rgba(248, 113, 113, 0.4)',
                  }}
                >
                  <h3 style={{ margin: '0 0 8px', color: '#fca5a5' }}>
                    Scenario E: Insufficient Knowledge Detected
                  </h3>
                  <p style={{ color: '#e2e8f0', margin: 0 }}>{searchResult.answer}</p>
                  <div style={{ marginTop: '14px' }}>
                    <span className="mock-badge" style={{ borderColor: '#f87171', color: '#fca5a5' }}>
                      ESCALATION TRIGGERED: {searchResult.escalation?.reason}
                    </span>
                    <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '6px' }}>
                      The system adheres to safety governance: no fabricated responses or hallucinations are produced when context is absent.
                    </p>
                  </div>
                  <div style={{ marginTop: '16px' }}>
                    <Link
                      to="/intake"
                      className="primary-button"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        textDecoration: 'none',
                        background: '#dc2626',
                        color: '#ffffff',
                        padding: '10px 18px',
                        borderRadius: '8px',
                        fontWeight: '600',
                        fontSize: '0.9rem',
                      }}
                    >
                      Create IT Inquiry Ticket
                    </Link>
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    padding: '20px',
                    borderRadius: '12px',
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                  }}
                >
                  <div className="section-heading">
                    <h3 style={{ margin: 0, color: '#93c5fd' }}>Grounded AI Answer</h3>
                    {searchResult.confidence && (
                      <span
                        style={{
                          fontSize: '0.8rem',
                          padding: '3px 10px',
                          borderRadius: '999px',
                          background: 'rgba(34, 197, 94, 0.15)',
                          color: '#86efac',
                          border: '1px solid rgba(34, 197, 94, 0.3)',
                        }}
                      >
                        Confidence: {(searchResult.confidence.score * 100).toFixed(0)}% ({searchResult.confidence.level})
                      </span>
                    )}
                  </div>

                  <p
                    style={{
                      margin: '14px 0',
                      fontSize: '1rem',
                      lineHeight: '1.6',
                      color: '#f1f5f9',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {searchResult.answer}
                  </p>

                  <div style={{ marginTop: '20px', borderTop: '1px solid rgba(148, 163, 184, 0.2)', paddingTop: '16px' }}>
                    <h4 style={{ margin: '0 0 12px' }}>
                      Retrieved Source Passages ({searchResult.hits.length})
                    </h4>
                    <div style={{ display: 'grid', gap: '12px' }}>
                      {searchResult.hits.map((hit, idx) => (
                        <div
                          key={hit.chunk_id || idx}
                          style={{
                            padding: '12px 16px',
                            borderRadius: '8px',
                            background: hit.cited ? 'rgba(37, 99, 235, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                            border: hit.cited
                              ? '1px solid rgba(96, 165, 250, 0.45)'
                              : '1px solid rgba(148, 163, 184, 0.2)',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <strong style={{ color: '#7dd3fc' }}>
                                [{idx + 1}] {hit.title}
                              </strong>
                              <span style={{ fontSize: '0.8rem', color: '#94a3b8', marginLeft: '8px' }}>
                                ({hit.category} — chunk {hit.chunk_index})
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                              {hit.cited && (
                                <span
                                  style={{
                                    fontSize: '0.72rem',
                                    fontWeight: 'bold',
                                    padding: '2px 8px',
                                    borderRadius: '999px',
                                    background: '#1d4ed8',
                                    color: '#fff',
                                  }}
                                >
                                  CITED IN ANSWER
                                </span>
                              )}
                              <span style={{ fontSize: '0.8rem', color: '#a5f3fc' }}>
                                Score: {(hit.score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <p style={{ margin: '8px 0 0', fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                            {hit.text || hit.excerpt}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'articles' && (
        <div style={{ marginTop: '20px' }}>
          {selectedArticle ? (
            <div>
              <button
                className="secondary-button"
                onClick={() => setSelectedArticle(null)}
                style={{ marginBottom: '14px' }}
              >
                ← Back to Article List
              </button>
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  borderRadius: '12px',
                  padding: '24px',
                }}
              >
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">{selectedArticle.category}</span>
                    <h2 style={{ margin: '4px 0' }}>{selectedArticle.title}</h2>
                  </div>
                  <span className="mock-badge">ID: {selectedArticle.article_id}</span>
                </div>

                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', margin: '10px 0 20px' }}>
                  {selectedArticle.tags?.map((t) => (
                    <span
                      key={t}
                      style={{
                        fontSize: '0.75rem',
                        background: 'rgba(96, 165, 250, 0.15)',
                        color: '#93c5fd',
                        padding: '2px 8px',
                        borderRadius: '999px',
                      }}
                    >
                      #{t}
                    </span>
                  ))}
                  {selectedArticle.automations?.map((a) => (
                    <span
                      key={a}
                      style={{
                        fontSize: '0.75rem',
                        background: 'rgba(34, 197, 94, 0.15)',
                        color: '#86efac',
                        padding: '2px 8px',
                        borderRadius: '999px',
                      }}
                    >
                      ⚡ Auto: {a}
                    </span>
                  ))}
                </div>

                <div
                  style={{
                    lineHeight: '1.7',
                    color: '#e2e8f0',
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'inherit',
                  }}
                >
                  {selectedArticle.content_markdown}
                </div>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    className="secondary-button"
                    onClick={() => setSelectedCategory(cat)}
                    style={{
                      textTransform: 'capitalize',
                      background: selectedCategory === cat ? '#2563eb' : 'rgba(15, 23, 42, 0.5)',
                      borderColor: selectedCategory === cat ? '#60a5fa' : 'rgba(148, 163, 184, 0.2)',
                    }}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {loadingArticles ? (
                <div className="analysis-box">Loading knowledge base articles...</div>
              ) : (
                <div style={{ display: 'grid', gap: '12px' }}>
                  {articles
                    .filter((a) => selectedCategory === 'all' || a.category === selectedCategory)
                    .map((art) => (
                      <div
                        key={art.article_id}
                        className="ticket-table-row"
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '16px 20px',
                        }}
                        onClick={() => handleViewArticle(art.article_id)}
                      >
                        <div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <strong style={{ fontSize: '1.05rem' }}>{art.title}</strong>
                            <span
                              style={{
                                fontSize: '0.75rem',
                                color: '#7dd3fc',
                                background: 'rgba(56, 189, 248, 0.1)',
                                padding: '2px 8px',
                                borderRadius: '999px',
                              }}
                            >
                              {art.category}
                            </span>
                          </div>
                          <p style={{ margin: '6px 0 0', fontSize: '0.88rem', color: '#94a3b8' }}>
                            {art.summary}
                          </p>
                        </div>
                        <span className="ticket-action-label" style={{ flexShrink: 0, marginLeft: '16px' }}>
                          Read Article →
                        </span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
