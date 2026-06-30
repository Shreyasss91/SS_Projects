# Folder Merge

Folder: C:\Users\admin\Desktop\openalgo_docs\GITHUB\full_tree\repository\openalgo-main\frontend\src\test



---

# FILE: frontend\src\test\a11y-utils.ts

```ts
import { configureAxe, toHaveNoViolations } from 'jest-axe'
import { expect } from 'vitest'

// Extend Vitest's expect with accessibility matchers
expect.extend(toHaveNoViolations)

// Configure axe with rules appropriate for our app
export const axe = configureAxe({
  rules: {
    // Disable rules that may not apply to all components
    region: { enabled: false }, // Components may not have landmarks
    'color-contrast': { enabled: true },
    'aria-allowed-attr': { enabled: true },
    'aria-required-attr': { enabled: true },
    'aria-valid-attr': { enabled: true },
    'button-name': { enabled: true },
    'image-alt': { enabled: true },
    label: { enabled: true },
    'link-name': { enabled: true },
  },
})

// Helper to run accessibility tests
export async function checkA11y(container: Element) {
  const results = await axe(container)
  expect(results).toHaveNoViolations()
}

```


---

# FILE: frontend\src\test\setup.ts

```ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Cleanup after each test case
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia for tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
window.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
window.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock scrollTo
window.scrollTo = vi.fn()

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
    readText: vi.fn().mockImplementation(() => Promise.resolve('')),
  },
})

```


---

# FILE: frontend\src\test\test-utils.tsx

[BINARY FILE]

Type: .tsx

Size: 763 bytes

Path: frontend\src\test\test-utils.tsx
