# Epic 6: UI Modernization & Navigation

## Epic Overview
**Epic ID**: EPIC-06
**Epic Name**: UI Modernization & Navigation
**Epic Description**: Redesign the frontend UI with a modern icon-only sidebar, tab-based navigation, and clean light theme to improve user experience and visual appeal
**Business Value**: Enhanced usability, professional appearance, and better navigation structure for growing feature set
**User Impact**: Intuitive navigation, cleaner interface, and more efficient workflow
**Success Metrics**: Improved navigation efficiency, modern visual design, maintained functionality
**Status**: 🔴 Not Started

## Design Goals

### Visual Design
- **Layout**: Icon-only sidebar (64px width) + main content area with tabs
- **Icons**: Lucide React library for clean, modern icons
- **Theme**: Full light mode with strategic accent colors
- **Responsive**: Mobile-friendly with collapsible sidebar

### Navigation Structure
```
Sidebar Menu:
├── 📊 Portfolio (Dashboard view)
├── 📤 Upload (Transaction import)
└── 🗄️ Database (expandable submenu)
    ├── 📈 Stats (Database statistics)
    └── 🗑️ Reset (Database reset)
```

### Content Organization
- **Tab-based**: Each main section gets its own tab
- **Smooth transitions**: Animated tab switching
- **Persistent state**: Remember last active tab
- **Tooltips**: Icon labels appear on hover

## Features in this Epic
- Feature 6.1: Icon-Only Sidebar Navigation
- Feature 6.2: Tab-Based Content System
- Feature 6.3: Modern Light Theme & Styling

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F6.1: Icon-Only Sidebar | 3 | 8 | 🔴 Not Started | 0% (0/8 pts) |
| F6.2: Tab-Based Content | 2 | 5 | 🔴 Not Started | 0% (0/5 pts) |
| F6.3: Modern Theme | 2 | 5 | 🔴 Not Started | 0% (0/5 pts) |
| **Total** | **7** | **18** | **Not Started** | **0% (0/18 pts)** |

---

## Feature 6.1: Icon-Only Sidebar Navigation
**Feature Description**: Vertical icon-only sidebar with tooltips and expandable submenus
**User Value**: Quick navigation without cluttering the interface
**Priority**: High

### Story F6.1-001: Create Sidebar Component
**Status**: 🔴 Not Started
**User Story**: As FX, I want a modern icon-only sidebar so that I can navigate efficiently without wasting screen space

**Acceptance Criteria**:
- **Given** I am viewing the application
- **When** I look at the left side of the screen
- **Then** I see a 64px wide vertical sidebar with icons
- **And** Icons include: Portfolio, Upload, Database
- **And** Hovering over an icon shows a tooltip with the label
- **And** The active section is visually highlighted
- **And** Transitions are smooth and professional

**Technical Requirements**:
- Create `frontend/src/components/Sidebar.tsx`
- Use Lucide React icons: LayoutDashboard, Upload, Database, BarChart3, Trash2
- Implement tooltip system (CSS or library)
- Active state management
- Hover effects with smooth transitions
- Responsive behavior (collapse on mobile)

**Component Structure**:
```tsx
interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  // Sidebar items configuration
  // Tooltip logic
  // Active state styling
  // Click handlers
}
```

**Styling Requirements**:
- Fixed position, left side
- 64px width on desktop
- Background: white with subtle shadow
- Icons: 24px, centered
- Hover: background color change
- Active: accent color + indicator bar
- Tooltips: appear on right side, dark background

**Definition of Done**:
- [ ] Sidebar component created with icon navigation
- [ ] Tooltips display on hover
- [ ] Active state highlighting works
- [ ] Smooth hover transitions
- [ ] Mobile responsive (collapses or hides)
- [ ] All icons from Lucide React library
- [ ] Unit tests for component (10 tests)
- [ ] Accessibility: keyboard navigation support
- [ ] Documentation in component comments

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: None
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F6.1-002: Implement Expandable Database Submenu
**Status**: 🔴 Not Started
**User Story**: As FX, I want the Database menu item to expand and show Stats/Reset options so that I can access these features without cluttering the main menu

**Acceptance Criteria**:
- **Given** the sidebar is displayed
- **When** I click the Database icon
- **Then** a submenu expands showing Stats and Reset options
- **And** The submenu appears as a popover/flyout to the right
- **And** Clicking outside or another menu item closes the submenu
- **And** Visual indicator shows the Database menu is active

**Technical Requirements**:
- Expandable menu state management
- Submenu positioning (flyout to the right)
- Click-outside detection to close
- Smooth expand/collapse animation
- Visual indicator (dot, arrow, or highlight)

**UI/UX Design**:
```
Sidebar:
[📊] Portfolio
[📤] Upload
[🗄️] Database ─→ Flyout Menu:
                  ┌─────────────┐
                  │ 📈 Stats    │
                  │ 🗑️ Reset    │
                  └─────────────┘
```

**Definition of Done**:
- [ ] Database menu expands on click
- [ ] Submenu flyout positioned correctly
- [ ] Click outside closes submenu
- [ ] Smooth animations
- [ ] Visual active indicator
- [ ] Keyboard navigation support (arrow keys)
- [ ] Unit tests for expand/collapse logic (8 tests)
- [ ] Mobile behavior defined and tested

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F6.1-001
**Risk Level**: Medium (Complex interaction)
**Assigned To**: Unassigned

---

### Story F6.1-003: Add Sidebar Tooltips
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see tooltips when hovering over sidebar icons so that I know what each icon represents without memorizing them

**Acceptance Criteria**:
- **Given** the sidebar is displayed
- **When** I hover over any icon
- **Then** a tooltip appears showing the label (Portfolio, Upload, Database, etc.)
- **And** The tooltip appears on the right side of the icon
- **And** The tooltip has a slight delay before appearing (300ms)
- **And** The tooltip disappears when I move away
- **And** Tooltips are styled consistently

**Technical Requirements**:
- Tooltip component or library (consider Radix UI Tooltip)
- Delay configuration (300ms hover delay)
- Position: right of icon with arrow
- Dark background, white text
- Z-index management
- Accessible (ARIA labels)

**Tooltip Styling**:
- Background: #1f2937 (dark gray)
- Text: white, 14px
- Padding: 8px 12px
- Border radius: 6px
- Arrow/pointer to sidebar
- Subtle shadow

**Definition of Done**:
- [ ] Tooltips appear on hover for all icons
- [ ] 300ms delay before showing
- [ ] Consistent positioning
- [ ] Professional styling
- [ ] Accessible with screen readers
- [ ] Works on all sidebar items including submenu
- [ ] Unit tests for tooltip behavior (6 tests)
- [ ] No tooltip on mobile (touch devices)

**Story Points**: 2
**Priority**: Should Have
**Dependencies**: F6.1-001
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 6.2: Tab-Based Content System
**Feature Description**: Organize main content into tabs with smooth transitions
**User Value**: Clear separation of concerns, easy switching between sections
**Priority**: High

### Story F6.2-001: Create Tab View Component
**Status**: 🔴 Not Started
**User Story**: As FX, I want the main content to be organized in tabs so that I can easily switch between Portfolio, Upload, and Database views

**Acceptance Criteria**:
- **Given** I am viewing the application
- **When** I click on a sidebar icon
- **Then** the corresponding tab content is displayed
- **And** Only one tab is visible at a time
- **And** Transition between tabs is smooth and animated
- **And** The active tab is visually indicated in the sidebar

**Technical Requirements**:
- Create `frontend/src/components/TabView.tsx`
- Tab content panels for: Portfolio, Upload, Database
- Fade/slide transitions between tabs
- State management for active tab
- Integrate with Sidebar component

**Component Structure**:
```tsx
interface TabViewProps {
  activeTab: string;
  children: React.ReactNode;
}

const TabView: React.FC<TabViewProps> = ({ activeTab, children }) => {
  // Tab switching logic
  // Animation/transition handling
  // Render active tab content
}
```

**Tab Definitions**:
- **Portfolio Tab**: Current portfolio overview (existing content)
- **Upload Tab**: TransactionImport component
- **Database Tab**: Container for Stats and Reset views

**Definition of Done**:
- [ ] TabView component created
- [ ] All three tabs render correctly
- [ ] Smooth transitions between tabs
- [ ] State management works with sidebar
- [ ] No content flashing during transitions
- [ ] Previous tab content unmounts properly
- [ ] Unit tests for tab switching (12 tests)
- [ ] Performance: no lag during transitions

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F6.1-001
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F6.2-002: Integrate Existing Components into Tabs
**Status**: 🔴 Not Started
**User Story**: As FX, I want my existing features (upload, stats, reset) to work seamlessly in the new tab layout so that I don't lose any functionality

**Acceptance Criteria**:
- **Given** the new tab system is in place
- **When** I navigate to each tab
- **Then** all existing functionality works as before
- **And** Upload component works in Upload tab
- **And** Database Stats displays in Database tab (Stats view)
- **And** Database Reset works in Database tab (Reset view)
- **And** No features are broken or degraded

**Technical Requirements**:
- Move TransactionImport to Upload tab
- Convert DatabaseStats from modal to inline view in Database tab
- Convert DatabaseReset from modal to inline view in Database tab
- Maintain all existing functionality
- Update state management as needed
- Clean up old modal code if not needed

**Integration Points**:
```tsx
// Portfolio Tab
<div className="portfolio-tab">
  {/* Existing portfolio overview content */}
</div>

// Upload Tab
<div className="upload-tab">
  <TransactionImport />
</div>

// Database Tab with sub-navigation
<div className="database-tab">
  {databaseView === 'stats' ? (
    <DatabaseStatsInline />
  ) : (
    <DatabaseResetInline />
  )}
</div>
```

**Definition of Done**:
- [ ] All components integrated into tabs
- [ ] Upload functionality works in Upload tab
- [ ] Stats displays correctly in Database tab
- [ ] Reset works correctly in Database tab
- [ ] Sub-navigation between Stats/Reset in Database tab
- [ ] No regression in existing features
- [ ] Integration tests for all workflows (15 tests)
- [ ] User flows tested end-to-end

**Story Points**: 2
**Priority**: Must Have
**Dependencies**: F6.2-001
**Risk Level**: Medium (Integration complexity)
**Assigned To**: Unassigned

---

## Feature 6.3: Modern Light Theme & Styling
**Feature Description**: Apply modern, clean light theme with strategic accent colors
**User Value**: Professional appearance, pleasant user experience, reduced eye strain
**Priority**: High

### Story F6.3-001: Design System & Color Palette
**Status**: 🔴 Not Started
**User Story**: As FX, I want a cohesive, professional color scheme so that the application looks polished and modern

**Acceptance Criteria**:
- **Given** the application is loaded
- **When** I view any part of the UI
- **Then** colors are consistent and professional
- **And** Accent colors are used strategically
- **And** Contrast ratios meet accessibility standards (WCAG AA)
- **And** The theme is cohesive across all components

**Color Palette**:
```css
/* Primary Colors */
--color-primary: #3b82f6;      /* Blue - main actions */
--color-primary-dark: #2563eb;
--color-primary-light: #93c5fd;

/* Semantic Colors */
--color-success: #10b981;      /* Green - success states */
--color-warning: #f59e0b;      /* Amber - warnings */
--color-danger: #ef4444;       /* Red - destructive actions */

/* Neutral Colors */
--color-bg-primary: #ffffff;   /* White - main background */
--color-bg-secondary: #f9fafb; /* Light gray - cards */
--color-bg-tertiary: #f3f4f6;  /* Lighter gray - hover */
--color-border: #e5e7eb;       /* Border color */
--color-text-primary: #111827; /* Dark gray - headings */
--color-text-secondary: #6b7280; /* Medium gray - body */
--color-text-tertiary: #9ca3af;  /* Light gray - muted */

/* Shadows */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
```

**Typography**:
- Font family: system font stack or Inter
- Headings: 600-700 weight
- Body: 400 weight
- Font sizes: 12px, 14px, 16px, 18px, 24px, 32px

**Definition of Done**:
- [ ] CSS variables defined for all colors
- [ ] Color palette documented
- [ ] Accessibility contrast ratios verified (WCAG AA)
- [ ] Typography system established
- [ ] Shadow system defined
- [ ] Design tokens exported
- [ ] All components use design system
- [ ] Documentation updated with design guidelines

**Story Points**: 2
**Priority**: Must Have
**Dependencies**: None
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F6.3-002: Apply Modern Styling to All Components
**Status**: 🔴 Not Started
**User Story**: As FX, I want all components to have a consistent, modern look so that the application feels cohesive and professional

**Acceptance Criteria**:
- **Given** the design system is defined
- **When** I view any component
- **Then** it uses the new color palette and styling
- **And** Cards have subtle shadows and rounded corners
- **And** Buttons have consistent styling
- **And** Spacing is uniform and balanced
- **And** Hover states are smooth and pleasant

**Components to Style**:
- Sidebar (already styled in F6.1-001)
- Tab content areas
- Portfolio cards and tables
- Upload component
- Database stats display
- Forms and inputs
- Buttons (primary, secondary, danger)
- Modals (if any remain)

**Styling Guidelines**:
- Border radius: 8px for cards, 6px for buttons
- Padding: 16px, 20px, 24px (based on component)
- Gaps: 8px, 12px, 16px, 24px
- Transitions: 200ms ease for interactions
- Cards: white background, subtle shadow
- Buttons: solid fill, hover effects

**Definition of Done**:
- [ ] All components styled with new design system
- [ ] Consistent spacing throughout
- [ ] Smooth hover/active states
- [ ] Cards have professional appearance
- [ ] Tables are clean and readable
- [ ] Forms are well-aligned
- [ ] Visual regression tests pass
- [ ] Cross-browser compatibility verified

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F6.3-001, F6.2-001
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Technical Design Notes

### Component Architecture
```
App.tsx
├── Sidebar.tsx (icon-only navigation)
│   ├── MenuItem (Portfolio)
│   ├── MenuItem (Upload)
│   └── MenuItem (Database)
│       └── Submenu (Stats, Reset)
└── MainContent
    └── TabView.tsx
        ├── PortfolioTab
        ├── UploadTab
        └── DatabaseTab
            ├── StatsView
            └── ResetView
```

### Layout System
```css
.app-layout {
  display: grid;
  grid-template-columns: 64px 1fr;
  height: 100vh;
}

.sidebar {
  /* Fixed width, full height */
}

.main-content {
  /* Flex-grow, scrollable */
}
```

### State Management
- Use React Context or local state for:
  - Active tab
  - Database submenu open/closed
  - Theme preferences (future)

### Responsive Breakpoints
- Desktop: > 1024px (sidebar visible)
- Tablet: 768px - 1024px (sidebar collapsed to icons)
- Mobile: < 768px (sidebar hidden, hamburger menu)

### Dependencies to Add
```json
{
  "lucide-react": "^0.263.1"
}
```

### Optional Enhancements (Post-Epic)
- URL-based routing (react-router)
- Keyboard shortcuts
- Dark mode toggle
- Custom theme builder
- Animations library (framer-motion)

---

## Testing Strategy

### Unit Tests (Minimum 40 tests)
- Sidebar component: navigation, tooltips, active states (10 tests)
- Submenu: expand/collapse, click outside (8 tests)
- TabView: switching, transitions, content (12 tests)
- Integration: sidebar → tabs (10 tests)

### Integration Tests (Minimum 15 tests)
- Full navigation workflows
- Database submenu → Stats/Reset views
- Upload flow in new layout
- Responsive behavior

### Visual Regression Tests
- Screenshot comparison before/after
- Multiple screen sizes
- All tab states

### Accessibility Tests
- Keyboard navigation
- Screen reader compatibility
- Color contrast
- Focus management

---

## Epic Success Criteria
- [ ] Modern, professional UI appearance
- [ ] Icon-only sidebar with smooth interactions
- [ ] Tab-based content navigation
- [ ] All existing functionality preserved
- [ ] Clean light theme applied throughout
- [ ] Responsive on mobile/tablet/desktop
- [ ] 55+ tests passing (40 unit + 15 integration)
- [ ] Accessibility standards met (WCAG AA)
- [ ] Performance: no lag, smooth animations
- [ ] Cross-browser compatibility (Chrome, Firefox, Safari)

---

## Implementation Timeline
**Estimated Duration**: 2-3 days
- Day 1 Morning: F6.1-001, F6.1-003 (Sidebar + Tooltips)
- Day 1 Afternoon: F6.1-002 (Submenu)
- Day 2 Morning: F6.2-001 (Tab System)
- Day 2 Afternoon: F6.2-002 (Integration)
- Day 3 Morning: F6.3-001, F6.3-002 (Theme + Styling)
- Day 3 Afternoon: Testing, polish, documentation

---

## Dependencies
**Blocks**: None
**Blocked By**: None
**Related**: Epic 1 (uses existing components)

---

*Epic 6 will modernize the UI without changing backend functionality or data structures. All existing features will be preserved and enhanced with better navigation and visual design.*
