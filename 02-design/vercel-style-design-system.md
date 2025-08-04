# Seiketsu AI Design System
## Vercel-Inspired Enterprise Voice Agent Platform

*Version 1.0 | WCAG 2.1 AA Compliant | Voice-First Design*

---

## 🎯 Design Principles

### Core Philosophy
- **Clarity Above All**: Every element serves a purpose in voice-first interactions
- **Monochromatic Excellence**: High contrast through grays, not colors
- **Enterprise Focus**: Built for 50-500 agent agencies with complex data needs
- **Accessibility First**: WCAG 2.1 AA compliance baked into every component
- **Voice-Visual Harmony**: UI supports and enhances voice interactions

### Design Values
1. **Functional Beauty**: Form follows voice interaction function
2. **Cognitive Load Reduction**: Minimal visual noise for maximum focus
3. **Scalable Consistency**: Works across all enterprise use cases
4. **Progressive Disclosure**: Complex features revealed when needed
5. **Cross-Device Continuity**: Seamless experience across all devices

---

## 🎨 Foundation Elements

### Color System (OKLCH-Based)

#### Primary Palette
```css
/* Core Colors - Monochromatic System */
--background: oklch(100% 0 0);        /* Pure white */
--foreground: oklch(0% 0 0);          /* Pure black */
--muted: oklch(96% 0 0);              /* Light gray */
--muted-foreground: oklch(20% 0 0);   /* Dark gray */
--accent: oklch(90% 0 0);             /* Accent gray */
--accent-foreground: oklch(10% 0 0);  /* Dark accent */
--border: oklch(85% 0 0);             /* Border gray */
--card: oklch(98% 0 0);               /* Card background */
--card-foreground: oklch(5% 0 0);     /* Card text */
```

#### Semantic Colors
```css
/* Status & Feedback */
--success: oklch(65% 0.15 145);       /* Green for success states */
--warning: oklch(75% 0.15 85);        /* Amber for warnings */
--error: oklch(60% 0.15 25);          /* Red for errors */
--info: oklch(70% 0.08 250);          /* Blue for information */

/* Voice-Specific States */
--voice-listening: oklch(70% 0.12 180);   /* Cyan for listening */
--voice-processing: oklch(75% 0.10 60);   /* Yellow for processing */
--voice-speaking: oklch(65% 0.14 145);    /* Green for speaking */
--voice-muted: oklch(40% 0 0);            /* Gray for muted */
```

#### Dark Mode Variants
```css
/* Dark Mode Color System */
--dark-background: oklch(8% 0 0);
--dark-foreground: oklch(98% 0 0);
--dark-muted: oklch(15% 0 0);
--dark-muted-foreground: oklch(80% 0 0);
--dark-border: oklch(25% 0 0);
--dark-card: oklch(12% 0 0);
--dark-card-foreground: oklch(95% 0 0);
```

### Typography Scale

#### Font Stack
```css
/* Primary Font - Inter */
font-family: 'Inter', system-ui, sans-serif;
font-feature-settings: "rlig" 1, "calt" 1, "ss01" 1;

/* Monospace Font - JetBrains Mono */
font-family: 'JetBrains Mono', 'SF Mono', monospace;
```

#### Type Scale (Voice-Optimized)
```css
/* Display Typography */
.text-display-xl {
  font-size: 3.75rem;    /* 60px */
  line-height: 1.1;
  letter-spacing: -0.025em;
  font-weight: 700;
}

.text-display-lg {
  font-size: 3rem;       /* 48px */
  line-height: 1.125;
  letter-spacing: -0.02em;
  font-weight: 600;
}

.text-display-md {
  font-size: 2.25rem;    /* 36px */
  line-height: 1.2;
  letter-spacing: -0.015em;
  font-weight: 600;
}

/* Heading Typography */
.text-h1 {
  font-size: 1.875rem;   /* 30px */
  line-height: 1.3;
  font-weight: 600;
}

.text-h2 {
  font-size: 1.5rem;     /* 24px */
  line-height: 1.35;
  font-weight: 600;
}

.text-h3 {
  font-size: 1.25rem;    /* 20px */
  line-height: 1.4;
  font-weight: 500;
}

.text-h4 {
  font-size: 1.125rem;   /* 18px */
  line-height: 1.45;
  font-weight: 500;
}

/* Body Typography */
.text-body-lg {
  font-size: 1.125rem;   /* 18px */
  line-height: 1.6;
  font-weight: 400;
}

.text-body {
  font-size: 1rem;       /* 16px */
  line-height: 1.6;
  font-weight: 400;
}

.text-body-sm {
  font-size: 0.875rem;   /* 14px */
  line-height: 1.5;
  font-weight: 400;
}

.text-caption {
  font-size: 0.75rem;    /* 12px */
  line-height: 1.4;
  font-weight: 400;
  letter-spacing: 0.025em;
}

/* Voice Interface Typography */
.text-voice-command {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.025em;
}

.text-transcript {
  font-size: 1rem;
  line-height: 1.7;
  font-weight: 400;
  font-style: italic;
}
```

### Spacing System

#### Grid System (8px Base Unit)
```css
/* Spacing Scale */
--space-0: 0;           /* 0px */
--space-px: 1px;        /* 1px */
--space-0-5: 0.125rem;  /* 2px */
--space-1: 0.25rem;     /* 4px */
--space-1-5: 0.375rem;  /* 6px */
--space-2: 0.5rem;      /* 8px */
--space-2-5: 0.625rem;  /* 10px */
--space-3: 0.75rem;     /* 12px */
--space-3-5: 0.875rem;  /* 14px */
--space-4: 1rem;        /* 16px */
--space-5: 1.25rem;     /* 20px */
--space-6: 1.5rem;      /* 24px */
--space-7: 1.75rem;     /* 28px */
--space-8: 2rem;        /* 32px */
--space-10: 2.5rem;     /* 40px */
--space-12: 3rem;       /* 48px */
--space-16: 4rem;       /* 64px */
--space-20: 5rem;       /* 80px */
--space-24: 6rem;       /* 96px */
--space-32: 8rem;       /* 128px */

/* Semantic Spacing */
--spacing-component: var(--space-4);    /* Component internal spacing */
--spacing-section: var(--space-12);     /* Section spacing */
--spacing-page: var(--space-16);        /* Page-level spacing */
```

#### Container System
```css
/* Container Widths */
.container-xs { max-width: 20rem; }     /* 320px */
.container-sm { max-width: 24rem; }     /* 384px */
.container-md { max-width: 28rem; }     /* 448px */
.container-lg { max-width: 32rem; }     /* 512px */
.container-xl { max-width: 36rem; }     /* 576px */
.container-2xl { max-width: 42rem; }    /* 672px */
.container-3xl { max-width: 48rem; }    /* 768px */
.container-4xl { max-width: 56rem; }    /* 896px */
.container-5xl { max-width: 64rem; }    /* 1024px */
.container-6xl { max-width: 72rem; }    /* 1152px */
.container-7xl { max-width: 80rem; }    /* 1280px */

/* Content Width System */
.content-narrow { max-width: 65ch; }    /* Optimal reading width */
.content-wide { max-width: 90ch; }      /* Wide content */
.content-full { max-width: 100%; }      /* Full width */
```

### Elevation & Shadows

#### Shadow System
```css
/* Elevation Shadows */
--shadow-xs: 0 1px 2px 0 oklch(0% 0 0 / 0.05);
--shadow-sm: 0 1px 3px 0 oklch(0% 0 0 / 0.1), 0 1px 2px -1px oklch(0% 0 0 / 0.1);
--shadow-md: 0 4px 6px -1px oklch(0% 0 0 / 0.1), 0 2px 4px -2px oklch(0% 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px oklch(0% 0 0 / 0.1), 0 4px 6px -4px oklch(0% 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px oklch(0% 0 0 / 0.1), 0 8px 10px -6px oklch(0% 0 0 / 0.1);
--shadow-2xl: 0 25px 50px -12px oklch(0% 0 0 / 0.25);

/* Inner Shadows */
--shadow-inner: inset 0 2px 4px 0 oklch(0% 0 0 / 0.05);

/* Voice-Specific Glows */
--glow-voice-active: 0 0 20px oklch(70% 0.12 180 / 0.3);
--glow-voice-processing: 0 0 16px oklch(75% 0.10 60 / 0.25);
--glow-voice-speaking: 0 0 18px oklch(65% 0.14 145 / 0.3);
```

### Border Radius

#### Radius Scale
```css
--radius-none: 0;
--radius-sm: 0.125rem;    /* 2px */
--radius-md: 0.375rem;    /* 6px */
--radius-lg: 0.5rem;      /* 8px */
--radius-xl: 0.75rem;     /* 12px */
--radius-2xl: 1rem;       /* 16px */
--radius-3xl: 1.5rem;     /* 24px */
--radius-full: 9999px;    /* Full rounded */

/* Component-Specific Radius */
--radius-button: var(--radius-lg);
--radius-card: var(--radius-xl);
--radius-input: var(--radius-md);
--radius-modal: var(--radius-2xl);
```

---

## 🗣️ Voice-First UI Patterns

### Voice Status Indicators

#### Primary Voice Status Component
```tsx
interface VoiceStatusProps {
  status: 'idle' | 'listening' | 'processing' | 'speaking' | 'error';
  level?: number; // 0-100 for audio level
}

const VoiceStatus: React.FC<VoiceStatusProps> = ({ status, level = 0 }) => {
  return (
    <div className={`voice-indicator voice-${status}`}>
      <div className="voice-visualizer">
        {/* Audio level visualization */}
      </div>
      <span className="voice-status-text">{status}</span>
    </div>
  );
};
```

#### CSS Implementation
```css
/* Voice Status Indicators */
.voice-indicator {
  @apply relative inline-flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-300;
}

.voice-idle {
  @apply bg-muted text-muted-foreground;
}

.voice-listening {
  @apply bg-blue-50 text-blue-700 shadow-lg;
  box-shadow: 0 0 20px oklch(70% 0.12 180 / 0.3);
  animation: pulse-voice 2s ease-in-out infinite;
}

.voice-processing {
  @apply bg-yellow-50 text-yellow-700;
  animation: processing-spin 1s linear infinite;
}

.voice-speaking {
  @apply bg-green-50 text-green-700 shadow-lg;
  box-shadow: 0 0 18px oklch(65% 0.14 145 / 0.3);
}

.voice-error {
  @apply bg-red-50 text-red-700 border border-red-200;
}

/* Voice Animations */
@keyframes pulse-voice {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

@keyframes processing-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

### Audio Waveform Visualization

#### Waveform Component
```css
.waveform-container {
  @apply flex items-center justify-center gap-1 h-8;
}

.waveform-bar {
  @apply bg-current rounded-full transition-all duration-100;
  width: 3px;
  min-height: 4px;
}

.waveform-active .waveform-bar {
  animation: waveform-bounce 0.6s ease-in-out infinite alternate;
}

@keyframes waveform-bounce {
  from { height: 4px; }
  to { height: 24px; }
}
```

### Conversation Transcript

#### Transcript Styling
```css
.transcript-container {
  @apply space-y-4 max-h-96 overflow-y-auto p-4 bg-card rounded-lg border;
}

.transcript-message {
  @apply flex gap-3;
}

.transcript-user {
  @apply justify-end;
}

.transcript-assistant {
  @apply justify-start;
}

.transcript-bubble {
  @apply max-w-sm px-4 py-2 rounded-2xl text-sm;
}

.transcript-user .transcript-bubble {
  @apply bg-foreground text-background;
}

.transcript-assistant .transcript-bubble {
  @apply bg-muted text-muted-foreground;
}

.transcript-timestamp {
  @apply text-xs text-muted-foreground mt-1;
}
```

---

## 🏢 Enterprise Component Library

### Data Tables

#### Enterprise Data Table Component
```css
.data-table {
  @apply w-full border-collapse bg-card rounded-lg overflow-hidden shadow-sm;
}

.data-table-header {
  @apply bg-muted/50 border-b border-border;
}

.data-table-header-cell {
  @apply px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider;
}

.data-table-row {
  @apply border-b border-border transition-colors hover:bg-muted/20;
}

.data-table-cell {
  @apply px-4 py-3 text-sm text-card-foreground;
}

.data-table-actions {
  @apply flex items-center gap-2;
}

/* Responsive Table */
@media (max-width: 768px) {
  .data-table-responsive {
    @apply block;
  }
  
  .data-table-responsive .data-table-row {
    @apply block border border-border rounded-lg mb-4 p-4;
  }
  
  .data-table-responsive .data-table-cell {
    @apply block px-0 py-1;
  }
  
  .data-table-responsive .data-table-cell::before {
    content: attr(data-label) ": ";
    @apply font-medium text-muted-foreground;
  }
}
```

### Multi-Tenant Switching

#### Tenant Switcher Component
```css
.tenant-switcher {
  @apply relative inline-block;
}

.tenant-switcher-trigger {
  @apply flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg hover:bg-muted/50 focus:ring-2 focus:ring-foreground focus:ring-offset-2;
}

.tenant-switcher-dropdown {
  @apply absolute top-full left-0 z-50 mt-1 w-64 bg-card border border-border rounded-lg shadow-lg;
}

.tenant-switcher-item {
  @apply flex items-center gap-3 px-3 py-2 hover:bg-muted/50 focus:bg-muted/50 cursor-pointer;
}

.tenant-switcher-avatar {
  @apply w-8 h-8 bg-muted rounded-full flex items-center justify-center text-xs font-medium;
}

.tenant-switcher-info {
  @apply flex-1 min-w-0;
}

.tenant-switcher-name {
  @apply font-medium text-sm truncate;
}

.tenant-switcher-role {
  @apply text-xs text-muted-foreground;
}
```

### Dashboard Widgets

#### Widget Container System
```css
.dashboard-grid {
  @apply grid gap-6;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.widget {
  @apply bg-card rounded-xl border border-border p-6 shadow-sm;
}

.widget-header {
  @apply flex items-center justify-between mb-4;
}

.widget-title {
  @apply text-lg font-semibold text-card-foreground;
}

.widget-content {
  @apply space-y-4;
}

.widget-metric {
  @apply text-3xl font-boldtabular-nums;
}

.widget-trend {
  @apply flex items-center gap-1 text-sm;
}

.widget-trend-up {
  @apply text-green-600;
}

.widget-trend-down {
  @apply text-red-600;
}

.widget-chart {
  @apply h-48 w-full;
}
```

### Form Components

#### Accessible Form Elements
```css
.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-foreground;
}

.form-label-required::after {
  content: " *";
  @apply text-red-500;
}

.form-input {
  @apply w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground focus:border-transparent;
}

.form-input:disabled {
  @apply bg-muted cursor-not-allowed opacity-50;
}

.form-input-error {
  @apply border-red-300 focus:ring-red-500;
}

.form-error {
  @apply text-sm text-red-600 mt-1;
}

.form-help {
  @apply text-sm text-muted-foreground mt-1;
}

.form-fieldset {
  @apply space-y-4 p-4 border border-border rounded-lg;
}

.form-legend {
  @apply text-base font-medium text-foreground px-2;
}

/* Voice Command Input */
.voice-input {
  @apply relative;
}

.voice-input-field {
  @apply form-input pr-12;
}

.voice-input-button {
  @apply absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-md hover:bg-muted;
}
```

---

## ♿ Accessibility Features

### WCAG 2.1 AA Compliance Standards

#### Color Contrast Requirements
```css
/* Minimum contrast ratios */
.contrast-normal {
  /* Normal text: 4.5:1 minimum */
  color: oklch(20% 0 0); /* on white background */
}

.contrast-large {
  /* Large text (18px+ or 14px+ bold): 3:1 minimum */
  color: oklch(35% 0 0); /* on white background */
}

.contrast-ui {
  /* UI components: 3:1 minimum */
  border-color: oklch(40% 0 0); /* on white background */
}
```

#### Focus States
```css
/* Universal Focus Ring */
.focus-ring {
  @apply focus:outline-none focus:ring-2 focus:ring-foreground focus:ring-offset-2 focus:ring-offset-background;
}

/* High Contrast Focus for Dark Backgrounds */
.focus-ring-inverse {
  @apply focus:outline-none focus:ring-2 focus:ring-background focus:ring-offset-2 focus:ring-offset-foreground;
}

/* Custom Focus Styles */
.btn:focus-visible,
.form-input:focus-visible,
.link:focus-visible {
  @apply outline-none ring-2 ring-foreground ring-offset-2;
}

/* Skip Links */
.skip-link {
  @apply sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-foreground text-background px-4 py-2 rounded-md z-50;
}
```

#### Screen Reader Support
```css
/* Screen Reader Only Content */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}

/* Accessible Labels */
.visually-hidden {
  @apply sr-only;
}

/* High Contrast Mode Support */
@media (prefers-contrast: high) {
  .card {
    @apply border-2;
  }
  
  .btn {
    @apply border-2 border-current;
  }
}
```

#### Voice Interface Accessibility
```css
/* Voice Command Indicators */
.voice-command-available::before {
  content: "Voice command available";
  @apply sr-only;
}

.voice-status[aria-live="polite"] {
  /* Announces voice status changes to screen readers */
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  .voice-indicator::before,
  .waveform-bar,
  .animate-pulse,
  .animate-spin {
    animation: none;
  }
}
```

### High Contrast Mode

#### High Contrast Color Overrides
```css
.high-contrast {
  --background: oklch(100% 0 0);
  --foreground: oklch(0% 0 0);
  --muted: oklch(90% 0 0);
  --muted-foreground: oklch(10% 0 0);
  --border: oklch(0% 0 0);
  --accent: oklch(85% 0 0);
}

.high-contrast .card {
  @apply border-2 border-foreground;
}

.high-contrast .btn {
  @apply border-2 border-current;
}

.high-contrast .focus-ring {
  @apply ring-4 ring-foreground;
}
```

---

## 📱 Multi-Modal Integration

### Responsive Breakpoints

#### Breakpoint System
```css
/* Mobile First Breakpoints */
.container {
  @apply w-full px-4;
}

/* Small devices (landscape phones, 576px and up) */
@media (min-width: 576px) {
  .container {
    @apply max-w-screen-sm px-6;
  }
}

/* Medium devices (tablets, 768px and up) */
@media (min-width: 768px) {
  .container {
    @apply max-w-screen-md px-8;
  }
}

/* Large devices (desktops, 992px and up) */
@media (min-width: 992px) {
  .container {
    @apply max-w-screen-lg px-12;
  }
}

/* Extra large devices (large desktops, 1200px and up) */
@media (min-width: 1200px) {
  .container {
    @apply max-w-screen-xl px-16;
  }
}
```

#### Touch-Friendly Interactions
```css
/* Minimum Touch Target Size: 44px */
.touch-target {
  @apply min-h-11 min-w-11 flex items-center justify-center;
}

.btn {
  @apply min-h-11 px-4 py-2;
}

.form-input {
  @apply min-h-11 px-3 py-2;
}

/* Touch Feedback */
.btn:active {
  @apply scale-95 transition-transform duration-75;
}

/* Hover States Only on Non-Touch Devices */
@media (hover: hover) {
  .btn:hover {
    @apply opacity-90;
  }
}
```

### Voice + Visual Confirmation Patterns

#### Confirmation Components
```css
.confirmation-overlay {
  @apply fixed inset-0 bg-black/50 flex items-center justify-center z-50;
}

.confirmation-modal {
  @apply bg-card rounded-2xl p-6 max-w-md mx-4 shadow-2xl;
}

.confirmation-voice-visual {
  @apply flex items-center gap-4 mb-4;
}

.confirmation-icon {
  @apply w-12 h-12 rounded-full flex items-center justify-center;
}

.confirmation-text {
  @apply text-lg font-medium;
}

.confirmation-actions {
  @apply flex gap-3 justify-end mt-6;
}

/* Voice Confirmation Animation */
.voice-confirmation-success {
  animation: voice-success-pulse 0.6s ease-out;
}

@keyframes voice-success-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); background-color: oklch(65% 0.14 145 / 0.1); }
  100% { transform: scale(1); }
}
```

### Progressive Disclosure

#### Collapsible Content System
```css
.disclosure {
  @apply border border-border rounded-lg overflow-hidden;
}

.disclosure-trigger {
  @apply w-full px-4 py-3 text-left bg-muted/20 hover:bg-muted/40 focus:bg-muted/40 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-foreground;
}

.disclosure-content {
  @apply px-4 py-3 border-t border-border;
}

.disclosure-icon {
  @apply transition-transform duration-200;
}

.disclosure[open] .disclosure-icon {
  @apply rotate-180;
}

/* Advanced/Simple View Toggle */
.view-toggle {
  @apply flex bg-muted rounded-lg p-1;
}

.view-toggle-option {
  @apply flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-foreground focus:ring-offset-2 focus:ring-offset-muted;
}

.view-toggle-option[aria-selected="true"] {
  @apply bg-background shadow-sm;
}
```

---

## 🎭 Animation System

### Micro-Interactions

#### Button Animations
```css
.btn {
  @apply transition-all duration-150 ease-in-out;
}

.btn:hover {
  @apply -translate-y-0.5 shadow-lg;
}

.btn:active {
  @apply translate-y-0 shadow-md;
}

.btn-loading {
  @apply cursor-not-allowed opacity-75;
}

.btn-loading::after {
  content: "";
  @apply w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin ml-2;
}
```

#### Form Animations
```css
.form-input {
  @apply transition-all duration-200 ease-out;
}

.form-input:focus {
  @apply transform scale-105 shadow-md;
}

.form-error-enter {
  @apply animate-slide-down;
}

@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

#### Loading States
```css
.skeleton {
  @apply animate-pulse bg-muted rounded;
}

.skeleton-text {
  @apply h-4 bg-muted rounded;
}

.skeleton-circle {
  @apply rounded-full bg-muted;
}

.skeleton-card {
  @apply space-y-3 p-4;
}

/* Loading Spinner */
.spinner {
  @apply w-6 h-6 border-2 border-muted border-t-foreground rounded-full animate-spin;
}

/* Progress Bar */
.progress {
  @apply w-full bg-muted rounded-full h-2 overflow-hidden;
}

.progress-bar {
  @apply h-full bg-foreground transition-all duration-300 ease-out;
}
```

---

## 📊 Component Usage Guidelines

### Button Hierarchy

#### Primary Actions
```html
<!-- Primary CTA -->
<button class="btn btn-primary">
  Get Started
</button>

<!-- Voice Action Button -->
<button class="btn btn-primary voice-enabled" aria-label="Start voice recording">
  <svg><!-- microphone icon --></svg>
  Start Recording
</button>
```

#### Secondary Actions
```html
<!-- Secondary Button -->
<button class="btn btn-secondary">
  Learn More
</button>

<!-- Ghost Button -->
<button class="btn btn-ghost">
  Cancel
</button>
```

### Form Best Practices

#### Voice-Enhanced Forms
```html
<form class="space-y-6">
  <div class="form-group">
    <label for="company-name" class="form-label form-label-required">
      Company Name
    </label>
    <div class="voice-input">
      <input 
        type="text" 
        id="company-name" 
        class="form-input voice-input-field"
        placeholder="Enter your company name"
        aria-describedby="company-help"
      />
      <button 
        type="button" 
        class="voice-input-button"
        aria-label="Use voice input for company name"
      >
        <svg><!-- microphone icon --></svg>
      </button>
    </div>
    <p id="company-help" class="form-help">
      You can use voice input or type manually
    </p>
  </div>
</form>
```

### Data Display Patterns

#### Enterprise Dashboard Card
```html
<div class="widget">
  <div class="widget-header">
    <h3 class="widget-title">Conversion Rate</h3>
    <button class="btn btn-ghost btn-sm" aria-label="Widget options">
      <svg><!-- options icon --></svg>
    </button>
  </div>
  <div class="widget-content">
    <div class="widget-metric">24.5%</div>
    <div class="widget-trend widget-trend-up">
      <svg><!-- trend up icon --></svg>
      +12% from last month
    </div>
    <div class="widget-chart">
      <!-- Chart component -->
    </div>
  </div>
</div>
```

---

## 🔧 Implementation Guidelines

### CSS Architecture

#### File Structure
```
styles/
├── foundations/
│   ├── colors.css
│   ├── typography.css
│   ├── spacing.css
│   └── animations.css
├── components/
│   ├── buttons.css
│   ├── forms.css
│   ├── cards.css
│   ├── voice.css
│   └── data-tables.css
├── utilities/
│   ├── accessibility.css
│   ├── responsive.css
│   └── helpers.css
└── main.css
```

#### CSS Custom Properties Setup
```css
/* CSS Custom Properties for Runtime Theming */
:root {
  /* Design Tokens */
  --color-background: oklch(100% 0 0);
  --color-foreground: oklch(0% 0 0);
  --spacing-unit: 0.25rem;
  --border-radius-base: 0.5rem;
  --font-family-sans: 'Inter', system-ui, sans-serif;
  --font-family-mono: 'JetBrains Mono', monospace;
  
  /* Component Tokens */
  --button-height: 2.75rem;
  --input-height: 2.75rem;
  --card-padding: 1.5rem;
  --section-spacing: 3rem;
}

/* Dark Mode Override */
[data-theme="dark"] {
  --color-background: oklch(8% 0 0);
  --color-foreground: oklch(98% 0 0);
}

/* High Contrast Override */
[data-contrast="high"] {
  --color-border: oklch(0% 0 0);
}
```

### Tailwind Configuration

#### Complete Tailwind Config
```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // OKLCH Monochromatic System
        background: 'oklch(var(--color-background) / <alpha-value>)',
        foreground: 'oklch(var(--color-foreground) / <alpha-value>)',
        muted: {
          DEFAULT: 'oklch(96% 0 0 / <alpha-value>)',
          foreground: 'oklch(20% 0 0 / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'oklch(90% 0 0 / <alpha-value>)',
          foreground: 'oklch(10% 0 0 / <alpha-value>)',
        },
        border: 'oklch(85% 0 0 / <alpha-value>)',
        card: {
          DEFAULT: 'oklch(98% 0 0 / <alpha-value>)',
          foreground: 'oklch(5% 0 0 / <alpha-value>)',
        },
        // Voice-specific colors
        voice: {
          listening: 'oklch(70% 0.12 180 / <alpha-value>)',
          processing: 'oklch(75% 0.10 60 / <alpha-value>)',
          speaking: 'oklch(65% 0.14 145 / <alpha-value>)',
          muted: 'oklch(40% 0 0 / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'display-xl': ['3.75rem', { lineHeight: '1.1', letterSpacing: '-0.025em' }],
        'display-lg': ['3rem', { lineHeight: '1.125', letterSpacing: '-0.02em' }],
        'display-md': ['2.25rem', { lineHeight: '1.2', letterSpacing: '-0.015em' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      boxShadow: {
        'voice-glow': '0 0 20px oklch(70% 0.12 180 / 0.3)',
        'processing-glow': '0 0 16px oklch(75% 0.10 60 / 0.25)',
        'speaking-glow': '0 0 18px oklch(65% 0.14 145 / 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-voice': 'pulseVoice 2s ease-in-out infinite',
        'waveform-bounce': 'waveformBounce 0.6s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseVoice: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.05)' },
        },
        waveformBounce: {
          'from': { height: '4px' },
          'to': { height: '24px' },
        },
      },
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}

export default config
```

### Component Library Structure

#### React Component Template
```tsx
// components/ui/Button.tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  voiceEnabled?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', voiceEnabled, loading, children, ...props }, ref) => {
    return (
      <button
        className={cn(
          'btn',
          `btn-${variant}`,
          `btn-${size}`,
          voiceEnabled && 'voice-enabled',
          loading && 'btn-loading',
          className
        )}
        ref={ref}
        disabled={loading}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
```

---

## 📋 Quality Assurance Checklist

### Pre-Launch Component Checklist

#### ✅ Accessibility Requirements
- [ ] WCAG 2.1 AA color contrast ratios met (4.5:1 normal, 3:1 large text)
- [ ] All interactive elements have focus states
- [ ] Keyboard navigation works for all components
- [ ] Screen reader compatibility tested
- [ ] Alternative text provided for images and icons
- [ ] Form labels properly associated with inputs
- [ ] Error messages are descriptive and helpful
- [ ] Skip links implemented for keyboard users

#### ✅ Voice Interface Requirements
- [ ] Voice status clearly indicated to users
- [ ] Audio level visualization working
- [ ] Voice commands have visual confirmation
- [ ] Error states handle voice interaction failures
- [ ] Voice input alternative always available
- [ ] Transcript display is readable and scrollable
- [ ] Voice feedback doesn't interfere with screen readers

#### ✅ Responsive Design Requirements
- [ ] Mobile-first approach implemented
- [ ] Touch targets minimum 44px
- [ ] Text remains readable at all screen sizes
- [ ] Navigation adapts appropriately
- [ ] Data tables have mobile fallbacks
- [ ] Forms are usable on small screens
- [ ] Voice interface works on all devices

#### ✅ Performance Requirements
- [ ] Components load quickly (<200ms)
- [ ] Animations respect prefers-reduced-motion
- [ ] Images optimized and properly sized
- [ ] CSS is optimized and minimal
- [ ] JavaScript bundles are code-split
- [ ] Voice processing doesn't block UI

#### ✅ Enterprise Requirements
- [ ] Multi-tenant switching works smoothly
- [ ] Data tables handle large datasets
- [ ] Export functionality available
- [ ] Bulk actions are accessible
- [ ] Complex forms validate properly
- [ ] Dashboard widgets are configurable

### Testing Protocol

#### Manual Testing Checklist
1. **Keyboard Navigation**: Tab through all interactive elements
2. **Screen Reader**: Test with NVDA/JAWS/VoiceOver
3. **Voice Interface**: Test all voice commands and states
4. **Responsive**: Test on mobile, tablet, desktop breakpoints
5. **High Contrast**: Test in high contrast mode
6. **Dark Mode**: Verify dark mode compatibility
7. **Performance**: Check load times and animation smoothness

#### Automated Testing
- Lighthouse accessibility audits (score >95)
- axe-core accessibility testing
- Visual regression testing with Percy/Chromatic
- Performance budgets enforced
- Cross-browser compatibility testing

---

## 📁 Figma File Organization

### Design System File Structure
```
Seiketsu Design System.fig
├── 📄 Cover & Documentation
├── 🎨 Design Tokens
│   ├── Colors (OKLCH values)
│   ├── Typography scales
│   ├── Spacing system
│   └── Shadow & radius tokens
├── 🧩 Foundation Components
│   ├── Buttons (all variants)
│   ├── Forms (inputs, labels, validation)
│   ├── Cards & containers
│   └── Navigation elements
├── 🗣️ Voice Interface Components
│   ├── Voice status indicators
│   ├── Waveform visualizations
│   ├── Transcript displays
│   └── Voice command patterns
├── 🏢 Enterprise Components
│   ├── Data tables
│   ├── Dashboard widgets
│   ├── Multi-tenant switching
│   └── Complex forms
├── 📱 Responsive Templates
│   ├── Mobile layouts
│   ├── Tablet adaptations
│   └── Desktop variations
├── ♿ Accessibility Variants
│   ├── High contrast versions
│   ├── Focus state examples
│   └── Screen reader annotations
└── 🎭 Animation Specifications
    ├── Micro-interaction demos
    ├── Loading state animations
    └── Voice feedback animations
```

### Figma Best Practices
- Use Auto Layout for all components
- Create comprehensive component variants
- Document component usage in descriptions
- Use consistent naming conventions
- Include accessibility annotations
- Provide implementation notes for developers
- Create responsive component examples
- Use component properties for state management

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Set up design tokens and CSS custom properties
- [ ] Implement color system with OKLCH values
- [ ] Create typography scale and spacing system
- [ ] Build basic button and form components
- [ ] Establish accessibility standards

### Phase 2: Voice Interface (Week 2)
- [ ] Develop voice status indicator components
- [ ] Create audio visualization patterns
- [ ] Build transcript display component
- [ ] Implement voice command confirmation patterns
- [ ] Test voice interface accessibility

### Phase 3: Enterprise Features (Week 3)
- [ ] Build data table components
- [ ] Create dashboard widget system
- [ ] Implement multi-tenant switching
- [ ] Develop complex form patterns
- [ ] Add bulk action capabilities

### Phase 4: Polish & Testing (Week 4)
- [ ] Comprehensive accessibility testing
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] Mobile optimization
- [ ] Documentation completion

---

## 📖 Resources & References

### Design References
- [Vercel Design System](https://vercel.com/design)
- [Linear Design System](https://linear.app/design)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [Tailwind UI Components](https://tailwindui.com/)

### Accessibility Guidelines
- [WCAG 2.1 AA Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Accessibility Resources](https://webaim.org/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

### Voice Interface Patterns
- [Voice User Interface Design Guidelines](https://developer.amazon.com/en-US/docs/alexa/voice-design/design-principles.html)
- [Google Assistant Design Guidelines](https://developers.google.com/assistant/actions/design)

### Technical Implementation
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [OKLCH Color Space](https://oklch.com/)
- [Framer Motion Documentation](https://www.framer.com/motion/)

---

*Seiketsu AI Design System v1.0 | Built for enterprise voice agent platforms | WCAG 2.1 AA Compliant*