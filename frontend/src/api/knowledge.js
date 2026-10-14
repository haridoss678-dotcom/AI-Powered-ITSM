import { apiFetch } from './http';

export async function listArticles({ category, limit = 50, skip = 0 } = {}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  params.set('limit', String(limit));
  params.set('skip', String(skip));
  return apiFetch(`/knowledge/articles?${params.toString()}`);
}

export async function getArticle(articleId) {
  return apiFetch(`/knowledge/articles/${encodeURIComponent(articleId)}`);
}

export async function searchKnowledge({ query, topK = 4, mode = 'retrieve', category } = {}) {
  return apiFetch('/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      top_k: topK,
      mode,
      category: category || null,
    }),
  });
}
