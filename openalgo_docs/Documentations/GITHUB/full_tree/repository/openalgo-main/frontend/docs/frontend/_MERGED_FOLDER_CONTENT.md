# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\docs\frontend



---

# FILE: frontend\docs\frontend\api-reference.md

```md
# API Reference

This document covers the API modules, stores, and hooks used in the OpenAlgo frontend.

## API Modules

All API modules are located in `src/api/` and follow a consistent pattern.

### Authentication API

```tsx
// src/api/auth.ts
import { authApi } from '@/api/auth'

// Login
await authApi.login(username, password)

// Logout
await authApi.logout()

// Get session status
const session = await authApi.getSessionStatus()
// Returns: { status, logged_in, authenticated, broker, username }

// Check if setup is needed
const setup = await authApi.checkSetup()
// Returns: { needs_setup: boolean }

// Reset password
await authApi.resetPassword(currentPassword, newPassword)
```

### Broker API

```tsx
// src/api/broker.ts
import { brokerApi } from '@/api/broker'

// Get available brokers
const brokers = await brokerApi.getBrokers()
// Returns: string[] e.g., ['angel', 'zerodha', 'fyers']

// Login to broker
await brokerApi.loginBroker(broker, credentials)

// Logout from broker
await brokerApi.logoutBroker()

// Get broker status
const status = await brokerApi.getBrokerStatus()
```

### Orders API

```tsx
// src/api/orders.ts
import { ordersApi } from '@/api/orders'

// Get order book
const orders = await ordersApi.getOrderBook()

// Get trade book
const trades = await ordersApi.getTradeBook()

// Get positions
const positions = await ordersApi.getPositions()

// Get holdings
const holdings = await ordersApi.getHoldings()

// Place order
await ordersApi.placeOrder({
  symbol: 'RELIANCE',
  exchange: 'NSE',
  action: 'BUY',
  quantity: 1,
  product: 'MIS',
  pricetype: 'MARKET',
})

// Cancel order
await ordersApi.cancelOrder(orderId)

// Modify order
await ordersApi.modifyOrder(orderId, modifications)
```

### Strategy API

```tsx
// src/api/strategy.ts
import { strategyApi } from '@/api/strategy'

// Get all strategies
const strategies = await strategyApi.getStrategies()

// Get single strategy
const strategy = await strategyApi.getStrategy(strategyId)

// Create strategy
const newStrategy = await strategyApi.createStrategy({
  name: 'My Strategy',
  description: 'Strategy description',
})

// Update strategy
await strategyApi.updateStrategy(strategyId, updates)

// Delete strategy
await strategyApi.deleteStrategy(strategyId)

// Get webhook URL
const webhookUrl = strategyApi.getWebhookUrl(webhookId)

// Configure symbols
await strategyApi.configureSymbols(strategyId, symbols)
```

### Chartink API

```tsx
// src/api/chartink.ts
import { chartinkApi } from '@/api/chartink'

// Get all Chartink strategies
const strategies = await chartinkApi.getStrategies()

// Get single strategy
const strategy = await chartinkApi.getStrategy(strategyId)

// Create Chartink strategy
const newStrategy = await chartinkApi.createStrategy({
  name: 'Chartink Strategy',
  is_intraday: true,
  start_time: '09:15',
  end_time: '15:15',
})

// Update strategy
await chartinkApi.updateStrategy(strategyId, updates)

// Delete strategy
await chartinkApi.deleteStrategy(strategyId)

// Get webhook URL
const webhookUrl = chartinkApi.getWebhookUrl(webhookId)
```

### Python Strategy API

```tsx
// src/api/pythonStrategy.ts
import { pythonStrategyApi } from '@/api/pythonStrategy'

// Get all Python strategies
const strategies = await pythonStrategyApi.getStrategies()

// Get strategy with code
const strategy = await pythonStrategyApi.getStrategy(strategyId)

// Create strategy
const newStrategy = await pythonStrategyApi.createStrategy({
  name: 'My Python Strategy',
  code: 'def execute(): pass',
})

// Update strategy code
await pythonStrategyApi.updateStrategy(strategyId, { code: newCode })

// Start strategy
await pythonStrategyApi.startStrategy(strategyId)

// Stop strategy
await pythonStrategyApi.stopStrategy(strategyId)

// Get logs
const logs = await pythonStrategyApi.getLogs(strategyId)
```

### Search API

```tsx
// src/api/search.ts
import { searchApi } from '@/api/search'

// Search symbols
const results = await searchApi.search(query, exchange)
// Returns: { symbol, name, exchange, token }[]

// Get token for symbol
const token = await searchApi.getToken(symbol, exchange)
```

### Telegram API

```tsx
// src/api/telegram.ts
import { telegramApi } from '@/api/telegram'

// Get config
const config = await telegramApi.getConfig()

// Update config
await telegramApi.updateConfig({ bot_token, chat_id })

// Get users
const users = await telegramApi.getUsers()

// Get analytics
const analytics = await telegramApi.getAnalytics()
```

### Admin API

```tsx
// src/api/admin.ts
import { adminApi } from '@/api/admin'

// Get freeze quantities
const freezeQty = await adminApi.getFreezeQty()

// Update freeze quantities
await adminApi.updateFreezeQty(data)

// Get holidays
const holidays = await adminApi.getHolidays()

// Get market timings
const timings = await adminApi.getMarketTimings()
```

## State Stores (Zustand)

### Auth Store

Manages authentication state.

```tsx
// src/stores/authStore.ts
import { useAuthStore } from '@/stores/authStore'

// Access state
const { user, isAuthenticated } = useAuthStore()

// Actions
const { login, logout, setUser } = useAuthStore()

// Login
login(username, broker)

// Logout
logout()

// Check auth
if (isAuthenticated) {
  // User is logged in
}
```

**State Shape:**
```tsx
interface AuthState {
  user: {
    username: string
    broker: string
  } | null
  isAuthenticated: boolean
  login: (username: string, broker: string) => void
  logout: () => void
  setUser: (user: User | null) => void
}
```

### Theme Store

Manages theme and app mode.

```tsx
// src/stores/themeStore.ts
import { useThemeStore } from '@/stores/themeStore'

// Access state
const { mode, appMode } = useThemeStore()

// Actions
const { toggleMode, toggleAppMode, setMode } = useThemeStore()

// Toggle light/dark
toggleMode()

// Toggle live/analyzer mode
const result = await toggleAppMode()
if (result.success) {
  // Mode toggled
}

// Set specific mode
setMode('dark')
```

**State Shape:**
```tsx
interface ThemeState {
  mode: 'light' | 'dark'
  appMode: 'live' | 'analyzer'
  isTogglingMode: boolean
  toggleMode: () => void
  toggleAppMode: () => Promise<{ success: boolean; message?: string }>
  setMode: (mode: 'light' | 'dark') => void
  setAppMode: (mode: 'live' | 'analyzer') => void
}
```

## Custom Hooks

### useAuth

Authentication hook with loading state.

```tsx
import { useAuth } from '@/hooks/useAuth'

function MyComponent() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth()

  if (isLoading) return <PageLoader />
  if (!isAuthenticated) return <Navigate to="/login" />

  return <div>Welcome, {user.username}</div>
}
```

### useLocalStorage

Persist state to localStorage.

```tsx
import { useLocalStorage } from '@/hooks/useLocalStorage'

function MyComponent() {
  const [value, setValue] = useLocalStorage('my-key', defaultValue)

  return (
    <input
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  )
}
```

### useMediaQuery

Responsive breakpoint detection.

```tsx
import { useMediaQuery } from '@/hooks/useMediaQuery'

function MyComponent() {
  const isMobile = useMediaQuery('(max-width: 768px)')

  return isMobile ? <MobileView /> : <DesktopView />
}
```

### useDebounce

Debounce value changes.

```tsx
import { useDebounce } from '@/hooks/useDebounce'

function SearchComponent() {
  const [query, setQuery] = useState('')
  const debouncedQuery = useDebounce(query, 300)

  useEffect(() => {
    if (debouncedQuery) {
      performSearch(debouncedQuery)
    }
  }, [debouncedQuery])

  return <input value={query} onChange={(e) => setQuery(e.target.value)} />
}
```

## TanStack Query Patterns

### Basic Query

```tsx
import { useQuery } from '@tanstack/react-query'

function OrderBook() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['orderbook'],
    queryFn: () => ordersApi.getOrderBook(),
    refetchInterval: 5000, // Auto-refresh every 5s
  })

  if (isLoading) return <Skeleton />
  if (error) return <ErrorAlert error={error} />

  return <OrderTable orders={data} />
}
```

### Mutation

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'

function PlaceOrderForm() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (order) => ordersApi.placeOrder(order),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orderbook'] })
      toast.success('Order placed successfully')
    },
    onError: (error) => {
      toast.error(error.message)
    },
  })

  const handleSubmit = (data) => {
    mutation.mutate(data)
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Placing...' : 'Place Order'}
      </Button>
    </form>
  )
}
```

### Dependent Queries

```tsx
function StrategyDetails({ strategyId }) {
  // First query
  const strategyQuery = useQuery({
    queryKey: ['strategy', strategyId],
    queryFn: () => strategyApi.getStrategy(strategyId),
  })

  // Dependent query
  const symbolsQuery = useQuery({
    queryKey: ['strategy-symbols', strategyId],
    queryFn: () => strategyApi.getSymbols(strategyId),
    enabled: !!strategyQuery.data, // Only run when strategy is loaded
  })

  // ...
}
```

### Optimistic Updates

```tsx
const mutation = useMutation({
  mutationFn: updateTodo,
  onMutate: async (newTodo) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['todos'] })

    // Snapshot previous value
    const previousTodos = queryClient.getQueryData(['todos'])

    // Optimistically update
    queryClient.setQueryData(['todos'], (old) =>
      old.map((todo) => (todo.id === newTodo.id ? newTodo : todo))
    )

    return { previousTodos }
  },
  onError: (err, newTodo, context) => {
    // Rollback on error
    queryClient.setQueryData(['todos'], context.previousTodos)
  },
  onSettled: () => {
    // Always refetch after error or success
    queryClient.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

## WebSocket Integration

### Socket.IO Connection

```tsx
import { io } from 'socket.io-client'

// Connect
const socket = io('/', {
  path: '/socket.io',
  transports: ['websocket', 'polling'],
})

// Listen for events
socket.on('connect', () => {
  console.log('Connected')
})

socket.on('order_update', (data) => {
  // Handle order update
})

socket.on('position_update', (data) => {
  // Handle position update
})

// Disconnect
socket.disconnect()
```

### Real-time Hook Pattern

```tsx
function useRealTimeOrders() {
  const queryClient = useQueryClient()

  useEffect(() => {
    const socket = io('/')

    socket.on('order_update', (order) => {
      queryClient.setQueryData(['orderbook'], (old) => {
        // Update order in cache
        return old.map((o) => (o.id === order.id ? order : o))
      })
    })

    return () => {
      socket.disconnect()
    }
  }, [queryClient])
}
```

## Type Definitions

### Common Types

```tsx
// src/types/common.ts

interface ApiResponse<T> {
  status: 'success' | 'error'
  data?: T
  message?: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
```

### Order Types

```tsx
// src/types/orders.ts

interface Order {
  id: string
  symbol: string
  exchange: string
  action: 'BUY' | 'SELL'
  quantity: number
  price: number
  product: 'MIS' | 'NRML' | 'CNC'
  pricetype: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'
  status: 'PENDING' | 'OPEN' | 'COMPLETE' | 'CANCELLED' | 'REJECTED'
  timestamp: string
}

interface Position {
  symbol: string
  exchange: string
  quantity: number
  averagePrice: number
  ltp: number
  pnl: number
  product: string
}
```

### Strategy Types

```tsx
// src/types/strategy.ts

interface Strategy {
  id: string
  name: string
  description?: string
  webhook_id: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface ChartinkStrategy extends Strategy {
  is_intraday: boolean
  start_time?: string
  end_time?: string
  squareoff_time?: string
}
```

## Error Handling

### API Error Pattern

```tsx
class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchWithError(url: string, options?: RequestInit) {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new ApiError(
      error.message || 'Request failed',
      response.status,
      error.code
    )
  }

  return response.json()
}
```

### Error Boundary

```tsx
import { ErrorBoundary } from 'react-error-boundary'

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>Something went wrong</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
      <Button onClick={resetErrorBoundary}>Try again</Button>
    </Alert>
  )
}

// Usage
<ErrorBoundary FallbackComponent={ErrorFallback}>
  <MyComponent />
</ErrorBoundary>
```

```


---

# FILE: frontend\docs\frontend\components.md

```md
# Component Documentation

This document covers the UI components used in the OpenAlgo frontend.

## Component Architecture

```
components/
├── auth/           # Authentication components
├── layout/         # Layout components
└── ui/             # Base UI components (shadcn/ui)
```

## Layout Components

### Layout

Main application layout with navbar, content area, and footer.

```tsx
import { Layout } from '@/components/layout/Layout'

// Used in App.tsx for protected routes
<Route element={<Layout />}>
  <Route path="/dashboard" element={<Dashboard />} />
</Route>
```

**Features:**
- Responsive navbar with desktop/mobile variants
- Mobile bottom navigation (visible on `< md` screens)
- Footer with version info and social links
- Safe area padding for notched devices

### Navbar

Top navigation bar with logo, navigation links, and user menu.

```tsx
import { Navbar } from '@/components/layout/Navbar'
```

**Features:**
- Desktop: Horizontal navigation links
- Mobile: Hamburger menu with slide-out sheet
- Mode toggle (Live/Analyze)
- Theme toggle (Light/Dark)
- Profile dropdown menu
- Broker badge display

### MobileBottomNav

Fixed bottom navigation for mobile devices.

```tsx
import { MobileBottomNav } from '@/components/layout/MobileBottomNav'
```

**Navigation Items:**
1. Dashboard
2. Orderbook
3. Tradebook
4. Positions
5. Strategy

**Accessibility:**
- 44px minimum touch targets
- `touch-manipulation` for instant response
- Active state indication
- Safe area bottom padding

### Footer

Application footer with links and version info.

```tsx
import { Footer } from '@/components/layout/Footer'

<Footer className="custom-class" />
```

**Features:**
- Copyright and website link
- Version badge (fetched from API)
- Social media links (GitHub, Discord, X, YouTube)

### FullWidthLayout

Alternative layout without sidebar constraints.

```tsx
<Route element={<FullWidthLayout />}>
  <Route path="/playground" element={<Playground />} />
</Route>
```

## UI Components (shadcn/ui)

All base UI components are from [shadcn/ui](https://ui.shadcn.com/) with Radix UI primitives.

### Button

```tsx
import { Button } from '@/components/ui/button'

// Variants
<Button variant="default">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>
<Button variant="destructive">Destructive</Button>

// Sizes
<Button size="default">Default</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button size="icon">Icon</Button>

// With icon
<Button>
  <Plus className="h-4 w-4 mr-2" />
  Add Item
</Button>

// Icon-only (always add aria-label!)
<Button size="icon" aria-label="Open menu">
  <Menu className="h-4 w-4" />
</Button>

// As child (renders as anchor)
<Button asChild>
  <Link to="/dashboard">Go to Dashboard</Link>
</Button>
```

### Card

```tsx
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description text</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content goes here</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### Input

```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input
    id="email"
    type="email"
    placeholder="Enter your email"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
  />
</div>
```

### Select

```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

<Select value={value} onValueChange={setValue}>
  <SelectTrigger>
    <SelectValue placeholder="Select option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

### Dialog

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog'

<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Dialog Title</DialogTitle>
      <DialogDescription>Dialog description</DialogDescription>
    </DialogHeader>
    <div>Dialog content</div>
    <DialogFooter>
      <Button onClick={() => setOpen(false)}>Close</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Sheet (Mobile Drawer)

```tsx
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

<Sheet>
  <SheetTrigger asChild>
    <Button variant="ghost" size="icon" aria-label="Open menu">
      <Menu className="h-5 w-5" />
    </Button>
  </SheetTrigger>
  <SheetContent side="left">
    <SheetHeader>
      <SheetTitle>Menu</SheetTitle>
    </SheetHeader>
    <nav>...</nav>
  </SheetContent>
</Sheet>
```

### DropdownMenu

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon" aria-label="Open user menu">
      <User className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onSelect={() => navigate('/profile')}>
      Profile
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem onSelect={handleLogout}>
      Logout
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Tabs

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

<Tabs defaultValue="tab1">
  <TabsList>
    <TabsTrigger value="tab1">Tab 1</TabsTrigger>
    <TabsTrigger value="tab2">Tab 2</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">Content 1</TabsContent>
  <TabsContent value="tab2">Content 2</TabsContent>
</Tabs>
```

### Alert

```tsx
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle, Info } from 'lucide-react'

// Info alert
<Alert>
  <Info className="h-4 w-4" />
  <AlertTitle>Information</AlertTitle>
  <AlertDescription>This is an info message.</AlertDescription>
</Alert>

// Destructive alert
<Alert variant="destructive">
  <AlertTriangle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>Something went wrong.</AlertDescription>
</Alert>
```

### Badge

```tsx
import { Badge } from '@/components/ui/badge'

<Badge>Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="outline">Outline</Badge>
<Badge variant="destructive">Destructive</Badge>
```

### Skeleton

```tsx
import { Skeleton } from '@/components/ui/skeleton'

// Loading placeholder
<div className="space-y-2">
  <Skeleton className="h-4 w-[250px]" />
  <Skeleton className="h-4 w-[200px]" />
</div>

// Card skeleton
<Card>
  <CardHeader>
    <Skeleton className="h-6 w-32" />
  </CardHeader>
  <CardContent>
    <Skeleton className="h-24 w-full" />
  </CardContent>
</Card>
```

### Toast (Sonner)

```tsx
import { toast } from 'sonner'

// Success
toast.success('Operation completed successfully')

// Error
toast.error('Something went wrong')

// Warning
toast.warning('Please check your input')

// With description
toast.success('Saved', {
  description: 'Your changes have been saved.',
})

// With action
toast('Event created', {
  action: {
    label: 'Undo',
    onClick: () => undoAction(),
  },
})
```

## Custom Components

### PageLoader

Full-page loading spinner for lazy-loaded routes.

```tsx
import { PageLoader } from '@/components/ui/page-loader'

// Used in App.tsx Suspense fallback
<Suspense fallback={<PageLoader />}>
  <Routes>...</Routes>
</Suspense>
```

### AuthSync

Syncs authentication state on app load.

```tsx
import { AuthSync } from '@/components/auth/AuthSync'

// Wraps the app in App.tsx
<AuthSync>
  <Routes>...</Routes>
</AuthSync>
```

## Component Patterns

### Loading States

```tsx
function MyComponent() {
  const [loading, setLoading] = useState(true)

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return <div>Content</div>
}
```

### Error States

```tsx
function MyComponent() {
  const [error, setError] = useState<string | null>(null)

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  return <div>Content</div>
}
```

### Empty States

```tsx
function MyList({ items }) {
  if (items.length === 0) {
    return (
      <Card className="py-12">
        <CardContent className="flex flex-col items-center text-center">
          <Inbox className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No items</h3>
          <p className="text-muted-foreground mb-4">
            Get started by creating your first item.
          </p>
          <Button>Create Item</Button>
        </CardContent>
      </Card>
    )
  }

  return <div>{/* List content */}</div>
}
```

### Form Pattern

```tsx
function MyForm() {
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await submitData()
      toast.success('Saved successfully')
    } catch (error) {
      toast.error('Failed to save')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input id="name" required />
      </div>
      <Button type="submit" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Saving...
          </>
        ) : (
          'Save'
        )}
      </Button>
    </form>
  )
}
```

## Accessibility Guidelines

### Icon Buttons

Always add `aria-label` to icon-only buttons:

```tsx
// Good
<Button size="icon" aria-label="Open menu">
  <Menu className="h-4 w-4" />
</Button>

// Bad - no accessible name
<Button size="icon">
  <Menu className="h-4 w-4" />
</Button>
```

### Form Labels

Always associate labels with inputs:

```tsx
// Good
<Label htmlFor="email">Email</Label>
<Input id="email" type="email" />

// Bad - no association
<Label>Email</Label>
<Input type="email" />
```

### Focus Management

Ensure focus is visible and logical:

```tsx
// Button has built-in focus styles
<Button>Focusable</Button>

// Custom focus styles if needed
<div
  tabIndex={0}
  className="focus:outline-none focus:ring-2 focus:ring-primary"
>
  Focusable div
</div>
```

### Color Contrast

Use semantic color tokens that ensure contrast:

```tsx
// Good - uses theme tokens
<p className="text-foreground">Primary text</p>
<p className="text-muted-foreground">Secondary text</p>

// Avoid - may have contrast issues
<p className="text-gray-400">Low contrast text</p>
```

```


---

# FILE: frontend\docs\frontend\developer-guide.md

```md
# Developer Guide

This guide covers everything you need to know to develop the OpenAlgo frontend.

## Prerequisites

- Node.js 20.19+ or 22.12+
- npm 10+
- Git

## Getting Started

### 1. Clone and Install

```bash
cd openalgo/frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The app runs at `http://localhost:5173` with hot module replacement (HMR).

### 3. Backend Proxy

The Vite dev server proxies API requests to the Flask backend:

| Path | Target |
|------|--------|
| `/api/*` | `http://localhost:5000` |
| `/auth/*` | `http://localhost:5000` |
| `/socket.io/*` | `http://localhost:5000` (WebSocket) |

Ensure the Flask backend is running on port 5000.

## Project Structure

```
frontend/
├── docs/                 # Documentation
├── e2e/                  # Playwright E2E tests
├── public/               # Static assets
├── src/
│   ├── api/              # API client modules
│   │   ├── auth.ts       # Authentication API
│   │   ├── broker.ts     # Broker operations
│   │   ├── chartink.ts   # Chartink strategies
│   │   ├── orders.ts     # Order management
│   │   ├── strategy.ts   # Webhook strategies
│   │   └── ...
│   ├── app/
│   │   └── providers.tsx # App-wide providers
│   ├── components/
│   │   ├── auth/         # Auth components
│   │   ├── layout/       # Layout components
│   │   │   ├── Layout.tsx
│   │   │   ├── Navbar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MobileBottomNav.tsx
│   │   └── ui/           # shadcn/ui components
│   ├── config/
│   │   └── navigation.ts # Navigation configuration
│   ├── hooks/            # Custom hooks
│   ├── lib/
│   │   └── utils.ts      # Utility functions
│   ├── pages/            # Page components
│   │   ├── admin/        # Admin pages
│   │   ├── chartink/     # Chartink pages
│   │   ├── monitoring/   # Monitoring pages
│   │   ├── python-strategy/
│   │   ├── strategy/     # Strategy pages
│   │   ├── telegram/     # Telegram pages
│   │   └── ...
│   ├── stores/           # Zustand stores
│   │   ├── authStore.ts
│   │   └── themeStore.ts
│   ├── test/             # Test utilities
│   ├── types/            # TypeScript types
│   ├── App.tsx           # Root component
│   ├── index.css         # Global styles
│   └── main.tsx          # Entry point
├── index.html
├── package.json
├── playwright.config.ts
├── tsconfig.json
├── vite.config.ts
└── vitest.config.ts
```

## NPM Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run Biome linter |
| `npm run format` | Format code with Biome |
| `npm run check` | Lint and format |
| `npm run test` | Run unit tests (watch mode) |
| `npm run test:run` | Run unit tests once |
| `npm run test:coverage` | Run tests with coverage |
| `npm run e2e` | Run E2E tests |
| `npm run e2e:ui` | Run E2E tests with UI |

## Code Conventions

### File Naming

- **Components**: PascalCase (`Button.tsx`, `MobileBottomNav.tsx`)
- **Utilities**: camelCase (`utils.ts`, `authStore.ts`)
- **Types**: PascalCase for types, camelCase for files (`types/chartink.ts`)
- **Tests**: Same name with `.test.tsx` suffix (`button.test.tsx`)

### Component Structure

```tsx
// 1. Imports (external, then internal)
import { useState } from 'react'
import { Button } from '@/components/ui/button'

// 2. Types/Interfaces
interface MyComponentProps {
  title: string
  onAction: () => void
}

// 3. Component
export function MyComponent({ title, onAction }: MyComponentProps) {
  // State
  const [isOpen, setIsOpen] = useState(false)

  // Handlers
  const handleClick = () => {
    setIsOpen(true)
    onAction()
  }

  // Render
  return (
    <div>
      <h1>{title}</h1>
      <Button onClick={handleClick}>Click me</Button>
    </div>
  )
}
```

### Import Aliases

Use `@/` alias for src imports:

```tsx
// Good
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'

// Avoid
import { Button } from '../../../components/ui/button'
```

### Styling

Use Tailwind CSS utility classes:

```tsx
// Good - Tailwind utilities
<div className="flex items-center gap-4 p-4 bg-background">

// Avoid - inline styles
<div style={{ display: 'flex', alignItems: 'center' }}>
```

Use `cn()` helper for conditional classes:

```tsx
import { cn } from '@/lib/utils'

<button className={cn(
  'px-4 py-2 rounded-md',
  isActive && 'bg-primary text-primary-foreground',
  isDisabled && 'opacity-50 cursor-not-allowed'
)}>
```

### State Management

Use Zustand for global state:

```tsx
// stores/myStore.ts
import { create } from 'zustand'

interface MyStore {
  count: number
  increment: () => void
}

export const useMyStore = create<MyStore>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
}))

// Usage in component
const { count, increment } = useMyStore()
```

Use TanStack Query for server state:

```tsx
import { useQuery } from '@tanstack/react-query'

const { data, isLoading, error } = useQuery({
  queryKey: ['orders'],
  queryFn: () => ordersApi.getOrders(),
})
```

## Adding New Features

### 1. Add a New Page

```tsx
// src/pages/MyNewPage.tsx
export default function MyNewPage() {
  return (
    <div className="container mx-auto py-6">
      <h1>My New Page</h1>
    </div>
  )
}
```

```tsx
// src/App.tsx - Add lazy import
const MyNewPage = lazy(() => import('@/pages/MyNewPage'))

// Add route
<Route path="/my-new-page" element={<MyNewPage />} />
```

### 2. Add a New API Module

```tsx
// src/api/myApi.ts
export const myApi = {
  async getData(): Promise<MyData[]> {
    const response = await fetch('/api/v1/my-endpoint', {
      credentials: 'include',
    })
    if (!response.ok) throw new Error('Failed to fetch')
    return response.json()
  },

  async createItem(data: CreateItemData): Promise<MyData> {
    const response = await fetch('/api/v1/my-endpoint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error('Failed to create')
    return response.json()
  },
}
```

### 3. Add a New UI Component

```tsx
// src/components/ui/my-component.tsx
import { cn } from '@/lib/utils'

interface MyComponentProps {
  className?: string
  children: React.ReactNode
}

export function MyComponent({ className, children }: MyComponentProps) {
  return (
    <div className={cn('base-classes', className)}>
      {children}
    </div>
  )
}
```

## Environment Variables

Vite exposes env vars prefixed with `VITE_`:

```env
# .env.local
VITE_API_URL=http://localhost:5000
VITE_FEATURE_FLAG=true
```

```tsx
// Access in code
const apiUrl = import.meta.env.VITE_API_URL
```

## Build & Deployment

### Production Build

```bash
npm run build
```

Output is in `dist/` directory with:
- Code splitting (lazy-loaded chunks)
- Vendor chunks (react, router, radix, icons, charts, syntax)
- Minified and tree-shaken

### Bundle Analysis

The build uses manual chunks for optimal caching:

| Chunk | Contents |
|-------|----------|
| `vendor-react` | React, ReactDOM, scheduler |
| `vendor-router` | React Router |
| `vendor-radix` | Radix UI primitives |
| `vendor-icons` | Lucide icons |
| `vendor-syntax` | Syntax highlighter (lazy) |
| `vendor-charts` | Recharts, D3 (lazy) |

### Deployment Checklist

1. Run tests: `npm run test:run && npm run e2e`
2. Run linter: `npm run lint`
3. Build: `npm run build`
4. Test build: `npm run preview`
5. Deploy `dist/` to static hosting

## Troubleshooting

### Common Issues

**Port already in use**
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

**Module not found**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**TypeScript errors**
```bash
# Check types
npx tsc --noEmit
```

**Vite cache issues**
```bash
# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

```


---

# FILE: frontend\docs\frontend\README.md

```md
# OpenAlgo Frontend Documentation

Welcome to the OpenAlgo React frontend documentation. This guide covers everything you need to know to develop, test, and maintain the frontend application.

## Table of Contents

1. [Developer Guide](./developer-guide.md) - Getting started, project structure, conventions
2. [Components](./components.md) - UI components, layouts, and patterns
3. [API Reference](./api-reference.md) - Hooks, stores, and API integration
4. [Testing Guide](./testing-guide.md) - Unit tests, E2E tests, accessibility testing

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | React 19 |
| Language | TypeScript |
| Build Tool | Vite 7 |
| Styling | Tailwind CSS 4 |
| UI Components | Radix UI + shadcn/ui |
| State Management | Zustand |
| Data Fetching | TanStack Query |
| Routing | React Router 7 |
| Testing | Vitest + Playwright |
| Linting | Biome |

## Project Overview

OpenAlgo frontend is a single-page application (SPA) that provides:

- **Dashboard** - Real-time trading overview
- **Order Management** - Orderbook, tradebook, positions
- **Strategy Management** - Webhook strategies, Python strategies, Chartink
- **Platform Integration** - TradingView, GoCharting webhooks
- **Admin Tools** - System configuration, monitoring, logs
- **Responsive Design** - Mobile-first with bottom navigation

## Architecture

```
src/
├── api/          # API client functions
├── components/   # Reusable UI components
├── config/       # App configuration
├── hooks/        # Custom React hooks
├── lib/          # Utility functions
├── pages/        # Route page components
├── stores/       # Zustand state stores
├── test/         # Test utilities
└── types/        # TypeScript type definitions
```

## Key Features

- **Code Splitting** - Lazy-loaded pages for optimal performance
- **Theme Support** - Light/dark mode with system preference
- **Accessibility** - WCAG 2.1 AA compliant
- **Real-time Updates** - WebSocket integration for live data
- **Offline Ready** - Graceful degradation when offline

```


---

# FILE: frontend\docs\frontend\session-management.md

```md
# Session Management

## Overview

OpenAlgo supports multi-device login with automatic session synchronization. A user can authenticate once with their broker (OAuth) and then access OpenAlgo from additional devices without repeating the broker login flow.

## Architecture

```
Device A (Desktop)                    Server                    Device B (Mobile)
     |                                  |                            |
     |-- POST /auth/login ------------>|                            |
     |   (username + password)         |                            |
     |                                 |-- Check DB for valid      |
     |                                 |   broker token            |
     |                                 |-- Validate via funds API  |
     |                                 |                            |
     |<-- {redirect: /dashboard} ------|                            |
     |   (session cookie set)          |                            |
     |                                 |                            |
     |                                 |   (Later, from mobile)     |
     |                                 |<-- POST /auth/login -------|
     |                                 |   (username + password)    |
     |                                 |-- Find existing token      |
     |                                 |-- Validate via funds API   |
     |                                 |-- Resume session (no OAuth)|
     |                                 |-----> {redirect: /dashboard}
     |                                 |                            |
     |   (Logout from any device)      |                            |
     |-- POST /auth/logout ----------->|                            |
     |                                 |-- Revoke broker token      |
     |                                 |-- Clear all sessions       |
     |                                 |-- Emit force_logout ------>|
     |                                 |                            |-- Auto-redirect
     |                                 |                            |   to /login
```

## Login Flow

### Single Device (First Login of the Day)

1. User enters username/password at `/login`
2. Server checks DB for an existing non-revoked broker token
3. **No valid token found** -> redirect to `/broker` for OAuth
4. User completes broker OAuth (Zerodha, Dhan, etc.)
5. `handle_auth_success()` stores token in DB + sets session cookie
6. User lands on `/dashboard`

### Multi-Device (Session Resume)

1. User enters username/password on a second device
2. Server finds a valid broker token in the DB (from device A's login)
3. Server validates the token with a lightweight `get_margin_data()` API call
4. **Token valid** -> `handle_auth_success()` creates a new session cookie for this device
5. Returns `{redirect: "/dashboard", broker: "dhan"}` -> user goes straight to dashboard
6. **Token invalid/expired** -> falls through to normal OAuth flow

### Token Validation

The resume flow validates the broker token by calling the broker's funds API (`get_margin_data()`). This is chosen because:
- It's lightweight (single API call, no side effects)
- It returns an empty dict `{}` if the token is expired/invalid
- It works consistently across all 24+ brokers

If the funds API returns empty or throws, the resume is aborted and the user is redirected to broker OAuth.

## Session Storage

### Flask Session (Client-Side Cookie)

- Signed by `APP_KEY` (tamper-proof, not encrypted)
- Contains: `logged_in`, `AUTH_TOKEN`, `broker`, `session_id`, `login_time`
- `HttpOnly`, `SameSite=Lax`, `Secure` (when HTTPS enabled)
- Expires daily at 3:00 AM IST (configurable via `SESSION_EXPIRY_TIME`)

### Auth Table (Server-Side)

- `auth` table stores encrypted broker token per user (single row, upserted)
- `is_revoked` flag marks invalid tokens
- Shared across all devices (devices read the same token)

### ActiveSession Table (Server-Side)

- Tracks which devices are currently logged in
- Columns: `username`, `session_id`, `device_info` (User-Agent), `ip_address`, `broker`, `login_time`, `last_seen`
- Deduplication: same `(username, ip_address)` replaces old entry
- Safety cap: maximum 5 sessions per user (oldest evicted)
- Cleared on logout and on 3 AM auto-expiry

## Logout Behavior

Logout from **any device** triggers a global logout:

1. Broker token revoked in DB (`is_revoked = True`)
2. All `ActiveSession` rows for the user are deleted
3. `force_logout` SocketIO event emitted to all connected clients
4. Other devices receive the event, show an error toast, and redirect to `/login`
5. Session cookie cleared on the requesting device

### 3 AM Auto-Expiry

- `is_session_valid()` checks if current time has passed the daily expiry (3 AM IST)
- On expiry: `revoke_user_tokens()` revokes the DB token and clears all active sessions
- Next login requires fresh broker OAuth (correct for Indian brokers with daily token validity)
- Crypto brokers can disable expiry via `DISABLE_SESSION_EXPIRY=true`

## Frontend Integration

### Zustand Auth Store

- `useAuthStore` persists `{username, broker, isLoggedIn}` to `localStorage`
- On login with resume, the backend returns `broker` in the response so the store is populated immediately (avoids Layout redirect guard)

### Active Sessions in Footer

- Initial count loaded from `GET /auth/session-status` (`active_sessions` field)
- Live updates via `active_sessions_update` SocketIO event (no polling)
- Displayed as `[Monitor icon] N sessions` badge in the footer

### Force Logout (SocketIO)

- `force_logout` event triggers immediate client-side logout
- Shows error toast: "You have been logged out from another device."
- 2-second delay before redirect so user sees the message

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/auth/login` | POST | Username/password auth + session resume attempt |
| `/auth/logout` | POST | Logout all devices, revoke broker token |
| `/auth/session-status` | GET | Session info + `active_sessions` count |
| `/auth/active-sessions` | GET | Full list of active sessions with device info |

## Security

- **Password required**: Session resume only works after valid username/password authentication
- **Token validation**: Broker token is validated with a live API call before resume
- **Session ID**: Generated with `secrets.token_hex(32)` (cryptographically secure)
- **Session cap**: Maximum 5 active sessions per user (prevents unbounded growth)
- **IP deduplication**: Repeated logins from the same IP replace the old session entry
- **Global logout**: Any device can trigger logout for all devices
- **Auto-cleanup**: 3 AM IST daily expiry clears all sessions and revokes broker tokens

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `SESSION_EXPIRY_TIME` | `03:00` | Daily session expiry time (HH:MM, IST) |
| `DISABLE_SESSION_EXPIRY` | `false` | Set to `true` for crypto brokers (24/7) |
| `APP_KEY` | (required) | Flask secret key for signing session cookies |

```


---

# FILE: frontend\docs\frontend\testing-guide.md

```md
# Testing Guide

This guide covers testing practices for the OpenAlgo frontend, including unit tests, E2E tests, and accessibility testing.

## Testing Stack

| Tool | Purpose |
|------|---------|
| Vitest | Unit testing framework |
| Testing Library | React component testing |
| jest-axe | Accessibility testing (unit) |
| Playwright | End-to-end testing |
| @axe-core/playwright | Accessibility testing (E2E) |

## Running Tests

```bash
# Unit tests (watch mode)
npm run test

# Unit tests (single run)
npm run test:run

# Unit tests with coverage
npm run test:coverage

# Accessibility-focused unit tests
npm run test:a11y

# E2E tests (all browsers)
npm run e2e

# E2E tests (with UI)
npm run e2e:ui

# E2E tests (debug mode)
npm run e2e:debug

# E2E codegen (record tests)
npm run e2e:codegen
```

## Unit Testing

### File Structure

```
src/
├── components/
│   └── ui/
│       ├── button.tsx
│       └── button.test.tsx     # Test file next to component
├── config/
│   ├── navigation.ts
│   └── navigation.test.ts
└── test/
    ├── setup.ts               # Test setup
    ├── test-utils.tsx         # Custom render
    └── a11y-utils.ts          # Accessibility helpers
```

### Test Setup

The test setup file (`src/test/setup.ts`) configures:

- Testing Library DOM matchers
- Window/browser API mocks
- Cleanup after each test

```tsx
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(() => {
  cleanup()
})

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))
```

### Custom Render

Use the custom render for components that need providers:

```tsx
// src/test/test-utils.tsx
import { render } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

function AllTheProviders({ children }) {
  return <BrowserRouter>{children}</BrowserRouter>
}

function customRender(ui, options) {
  return render(ui, { wrapper: AllTheProviders, ...options })
}

export * from '@testing-library/react'
export { customRender as render }
```

### Writing Unit Tests

#### Basic Component Test

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { Button } from './button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)

    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('applies variant classes', () => {
    render(<Button variant="destructive">Delete</Button>)

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('data-variant', 'destructive')
  })
})
```

#### Testing User Interactions

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, userEvent } from '@/test/test-utils'
import { Button } from './button'

describe('Button interactions', () => {
  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(<Button onClick={handleClick}>Click me</Button>)

    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(<Button disabled onClick={handleClick}>Click me</Button>)

    await user.click(screen.getByRole('button'))

    expect(handleClick).not.toHaveBeenCalled()
  })
})
```

#### Testing with Router

```tsx
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { MobileBottomNav } from './MobileBottomNav'

function renderWithRouter(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <MobileBottomNav />
    </MemoryRouter>
  )
}

describe('MobileBottomNav', () => {
  it('highlights active route', () => {
    renderWithRouter('/dashboard')

    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    expect(dashboardLink).toHaveClass('text-primary')
  })
})
```

#### Testing Async Operations

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@/test/test-utils'
import { OrderBook } from './OrderBook'

// Mock the API
vi.mock('@/api/orders', () => ({
  ordersApi: {
    getOrderBook: vi.fn().mockResolvedValue([
      { id: '1', symbol: 'RELIANCE', status: 'COMPLETE' },
    ]),
  },
}))

describe('OrderBook', () => {
  it('loads and displays orders', async () => {
    render(<OrderBook />)

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('RELIANCE')).toBeInTheDocument()
    })
  })
})
```

### Accessibility Testing (Unit)

```tsx
import { axe, toHaveNoViolations } from 'jest-axe'
import { describe, expect, it } from 'vitest'
import { render } from '@/test/test-utils'
import { Button } from './button'

expect.extend(toHaveNoViolations)

describe('Button accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>)

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('icon button needs aria-label', async () => {
    const { container } = render(
      <Button size="icon" aria-label="Close">
        X
      </Button>
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

### Snapshot Testing

```tsx
import { describe, expect, it } from 'vitest'
import { render } from '@/test/test-utils'
import { Badge } from './badge'

describe('Badge', () => {
  it('matches snapshot', () => {
    const { container } = render(<Badge>New</Badge>)
    expect(container).toMatchSnapshot()
  })
})
```

## E2E Testing

### Playwright Configuration

```tsx
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

### Writing E2E Tests

#### Basic Page Test

```tsx
// e2e/home.spec.ts
import { expect, test } from '@playwright/test'

test.describe('Home Page', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    await expect(page.locator('body')).toBeVisible()
  })

  test('should navigate to login', async ({ page }) => {
    await page.goto('/')

    const loginLink = page.getByRole('link', { name: /login/i })
    if (await loginLink.isVisible()) {
      await loginLink.click()
      await expect(page).toHaveURL(/login/)
    }
  })
})
```

#### Testing Forms

```tsx
// e2e/auth.spec.ts
import { expect, test } from '@playwright/test'

test.describe('Authentication', () => {
  test('should show login form', async ({ page }) => {
    await page.goto('/login')

    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('should handle login', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[id="username"]', 'testuser')
    await page.fill('input[id="password"]', 'testpass')
    await page.click('button[type="submit"]')

    // Wait for redirect or error
    await page.waitForLoadState('networkidle')
  })
})
```

#### Mobile Testing

```tsx
// e2e/navigation.spec.ts
import { expect, test } from '@playwright/test'

test.describe('Mobile Navigation', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('should show bottom navigation', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    // Check for bottom nav on mobile
    const bottomNav = page.locator('nav.md\\:hidden')
    if (await bottomNav.isVisible()) {
      await expect(bottomNav).toBeVisible()
    }
  })

  test('should have touch-friendly buttons', async ({ page }) => {
    await page.goto('/dashboard')

    const navLinks = page.locator('.touch-manipulation')
    const count = await navLinks.count()
    expect(count).toBeGreaterThan(0)
  })
})
```

#### Responsive Testing

```tsx
test('should adapt to viewport changes', async ({ page }) => {
  await page.goto('/')

  // Desktop
  await page.setViewportSize({ width: 1280, height: 720 })
  await expect(page.locator('.hidden.md\\:flex')).toBeVisible()

  // Mobile
  await page.setViewportSize({ width: 375, height: 667 })
  await expect(page.locator('.md\\:hidden')).toBeVisible()
})
```

### Accessibility Testing (E2E)

```tsx
// e2e/accessibility.spec.ts
import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

test.describe('Accessibility', () => {
  test('home page accessibility scan', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    // Log violations for review
    if (results.violations.length > 0) {
      console.log('Violations:', results.violations.map(v => v.id))
    }

    // Filter critical violations
    const critical = results.violations.filter(
      v => v.impact === 'critical'
    )
    expect(critical).toEqual([])
  })

  test('color contrast check', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const results = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze()

    const critical = results.violations.filter(
      v => v.impact === 'critical'
    )
    expect(critical).toEqual([])
  })
})
```

### Visual Regression Testing

```tsx
test('visual regression', async ({ page }) => {
  await page.goto('/dashboard')
  await page.waitForLoadState('networkidle')

  // Full page screenshot
  await expect(page).toHaveScreenshot('dashboard.png', {
    fullPage: true,
    maxDiffPixels: 100,
  })

  // Component screenshot
  const card = page.locator('.card').first()
  await expect(card).toHaveScreenshot('card.png')
})
```

### Test Fixtures

```tsx
// e2e/fixtures.ts
import { test as base } from '@playwright/test'

// Custom fixture with authenticated user
export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    // Login before test
    await page.goto('/login')
    await page.fill('#username', 'testuser')
    await page.fill('#password', 'testpass')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')

    await use(page)
  },
})

// Usage
test('authenticated test', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/positions')
  // User is already logged in
})
```

## Test Coverage

### Running Coverage

```bash
npm run test:coverage
```

### Coverage Report

Coverage reports are generated in `coverage/` directory:
- `coverage/index.html` - HTML report
- `coverage/lcov.info` - LCOV format

### Coverage Thresholds

Configure in `vitest.config.ts`:

```tsx
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
      // Thresholds (optional)
      // thresholds: {
      //   statements: 80,
      //   branches: 80,
      //   functions: 80,
      //   lines: 80,
      // },
    },
  },
})
```

## Best Practices

### Test Organization

```tsx
describe('ComponentName', () => {
  describe('rendering', () => {
    it('renders with default props', () => {})
    it('renders with custom props', () => {})
  })

  describe('interactions', () => {
    it('handles click', () => {})
    it('handles keyboard', () => {})
  })

  describe('accessibility', () => {
    it('has no violations', () => {})
    it('supports keyboard navigation', () => {})
  })
})
```

### Naming Conventions

```tsx
// Good - describes behavior
it('disables submit button when form is invalid', () => {})
it('shows error message when API fails', () => {})

// Avoid - implementation details
it('sets isDisabled to true', () => {})
it('calls setError with message', () => {})
```

### Testing User Behavior

```tsx
// Good - test what user sees
await user.click(screen.getByRole('button', { name: /submit/i }))
expect(screen.getByText(/success/i)).toBeInTheDocument()

// Avoid - testing implementation
expect(component.state.isSubmitting).toBe(true)
```

### Async Best Practices

```tsx
// Good - use waitFor for async assertions
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Good - use findBy for async queries
const element = await screen.findByText('Loaded')

// Avoid - arbitrary waits
await new Promise(r => setTimeout(r, 1000))
```

### Mocking Guidelines

```tsx
// Mock at the module level
vi.mock('@/api/orders', () => ({
  ordersApi: {
    getOrders: vi.fn(),
  },
}))

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks()
})

// Provide specific return values per test
it('handles error', async () => {
  vi.mocked(ordersApi.getOrders).mockRejectedValueOnce(
    new Error('Network error')
  )
  // ...
})
```

## Debugging Tests

### Unit Tests

```bash
# Run specific test file
npm run test -- button.test.tsx

# Run tests matching pattern
npm run test -- --grep "accessibility"

# Debug in VS Code
# Add breakpoints and run "Debug Test" from VS Code
```

### E2E Tests

```bash
# Debug mode (step through)
npm run e2e:debug

# UI mode (visual debugging)
npm run e2e:ui

# Record new test
npm run e2e:codegen

# Run specific test
npm run e2e -- --grep "login"

# Headed mode (see browser)
npm run e2e -- --headed
```

### Trace Viewer

```bash
# View trace after failure
npx playwright show-trace test-results/*/trace.zip
```

```


---

# FILE: frontend\docs\frontend\websocket-manager.md

```md
# WebSocket Connection Manager

## Product Requirements Document (PRD)

### Overview

**Feature:** Shared WebSocket Connection Manager
**Issue:** [#848](https://github.com/marketcalls/openalgo/issues/848)
**Status:** Implemented
**Release:** v2.x

### Problem Statement

The OpenAlgo React frontend requires real-time market data across multiple pages and components. Previously, each component that needed market data created its own WebSocket connection, leading to:

| Problem | Impact |
|---------|--------|
| Multiple WebSocket connections | 3-4 connections per user session |
| Redundant authentication | Each connection authenticates separately |
| Duplicate subscriptions | Same symbol subscribed multiple times |
| Resource waste | Server handles N connections instead of 1 |
| Inconsistent state | Each component manages its own connection lifecycle |

**Example of the problem:**
```
Holdings page    → WebSocket #1 → Subscribe RELIANCE, TCS
Positions page   → WebSocket #2 → Subscribe RELIANCE, INFY
PlaceOrderDialog → WebSocket #3 → Subscribe RELIANCE
OptionChain      → WebSocket #4 → Subscribe NIFTY options (50+ symbols)
```
Result: 4 connections, 4 authentications, RELIANCE subscribed 3 times.

### Goals

1. **Single Connection:** One WebSocket connection shared across all components
2. **Ref-counted Subscriptions:** Subscribe to each symbol only once, regardless of how many components need it
3. **Centralized Lifecycle:** Single point of control for connect/disconnect/pause/resume
4. **Backward Compatibility:** Existing hooks (`useMarketData`, `useLivePrice`, `useLiveQuote`) continue to work with unchanged API
5. **Resource Optimization:** Pause connection when tab is hidden to save bandwidth

### Non-Goals

- Persisting WebSocket connection across page refreshes (requires Service Workers)
- Multi-tab connection sharing (out of scope)
- Modifying the WebSocket server protocol

### REST API Fallback

When WebSocket connections fail (e.g., after market hours when the broker WebSocket is unavailable), the system automatically falls back to REST API polling:

| Scenario | Behavior |
|----------|----------|
| WebSocket connects successfully | Real-time data via WebSocket |
| WebSocket fails 3 consecutive times | Automatic switch to REST API polling |
| REST API polling | Fetches `/api/v1/multiquotes` every 5 seconds |
| WebSocket restored | Automatic switch back to WebSocket |

### Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| WebSocket connections per session | 3-4 | 1 | 1 |
| Authentication requests | 3-4 | 1 | 1 |
| Duplicate symbol subscriptions | Yes | No | No |
| Memory usage (callbacks) | N × data | 1 × data | Reduced |

### User Stories

1. **As a trader**, I want real-time prices on Holdings and Positions pages without creating multiple server connections.

2. **As a trader**, I want the WebSocket to pause when I switch to another browser tab to save bandwidth.

3. **As a trader**, I want the connection to resume automatically when I return to the OpenAlgo tab.

4. **As a developer**, I want to use the same `useMarketData` hook API without worrying about connection management.

---

## Technical Design Document

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                            App.tsx                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                        Providers.tsx                           │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │                  MarketDataProvider                      │  │  │
│  │  │         (React Context + Visibility Handling)            │  │  │
│  │  │                         │                                │  │  │
│  │  │                         ▼                                │  │  │
│  │  │              MarketDataManager (Singleton)               │  │  │
│  │  │                         │                                │  │  │
│  │  │                         ▼                                │  │  │
│  │  │              Single WebSocket to :8765                   │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Holdings │  │Positions │  │  Order   │  │   OptionChain    │    │
│  │          │  │          │  │  Dialog  │  │                  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘    │
│       │             │             │                  │              │
│       ▼             ▼             ▼                  ▼              │
│  useLivePrice  useLivePrice  useLiveQuote   useOptionChainLive     │
│       │             │             │                  │              │
│       └─────────────┴─────────────┴──────────────────┘              │
│                              │                                       │
│                              ▼                                       │
│                       useMarketData                                  │
│                              │                                       │
│                              ▼                                       │
│                    MarketDataManager.subscribe()                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Design

#### 1. MarketDataManager (Singleton)

**Location:** `src/lib/MarketDataManager.ts`

**Purpose:** Centralized WebSocket connection and subscription management.

**Design Pattern:** Singleton with ref-counted subscriptions and callback registry.

```typescript
class MarketDataManager {
  // Singleton instance
  private static instance: MarketDataManager | null = null

  // WebSocket connection
  private socket: WebSocket | null = null

  // Subscriptions with reference counting
  // Key: "EXCHANGE:SYMBOL:MODE" (e.g., "NSE:RELIANCE:LTP")
  private subscriptions: Map<string, SubscriptionEntry> = new Map()

  // Cached market data for immediate delivery to new subscribers
  // Key: "EXCHANGE:SYMBOL" (e.g., "NSE:RELIANCE")
  private dataCache: Map<string, SymbolData> = new Map()

  // Connection state listeners
  private stateListeners: Set<StateListener> = new Set()
}
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `getInstance()` | Get singleton instance |
| `subscribe(symbol, exchange, mode, callback)` | Subscribe to market data, returns unsubscribe function |
| `connect()` | Establish WebSocket connection |
| `disconnect()` | Close connection |
| `pauseConnection()` | Close connection but keep subscriptions in memory |
| `resumeConnection()` | Reconnect and resubscribe all symbols |
| `addStateListener(listener)` | Listen for connection state changes |
| `getCachedData(symbol, exchange)` | Get cached data for immediate display |

**Subscription Reference Counting:**

```
Component A subscribes to RELIANCE
  └─► subscriptions["NSE:RELIANCE:LTP"] = { refCount: 1, callbacks: [A] }
  └─► WebSocket: SUBSCRIBE RELIANCE

Component B subscribes to RELIANCE
  └─► subscriptions["NSE:RELIANCE:LTP"] = { refCount: 2, callbacks: [A, B] }
  └─► WebSocket: (no message - already subscribed)

Component A unsubscribes
  └─► subscriptions["NSE:RELIANCE:LTP"] = { refCount: 1, callbacks: [B] }
  └─► WebSocket: (no message - still has subscribers)

Component B unsubscribes
  └─► subscriptions["NSE:RELIANCE:LTP"] = (deleted)
  └─► WebSocket: UNSUBSCRIBE RELIANCE
```

#### 2. MarketDataContext (React Context)

**Location:** `src/contexts/MarketDataContext.tsx`

**Purpose:** Provide MarketDataManager to React component tree with centralized visibility handling.

**Key Features:**
- Wraps MarketDataManager singleton
- Handles tab visibility (pause after 5s hidden, resume on visible)
- Exposes connection state to all children

```typescript
interface MarketDataContextValue {
  manager: MarketDataManager
  connectionState: ConnectionState
  isConnected: boolean
  isAuthenticated: boolean
  isPaused: boolean
  isFallbackMode: boolean  // NEW: true when using REST API polling
  error: string | null
  subscribe: (symbol, exchange, mode, callback) => () => void
  getCachedData: (symbol, exchange) => SymbolData | undefined
  connect: () => Promise<void>
  disconnect: () => void
}
```

#### 3. useMarketData Hook (Refactored)

**Location:** `src/hooks/useMarketData.ts`

**Purpose:** React hook for subscribing to market data (backward-compatible API).

**Before Refactor:** ~464 lines, manages own WebSocket
**After Refactor:** ~150 lines, delegates to MarketDataManager

**API (unchanged):**
```typescript
function useMarketData({
  symbols: Array<{ symbol: string; exchange: string }>,
  mode?: 'LTP' | 'Quote' | 'Depth',
  enabled?: boolean,
}): {
  data: Map<string, SymbolData>,
  isConnected: boolean,
  isAuthenticated: boolean,
  isConnecting: boolean,
  isPaused: boolean,
  isFallbackMode: boolean,  // NEW: true when using REST API polling
  error: string | null,
  connect: () => Promise<void>,
  disconnect: () => void,
}
```

### State Machine

```
                                    ┌─────────────┐
                                    │ disconnected│◄──────────────────┐
                                    └──────┬──────┘                   │
                                           │                          │
                                    connect()                         │
                                           │                          │
                                           ▼                          │
                                    ┌─────────────┐                   │
                                    │ connecting  │                   │
                                    └──────┬──────┘                   │
                                           │                          │
                                    socket.onopen                     │
                                           │                          │
                                           ▼                          │
                                    ┌─────────────┐                   │
                                    │  connected  │                   │
                                    └──────┬──────┘                   │
                                           │                          │
                                    send auth                    disconnect()
                                           │                     or error
                                           ▼                          │
                                    ┌──────────────┐                  │
                                    │authenticating│                  │
                                    └──────┬───────┘                  │
                                           │                          │
                                    auth success                      │
                                           │                          │
                                           ▼                          │
┌────────┐  pauseConnection()      ┌──────────────┐                   │
│ paused │◄────────────────────────│authenticated │───────────────────┘
└───┬────┘                         └──────────────┘
    │
    │ resumeConnection()
    │
    └──────────────────────────────► connecting
```

### REST API Fallback Mode

When WebSocket connections fail repeatedly (e.g., after market hours), the system automatically switches to REST API polling:

```
WebSocket Connection Attempt
           │
     Connection fails
           │
           ▼
┌──────────────────┐
│ Increment failure│
│ counter          │
└────────┬─────────┘
         │
         ├───── failures < 3 ──────► Retry WebSocket
         │
         └───── failures >= 3
                     │
                     ▼
          ┌─────────────────┐
          │ Enable Fallback │
          │    Mode         │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Fetch API Key   │
          │ from server     │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Start polling   │
          │ /api/v1/multi   │
          │ quotes (5s)     │
          └────────┬────────┘
                   │
     ┌─────────────┴─────────────┐
     │                           │
WebSocket restored        Continue polling
     │                           │
     ▼                           ▼
┌─────────────────┐    ┌─────────────────┐
│ Disable fallback│    │ Update market   │
│ Stop polling    │    │ data cache      │
│ Reset failures  │    │ Notify callbacks│
└─────────────────┘    └─────────────────┘
```

**Key behaviors:**
- **Trigger:** 3 consecutive WebSocket connection failures OR max reconnect attempts reached
- **Polling interval:** 5 seconds (configurable via `setFallbackPollingRate()`)
- **API endpoint:** `/api/v1/multiquotes` with all subscribed symbols
- **Auto-recovery:** When WebSocket successfully reconnects, fallback mode is automatically disabled

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      WebSocket Server :8765                      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                          market_data message
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MarketDataManager                           │
│                                                                  │
│  1. Parse message: { symbol: "RELIANCE", exchange: "NSE", ... } │
│  2. Update dataCache["NSE:RELIANCE"]                            │
│  3. Find subscriptions for NSE:RELIANCE                         │
│  4. Call each callback with updated data                        │
│                                                                  │
└──────────────┬─────────────────┬─────────────────┬──────────────┘
               │                 │                 │
               ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ Holdings │      │ Positions│      │  Order   │
        │ callback │      │ callback │      │  Dialog  │
        │          │      │          │      │ callback │
        └──────────┘      └──────────┘      └──────────┘
               │                 │                 │
               ▼                 ▼                 ▼
        setMarketData()   setMarketData()   setMarketData()
               │                 │                 │
               ▼                 ▼                 ▼
          React re-render with new LTP values
```

### Visibility Handling

**Purpose:** Save bandwidth and server resources when user isn't viewing the page.

**Flow:**
```
Tab Hidden
    │
    ▼
Start 5-second timer
    │
    ├─► Tab Visible before 5s → Cancel timer, no action
    │
    └─► Still hidden after 5s
            │
            ▼
        pauseConnection()
            │
            ├─► Close WebSocket
            └─► Keep subscriptions in memory
                    │
                    ▼
                Tab Visible
                    │
                    ▼
                resumeConnection()
                    │
                    ├─► Create new WebSocket
                    ├─► Authenticate
                    └─► Resubscribe all symbols
```

**Why 5-second delay?**
- Prevents unnecessary disconnect for quick tab switches
- User might switch tabs briefly to check something
- Reconnection has overhead (auth, resubscribe)

### Connection Guard

**Problem:** Multiple components calling `connect()` simultaneously could create race conditions.

**Solution:** Comprehensive state checking before creating new connection:

```typescript
async connect(): Promise<void> {
  // Guard against multiple connections
  if (
    this.socket?.readyState === WebSocket.OPEN ||
    this.socket?.readyState === WebSocket.CONNECTING ||
    this.connectionState === 'connecting' ||
    this.connectionState === 'connected' ||
    this.connectionState === 'authenticating' ||
    this.connectionState === 'authenticated'
  ) {
    return  // Already connected or connecting
  }

  this.setConnectionState('connecting')
  // ... proceed with connection
}
```

---

## Implementation Details

### Files Created

| File | Purpose |
|------|---------|
| `src/lib/MarketDataManager.ts` | Singleton WebSocket manager |
| `src/contexts/MarketDataContext.tsx` | React context and provider |

### Files Modified

| File | Change |
|------|--------|
| `src/app/providers.tsx` | Added `<MarketDataProvider>` |
| `src/hooks/useMarketData.ts` | Refactored to use MarketDataManager |

### Files Unchanged

| File | Reason |
|------|--------|
| `src/hooks/useLivePrice.ts` | Uses useMarketData internally (API unchanged) |
| `src/hooks/useLiveQuote.ts` | Uses useMarketData internally (API unchanged) |
| `src/hooks/useOptionChainLive.ts` | Uses useMarketData internally (API unchanged) |
| `src/pages/WebSocketTest.tsx` | Intentionally independent for testing |

### Hook Dependency Chain

```
useLivePrice ────────┐
                     │
useLiveQuote ────────┼───► useMarketData ───► MarketDataManager
                     │
useOptionChainLive ──┘
```

---

## API Reference

### MarketDataManager

```typescript
class MarketDataManager {
  /**
   * Get the singleton instance
   */
  static getInstance(): MarketDataManager

  /**
   * Subscribe to market data for a symbol
   * @returns Unsubscribe function
   */
  subscribe(
    symbol: string,
    exchange: string,
    mode: 'LTP' | 'Quote' | 'Depth',
    callback: (data: SymbolData) => void
  ): () => void

  /**
   * Connect to WebSocket server
   * Safe to call multiple times - will not create duplicate connections
   */
  connect(): Promise<void>

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void

  /**
   * Pause connection (close socket, keep subscriptions)
   * Used when tab is hidden
   */
  pauseConnection(): void

  /**
   * Resume connection after pause
   * Reconnects and resubscribes to all symbols
   */
  resumeConnection(): Promise<void>

  /**
   * Add listener for connection state changes
   * @returns Unsubscribe function
   */
  addStateListener(listener: StateListener): () => void

  /**
   * Get current connection state
   */
  getState(): {
    connectionState: ConnectionState
    isConnected: boolean
    isAuthenticated: boolean
    isPaused: boolean
    isFallbackMode: boolean  // true when using REST API polling
    error: string | null
  }

  /**
   * Check if currently in fallback mode (REST API polling)
   */
  isFallback(): boolean

  /**
   * Set the polling rate for REST API fallback mode
   * @param rate Polling interval in milliseconds (default: 5000)
   */
  setFallbackPollingRate(rate: number): void

  /**
   * Get cached data for a symbol (for immediate display)
   */
  getCachedData(symbol: string, exchange: string): SymbolData | undefined
}
```

### Types

```typescript
type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'authenticating'
  | 'authenticated'
  | 'paused'

type SubscriptionMode = 'LTP' | 'Quote' | 'Depth'

interface SymbolData {
  symbol: string
  exchange: string
  data: MarketData
  lastUpdate?: number
}

interface MarketData {
  ltp?: number
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
  change?: number
  change_percent?: number
  bid_price?: number
  ask_price?: number
  bid_size?: number
  ask_size?: number
  depth?: {
    buy: DepthLevel[]
    sell: DepthLevel[]
  }
}
```

---

## Testing Guide

### Manual Testing Checklist

- [x] Only 1 WebSocket in DevTools Network tab (Socket filter)
- [x] Same symbol subscribed once even if multiple components need it
- [x] Tab hidden >5s → connection pauses
- [x] Tab visible → connection resumes and resubscribes
- [x] PlaceOrderDialog uses existing connection
- [x] OptionChain streams LTP correctly
- [x] Holdings/Positions show live P&L updates
- [x] Navigation between pages doesn't create new connections
- [x] Page refresh creates new connection (expected)

### REST API Fallback Testing

- [x] WebSocket fails 3+ times → switches to REST API polling
- [x] Console shows `[MarketDataManager] Switching to REST API fallback mode`
- [x] Market data still updates every 5 seconds in fallback mode
- [x] `isFallbackMode` is `true` in fallback mode
- [x] WebSocket restored → automatic switch back (console: `Disabling REST API fallback mode`)
- [x] After-market-hours usage works with REST API polling

### How to Verify Single Connection

1. Open DevTools → Network tab
2. Click **Clear** (🚫) to reset history
3. Click **Socket** filter (or **WS** in some browsers)
4. Navigate to a page with market data (e.g., Positions)
5. Verify **1 WebSocket connection** appears with status "Pending"
6. Navigate to other pages (Holdings, OptionChain, Dashboard)
7. Verify **still only 1 WebSocket** (same connection reused)

### DevTools Connection Status

| Time Column | Meaning |
|-------------|---------|
| `Pending` | Active connection |
| `14.35 s` | Closed (was open for 14.35 seconds) |
| `(unknown)` | Closed immediately or failed |

---

## FAQ

### Why do I see multiple WebSocket connections in DevTools?

DevTools keeps a **history** of all connections. Connections with a time duration (e.g., "14.35 s") are **closed**. Only "Pending" connections are active. Click Clear to reset the history.

### Why does refreshing the page create a new connection?

Page refresh destroys the JavaScript context, including the singleton instance. This is unavoidable without using Service Workers or SharedWorkers.

### Why does switching tabs close the connection?

This is a **feature** to save bandwidth and server resources. When you're not viewing the page, there's no need to receive market data updates. The connection resumes automatically when you return.

### Can I disable the pause-when-hidden behavior?

Yes, pass `pauseWhenHidden: false` to the MarketDataProvider:

```tsx
<MarketDataProvider pauseWhenHidden={false}>
  {children}
</MarketDataProvider>
```

### How does subscription deduplication work?

Each subscription is keyed by `EXCHANGE:SYMBOL:MODE`. If two components subscribe to the same key, only one WebSocket subscription is created. A reference count tracks how many components are using it. The WebSocket unsubscribe is only sent when the last component unsubscribes.

### Why is the app using REST API instead of WebSocket?

This happens when the WebSocket connection fails repeatedly (3+ times). Common causes:
- **After market hours:** Broker WebSocket servers may be unavailable
- **Network issues:** Unstable connection causing frequent disconnects
- **Server maintenance:** WebSocket server temporarily down

The app automatically switches to REST API polling (`/api/v1/multiquotes`) every 5 seconds. When WebSocket becomes available again, it will automatically switch back.

### How can I tell if I'm in fallback mode?

Check the `isFallbackMode` property in your hook or context:

```typescript
const { isFallbackMode } = useMarketData({ symbols, mode: 'LTP' })

if (isFallbackMode) {
  console.log('Using REST API polling - WebSocket unavailable')
}
```

### Can I change the REST API polling interval?

Yes, use the `setFallbackPollingRate()` method on the MarketDataManager:

```typescript
const manager = MarketDataManager.getInstance()
manager.setFallbackPollingRate(10000) // Poll every 10 seconds
```

### Why does REST API fallback need an API key?

The `/api/v1/multiquotes` endpoint requires authentication. The MarketDataManager automatically fetches your API key from `/api/v1/apikey` when entering fallback mode.

---

## Changelog

### v1.1.0 (REST API Fallback)

- **NEW:** Automatic REST API fallback when WebSocket fails
  - Triggers after 3 consecutive connection failures
  - Polls `/api/v1/multiquotes` every 5 seconds
  - Automatically recovers when WebSocket is restored
- **NEW:** `isFallbackMode` state exposed in hook, context, and manager
- **NEW:** `setFallbackPollingRate()` method to customize polling interval
- **NEW:** `isFallback()` method on MarketDataManager
- Improved reliability for after-market-hours usage

### v1.0.0 (Issue #848)

- Initial implementation of shared WebSocket connection manager
- Singleton pattern for MarketDataManager
- Ref-counted subscriptions
- React Context for provider integration
- Visibility handling (pause after 5s hidden)
- Backward-compatible useMarketData API
- Connection guard to prevent duplicate connections

```
