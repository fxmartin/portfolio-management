# Epic 4: Portfolio Visualization

## Epic Overview
**Epic ID**: EPIC-04
**Epic Name**: Portfolio Visualization
**Epic Description**: Display portfolio data with interactive dashboard and charts
**Business Value**: Visual understanding of portfolio performance and asset allocation
**User Impact**: Quick insights into portfolio health and performance trends
**Success Metrics**: Dashboard loads in <2 seconds, charts update in real-time
**Status**: 🔴 Not Started

## Features in this Epic
- Feature 4.1: Portfolio Dashboard
- Feature 4.2: Performance Charts
- Feature 4.3: Asset Allocation View (Future)

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F4.1: Portfolio Dashboard | 2 | 8 | 🔴 Not Started | 0% |
| F4.2: Performance Charts | 2 | 11 | 🔴 Not Started | 0% |
| **Total** | **4** | **19** | **Not Started** | **0%** |

---

## Feature 4.1: Portfolio Dashboard
**Feature Description**: Main dashboard showing portfolio summary and holdings table
**User Value**: At-a-glance view of entire portfolio status and performance
**Priority**: High
**Complexity**: 8 story points

### Story F4.1-001: Portfolio Summary View
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see my total portfolio value and cash balance so that I know my net worth

**Acceptance Criteria**:
- **Given** I have imported my transactions and prices are loaded
- **When** viewing the dashboard
- **Then** I see total portfolio value in base currency (USD/EUR)
- **And** I see available cash balance by currency
- **And** I see total P&L (realized + unrealized)
- **And** I see today's change in value and percentage
- **And** values update in real-time when prices change
- **And** loading states are shown while data fetches

**Technical Requirements**:
- React component with TypeScript
- Real-time updates via WebSocket/polling
- Currency formatting utilities
- Loading and error states
- Responsive design

**Component Design**:
```typescript
interface PortfolioSummary {
  totalValue: number;
  cashBalances: Map<string, number>;
  totalPnL: number;
  totalPnLPercent: number;
  dayChange: number;
  dayChangePercent: number;
  lastUpdated: Date;
}

const PortfolioSummaryCard: React.FC = () => {
  const [summary, setSummary] = useState<PortfolioSummary>();
  const [loading, setLoading] = useState(true);

  // WebSocket subscription for real-time updates
  useEffect(() => {
    const ws = subscribeToPortfolio((data) => {
      setSummary(data);
    });
    return () => ws.close();
  }, []);

  return (
    <Card className="portfolio-summary">
      <h2>Portfolio Value</h2>
      <div className="total-value">
        ${formatCurrency(summary?.totalValue)}
      </div>
      <div className="day-change">
        {formatChange(summary?.dayChange, summary?.dayChangePercent)}
      </div>
      // ... more summary details
    </Card>
  );
};
```

**UI Mockup**:
```
┌─────────────────────────────────────┐
│ Portfolio Summary                    │
├─────────────────────────────────────┤
│ Total Value:     $125,450.32        │
│ Day Change:      +$1,234.56 (+1.0%) │
│                                      │
│ Cash:            $10,000.00         │
│ Investments:     $115,450.32        │
│                                      │
│ Total P&L:       +$15,450.32        │
│ Unrealized:      +$8,230.15         │
│ Realized:        +$7,220.17         │
│                                      │
│ Last Updated: 10:30:45 AM           │
└─────────────────────────────────────┘
```

**Definition of Done**:
- [ ] Summary component implemented with TypeScript
- [ ] Real-time value updates working
- [ ] Currency formatting with locale support
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Loading and error states handled
- [ ] Color coding for positive/negative changes
- [ ] Unit tests for component logic
- [ ] Integration test with API
- [ ] Accessibility (ARIA labels, keyboard navigation)

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F2.3-001 (P&L Calculations)
**Risk Level**: Low
**Assigned To**: Unassigned

---

### Story F4.1-002: Holdings Table
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see all my positions in a table so that I can review my investments at a glance

**Acceptance Criteria**:
- **Given** I have open positions in my portfolio
- **When** viewing the holdings table
- **Then** I see columns: Ticker, Name, Quantity, Avg Cost, Current Price, Value, P&L, P&L%
- **And** profits are shown in green, losses in red
- **And** I can sort by any column (ascending/descending)
- **And** I can filter by asset type (stock/crypto)
- **And** I can search by ticker or name
- **And** clicking a row shows position details
- **And** table is paginated for >20 positions

**Technical Requirements**:
- React Table or similar library
- Sortable columns
- Search/filter functionality
- Row click handlers
- Pagination or virtualization
- Export to CSV

**Table Component Design**:
```typescript
interface Position {
  ticker: string;
  name: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  dayChange: number;
  assetType: 'stock' | 'crypto' | 'forex';
}

const HoldingsTable: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [sortConfig, setSortConfig] = useState({ key: 'value', direction: 'desc' });
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const columns = [
    { key: 'ticker', label: 'Ticker', sortable: true },
    { key: 'quantity', label: 'Quantity', sortable: true, align: 'right' },
    { key: 'avgCost', label: 'Avg Cost', sortable: true, align: 'right', format: 'currency' },
    { key: 'currentPrice', label: 'Price', sortable: true, align: 'right', format: 'currency' },
    { key: 'marketValue', label: 'Value', sortable: true, align: 'right', format: 'currency' },
    { key: 'unrealizedPnL', label: 'P&L', sortable: true, align: 'right', format: 'pnl' },
    { key: 'unrealizedPnLPercent', label: 'P&L %', sortable: true, align: 'right', format: 'percent' }
  ];

  return (
    <div className="holdings-table-container">
      <TableControls onSearch={setSearchTerm} onFilter={setFilter} />
      <Table
        data={filteredAndSortedPositions}
        columns={columns}
        onSort={handleSort}
        onRowClick={handleRowClick}
      />
      <ExportButton data={positions} filename="portfolio.csv" />
    </div>
  );
};
```

**Table UI Example**:
```
┌────────┬──────────┬──────────┬─────────┬──────────┬────────────┬──────────┐
│ Ticker │ Quantity │ Avg Cost │ Price   │ Value    │ P&L        │ P&L %    │
├────────┼──────────┼──────────┼─────────┼──────────┼────────────┼──────────┤
│ AAPL   │ 100      │ $145.50  │ $150.25 │ $15,025  │ +$475.00   │ +3.26%   │
│ TSLA   │ 50       │ $250.00  │ $245.60 │ $12,280  │ -$220.00   │ -1.76%   │
│ BTC    │ 0.5      │ $45,000  │ $50,000 │ $25,000  │ +$2,500.00 │ +11.11%  │
└────────┴──────────┴──────────┴─────────┴──────────┴────────────┴──────────┘
```

**Definition of Done**:
- [ ] Table component with all required columns
- [ ] Color coding for P&L (green/red)
- [ ] Sortable columns (click to sort)
- [ ] Filter by asset type dropdown
- [ ] Search box for ticker/name
- [ ] Row click shows details modal/drawer
- [ ] Pagination or virtual scrolling for performance
- [ ] Export to CSV functionality
- [ ] Responsive table design
- [ ] Unit tests for sorting/filtering logic
- [ ] Accessibility compliant

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F4.1-001 (Summary View)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Feature 4.2: Performance Charts
**Feature Description**: Visual charts showing portfolio performance over time
**User Value**: Understand portfolio trends and asset allocation visually
**Priority**: Should Have
**Complexity**: 11 story points

### Story F4.2-001: Portfolio Value Chart
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see my portfolio value over time so that I can track my investment growth

**Acceptance Criteria**:
- **Given** historical transaction and price data
- **When** viewing the portfolio chart
- **Then** I see a line chart of portfolio value over time
- **And** I can select time periods (1D, 1W, 1M, 3M, 1Y, All)
- **And** chart shows daily closing values for periods >1 week
- **And** chart shows hourly values for 1D view
- **And** current value is highlighted with a dot
- **And** I can hover to see exact values and dates
- **And** chart is responsive to screen size

**Technical Requirements**:
- Recharts or Chart.js library
- Time period selector
- Data aggregation logic
- Responsive chart sizing
- Touch support for mobile

**Chart Component Design**:
```typescript
interface ChartDataPoint {
  date: Date;
  value: number;
  change: number;
}

const PortfolioValueChart: React.FC = () => {
  const [period, setPeriod] = useState<'1D'|'1W'|'1M'|'3M'|'1Y'|'All'>('1M');
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  const timeRanges = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: '3M', value: '3M' },
    { label: '1Y', value: '1Y' },
    { label: 'All', value: 'All' }
  ];

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3>Portfolio Performance</h3>
        <TimeRangeSelector
          ranges={timeRanges}
          selected={period}
          onChange={setPeriod}
        />
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
          />
          <YAxis
            domain={['dataMin', 'dataMax']}
            tickFormatter={formatCurrency}
          />
          <Tooltip
            content={<CustomTooltip />}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
          />
          <ReferenceLine
            y={initialValue}
            stroke="#666"
            strokeDasharray="3 3"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

**Chart Features**:
- Smooth line chart with gradient fill
- Interactive tooltips showing date and value
- Reference line for initial investment
- Zoom and pan capabilities (optional)
- Export chart as image (optional)

**Definition of Done**:
- [ ] Line chart component implemented (Recharts)
- [ ] Time period selector working
- [ ] Data aggregation for different periods
- [ ] Historical data calculation logic
- [ ] Interactive tooltips with formatting
- [ ] Responsive chart sizing
- [ ] Touch support for mobile devices
- [ ] Loading state while fetching data
- [ ] Handle empty data gracefully
- [ ] Unit tests for data aggregation
- [ ] Performance: Render 1000 data points smoothly

**Story Points**: 8
**Priority**: Should Have
**Dependencies**: F4.1-002 (Holdings Table)
**Risk Level**: Medium
**Assigned To**: Unassigned

---

### Story F4.2-002: Asset Allocation Pie Chart
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see my asset allocation so that I can understand my portfolio diversification

**Acceptance Criteria**:
- **Given** current portfolio positions
- **When** viewing the allocation chart
- **Then** I see a pie chart of holdings by value
- **And** each slice shows ticker and percentage
- **And** slices are colored distinctly
- **And** small positions (<2%) are grouped as "Other"
- **And** clicking a slice shows position details
- **And** legend shows all positions with values
- **And** chart updates with price changes

**Technical Requirements**:
- Pie chart with animations
- Interactive slices
- Dynamic color palette
- Legend component
- Grouping logic for small positions

**Pie Chart Design**:
```typescript
interface AllocationData {
  ticker: string;
  value: number;
  percentage: number;
  color: string;
}

const AssetAllocationChart: React.FC = () => {
  const [allocations, setAllocations] = useState<AllocationData[]>([]);
  const [selectedSlice, setSelectedSlice] = useState<string | null>(null);

  const processAllocations = (positions: Position[]) => {
    const total = positions.reduce((sum, p) => sum + p.marketValue, 0);

    return positions
      .map(p => ({
        ticker: p.ticker,
        value: p.marketValue,
        percentage: (p.marketValue / total) * 100,
        color: getColorForTicker(p.ticker)
      }))
      .sort((a, b) => b.value - a.value)
      .reduce((acc, item) => {
        if (item.percentage < 2) {
          const other = acc.find(a => a.ticker === 'Other');
          if (other) {
            other.value += item.value;
            other.percentage += item.percentage;
          } else {
            acc.push({ ...item, ticker: 'Other' });
          }
        } else {
          acc.push(item);
        }
        return acc;
      }, [] as AllocationData[]);
  };

  return (
    <div className="allocation-chart-container">
      <h3>Asset Allocation</h3>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={allocations}
            dataKey="value"
            nameKey="ticker"
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            onClick={handleSliceClick}
          >
            {allocations.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="middle"
            align="right"
            layout="vertical"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
```

**Definition of Done**:
- [ ] Pie chart component implemented
- [ ] Percentage calculations correct
- [ ] Interactive slice clicking
- [ ] Small positions grouped as "Other"
- [ ] Distinct colors for each slice
- [ ] Legend with ticker and values
- [ ] Responsive chart sizing
- [ ] Animation on load
- [ ] Real-time updates with price changes
- [ ] Handle single position gracefully
- [ ] Unit tests for allocation calculations

**Story Points**: 3
**Priority**: Should Have
**Dependencies**: F4.1-002 (Holdings Table)
**Risk Level**: Low
**Assigned To**: Unassigned

---

## Technical Design Notes

### Component Architecture
```
Dashboard/
├── components/
│   ├── PortfolioSummary/
│   │   ├── PortfolioSummary.tsx
│   │   ├── PortfolioSummary.test.tsx
│   │   └── PortfolioSummary.css
│   ├── HoldingsTable/
│   │   ├── HoldingsTable.tsx
│   │   ├── TableControls.tsx
│   │   └── HoldingsTable.test.tsx
│   └── Charts/
│       ├── PortfolioValueChart.tsx
│       ├── AssetAllocationChart.tsx
│       └── ChartUtils.ts
├── hooks/
│   ├── usePortfolio.ts
│   ├── useRealTimeUpdates.ts
│   └── useChartData.ts
└── utils/
    ├── formatters.ts
    ├── calculations.ts
    └── colors.ts
```

### State Management
```typescript
// Using Context API or Zustand
interface PortfolioState {
  summary: PortfolioSummary;
  positions: Position[];
  historicalData: ChartDataPoint[];
  isLoading: boolean;
  error: Error | null;

  // Actions
  fetchPortfolio: () => Promise<void>;
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;
}
```

### Real-time Updates
- WebSocket connection for price updates
- Optimistic UI updates
- Debounced re-rendering
- Differential updates only

### Performance Optimization
- Virtual scrolling for large tables
- Memoized calculations
- Lazy loading for charts
- Code splitting by route
- Service worker for offline support

---

## Dependencies
- **External**: Portfolio data from Epic 2, Live prices from Epic 3
- **Internal**: Summary must load before table
- **Libraries**: React, TypeScript, Recharts, Tailwind CSS

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| Performance with large portfolios | Slow rendering | Virtual scrolling, pagination |
| Chart library limitations | Missing features | Evaluate alternatives, custom charts |
| Real-time update complexity | Buggy updates | Thorough testing, fallback to polling |
| Mobile responsiveness | Poor mobile UX | Mobile-first design, touch testing |

## Testing Strategy
1. **Unit Tests**: Component logic and calculations
2. **Integration Tests**: API integration, real-time updates
3. **Visual Regression Tests**: Chart rendering consistency
4. **Performance Tests**: Large dataset rendering
5. **E2E Tests**: Complete user flows
6. **Accessibility Tests**: Screen reader, keyboard navigation

## Performance Requirements
- Initial dashboard load: <2 seconds
- Chart render: <500ms for 1000 data points
- Table sort/filter: <100ms
- Real-time update latency: <200ms
- Smooth scrolling: 60fps

## Definition of Done for Epic
- [ ] All 4 stories completed
- [ ] Portfolio summary with real-time updates
- [ ] Holdings table with sort/filter/search
- [ ] Portfolio value chart with time ranges
- [ ] Asset allocation pie chart
- [ ] Responsive design for all screen sizes
- [ ] Real-time price updates working
- [ ] Performance meets requirements
- [ ] 80% unit test coverage
- [ ] Accessibility audit passed
- [ ] Documentation for component usage