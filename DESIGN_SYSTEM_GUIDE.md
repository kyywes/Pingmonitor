# PingMonitor Pro - Professional Design System Guide

## Overview

This design system provides a professional, modern, and consistent visual language for PingMonitor Pro. It's inspired by industry-leading dashboards like Grafana, DataDog, Linear, and Vercel.

---

## Color Palette

### Background Colors

| Token | Value | Usage |
|-------|-------|-------|
| `bg-primary` | `#0f172a` (Slate 950) | Main application background |
| `bg-secondary` | `#1e293b` (Slate 800) | Cards, panels, secondary surfaces |
| `bg-tertiary` | `#334155` (Slate 700) | Elevated elements, hover states |
| `bg-hover` | `#475569` (Slate 600) | Interactive hover backgrounds |

### Surface Colors

| Token | Value | Usage |
|-------|-------|-------|
| `surface-01` | `#1e293b` | Base card background |
| `surface-02` | `#334155` | Elevated cards, dialogs |
| `surface-03` | `#475569` | Modals, overlays |

### Border Colors

| Token | Value | Usage |
|-------|-------|-------|
| `border-subtle` | `#334155` | Subtle dividers, card borders |
| `border-default` | `#475569` | Standard borders |
| `border-strong` | `#64748b` | Emphasized borders |

### Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `text-primary` | `#f8fafc` (Slate 50) | Primary content, headings |
| `text-secondary` | `#cbd5e1` (Slate 300) | Secondary text, body copy |
| `text-tertiary` | `#94a3b8` (Slate 400) | Tertiary text, captions |
| `text-disabled` | `#64748b` (Slate 500) | Disabled state text |

### Status Colors

#### Online/Success (Emerald)
- **Color**: `#10b981` (Emerald 500)
- **Background**: `rgba(16, 185, 129, 0.1)`
- **Border**: `rgba(16, 185, 129, 0.3)`
- **Usage**: Online devices, successful operations

#### Offline/Error (Red)
- **Color**: `#ef4444` (Red 500)
- **Background**: `rgba(239, 68, 68, 0.1)`
- **Border**: `rgba(239, 68, 68, 0.3)`
- **Usage**: Offline devices, errors, failures

#### Warning/Degraded (Amber)
- **Color**: `#f59e0b` (Amber 500)
- **Background**: `rgba(245, 158, 11, 0.1)`
- **Border**: `rgba(245, 158, 11, 0.3)`
- **Usage**: Warnings, degraded performance

#### Info (Blue)
- **Color**: `#3b82f6` (Blue 500)
- **Background**: `rgba(59, 130, 246, 0.1)`
- **Border**: `rgba(59, 130, 246, 0.3)`
- **Usage**: Information, neutral states

### Brand/Accent Colors

| Token | Value | Usage |
|-------|-------|-------|
| `brand-primary` | `#6366f1` (Indigo 500) | Primary actions, links |
| `brand-hover` | `#4f46e5` (Indigo 600) | Hover state |
| `brand-active` | `#4338ca` (Indigo 700) | Active/pressed state |
| `brand-subtle` | `rgba(99, 102, 241, 0.1)` | Subtle backgrounds |

---

## Typography

### Font Families

```python
font-primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
font-mono: 'JetBrains Mono, "SF Mono", Monaco, Consolas, "Courier New", monospace'
```

### Font Sizes

| Token | Size | Usage |
|-------|------|-------|
| `text-xs` | 11px | Fine print, captions |
| `text-sm` | 13px | Secondary text, labels |
| `text-base` | 14px | Body text (default) |
| `text-md` | 16px | Emphasized text |
| `text-lg` | 18px | Section headers |
| `text-xl` | 20px | Card headers |
| `text-2xl` | 24px | Page titles |
| `text-3xl` | 32px | Display text |
| `text-4xl` | 40px | Hero text |

### Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `weight-regular` | 400 | Body text |
| `weight-medium` | 500 | Emphasized text |
| `weight-semibold` | 600 | Subheadings |
| `weight-bold` | 700 | Headings, important text |

### Line Heights

| Token | Value | Usage |
|-------|-------|-------|
| `leading-tight` | 1.2 | Headings |
| `leading-normal` | 1.5 | Body text |
| `leading-relaxed` | 1.75 | Long-form content |

### Letter Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `tracking-tight` | -0.02em | Large headings |
| `tracking-normal` | 0 | Body text |
| `tracking-wide` | 0.025em | Labels |
| `tracking-wider` | 0.05em | Uppercase labels |

---

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `space-0` | 0px | No spacing |
| `space-1` | 4px | Tight spacing |
| `space-2` | 8px | Small gaps |
| `space-3` | 12px | Default element spacing |
| `space-4` | 16px | Medium gaps |
| `space-5` | 20px | Card padding |
| `space-6` | 24px | Section spacing |
| `space-8` | 32px | Large gaps |
| `space-10` | 40px | Extra large spacing |
| `space-12` | 48px | XXL spacing |
| `space-16` | 64px | Hero spacing |
| `space-20` | 80px | Maximum spacing |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Small elements (checkboxes) |
| `radius-md` | 6px | Buttons, inputs |
| `radius-lg` | 8px | Cards, tables |
| `radius-xl` | 12px | Large cards, modals |
| `radius-2xl` | 16px | Feature cards |
| `radius-full` | 9999px | Pills, circular elements |

---

## Shadows & Elevation

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle elevation |
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.1)` | Small cards |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Dropdowns, popovers |
| `shadow-xl` | `0 20px 25px rgba(0,0,0,0.1)` | Modals |
| `shadow-2xl` | `0 25px 50px rgba(0,0,0,0.25)` | Hero sections |

---

## Component Specifications

### Status Indicators

#### Status Dot
- **Size Options**: Small (6px), Medium (8px), Large (10px)
- **Animation**: Pulse effect for active statuses (online, degraded)
- **Glow**: Radial gradient with pulsing opacity
- **States**: online, offline, degraded, warning, unknown, pending

#### Status Badge
- **Components**: Dot + Label
- **Padding**: 6-12px horizontal, 4-8px vertical
- **Border Radius**: 12px (pill shape)
- **Background**: Semi-transparent status color
- **Border**: 1px solid status color
- **Font**: 13px, weight 600

#### Usage Example
```python
from src.ui.components import StatusBadge, StatusDot

# Simple dot
dot = StatusDot(status='online', size=8, animate=True)

# Badge with label
badge = StatusBadge(status='offline', show_label=True, size='md')

# Table cell indicator
cell = StatusIndicatorCell(status='degraded')
```

### Buttons

#### Primary Button
- **Background**: Indigo 500 (`#6366f1`)
- **Hover**: Indigo 600 (`#4f46e5`)
- **Pressed**: Indigo 700 (`#4338ca`)
- **Text**: White, weight 500
- **Padding**: 8px 16px
- **Border Radius**: 6px
- **Min Height**: 36px

#### Success Button
- **Background**: Emerald 500 (`#10b981`)
- **Hover**: Emerald 600 (`#059669`)

#### Danger Button
- **Background**: Red 500 (`#ef4444`)
- **Hover**: Red 600 (`#dc2626`)

#### Ghost Button
- **Background**: Transparent
- **Hover**: `rgba(255, 255, 255, 0.05)`
- **Color**: Slate 300
- **Border**: Transparent

#### Usage Example
```python
from src.ui.design_system import DesignSystem as DS

btn_primary = QPushButton('Save')
btn_primary.setStyleSheet(DS.button_primary())

btn_danger = QPushButton('Delete')
btn_danger.setStyleSheet(DS.button_danger())
```

### Cards

#### Base Card
- **Background**: Surface 01 (`#1e293b`)
- **Border**: 1px solid border-subtle
- **Border Radius**: 12px
- **Padding**: 20px
- **Shadow**: Optional shadow-sm on hover

#### Elevated Card
- **Background**: Surface 02 (`#334155`)
- **Border**: 1px solid border-default
- **Shadow**: shadow-md

#### Usage Example
```python
card = QFrame()
card.setStyleSheet(DS.card())
```

### Tables

#### Modern Table Design
- **Background**: bg-primary
- **Alternate Rows**: bg-secondary
- **Grid Lines**: border-subtle
- **Border Radius**: 8px
- **Selection**: brand-subtle background

#### Header Style
- **Background**: surface-01
- **Text**: text-tertiary, uppercase
- **Font Size**: 13px
- **Font Weight**: 600
- **Letter Spacing**: 0.5px
- **Bottom Border**: 2px solid border-subtle
- **Padding**: 12px

#### Cell Style
- **Padding**: 12px
- **Text Color**: text-secondary
- **Hover**: interactive-hover background
- **Row Height**: 56px

#### Usage Example
```python
from src.ui.components import ModernDeviceTable

table = ModernDeviceTable()
table.set_devices(device_list)

# Connect signals
table.edit_device.connect(on_edit)
table.delete_device.connect(on_delete)
```

### Input Fields

#### Line Edit
- **Background**: surface-01
- **Border**: 1px solid border-subtle
- **Border Radius**: 6px
- **Padding**: 8px 12px
- **Focus**: Border changes to brand-primary
- **Hover**: Border changes to border-default

#### Placeholder
- **Color**: text-disabled
- **Font Style**: Regular

---

## Layout Guidelines

### Container Padding
- **Desktop**: 24px
- **Mobile**: 16px

### Section Gaps
- **Between sections**: 32px
- **Between cards**: 16px
- **Within cards**: 12px

### Grid System
- **Column Gap**: 16px
- **Row Gap**: 16px
- **Max Width**: 1400px (centered)

---

## Accessibility

### Color Contrast
All text colors meet WCAG 2.1 AA standards:
- **Primary text on bg-primary**: 16.8:1 (AAA)
- **Secondary text on bg-primary**: 9.3:1 (AAA)
- **Tertiary text on bg-primary**: 5.2:1 (AA)

### Focus States
- **Focus Ring**: 2px solid brand-primary
- **Focus Offset**: 2px
- **Visible on all interactive elements**

### Touch Targets
- **Minimum Size**: 44x44px
- **Applies to**: Buttons, checkboxes, icons

### Screen Reader Support
- All status indicators include text labels
- Tables use proper semantic HTML
- Forms have associated labels

---

## Animation Guidelines

### Timing Functions
- **Ease In Out**: Smooth transitions (200-300ms)
- **Ease Out**: Entering elements (300-400ms)
- **Ease In**: Exiting elements (200ms)

### Pulse Animation
```python
Duration: 2000ms
Keyframes:
  0%: opacity 1.0
  50%: opacity 0.3
  100%: opacity 1.0
Easing: InOutSine
Loop: Infinite
```

### Hover Effects
- **Transition**: 150ms ease-in-out
- **Properties**: background-color, border-color, transform

---

## Usage Examples

### Applying the Theme

```python
from src.ui.design_system import DesignSystem as DS

# Load global stylesheet
with open('src/ui/styles/professional_theme.qss', 'r') as f:
    app.setStyleSheet(f.read())
```

### Creating a Status Card

```python
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from src.ui.components import StatusDot
from src.ui.design_system import DesignSystem as DS

card = QFrame()
card.setStyleSheet(DS.card())

layout = QVBoxLayout(card)

# Add status indicator
status = StatusDot('online', size=10, animate=True)
layout.addWidget(status)

# Add title
title = QLabel('System Status')
title.setStyleSheet(DS.heading_3())
layout.addWidget(title)
```

### Building a Modern Table

```python
from src.ui.components import ModernDeviceTable

# Create table
table = ModernDeviceTable()

# Populate with data
table.set_devices(device_list)

# Connect signals
table.device_selected.connect(lambda id: print(f'Selected: {id}'))
table.edit_device.connect(open_edit_dialog)
table.delete_device.connect(confirm_delete)
```

---

## Best Practices

### Do's
- Use design tokens consistently
- Maintain proper spacing hierarchy
- Apply appropriate color contrast
- Use semantic status colors
- Include hover and focus states
- Add smooth transitions (150-300ms)
- Ensure 44px minimum touch targets

### Don'ts
- Don't use arbitrary colors
- Don't skip focus indicators
- Don't use emojis as sole indicators
- Don't create inconsistent spacing
- Don't use very long animations (>500ms)
- Don't rely solely on color for status

---

## File Structure

```
src/ui/
├── styles/
│   └── professional_theme.qss      # Global QSS theme
├── components/
│   ├── __init__.py                 # Component exports
│   ├── status_indicator.py         # Status components
│   └── modern_device_table.py      # Modern table
├── design_system.py                # Design tokens & helpers
└── [other UI modules]
```

---

## Migrating Existing UI

### Step 1: Apply Global Theme
```python
# In main application initialization
with open('src/ui/styles/professional_theme.qss', 'r') as f:
    app.setStyleSheet(f.read())
```

### Step 2: Replace Status Indicators
```python
# Old
label = QLabel("🟢 Online")

# New
from src.ui.components import StatusBadge
badge = StatusBadge(status='online', show_label=True)
```

### Step 3: Update Button Styles
```python
from src.ui.design_system import DesignSystem as DS

# Old button with inline styles
btn = QPushButton('Save')
btn.setStyleSheet("background: #10b981; ...")

# New with design system
btn = QPushButton('Save')
btn.setStyleSheet(DS.button_success())
```

### Step 4: Modernize Tables
```python
# Replace existing table with modern component
from src.ui.components import ModernDeviceTable

old_table = self.devices_table  # Remove this
new_table = ModernDeviceTable()  # Use this
```

---

## Testing the Design

### Visual Testing Checklist
- [ ] All text is readable (proper contrast)
- [ ] Status indicators are clearly visible
- [ ] Buttons have clear hover/active states
- [ ] Focus indicators are visible on all interactive elements
- [ ] Tables are easy to scan
- [ ] Spacing is consistent throughout
- [ ] Animations are smooth (no janky transitions)
- [ ] No color-only information

### Accessibility Testing
- [ ] Keyboard navigation works
- [ ] Screen reader announces status correctly
- [ ] All interactive elements are 44x44px minimum
- [ ] Color contrast passes WCAG AA
- [ ] Focus order is logical

---

## Support & Resources

### Design References
- [Tailwind CSS Colors](https://tailwindcss.com/docs/customizing-colors)
- [Material Design](https://material.io/design)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/)

### Inspiration
- Grafana Dashboard
- DataDog Monitoring
- Linear Project Management
- Vercel Dashboard

---

## Version History

- **v2.0** (Current) - Professional dark theme with modern components
- **v1.0** - Initial basic UI

---

**Created for PingMonitor Pro by Fabrizio Cerchia**
