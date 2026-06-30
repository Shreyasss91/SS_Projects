# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\utils



---

# FILE: frontend\src\utils\chunkReload.ts

```ts
// Detect "the user has a stale frontend bundle open in their browser, and
// CI just rebuilt the dist with new chunk hashes" — the classic SPA failure
// after a deploy. The browser's cached index.html still references
// Historify-OLDHASH.js, but the server only has Historify-NEWHASH.js.
// Lazy import() rejects with a browser-specific error message; we recognise
// any of those and force-reload to fetch the fresh index.html.
//
// See marketcalls/openalgo#1393 for the bug report.

const CHUNK_ERROR_PATTERNS = [
  // Safari: "Importing a module script failed."
  /Importing a module script failed/i,
  // Chrome / Edge
  /Failed to fetch dynamically imported module/i,
  // Firefox
  /error loading dynamically imported module/i,
  // Webpack legacy / generic
  /ChunkLoadError/i,
  // Vite preload helper
  /Unable to preload CSS for/i,
  /Failed to load resource.*\.(?:js|mjs|css)/i,
]

const RELOAD_FLAG = 'openalgo:chunk-reload-attempted'

/** True iff the error message looks like a stale-chunk import failure. */
export function isChunkLoadError(message: string | undefined | null): boolean {
  if (!message) return false
  return CHUNK_ERROR_PATTERNS.some((p) => p.test(message))
}

/**
 * If the error looks like a stale-chunk failure, force-reload the page
 * once per browser tab session to pick up the fresh index.html. Returns
 * true if a reload was triggered (caller should suppress further error
 * UI rendering, since the page is about to navigate).
 *
 * The session-storage flag prevents an infinite reload loop in the rare
 * case where the new index.html *also* fails to import a chunk (server
 * misconfiguration, partial deploy) — after one attempt, fall through
 * to the normal error UI so the user can see what's wrong.
 */
export function tryAutoReloadOnChunkError(message: string | undefined | null): boolean {
  if (!isChunkLoadError(message)) return false

  try {
    if (sessionStorage.getItem(RELOAD_FLAG)) {
      // Already tried once this session — surface the real error instead
      // of looping. User clicks the manual Reload button if they want
      // to retry.
      return false
    }
    sessionStorage.setItem(RELOAD_FLAG, String(Date.now()))
  } catch {
    // sessionStorage unavailable (private browsing edge cases).
    // Reload anyway; worst case is one extra reload if the chunks are
    // still missing — error UI will then surface as expected.
  }

  // Hard reload — bypasses any in-memory bfcache state.
  window.location.reload()
  return true
}

/**
 * Clear the reload-attempted flag. Called once on successful app mount —
 * if we got here, the new bundle loaded fine, so future stale-chunk
 * errors in this tab can retry the auto-reload trick.
 */
export function clearChunkReloadFlag(): void {
  try {
    sessionStorage.removeItem(RELOAD_FLAG)
  } catch {
    // ignore
  }
}

```


---

# FILE: frontend\src\utils\errorReporter.ts

```ts
/**
 * Browser error reporter.
 *
 * Routes uncaught errors and unhandled promise rejections to the backend so
 * they land in log/errors.jsonl alongside server errors. Designed to never
 * crash the app — every codepath is wrapped, and the reporter refuses to
 * recurse into itself.
 *
 * Privacy: only message + stack + URL + component stack are sent. No DOM,
 * no localStorage, no form values, no breadcrumbs.
 *
 * Throttling: dedups identical messages within 30s. Caps at 30 reports/min
 * (server enforces too).
 *
 * Auth: endpoint requires a valid admin session. On 401 we stop trying for
 * the rest of this page lifetime to avoid noise.
 */

import { tryAutoReloadOnChunkError } from '@/utils/chunkReload'

interface ClientErrorPayload {
  message: string
  stack?: string
  url?: string
  component_stack?: string
  user_agent?: string
  level?: 'ERROR' | 'WARN'
}

const ENDPOINT = '/admin/api/errors/client'
const DEDUP_WINDOW_MS = 30_000
const MAX_REPORTS_PER_MINUTE = 30
const RECENT_TTL_MS = 60_000

// Patterns that are noise — never report these.
const IGNORE_PATTERNS = [
  /ResizeObserver loop/i,
  /Non-Error promise rejection captured/i,
  /^Script error\.?$/, // cross-origin script with no CORS
  /Loading chunk \d+ failed/i, // stale build during deploy
  /ChunkLoadError/i,
  /Failed to fetch dynamically imported module/i,
]

const recentSends = new Map<string, number>()
const sendTimestamps: number[] = []
let isReporting = false
let isDisabled = false

function shouldIgnore(message: string): boolean {
  if (!message) return true
  return IGNORE_PATTERNS.some((rx) => rx.test(message))
}

function dedupKey(payload: ClientErrorPayload): string {
  return `${payload.level ?? 'ERROR'}|${payload.message}|${(payload.stack ?? '').slice(0, 200)}`
}

function withinRateLimit(): boolean {
  const now = Date.now()
  while (sendTimestamps.length > 0 && now - sendTimestamps[0] > RECENT_TTL_MS) {
    sendTimestamps.shift()
  }
  return sendTimestamps.length < MAX_REPORTS_PER_MINUTE
}

function pruneDedup(): void {
  const now = Date.now()
  for (const [key, ts] of recentSends.entries()) {
    if (now - ts > DEDUP_WINDOW_MS) recentSends.delete(key)
  }
}

async function fetchCSRFTokenSafe(): Promise<string | null> {
  try {
    const resp = await fetch('/auth/csrf-token', {
      credentials: 'include',
      keepalive: true,
    })
    if (!resp.ok) return null
    const data = await resp.json()
    return data?.csrf_token ?? null
  } catch {
    return null
  }
}

async function send(payload: ClientErrorPayload): Promise<void> {
  if (isDisabled || isReporting) return
  if (!withinRateLimit()) return

  pruneDedup()
  const key = dedupKey(payload)
  const now = Date.now()
  const last = recentSends.get(key)
  if (last !== undefined && now - last < DEDUP_WINDOW_MS) return
  recentSends.set(key, now)
  sendTimestamps.push(now)

  isReporting = true
  try {
    const csrf = await fetchCSRFTokenSafe()
    const resp = await fetch(ENDPOINT, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(csrf ? { 'X-CSRFToken': csrf } : {}),
      },
      body: JSON.stringify(payload),
      keepalive: true,
    })
    if (resp.status === 401 || resp.status === 403) {
      // Not logged in / no permission — stop trying this session.
      isDisabled = true
    }
  } catch {
    // Reporter is best-effort. Never throw.
  } finally {
    isReporting = false
  }
}

export function reportClientError(payload: ClientErrorPayload): void {
  try {
    const message = (payload.message || '').slice(0, 2000)
    if (shouldIgnore(message)) return
    void send({
      level: payload.level ?? 'ERROR',
      message,
      stack: payload.stack?.slice(0, 20_000),
      url: (payload.url || window.location.href).slice(0, 2000),
      component_stack: payload.component_stack?.slice(0, 5000),
      user_agent: navigator.userAgent.slice(0, 500),
    })
  } catch {
    // Reporter must never crash the app.
  }
}

let installed = false

export function installGlobalErrorReporter(): void {
  if (installed) return
  installed = true

  // Don't spam during local dev — React StrictMode double-renders
  // produce noise that isn't representative of production.
  if (import.meta.env.DEV) return

  window.addEventListener('error', (event: ErrorEvent) => {
    reportClientError({
      message: event.message || 'Uncaught error',
      stack: event.error?.stack,
      url: event.filename || window.location.href,
    })
    // Stale-bundle recovery: if a top-level script tag failed to load
    // (e.g. preload of the new entry chunk after a deploy), reload once
    // to fetch the fresh index.html.
    tryAutoReloadOnChunkError(event.message)
  })

  window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
    const reason = event.reason
    let message = 'Unhandled promise rejection'
    let stack: string | undefined
    if (reason instanceof Error) {
      message = reason.message || message
      stack = reason.stack
    } else if (typeof reason === 'string') {
      message = reason
    } else {
      try {
        message = JSON.stringify(reason).slice(0, 2000)
      } catch {
        // ignore — keep default message
      }
    }
    reportClientError({ message, stack })
    // Defense-in-depth: React.lazy() rejections normally land in the
    // ErrorBoundary, but rapid navigation or non-React import() callers
    // can let them surface here instead. tryAutoReloadOnChunkError is a
    // no-op for unrelated rejections.
    tryAutoReloadOnChunkError(message)
  })
}

```


---

# FILE: frontend\src\utils\toast.ts

```ts
/**
 * Toast utility with alert category support
 *
 * This utility wraps the sonner toast library to provide category-based
 * toast filtering. Toasts are only shown if:
 * 1. Master toasts toggle is enabled
 * 2. The specific category is enabled (if category is specified)
 *
 * Usage:
 * import { showToast } from '@/utils/toast'
 *
 * // With category (respects user settings)
 * showToast.success('Order placed', 'orders')
 * showToast.error('Failed to save', 'strategy')
 *
 * // Without category (always shows if master toggle enabled)
 * showToast.success('Copied to clipboard')
 *
 * // For validation errors (should always show - don't use category)
 * showToast.error('Please fill all required fields')
 */

import { toast } from 'sonner'
import { type AlertCategories, useAlertStore } from '@/stores/alertStore'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  duration?: number
  description?: string
}

/**
 * Show a toast notification respecting alert settings
 * @param type - Toast type (success, error, warning, info)
 * @param message - Toast message
 * @param category - Optional category for filtering
 * @param options - Optional toast options
 */
const show = (
  type: ToastType,
  message: string,
  category?: keyof AlertCategories,
  options?: ToastOptions
) => {
  const { shouldShowToast } = useAlertStore.getState()

  if (!shouldShowToast(category)) {
    return
  }

  toast[type](message, options)
}

/**
 * Show a success toast
 */
const success = (message: string, category?: keyof AlertCategories, options?: ToastOptions) => {
  show('success', message, category, options)
}

/**
 * Show an error toast
 */
const error = (message: string, category?: keyof AlertCategories, options?: ToastOptions) => {
  show('error', message, category, options)
}

/**
 * Show a warning toast
 */
const warning = (message: string, category?: keyof AlertCategories, options?: ToastOptions) => {
  show('warning', message, category, options)
}

/**
 * Show an info toast
 */
const info = (message: string, category?: keyof AlertCategories, options?: ToastOptions) => {
  show('info', message, category, options)
}

/**
 * Dismiss all toasts
 */
const dismissAll = () => {
  toast.dismiss()
}

/**
 * Show a dynamic toast based on type
 */
const dynamic = (
  type: ToastType,
  message: string,
  category?: keyof AlertCategories,
  options?: ToastOptions
) => {
  show(type, message, category, options)
}

export const showToast = {
  success,
  error,
  warning,
  info,
  dismissAll,
  dynamic,
  show,
}

// Re-export the raw toast for cases where category filtering is not needed
// (e.g., validation errors that must always show)
export { toast }

```
