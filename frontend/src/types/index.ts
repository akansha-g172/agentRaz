export interface Recommendation {
  product_id: number
  name: string
  brand: string | null
  price: number
  recommendation_score: number
  reasons: string[]
  specifications?: Record<string, string>
  stock_quantity?: number
}

export interface SearchResponse {
  query: string
  intent: {
    category: string | null
    max_price: number | null
    preferred_brands: string[]
    use_case: string | null
    preferences: string[]
  }
  recommendations: Recommendation[]
}

export interface CartLineItem {
  product_id: number
  name: string
  brand: string | null
  quantity: number
  unit_price: number
  line_total: number
  in_stock: boolean
  available_quantity: number
}

export interface PolicyResult {
  allowed: boolean
  reason: string
  limit: number
  requested_amount: number
  policy_result: string
}

export interface OrderResponse {
  session_id: string
  policy: PolicyResult
  order: {
    id: string
    total_amount: number
    status: string
    items: CartLineItem[]
  }
}

export interface AnalyticsSummary {
  revenue: { total_revenue: number; paid_orders: number; average_order_value: number }
  conversion: { sessions: number; conversion_rate: number; orders_paid: number }
  aov: { average_order_value: number; paid_orders: number }
  upsell: { upsell_rate: number; cross_sell_rate: number; avg_items_per_order: number }
  uplift: { revenue_per_session: number; conversion_rate: number }
}

export interface AuditAction {
  id: number
  agent_type: string
  action: string
  arguments: Record<string, unknown>
  result: Record<string, unknown>
  created_at: string
}

export interface AuditLog {
  id: number
  action: string
  reason: string | null
  amount: number | null
  authorization_status: string | null
  policy_result: string | null
  created_at: string
}

export interface AuditSession {
  found: boolean
  session: { id: string; started_at: string }
  agent_actions: AuditAction[]
  audit_logs: AuditLog[]
}
