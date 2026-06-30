# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\config



---

# FILE: frontend\src\config\navigation.test.ts

```ts
import { describe, expect, it } from 'vitest'
import {
  bottomNavItems,
  isActiveRoute,
  mobileSheetItems,
  navItems,
  profileMenuItems,
} from './navigation'

describe('Navigation Config', () => {
  describe('navItems', () => {
    it('contains the expected main navigation items', () => {
      expect(navItems).toHaveLength(9)

      const labels = navItems.map((item) => item.label)
      expect(labels).toContain('Dashboard')
      expect(labels).toContain('Tools')
      expect(labels).toContain('Orderbook')
      expect(labels).toContain('Positions')
      expect(labels).toContain('Strategy')
    })

    it('all items have required properties', () => {
      navItems.forEach((item) => {
        expect(item).toHaveProperty('href')
        expect(item).toHaveProperty('label')
        expect(item).toHaveProperty('icon')
        expect(item.href).toMatch(/^\//)
        expect(item.label.length).toBeGreaterThan(0)
      })
    })
  })

  describe('bottomNavItems', () => {
    it('contains exactly 5 items for mobile bottom nav', () => {
      expect(bottomNavItems).toHaveLength(5)
    })

    it('has the correct order: Dashboard, Orderbook, Tradebook, Positions, Strategy', () => {
      const labels = bottomNavItems.map((item) => item.label)
      expect(labels).toEqual(['Dashboard', 'Orderbook', 'Tradebook', 'Positions', 'Strategy'])
    })
  })

  describe('mobileSheetItems', () => {
    it('excludes items already in bottomNavItems', () => {
      const bottomPaths = bottomNavItems.map((item) => item.href)
      const sheetPaths = mobileSheetItems.map((item) => item.href)

      sheetPaths.forEach((path) => {
        expect(bottomPaths).not.toContain(path)
      })
    })

    it('contains remaining nav items', () => {
      const sheetLabels = mobileSheetItems.map((item) => item.label)
      expect(sheetLabels).toContain('Action Center')
      expect(sheetLabels).toContain('Platforms')
      expect(sheetLabels).toContain('Logs')
    })
  })

  describe('profileMenuItems', () => {
    it('contains profile-related menu items', () => {
      const labels = profileMenuItems.map((item) => item.label)
      expect(labels).toContain('Profile')
      expect(labels).toContain('API Key')
      expect(labels).toContain('Holdings')
    })
  })

  describe('isActiveRoute', () => {
    it('returns true for exact matches', () => {
      expect(isActiveRoute('/dashboard', '/dashboard')).toBe(true)
      expect(isActiveRoute('/orderbook', '/orderbook')).toBe(true)
      expect(isActiveRoute('/positions', '/positions')).toBe(true)
    })

    it('returns false for non-matching routes', () => {
      expect(isActiveRoute('/dashboard', '/orderbook')).toBe(false)
      expect(isActiveRoute('/positions', '/holdings')).toBe(false)
    })

    it('handles /strategy route with prefix matching', () => {
      // Strategy route should match nested pages
      expect(isActiveRoute('/strategy', '/strategy')).toBe(true)
      expect(isActiveRoute('/strategy/new', '/strategy')).toBe(true)
      expect(isActiveRoute('/strategy/123', '/strategy')).toBe(true)
      expect(isActiveRoute('/strategy/123/configure', '/strategy')).toBe(true)
    })

    it('does not prefix match non-strategy routes', () => {
      // Other routes should not prefix match
      expect(isActiveRoute('/dashboard/sub', '/dashboard')).toBe(false)
      expect(isActiveRoute('/orderbookextra', '/orderbook')).toBe(false)
    })
  })
})

```


---

# FILE: frontend\src\config\navigation.ts

```ts
import {
  BarChart3,
  Bell,
  BookOpen,
  ClipboardList,
  Code2,
  Database,
  FileBarChart,
  FileStack,
  FileText,
  FlaskConical,
  Gauge,
  Key,
  Layers,
  LayoutDashboard,
  type LucideIcon,
  MessageCircle,
  MessageSquare,
  Search,
  Settings,
  TrendingUp,
  User,
  Workflow,
  Wrench,
} from 'lucide-react'

export interface NavItem {
  href: string
  label: string
  icon: LucideIcon
}

// Main navigation items shown in desktop navbar
export const navItems: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/orderbook', label: 'Orderbook', icon: ClipboardList },
  { href: '/tradebook', label: 'Tradebook', icon: FileText },
  { href: '/positions', label: 'Positions', icon: TrendingUp },
  { href: '/action-center', label: 'Action Center', icon: Bell },
  { href: '/platforms', label: 'Platforms', icon: Layers },
  { href: '/strategy', label: 'Strategy', icon: Code2 },
  { href: '/logs', label: 'Logs', icon: FileBarChart },
  { href: '/tools', label: 'Tools', icon: Wrench },
]

// Items shown in mobile bottom navigation
export const bottomNavItems: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/orderbook', label: 'Orderbook', icon: ClipboardList },
  { href: '/tradebook', label: 'Tradebook', icon: FileText },
  { href: '/positions', label: 'Positions', icon: TrendingUp },
  { href: '/strategy', label: 'Strategy', icon: Code2 },
]

// Paths in bottom nav (for filtering mobile sheet items)
const bottomNavPaths = bottomNavItems.map((item) => item.href)

// Secondary items for mobile sheet (items not in bottom nav)
export const mobileSheetItems = navItems.filter((item) => !bottomNavPaths.includes(item.href))

// Profile dropdown menu items
export const profileMenuItems: NavItem[] = [
  { href: '/profile', label: 'Profile', icon: User },
  { href: '/apikey', label: 'API Key', icon: Key },
  { href: '/master-contract', label: 'Master Contract', icon: FileStack },
  { href: '/telegram', label: 'Telegram Bot', icon: MessageSquare },
  { href: '/whatsapp', label: 'WhatsApp Bot', icon: MessageCircle },
  { href: '/holdings', label: 'Holdings', icon: ClipboardList },
  { href: '/flow', label: 'Flow Editor', icon: Workflow },
  { href: '/python', label: 'Python Strategies', icon: Code2 },
  { href: '/pnl-tracker', label: 'PnL Tracker', icon: BarChart3 },
  { href: '/historify', label: 'Historify', icon: Database },
  { href: '/search/token', label: 'Search', icon: Search },
  { href: '/sandbox', label: 'Sandbox', icon: FlaskConical },
  { href: '/leverage', label: 'Leverage', icon: Gauge },
  { href: '/admin', label: 'Admin', icon: Settings },
]

// External links
export const externalLinks = {
  docs: { href: 'https://docs.openalgo.in', label: 'Docs', icon: BookOpen },
}

// Shared utility to check if a route is active
// Uses startsWith for routes with nested pages (like /strategy/*)
export function isActiveRoute(pathname: string, href: string): boolean {
  if (href === '/strategy') {
    return pathname.startsWith('/strategy')
  }
  return pathname === href
}

```
