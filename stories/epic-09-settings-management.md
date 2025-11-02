# Epic 9: Settings Management

## Epic Overview
**Epic ID**: EPIC-09
**Epic Name**: Settings Management & Configuration
**Epic Description**: User-configurable settings interface for managing application configuration, API keys, and preferences
**Business Value**: Centralized settings management without manual .env file editing, secure credential storage, and customizable user experience
**User Impact**: FX can modify settings through the UI instead of editing configuration files manually
**Success Metrics**: All settings manageable via UI, API keys securely stored, changes applied without restart
**Status**: 🔴 Not Started

## Features in this Epic
- Feature 9.1: Settings Database & Backend API
- Feature 9.2: Settings UI Components
- Feature 9.3: API Key Management & Security
- Feature 9.4: Prompt Management Integration
- Feature 9.5: Display & Preference Settings

## Progress Tracking
| Feature | Stories | Points | Status | Progress |
|---------|---------|--------|--------|----------|
| F9.1: Settings Backend | 3 | 13 | ✅ Complete | 100% (13/13 pts) |
| F9.2: Settings UI | 3 | 13 | 🟡 In Progress | 77% (10/13 pts) |
| F9.3: API Key Security | 2 | 8 | 🔴 Not Started | 0% |
| F9.4: Prompt Integration | 2 | 8 | 🔴 Not Started | 0% |
| F9.5: Display Settings | 2 | 8 | 🔴 Not Started | 0% |
| **Total** | **12** | **50** | **🟡 In Progress** | **46%** (23/50 pts) |

---

## Feature 9.1: Settings Database & Backend API
**Feature Description**: Database schema and REST API for settings management
**User Value**: Persistent configuration storage with versioning and validation
**Priority**: High
**Complexity**: 13 story points

### Story F9.1-001: Settings Database Schema
**Status**: ✅ Complete (PR #49)
**User Story**: As FX, I want settings stored in the database so that they persist across restarts and deployments

**Acceptance Criteria**:
- **Given** the application starts for the first time
- **When** connecting to the database
- **Then** `application_settings` table is created
- **And** `setting_history` table is created for audit trail
- **And** default settings are seeded automatically
- **And** settings are categorized (display, api_keys, prompts, system)
- **And** sensitive values are encrypted at rest
- **And** settings have validation rules stored

**Technical Requirements**:
- SQLAlchemy models for `ApplicationSetting` and `SettingHistory`
- Alembic migration for schema creation
- Seed data with sensible defaults
- Encryption for sensitive fields (API keys)
- Setting categories enum: DISPLAY, API_KEYS, PROMPTS, SYSTEM, ADVANCED
- Validation rules stored as JSON schema

**Database Schema Design**:
```python
# models.py additions
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSON
import enum

class SettingCategory(str, enum.Enum):
    DISPLAY = "display"
    API_KEYS = "api_keys"
    PROMPTS = "prompts"
    SYSTEM = "system"
    ADVANCED = "advanced"

class ApplicationSetting(Base):
    __tablename__ = 'application_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # JSON string for complex values
    category = Column(SQLEnum(SettingCategory), nullable=False, index=True)
    is_sensitive = Column(Boolean, default=False)  # Encrypted if True
    is_editable = Column(Boolean, default=True)  # Some settings are read-only
    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    validation_rules = Column(JSON, nullable=True)  # JSON schema for validation
    last_modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_settings_category', 'category'),
    )

class SettingHistory(Base):
    __tablename__ = 'setting_history'

    id = Column(Integer, primary_key=True)
    setting_id = Column(Integer, ForeignKey('application_settings.id'), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(100), default='system')  # Future: user tracking
    changed_at = Column(DateTime, default=func.now())
    change_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_setting_history_setting', 'setting_id', 'changed_at'),
    )
```

**Default Settings to Seed**:
```python
DEFAULT_SETTINGS = [
    # Display Settings
    {
        'key': 'base_currency',
        'value': 'EUR',
        'category': SettingCategory.DISPLAY,
        'is_sensitive': False,
        'description': 'Base currency for portfolio display',
        'validation_rules': {'enum': ['EUR', 'USD', 'GBP', 'CHF']}
    },
    {
        'key': 'date_format',
        'value': 'YYYY-MM-DD',
        'category': SettingCategory.DISPLAY,
        'is_sensitive': False,
        'description': 'Date format for transaction display',
        'validation_rules': {'enum': ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY']}
    },
    {
        'key': 'number_format',
        'value': 'en-US',
        'category': SettingCategory.DISPLAY,
        'is_sensitive': False,
        'description': 'Number formatting locale',
        'validation_rules': {'enum': ['en-US', 'de-DE', 'fr-FR', 'en-GB']}
    },

    # API Keys
    {
        'key': 'anthropic_api_key',
        'value': None,
        'category': SettingCategory.API_KEYS,
        'is_sensitive': True,
        'description': 'Anthropic Claude API key for AI analysis',
        'validation_rules': {'pattern': '^sk-ant-.*$', 'minLength': 20}
    },
    {
        'key': 'alpha_vantage_api_key',
        'value': None,
        'category': SettingCategory.API_KEYS,
        'is_sensitive': True,
        'description': 'Alpha Vantage API key for market data fallback',
        'validation_rules': {'minLength': 16, 'maxLength': 16}
    },

    # AI Settings
    {
        'key': 'anthropic_model',
        'value': 'claude-sonnet-4-5-20250929',
        'category': SettingCategory.PROMPTS,
        'is_sensitive': False,
        'description': 'Claude model to use for analysis',
        'validation_rules': {'enum': ['claude-sonnet-4-5-20250929', 'claude-opus-4-20250514', 'claude-haiku-4-20250702']}
    },
    {
        'key': 'anthropic_temperature',
        'value': '0.3',
        'category': SettingCategory.PROMPTS,
        'is_sensitive': False,
        'description': 'Temperature for Claude API (0-1)',
        'validation_rules': {'type': 'number', 'minimum': 0, 'maximum': 1}
    },
    {
        'key': 'anthropic_max_tokens',
        'value': '4096',
        'category': SettingCategory.PROMPTS,
        'is_sensitive': False,
        'description': 'Maximum tokens for Claude responses',
        'validation_rules': {'type': 'integer', 'minimum': 1024, 'maximum': 8192}
    },

    # System Settings
    {
        'key': 'crypto_price_refresh_seconds',
        'value': '60',
        'category': SettingCategory.SYSTEM,
        'is_sensitive': False,
        'description': 'Crypto price refresh interval (seconds)',
        'validation_rules': {'type': 'integer', 'minimum': 30, 'maximum': 600}
    },
    {
        'key': 'stock_price_refresh_seconds',
        'value': '120',
        'category': SettingCategory.SYSTEM,
        'is_sensitive': False,
        'description': 'Stock price refresh interval (seconds)',
        'validation_rules': {'type': 'integer', 'minimum': 60, 'maximum': 600}
    },
    {
        'key': 'cache_ttl_hours',
        'value': '1',
        'category': SettingCategory.SYSTEM,
        'is_sensitive': False,
        'description': 'Redis cache TTL for analysis results (hours)',
        'validation_rules': {'type': 'integer', 'minimum': 1, 'maximum': 48}
    },

    # Advanced Settings
    {
        'key': 'enable_debug_logging',
        'value': 'false',
        'category': SettingCategory.ADVANCED,
        'is_sensitive': False,
        'is_editable': True,
        'description': 'Enable debug-level logging',
        'validation_rules': {'type': 'boolean'}
    },
]
```

**Definition of Done**:
- [ ] SQLAlchemy models created for ApplicationSetting and SettingHistory
- [ ] Alembic migration file created and tested
- [ ] Seed script populates default settings
- [ ] Encryption helper functions for sensitive values
- [ ] Unit tests for models (10+ tests)
- [ ] Integration tests with database (5+ tests)
- [ ] Test coverage ≥85%

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: None (builds on Epic 5 database infrastructure)
**Risk Level**: Medium (encryption complexity)

---

### Story F9.1-002: Settings Service Layer
**Status**: ✅ Complete (PR #49)
**User Story**: As FX, I want a robust settings service so that settings can be retrieved, validated, and updated safely

**Acceptance Criteria**:
- **Given** settings exist in the database
- **When** requesting a setting by key
- **Then** the value is decrypted if sensitive
- **And** returned in the correct data type (string/int/bool/object)
- **And** validation rules are enforced on updates
- **And** change history is recorded
- **And** cache is invalidated on updates

**Technical Requirements**:
- `SettingsService` class with CRUD operations
- Encryption/decryption for sensitive values (Fernet symmetric encryption)
- Type conversion utilities (string → int/bool/object)
- JSON schema validation for updates
- Audit trail recording
- Redis cache integration for read performance
- Bulk get/update operations

**Service Interface**:
```python
# settings_service.py
from typing import Any, Dict, List, Optional
from cryptography.fernet import Fernet
import json
from jsonschema import validate, ValidationError

class SettingsService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache
        self.cipher = Fernet(settings.ENCRYPTION_KEY)

    async def get_setting(self, key: str, decrypt: bool = True) -> Optional[Any]:
        """Get single setting by key, with optional decryption"""
        # Check cache first
        cached = await self.cache.get(f"setting:{key}")
        if cached:
            return self._parse_value(cached)

        # Query database
        setting = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = setting.scalar_one_or_none()

        if not setting:
            return None

        value = setting.value
        if setting.is_sensitive and decrypt and value:
            value = self._decrypt(value)

        # Cache for 5 minutes
        await self.cache.setex(f"setting:{key}", 300, value)
        return self._parse_value(value)

    async def get_settings_by_category(
        self,
        category: SettingCategory,
        decrypt: bool = True
    ) -> Dict[str, Any]:
        """Get all settings in a category"""
        result = await self.db.execute(
            select(ApplicationSetting).filter_by(category=category)
        )
        settings = result.scalars().all()

        return {
            s.key: self._decrypt(s.value) if (s.is_sensitive and decrypt) else s.value
            for s in settings
        }

    async def update_setting(
        self,
        key: str,
        value: Any,
        change_reason: Optional[str] = None
    ) -> ApplicationSetting:
        """Update setting with validation and audit trail"""
        setting = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = setting.scalar_one_or_none()

        if not setting:
            raise ValueError(f"Setting '{key}' not found")

        if not setting.is_editable:
            raise ValueError(f"Setting '{key}' is read-only")

        # Validate against rules
        if setting.validation_rules:
            try:
                validate(instance=value, schema=setting.validation_rules)
            except ValidationError as e:
                raise ValueError(f"Validation failed: {e.message}")

        # Record history
        old_value = setting.value
        history = SettingHistory(
            setting_id=setting.id,
            old_value=old_value,
            new_value=str(value),
            change_reason=change_reason
        )
        self.db.add(history)

        # Update setting
        if setting.is_sensitive:
            value = self._encrypt(str(value))

        setting.value = str(value)
        await self.db.commit()

        # Invalidate cache
        await self.cache.delete(f"setting:{key}")

        return setting

    async def bulk_update(
        self,
        updates: Dict[str, Any],
        change_reason: Optional[str] = None
    ) -> List[ApplicationSetting]:
        """Update multiple settings in one transaction"""
        updated = []
        for key, value in updates.items():
            setting = await self.update_setting(key, value, change_reason)
            updated.append(setting)
        return updated

    async def reset_to_default(self, key: str) -> ApplicationSetting:
        """Reset setting to its default value"""
        setting = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = setting.scalar_one_or_none()

        if not setting or not setting.default_value:
            raise ValueError(f"No default value for setting '{key}'")

        return await self.update_setting(
            key,
            setting.default_value,
            change_reason="Reset to default"
        )

    async def get_history(self, key: str, limit: int = 50) -> List[SettingHistory]:
        """Get change history for a setting"""
        setting = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = setting.scalar_one_or_none()

        if not setting:
            raise ValueError(f"Setting '{key}' not found")

        result = await self.db.execute(
            select(SettingHistory)
            .filter_by(setting_id=setting.id)
            .order_by(SettingHistory.changed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    def _encrypt(self, value: str) -> str:
        """Encrypt sensitive value"""
        return self.cipher.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt sensitive value"""
        return self.cipher.decrypt(value.encode()).decode()

    def _parse_value(self, value: str) -> Any:
        """Parse string value to correct type"""
        if value is None:
            return None

        # Try JSON parse for objects/arrays
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Try boolean
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            # Try number
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                # Return as string
                return value
```

**Definition of Done**:
- [ ] SettingsService class implemented
- [ ] Encryption/decryption working with Fernet
- [ ] Type conversion utilities tested
- [ ] JSON schema validation integrated
- [ ] Audit trail recording tested
- [ ] Redis cache integration working
- [ ] Unit tests for all methods (25+ tests)
- [ ] Test coverage ≥85%

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F9.1-001
**Risk Level**: Medium (encryption key management)

---

### Story F9.1-003: Settings REST API
**Status**: ✅ Complete (PR #49)
**User Story**: As FX, I want REST API endpoints for settings so that the frontend can manage configuration

**Acceptance Criteria**:
- **Given** the settings service is implemented
- **When** calling API endpoints
- **Then** I can get settings by key or category
- **And** I can update settings with validation
- **And** I can view setting history
- **And** I can reset settings to defaults
- **And** sensitive values are never exposed in responses without authentication

**Technical Requirements**:
- FastAPI router with 8 endpoints
- Pydantic schemas for request/response validation
- Error handling for validation failures
- Masked sensitive values in responses
- OpenAPI documentation

**API Endpoints**:
```python
# settings_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Pydantic schemas
class SettingResponse(BaseModel):
    key: str
    value: Any
    category: SettingCategory
    is_sensitive: bool
    is_editable: bool
    description: Optional[str]
    last_modified_at: datetime

class SettingUpdateRequest(BaseModel):
    value: Any
    change_reason: Optional[str] = None

class BulkUpdateRequest(BaseModel):
    updates: Dict[str, Any]
    change_reason: Optional[str] = None

class SettingHistoryResponse(BaseModel):
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime
    change_reason: Optional[str]

# Endpoints
@router.get("/categories")
async def list_categories() -> List[str]:
    """Get all setting categories"""
    return [c.value for c in SettingCategory]

@router.get("/category/{category}")
async def get_settings_by_category(
    category: SettingCategory,
    service: SettingsService = Depends(get_settings_service)
) -> Dict[str, SettingResponse]:
    """Get all settings in a category"""
    settings = await service.get_settings_by_category(category, decrypt=False)
    # Mask sensitive values
    for key, setting in settings.items():
        if setting.is_sensitive and setting.value:
            setting.value = "********"
    return settings

@router.get("/{key}")
async def get_setting(
    key: str,
    reveal: bool = False,  # Query param to reveal sensitive values
    service: SettingsService = Depends(get_settings_service)
) -> SettingResponse:
    """Get single setting by key"""
    setting = await service.get_setting(key, decrypt=reveal)
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    # Mask sensitive values unless explicitly revealed
    if setting.is_sensitive and not reveal and setting.value:
        setting.value = "********"

    return setting

@router.put("/{key}")
async def update_setting(
    key: str,
    request: SettingUpdateRequest,
    service: SettingsService = Depends(get_settings_service)
) -> SettingResponse:
    """Update setting value"""
    try:
        setting = await service.update_setting(
            key,
            request.value,
            request.change_reason
        )
        return setting
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk")
async def bulk_update_settings(
    request: BulkUpdateRequest,
    service: SettingsService = Depends(get_settings_service)
) -> List[SettingResponse]:
    """Update multiple settings"""
    try:
        settings = await service.bulk_update(
            request.updates,
            request.change_reason
        )
        return settings
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{key}/reset")
async def reset_setting(
    key: str,
    service: SettingsService = Depends(get_settings_service)
) -> SettingResponse:
    """Reset setting to default value"""
    try:
        setting = await service.reset_to_default(key)
        return setting
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{key}/history")
async def get_setting_history(
    key: str,
    limit: int = 50,
    service: SettingsService = Depends(get_settings_service)
) -> List[SettingHistoryResponse]:
    """Get change history for setting"""
    try:
        history = await service.get_history(key, limit)
        return history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{key}/validate")
async def validate_setting_value(
    key: str,
    value: Any,
    service: SettingsService = Depends(get_settings_service)
) -> Dict[str, bool]:
    """Validate a value without saving"""
    try:
        setting = await service.get_setting_metadata(key)
        if setting.validation_rules:
            validate(instance=value, schema=setting.validation_rules)
        return {"valid": True}
    except ValidationError as e:
        return {"valid": False, "error": e.message}
```

**Definition of Done**:
- [ ] FastAPI router with 8 endpoints
- [ ] Pydantic schemas for validation
- [ ] Error handling for all endpoints
- [ ] Sensitive value masking in responses
- [ ] OpenAPI docs generated
- [ ] Integration tests for all endpoints (30+ tests)
- [ ] Test coverage ≥85%

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F9.1-002
**Risk Level**: Low

---

## Feature 9.2: Settings UI Components
**Feature Description**: React components for settings management interface
**User Value**: User-friendly interface for viewing and editing settings
**Priority**: High
**Complexity**: 13 story points

### Story F9.2-001: Settings Sidebar Navigation
**Status**: ✅ Complete (PR #50)
**User Story**: As FX, I want a Settings option in the sidebar so that I can access configuration easily

**Acceptance Criteria**:
- **Given** the application is running
- **When** viewing the sidebar
- **Then** I see a "Settings" icon (⚙️ Settings) at the bottom
- **And** clicking it navigates to `/settings`
- **And** the Settings view loads with category tabs
- **And** the active state is highlighted

**Technical Requirements**:
- Update `Sidebar.tsx` with Settings icon
- Add route in React Router
- Settings icon uses lucide-react `Settings` component
- Position at bottom of sidebar (before any help/support links)

**Implementation**:
```tsx
// Sidebar.tsx addition
import { Settings } from 'lucide-react';

// In navigation items array
{
  label: 'Settings',
  icon: Settings,
  path: '/settings',
  position: 'bottom'  // Special positioning
}
```

**Definition of Done**:
- [ ] Settings icon added to Sidebar
- [ ] Route configured in App.tsx
- [ ] Navigation works on click
- [ ] Active state highlighted
- [ ] Unit tests for Sidebar (5+ tests)

**Story Points**: 2
**Priority**: Must Have
**Dependencies**: Epic 6 (Sidebar infrastructure)
**Risk Level**: Low

---

### Story F9.2-002: Settings Layout Component
**Status**: ✅ Complete
**User Story**: As FX, I want settings organized by category so that I can find what I need quickly

**Acceptance Criteria**:
- **Given** I navigate to Settings
- **When** the page loads
- **Then** I see category tabs (Display, API Keys, AI Settings, System, Advanced)
- **And** clicking a tab shows settings for that category
- **And** the layout is clean and professional
- **And** each setting has a label, description, and input control

**Technical Requirements**:
- `SettingsPage` component with tab navigation
- `SettingsCategoryTab` component for each category
- `SettingItem` component for individual settings
- Different input types: text, select, number, checkbox, password
- Responsive layout

**Component Structure**:
```tsx
// SettingsPage.tsx
import { useState, useEffect } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

export const SettingsPage: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<SettingCategory>('display');
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings(activeCategory);
  }, [activeCategory]);

  const loadSettings = async (category: SettingCategory) => {
    const response = await fetch(`/api/settings/category/${category}`);
    const data = await response.json();
    setSettings(data);
    setLoading(false);
  };

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <Tabs value={activeCategory} onValueChange={setActiveCategory}>
        <TabsList>
          <TabsTrigger value="display">Display</TabsTrigger>
          <TabsTrigger value="api_keys">API Keys</TabsTrigger>
          <TabsTrigger value="prompts">AI Settings</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value={activeCategory}>
          <SettingsCategoryPanel
            category={activeCategory}
            settings={settings}
            onUpdate={handleUpdate}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

// SettingItem.tsx
interface SettingItemProps {
  setting: Setting;
  onUpdate: (key: string, value: any) => void;
}

export const SettingItem: React.FC<SettingItemProps> = ({ setting, onUpdate }) => {
  const renderInput = () => {
    switch (setting.input_type) {
      case 'text':
        return <Input type="text" value={setting.value} onChange={...} />;
      case 'password':
        return <Input type="password" value={setting.value} onChange={...} />;
      case 'select':
        return <Select value={setting.value} onValueChange={...}>{...}</Select>;
      case 'number':
        return <Input type="number" value={setting.value} onChange={...} />;
      case 'checkbox':
        return <Checkbox checked={setting.value} onCheckedChange={...} />;
    }
  };

  return (
    <div className="setting-item">
      <div className="setting-header">
        <label>{setting.label}</label>
        {setting.is_sensitive && <Badge>Sensitive</Badge>}
      </div>
      <p className="setting-description">{setting.description}</p>
      {renderInput()}
      {setting.validation_error && (
        <p className="error">{setting.validation_error}</p>
      )}
      <div className="setting-actions">
        <Button size="sm" onClick={() => onUpdate(setting.key, setting.value)}>
          Save
        </Button>
        <Button size="sm" variant="ghost" onClick={() => resetToDefault(setting.key)}>
          Reset
        </Button>
      </div>
    </div>
  );
};
```

**Definition of Done**:
- [x] SettingsPage component implemented
- [x] Tab navigation working
- [x] SettingItem component for all input types
- [x] Responsive layout
- [x] Loading states
- [x] Unit tests (48 tests - exceeded 15+ requirement)

**Story Points**: 8
**Priority**: Must Have
**Dependencies**: F9.2-001, F9.1-003
**Risk Level**: Low

---

### Story F9.2-003: Settings Update & Validation
**Status**: 🔴 Not Started
**User Story**: As FX, I want real-time validation when changing settings so that I don't save invalid values

**Acceptance Criteria**:
- **Given** I'm editing a setting
- **When** I change the value
- **Then** validation runs in real-time
- **And** invalid values show error messages
- **And** valid values show success feedback
- **And** Save button is disabled for invalid values
- **And** changes are persisted on successful save
- **And** I see a success toast notification

**Technical Requirements**:
- Real-time validation using API endpoint
- Debounced validation calls (300ms)
- Error/success visual feedback
- Toast notifications for save operations
- Optimistic UI updates

**Implementation**:
```tsx
// useSettingValidation hook
import { useState, useEffect } from 'react';
import { debounce } from 'lodash';

export const useSettingValidation = (key: string, value: any) => {
  const [isValid, setIsValid] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    const validate = debounce(async () => {
      setValidating(true);
      try {
        const response = await fetch(`/api/settings/${key}/validate`, {
          method: 'POST',
          body: JSON.stringify({ value }),
        });
        const result = await response.json();
        setIsValid(result.valid);
        setError(result.error || null);
      } catch (err) {
        setIsValid(false);
        setError('Validation failed');
      } finally {
        setValidating(false);
      }
    }, 300);

    validate();
    return () => validate.cancel();
  }, [key, value]);

  return { isValid, error, validating };
};

// Updated SettingItem with validation
export const SettingItem: React.FC<SettingItemProps> = ({ setting, onUpdate }) => {
  const [value, setValue] = useState(setting.value);
  const { isValid, error, validating } = useSettingValidation(setting.key, value);

  const handleSave = async () => {
    try {
      await fetch(`/api/settings/${setting.key}`, {
        method: 'PUT',
        body: JSON.stringify({ value }),
      });
      toast.success('Setting saved successfully');
      onUpdate(setting.key, value);
    } catch (err) {
      toast.error('Failed to save setting');
    }
  };

  return (
    <div className="setting-item">
      {/* ... */}
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className={error ? 'error' : ''}
      />
      {validating && <Spinner size="sm" />}
      {error && <p className="error">{error}</p>}
      <Button
        onClick={handleSave}
        disabled={!isValid || validating}
      >
        Save
      </Button>
    </div>
  );
};
```

**Definition of Done**:
- [ ] Real-time validation implemented
- [ ] Debounced API calls
- [ ] Error/success feedback
- [ ] Toast notifications
- [ ] Optimistic updates
- [ ] Unit tests (10+ tests)

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F9.2-002, F9.1-003
**Risk Level**: Low

---

## Feature 9.3: API Key Management & Security
**Feature Description**: Secure handling of sensitive API keys
**User Value**: Safe credential storage without exposing secrets
**Priority**: High
**Complexity**: 8 story points

### Story F9.3-001: Encryption Key Management
**Status**: 🔴 Not Started
**User Story**: As FX, I want API keys encrypted so that they're not stored in plain text

**Acceptance Criteria**:
- **Given** I save an API key
- **When** it's stored in the database
- **Then** it's encrypted using Fernet symmetric encryption
- **And** the encryption key is stored securely in environment variables
- **And** keys are never logged or exposed in error messages
- **And** old keys can be rotated without data loss

**Technical Requirements**:
- Fernet encryption from `cryptography` library
- Encryption key in environment variable (`SETTINGS_ENCRYPTION_KEY`)
- Key rotation utility script
- Secure key generation script

**Implementation**:
```python
# security_utils.py
from cryptography.fernet import Fernet
import os
import base64

def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key"""
    return Fernet.generate_key().decode()

def get_cipher() -> Fernet:
    """Get Fernet cipher with key from environment"""
    key = os.getenv('SETTINGS_ENCRYPTION_KEY')
    if not key:
        raise ValueError("SETTINGS_ENCRYPTION_KEY not set in environment")
    return Fernet(key.encode())

def encrypt_value(value: str) -> str:
    """Encrypt a sensitive value"""
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(encrypted: str) -> str:
    """Decrypt a sensitive value"""
    cipher = get_cipher()
    return cipher.decrypt(encrypted.encode()).decode()

# Key rotation script
async def rotate_encryption_key(old_key: str, new_key: str):
    """Rotate encryption key for all sensitive settings"""
    old_cipher = Fernet(old_key.encode())
    new_cipher = Fernet(new_key.encode())

    # Get all sensitive settings
    settings = await db.execute(
        select(ApplicationSetting).filter_by(is_sensitive=True)
    )

    for setting in settings.scalars():
        if setting.value:
            # Decrypt with old key
            decrypted = old_cipher.decrypt(setting.value.encode()).decode()
            # Re-encrypt with new key
            setting.value = new_cipher.encrypt(decrypted.encode()).decode()

    await db.commit()
```

**Definition of Done**:
- [ ] Fernet encryption implemented
- [ ] Environment variable for key
- [ ] Key generation script
- [ ] Key rotation utility
- [ ] Never log sensitive values
- [ ] Unit tests (15+ tests)
- [ ] Documentation for key management

**Story Points**: 5
**Priority**: Must Have
**Dependencies**: F9.1-001
**Risk Level**: High (security-critical)

---

### Story F9.3-002: API Key Input Component
**Status**: 🔴 Not Started
**User Story**: As FX, I want a secure input for API keys so that they're never exposed on screen

**Acceptance Criteria**:
- **Given** I'm viewing an API key setting
- **When** the field loads
- **Then** the value is masked (********)
- **And** I can toggle visibility with an eye icon
- **And** I can test the key before saving
- **And** invalid keys show helpful error messages
- **And** I see when the key was last updated

**Technical Requirements**:
- Password-style input with toggle
- Test key functionality (API health check)
- Last updated timestamp
- Helpful validation messages

**Implementation**:
```tsx
// ApiKeyInput.tsx
import { useState } from 'react';
import { Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';

interface ApiKeyInputProps {
  label: string;
  value: string;
  onSave: (value: string) => Promise<void>;
  testEndpoint?: string;  // Optional test endpoint
}

export const ApiKeyInput: React.FC<ApiKeyInputProps> = ({
  label,
  value,
  onSave,
  testEndpoint
}) => {
  const [revealed, setRevealed] = useState(false);
  const [currentValue, setCurrentValue] = useState(value);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const handleTest = async () => {
    if (!testEndpoint) return;

    setTesting(true);
    try {
      const response = await fetch(testEndpoint, {
        headers: {
          'Authorization': `Bearer ${currentValue}`
        }
      });
      setTestResult(response.ok ? 'success' : 'error');
    } catch {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="api-key-input">
      <label>{label}</label>
      <div className="input-group">
        <input
          type={revealed ? 'text' : 'password'}
          value={currentValue}
          onChange={(e) => setCurrentValue(e.target.value)}
          placeholder="sk-ant-..."
        />
        <button onClick={() => setRevealed(!revealed)}>
          {revealed ? <EyeOff /> : <Eye />}
        </button>
      </div>

      {testEndpoint && (
        <button onClick={handleTest} disabled={testing}>
          {testing ? 'Testing...' : 'Test Key'}
        </button>
      )}

      {testResult === 'success' && (
        <div className="success">
          <CheckCircle /> Key is valid
        </div>
      )}
      {testResult === 'error' && (
        <div className="error">
          <XCircle /> Key is invalid or expired
        </div>
      )}

      <button onClick={() => onSave(currentValue)}>
        Save
      </button>
    </div>
  );
};
```

**Definition of Done**:
- [ ] ApiKeyInput component implemented
- [ ] Toggle visibility working
- [ ] Test key functionality
- [ ] Error/success feedback
- [ ] Last updated timestamp
- [ ] Unit tests (10+ tests)

**Story Points**: 3
**Priority**: Must Have
**Dependencies**: F9.2-002, F9.3-001
**Risk Level**: Medium

---

## Feature 9.4: Prompt Management Integration
**Feature Description**: Integrate with Epic 8 prompt management system
**User Value**: Edit AI prompts directly from Settings UI
**Priority**: Medium
**Complexity**: 8 story points

### Story F9.4-001: Prompts Settings Tab
**Status**: 🔴 Not Started
**User Story**: As FX, I want to view and edit AI prompts in Settings so that I can customize analysis output

**Acceptance Criteria**:
- **Given** I navigate to AI Settings tab
- **When** the page loads
- **Then** I see a list of all prompts
- **And** I can click to edit a prompt
- **And** I can create new prompts
- **And** I see prompt variables highlighted
- **And** I can test prompts before saving

**Technical Requirements**:
- Integrate with existing Prompt API (F8.1-002)
- Prompt editor component with syntax highlighting
- Variable placeholder hints
- Prompt testing interface

**Definition of Done**:
- [ ] Prompts tab implemented
- [ ] List all prompts
- [ ] Edit/create prompts
- [ ] Variable highlighting
- [ ] Test prompts
- [ ] Unit tests (8+ tests)

**Story Points**: 5
**Priority**: Should Have
**Dependencies**: F9.2-002, Epic 8 F8.1-002
**Risk Level**: Low

---

### Story F9.4-002: Prompt Version History
**Status**: 🔴 Not Started
**User Story**: As FX, I want to see prompt version history so that I can revert changes if needed

**Acceptance Criteria**:
- **Given** I'm viewing a prompt
- **When** I click "History"
- **Then** I see all previous versions
- **And** I can compare versions side-by-side
- **And** I can restore a previous version
- **And** I see who made changes and when

**Technical Requirements**:
- Use existing PromptVersion API (F8.1-001)
- Diff viewer for version comparison
- Restore functionality

**Definition of Done**:
- [ ] Version history viewer
- [ ] Diff comparison
- [ ] Restore functionality
- [ ] Unit tests (5+ tests)

**Story Points**: 3
**Priority**: Should Have
**Dependencies**: F9.4-001
**Risk Level**: Low

---

## Feature 9.5: Display & Preference Settings
**Feature Description**: User preferences for display and formatting
**User Value**: Customize how portfolio data is displayed
**Priority**: Medium
**Complexity**: 8 story points

### Story F9.5-001: Currency & Format Settings
**Status**: 🔴 Not Started
**User Story**: As FX, I want to change base currency and number formatting so that data displays in my preferred format

**Acceptance Criteria**:
- **Given** I'm in Display settings
- **When** I change base currency
- **Then** portfolio values recalculate
- **And** all pages update with new currency
- **And** I can select date format (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)
- **And** I can select number format (en-US, de-DE, fr-FR, en-GB)
- **And** changes apply immediately without page refresh

**Technical Requirements**:
- Currency change triggers portfolio recalculation
- React Context for settings propagation
- Immediate UI updates

**Definition of Done**:
- [ ] Currency selector
- [ ] Date format selector
- [ ] Number format selector
- [ ] Real-time updates
- [ ] Portfolio recalculation
- [ ] Unit tests (8+ tests)

**Story Points**: 5
**Priority**: Should Have
**Dependencies**: F9.2-002
**Risk Level**: Medium (currency conversion complexity)

---

### Story F9.5-002: System Performance Settings
**Status**: 🔴 Not Started
**User Story**: As FX, I want to adjust refresh intervals so that I can balance freshness with API costs

**Acceptance Criteria**:
- **Given** I'm in System settings
- **When** I change refresh intervals
- **Then** price updates respect new intervals
- **And** I can set separate intervals for crypto (30-600s) and stocks (60-600s)
- **And** I can set cache TTL (1-48 hours)
- **And** changes apply immediately

**Technical Requirements**:
- Update refresh timers dynamically
- Validate interval ranges
- Clear/update Redis cache on TTL change

**Definition of Done**:
- [ ] Refresh interval controls
- [ ] Cache TTL control
- [ ] Dynamic timer updates
- [ ] Range validation
- [ ] Unit tests (6+ tests)

**Story Points**: 3
**Priority**: Should Have
**Dependencies**: F9.2-002
**Risk Level**: Low

---

## Dependencies
- **External**: cryptography (Fernet), jsonschema
- **Internal**: Epic 5 (Database), Epic 6 (Sidebar), Epic 8 (Prompts)
- **Libraries**: React Hook Form, Zod (optional for client-side validation)

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|---------|------------|
| Encryption key loss | Cannot decrypt API keys | Document key backup procedure, consider key recovery |
| Settings apply without restart | Requires hot-reload support | Implement settings observer pattern |
| Invalid settings break app | Application unusable | Always validate, keep defaults, rollback on error |
| Sensitive data leaked in logs | Security breach | Never log sensitive values, mask in error messages |

## Testing Strategy

**⚠️ MANDATORY TESTING REQUIREMENT**:
- **Minimum Coverage Threshold**: 85% code coverage for all modules
- **No story is complete without passing tests meeting this threshold**

1. **Unit Tests**: Service methods, encryption, validation (50+ tests)
2. **Integration Tests**: API endpoints, database operations (30+ tests)
3. **E2E Tests**: Full settings workflow from UI to database (10+ tests)
4. **Security Tests**: Encryption, key rotation, sensitive data handling (15+ tests)
5. **Performance Tests**: Settings load time <100ms, update time <200ms

## Performance Requirements
- Settings load: <100ms
- Setting update: <200ms
- Encryption/decryption: <10ms per operation
- Cache hit rate: >90% for frequently accessed settings
- Real-time validation: <500ms (including debounce)

## Definition of Done for Epic
- [ ] All 12 stories complete and tested
- [ ] Database schema created with seed data
- [ ] Settings API with 8+ endpoints
- [ ] Settings UI with 5 category tabs
- [ ] Encryption working for sensitive values
- [ ] Prompt management integrated
- [ ] Display preferences working
- [ ] System settings adjustable
- [ ] Unit test coverage ≥85% (mandatory threshold)
- [ ] Integration tests passing (30+ tests)
- [ ] Security audit passed
- [ ] Documentation for settings management
- [ ] Works on Mac, Linux, and Windows

## Security Considerations
- **Encryption at Rest**: All sensitive settings encrypted in database
- **Encryption in Transit**: HTTPS only (handled by reverse proxy in production)
- **Key Management**: Encryption key in environment variable, never committed
- **Access Control**: Settings API requires authentication (future: role-based access)
- **Audit Trail**: All changes logged in setting_history table
- **Sensitive Value Masking**: API keys never exposed in responses unless explicitly revealed
- **No Logging**: Sensitive values never logged, even in debug mode

## Future Enhancements (Post-Epic)
- User profiles with per-user settings
- Settings import/export (JSON)
- Settings templates (preset configurations)
- Settings search/filter
- Advanced validation rules (cross-field validation)
- Settings backup/restore
- Multi-tenant support (separate settings per user)
- Settings change notifications
- Dark mode preference
- Language localization settings

---

**Epic Status**: 🔴 Not Started (0%)
**Total Story Points**: 50
**Estimated Effort**: 10-15 development days
**Priority**: Medium (nice-to-have for MVP, essential for production)
**Blocking Dependencies**: Epic 5 (Database infrastructure)
**Target Milestone**: Post-MVP, before production deployment
