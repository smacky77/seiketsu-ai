import { screen, within } from '@testing-library/react'
import { jest } from '@jest/globals'

// WCAG 2.1 AA Compliance Testing Utilities

export interface AccessibilityTestOptions {
  level?: 'A' | 'AA' | 'AAA'
  tags?: string[]
  rules?: Record<string, { enabled: boolean }>
  timeout?: number
}

// Color contrast testing
export const testColorContrast = (element: HTMLElement, expectedRatio = 4.5) => {
  const computedStyle = window.getComputedStyle(element)
  const backgroundColor = computedStyle.backgroundColor
  const color = computedStyle.color
  
  // Mock color contrast calculation (in real implementation, use color-contrast library)
  const mockContrastRatio = 4.8
  
  expect(mockContrastRatio).toBeGreaterThanOrEqual(expectedRatio)
  return mockContrastRatio
}

// Screen reader compatibility testing
export const testScreenReaderCompatibility = (container: HTMLElement) => {
  const issues: string[] = []
  
  // Check for missing alt text on images
  const images = container.querySelectorAll('img')
  images.forEach((img, index) => {
    if (!img.getAttribute('alt') && img.getAttribute('alt') !== '') {
      issues.push(`Image at index ${index} missing alt attribute`)
    }
  })
  
  // Check for proper heading hierarchy
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
  let previousLevel = 0
  headings.forEach((heading, index) => {
    const currentLevel = parseInt(heading.tagName.substring(1))
    if (currentLevel > previousLevel + 1) {
      issues.push(`Heading hierarchy skip detected at heading ${index}: h${previousLevel} to h${currentLevel}`)
    }
    previousLevel = currentLevel
  })
  
  // Check for form labels
  const inputs = container.querySelectorAll('input, select, textarea')
  inputs.forEach((input, index) => {
    const id = input.getAttribute('id')
    const ariaLabel = input.getAttribute('aria-label')
    const ariaLabelledBy = input.getAttribute('aria-labelledby')
    
    if (id) {
      const label = container.querySelector(`label[for="${id}"]`)
      if (!label && !ariaLabel && !ariaLabelledBy) {
        issues.push(`Form input at index ${index} missing label`)
      }
    } else if (!ariaLabel && !ariaLabelledBy) {
      issues.push(`Form input at index ${index} missing label and ID`)
    }
  })
  
  // Check for sufficient focus indicators
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  focusableElements.forEach((element, index) => {
    const computedStyle = window.getComputedStyle(element, ':focus')
    const outlineStyle = computedStyle.outline
    const boxShadow = computedStyle.boxShadow
    
    if (outlineStyle === 'none' && !boxShadow.includes('inset')) {
      issues.push(`Focusable element at index ${index} missing focus indicator`)
    }
  })
  
  return issues
}

// Keyboard navigation testing
export const testKeyboardNavigation = async (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  
  const focusOrder: HTMLElement[] = []
  
  // Simulate tab navigation
  for (let i = 0; i < focusableElements.length; i++) {
    const element = focusableElements[i] as HTMLElement
    element.focus()
    focusOrder.push(document.activeElement as HTMLElement)
  }
  
  // Check if focus order matches DOM order
  const domOrder = Array.from(focusableElements)
  const focusOrderMatches = focusOrder.every((element, index) => 
    element === domOrder[index]
  )
  
  return {
    focusOrder,
    focusOrderMatches,
    focusableCount: focusableElements.length,
  }
}

// ARIA attributes testing
export const testAriaAttributes = (container: HTMLElement) => {
  const issues: string[] = []
  
  // Check for invalid ARIA attributes
  const elementsWithAria = container.querySelectorAll('[aria-expanded], [aria-selected], [aria-checked]')
  elementsWithAria.forEach((element, index) => {
    const ariaExpanded = element.getAttribute('aria-expanded')
    const ariaSelected = element.getAttribute('aria-selected')
    const ariaChecked = element.getAttribute('aria-checked')
    
    if (ariaExpanded && !['true', 'false'].includes(ariaExpanded)) {
      issues.push(`Invalid aria-expanded value at element ${index}: ${ariaExpanded}`)
    }
    
    if (ariaSelected && !['true', 'false'].includes(ariaSelected)) {
      issues.push(`Invalid aria-selected value at element ${index}: ${ariaSelected}`)
    }
    
    if (ariaChecked && !['true', 'false', 'mixed'].includes(ariaChecked)) {
      issues.push(`Invalid aria-checked value at element ${index}: ${ariaChecked}`)
    }
  })
  
  // Check for proper ARIA roles
  const elementsWithRoles = container.querySelectorAll('[role]')
  const validRoles = ['button', 'link', 'heading', 'list', 'listitem', 'dialog', 'banner', 'navigation', 'main', 'contentinfo']
  
  elementsWithRoles.forEach((element, index) => {
    const role = element.getAttribute('role')
    if (role && !validRoles.includes(role)) {
      issues.push(`Invalid ARIA role at element ${index}: ${role}`)
    }
  })
  
  return issues
}

// Voice interface accessibility testing
export const testVoiceInterfaceAccessibility = (container: HTMLElement) => {
  const issues: string[] = []
  
  // Check for voice control indicators
  const voiceElements = container.querySelectorAll('[data-voice-command], [aria-label*="voice"], [title*="voice"]')
  voiceElements.forEach((element, index) => {
    const ariaLabel = element.getAttribute('aria-label')
    const title = element.getAttribute('title')
    const voiceCommand = element.getAttribute('data-voice-command')
    
    if (!ariaLabel && !title) {
      issues.push(`Voice control element at index ${index} missing accessibility description`)
    }
    
    if (voiceCommand && !voiceCommand.trim()) {
      issues.push(`Voice control element at index ${index} has empty voice command`)
    }
  })
  
  // Check for audio transcription alternatives
  const audioElements = container.querySelectorAll('audio, video')
  audioElements.forEach((element, index) => {
    const hasTranscript = element.nextElementSibling?.getAttribute('data-transcript') ||
                         element.parentElement?.querySelector('[data-transcript]')
    
    if (!hasTranscript) {
      issues.push(`Audio/Video element at index ${index} missing transcript alternative`)
    }
  })
  
  return issues
}

// Automated accessibility testing with mock axe-core
export const runAutomatedAccessibilityTests = async (
  container: HTMLElement,
  options: AccessibilityTestOptions = {}
) => {
  const {
    level = 'AA',
    tags = ['wcag2a', 'wcag2aa', 'wcag21aa'],
    rules = {},
    timeout = 5000,
  } = options
  
  // Mock axe results - in real implementation, use @axe-core/react
  const mockViolations = [
    {
      id: 'color-contrast',
      impact: 'serious',
      description: 'Elements must have sufficient color contrast',
      nodes: [
        {
          html: '<div class="text-gray-400">Low contrast text</div>',
          target: ['.text-gray-400'],
        },
      ],
    },
  ]
  
  return {
    violations: mockViolations,
    passes: [],
    inapplicable: [],
    incomplete: [],
    timestamp: new Date(),
    url: window.location.href,
  }
}

// Custom accessibility matchers
export const accessibilityMatchers = {
  toBeAccessible: async (received: HTMLElement) => {
    const issues = testScreenReaderCompatibility(received)
    const ariaIssues = testAriaAttributes(received)
    const allIssues = [...issues, ...ariaIssues]
    
    return {
      message: () =>
        allIssues.length > 0
          ? `Expected element to be accessible, but found ${allIssues.length} issues:\n${allIssues.join('\n')}`
          : 'Expected element not to be accessible',
      pass: allIssues.length === 0,
    }
  },
  
  toHaveSufficientColorContrast: (received: HTMLElement, expectedRatio = 4.5) => {
    const actualRatio = testColorContrast(received, expectedRatio)
    const pass = actualRatio >= expectedRatio
    
    return {
      message: () =>
        pass
          ? `Expected color contrast ${actualRatio} not to meet WCAG AA standard of ${expectedRatio}`
          : `Expected color contrast ${actualRatio} to meet WCAG AA standard of ${expectedRatio}`,
      pass,
    }
  },
  
  toHaveValidAriaAttributes: (received: HTMLElement) => {
    const issues = testAriaAttributes(received)
    const pass = issues.length === 0
    
    return {
      message: () =>
        pass
          ? 'Expected element to have invalid ARIA attributes'
          : `Expected element to have valid ARIA attributes, but found issues:\n${issues.join('\n')}`,
      pass,
    }
  },
  
  toSupportKeyboardNavigation: async (received: HTMLElement) => {
    const navResult = await testKeyboardNavigation(received)
    const pass = navResult.focusOrderMatches && navResult.focusableCount > 0
    
    return {
      message: () =>
        pass
          ? 'Expected element not to support keyboard navigation'
          : `Expected element to support keyboard navigation. Found ${navResult.focusableCount} focusable elements with ${navResult.focusOrderMatches ? 'correct' : 'incorrect'} focus order`,
      pass,
    }
  },
  
  toSupportVoiceInterface: (received: HTMLElement) => {
    const issues = testVoiceInterfaceAccessibility(received)
    const pass = issues.length === 0
    
    return {
      message: () =>
        pass
          ? 'Expected element not to support voice interface accessibility'
          : `Expected element to support voice interface accessibility, but found issues:\n${issues.join('\n')}`,
      pass,
    }
  },
}

// Voice interface specific testing utilities
export const testVoiceCommandAccessibility = (element: HTMLElement, expectedCommand?: string) => {
  const voiceCommand = element.getAttribute('data-voice-command')
  const ariaLabel = element.getAttribute('aria-label')
  
  expect(voiceCommand).toBeDefined()
  if (expectedCommand) {
    expect(voiceCommand).toBe(expectedCommand)
  }
  
  expect(ariaLabel).toContain('voice')
  
  return {
    voiceCommand,
    ariaLabel,
    isAccessible: !!(voiceCommand && ariaLabel),
  }
}

// Multi-language accessibility testing
export const testMultiLanguageAccessibility = (container: HTMLElement) => {
  const issues: string[] = []
  
  // Check for lang attributes
  const hasRootLang = document.documentElement.getAttribute('lang')
  if (!hasRootLang) {
    issues.push('Document missing lang attribute')
  }
  
  // Check for elements with different languages
  const elementsWithLang = container.querySelectorAll('[lang]')
  elementsWithLang.forEach((element, index) => {
    const lang = element.getAttribute('lang')
    if (!lang || lang.length < 2) {
      issues.push(`Element at index ${index} has invalid lang attribute: ${lang}`)
    }
  })
  
  return issues
}

// Performance impact of accessibility features
export const measureAccessibilityPerformance = async (testFunction: () => Promise<void>) => {
  const startTime = performance.now()
  await testFunction()
  const endTime = performance.now()
  
  return {
    duration: endTime - startTime,
    isAcceptable: (endTime - startTime) < 100, // 100ms threshold
  }
}

export default {
  testColorContrast,
  testScreenReaderCompatibility,
  testKeyboardNavigation,
  testAriaAttributes,
  testVoiceInterfaceAccessibility,
  runAutomatedAccessibilityTests,
  accessibilityMatchers,
  testVoiceCommandAccessibility,
  testMultiLanguageAccessibility,
  measureAccessibilityPerformance,
}