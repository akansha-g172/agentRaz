import type { AnalyticsSummary, AuditSession, CartLineItem, OrderResponse, SearchResponse } from '../types'

const API = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
  }
  return res.json()
}

export const api = {
  search: (message: string) =>
    request<SearchResponse>('/buyer-agent/search', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),

  calculateCart: (items: { product_id: number; quantity: number }[]) =>
    request<{ subtotal: number; items: CartLineItem[] }>('/cart/calculate', {
      method: 'POST',
      body: JSON.stringify({ items }),
    }),

  createOrder: (items: { product_id: number; quantity: number }[]) =>
    request<OrderResponse>('/orders/', {
      method: 'POST',
      body: JSON.stringify({ items }),
    }),

  getAnalytics: () => request<AnalyticsSummary>('/analytics/summary'),

  getAuditSession: (sessionId: string) =>
    request<AuditSession>(`/audit/sessions/${sessionId}`),
}
