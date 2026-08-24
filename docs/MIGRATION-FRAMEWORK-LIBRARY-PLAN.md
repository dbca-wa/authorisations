# JSON Schema Migration Framework - Library Extraction Plan

## Executive Summary

The schema migration framework currently integrated into the `questionnaires` module can be extracted as a reusable Django plugin (`django-json-schema-migrations` or similar) to support any Django app with versioned JSON document fields.

**Estimated effort**:
- Phase 1: Abstraction layer design — 4 hours
- Phase 2: Core library extraction — 6 hours
- Phase 3: Plugin integration & packaging — 4 hours
- Phase 4: Testing & documentation — 6 hours
- **Total: ~20 hours**

**Current state**: Framework is fully functional but tightly coupled to questionnaires. Can be generalized through abstraction.

---

## Current Implementation Analysis

### What's Generic (Reusable)

1. **Migration Discovery & Loading** (`schema_migrations_loader.py`)
   - File glob scanning for migration files
   - Dynamic module import via `importlib`
   - Pattern matching for migration numbers
   - Status: ✅ Zero dependencies on questionnaires

2. **Path Finding Algorithm** (`schema_migrations_loader.py`)
   - `find_path(from_version, to_version) -> list[str]`
   - Determines transformation sequence
   - Handles forward/backward migrations
   - Status: ✅ Zero dependencies on questionnaires

3. **Validation Framework** (`schema_migration_utils.py`)
   - `validate_transform(doc, from_version, to_version, from_schema, to_schema)`
   - JSON Schema validation against frozen schemas
   - Error collection and reporting
   - Status: ✅ Zero dependencies on questionnaires (uses `jsonschema` library)

4. **Management Command Patterns**
   - Argument parsing (migration number)
   - Idempotency checks
   - Dry-run support
   - Transaction management
   - Status: ⚠️ Command names hardcoded, needs parameterization

5. **Database Version Detection**
   - `get_db_schema_version()` queries database for schema_version
   - Handles mixed-version detection
   - Status: ⚠️ Hardcoded field/model, needs parameterization

### What's App-Specific (Needs Abstraction)

1. **Model Integration**
   - References `Questionnaire` model directly
   - Assumes `document` JSONField
   - Queries `Questionnaire.objects.filter()`
   - **Solution**: Make model pluggable via configuration class

2. **Serializer Validation**
   - `QuestionnaireSerialiser.validate_document()` checks schema_version
   - Tightly coupled to DRF serializer
   - **Solution**: Provide mixin or decorator for automatic integration

3. **Schema Provider**
   - `get_questionnaire_schema()` returns current schema
   - Schema version hardcoded in schema module
   - **Solution**: Make schema provider an abstract interface

4. **Command Names**
   - `schema_migrate_questionnaire` (hardcoded)
   - `schema_rollback_questionnaire` (hardcoded)
   - `schema_status_questionnaire` (hardcoded)
   - **Solution**: Allow command names via app label configuration

5. **Migration Directory**
   - Hardcoded to `questionnaires/schema_migrations/`
   - **Solution**: Configurable via app config

---

## Architecture for Library Extraction

### 1. Core Package Structure

```
django_json_schema_migrations/
├── __init__.py
├── apps.py                          # AppConfig with pluggable settings
├── core/
│   ├── __init__.py
│   ├── loader.py                    # Migration discovery & loading
│   ├── validator.py                 # Transform validation
│   └── versioning.py                # Version detection & handling
├── commands/
│   ├── __init__.py
│   ├── base.py                      # Base command classes (generic)
│   └── management/
│       └── commands/
│           ├── migrate_documents.py          # Generic template
│           ├── rollback_documents.py         # Generic template
│           └── status_documents.py           # Generic template
├── serializers/
│   ├── __init__.py
│   └── mixins.py                    # DRF serializer mixin
├── config.py                        # Configuration & registry
├── exceptions.py                    # Custom exceptions
└── tests/
    ├── __init__.py
    ├── test_loader.py
    ├── test_validator.py
    └── test_commands.py
```

### 2. Configuration Registry Pattern

**File**: `django_json_schema_migrations/config.py`

```python
"""Configuration registry for JSON schema migrations."""

from typing import Callable, Type
from django.db.models import Model
from rest_framework.serializers import Serializer


class MigrationConfig:
    """Configuration for a model with versioned JSON documents."""
    
    def __init__(
        self,
        model: Type[Model],
        document_field: str = "document",
        version_field: str = "schema_version",
        migrations_package: str = None,
        schema_provider: Callable = None,
        serializer_class: Type[Serializer] = None,
    ):
        """
        Args:
            model: Django model with JSON document field (e.g., Questionnaire)
            document_field: Name of JSON document field on model
            version_field: Name of version field within document (usually "schema_version")
            migrations_package: Python path to migrations dir (e.g., "myapp.schema_migrations")
            schema_provider: Callable that returns current schema dict
            serializer_class: DRF serializer class for the model
        """
        self.model = model
        self.document_field = document_field
        self.version_field = version_field
        self.migrations_package = migrations_package
        self.schema_provider = schema_provider
        self.serializer_class = serializer_class


# Global registry mapping model labels to configs
_REGISTRY: dict[str, MigrationConfig] = {}


def register(config: MigrationConfig) -> None:
    """Register a model for schema migrations."""
    app_label = config.model._meta.app_label
    model_name = config.model._meta.model_name
    key = f"{app_label}.{model_name}"
    _REGISTRY[key] = config


def get_config(model: Type[Model]) -> MigrationConfig:
    """Get configuration for a model."""
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    key = f"{app_label}.{model_name}"
    
    if key not in _REGISTRY:
        raise ValueError(
            f"Model {key} not registered for schema migrations. "
            f"Call django_json_schema_migrations.config.register() in your app config."
        )
    
    return _REGISTRY[key]
```

### 3. Core Loader (Minimal Changes)

**File**: `django_json_schema_migrations/core/loader.py`

```python
"""Migration discovery and loading (generic, zero questionnaire coupling)."""

import importlib.util
import sys
from pathlib import Path


def get_migration(migrations_package: str, migration_number: str):
    """Load migration module by number.
    
    Args:
        migrations_package: Python import path (e.g., "myapp.schema_migrations")
        migration_number: Version number (e.g., "0001")
    
    Returns:
        Loaded module with SCHEMA_VERSION, previous_schema(), etc.
    """
    # Convert package path to file path
    parts = migrations_package.split('.')
    module = __import__(migrations_package)
    for part in parts[1:]:
        module = getattr(module, part)
    
    migrations_dir = Path(module.__file__).parent
    matching_files = list(migrations_dir.glob(f"{migration_number}_*.py"))
    
    if not matching_files:
        raise FileNotFoundError(
            f"Migration {migration_number} not found in {migrations_dir}"
        )
    
    migration_file = matching_files[0]
    spec = importlib.util.spec_from_file_location(
        f"{migrations_package}.{migration_number}",
        migration_file,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load migration {migration_number}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    
    return module


def list_migrations(migrations_package: str) -> list[str]:
    """Discover all available migrations in a package."""
    # Same pattern as above but returns all found numbers
    pass


def find_path(migrations_package: str, from_version: str, to_version: str) -> list[str]:
    """Find transformation path between versions."""
    # Same algorithm, now parameterized on migrations_package
    pass
```

### 4. Generic Serializer Mixin

**File**: `django_json_schema_migrations/serializers/mixins.py`

```python
"""DRF serializer mixin for automatic schema version validation."""

from rest_framework import serializers
from ..config import get_config
from ..core.validator import validate_transform


class SchemaMigrationValidatorMixin(serializers.Serializer):
    """Mixin to add schema version validation to any DRF serializer.
    
    Usage:
        class MyModelSerialiser(SchemaMigrationValidatorMixin, serializers.ModelSerializer):
            class Meta:
                model = MyModel
                fields = ['document', ...]
    
    The mixin:
    1. Calls the config's schema_provider to get current schema
    2. Validates document.schema_version matches current version
    3. Provides actionable error messages
    """
    
    def validate_document(self, value):
        """Validate document schema_version and structure."""
        config = get_config(self.Meta.model)
        current_schema = config.schema_provider()
        expected_version = current_schema["properties"][config.version_field]["default"]
        
        doc_version = value.get(config.version_field) if isinstance(value, dict) else None
        
        if doc_version != expected_version:
            raise serializers.ValidationError(
                f"Document schema version must be '{expected_version}', but got '{doc_version}'. "
                f"Run migration command to migrate."
            )
        
        # Validate structure
        try:
            from jsonschema import validate
            validate(value, current_schema)
        except Exception as e:
            raise serializers.ValidationError(f"Schema validation failed: {e}")
        
        return value
```

### 5. Generic Command Base Classes

**File**: `django_json_schema_migrations/commands/base.py`

```python
"""Base classes for schema migration commands."""

from django.core.management.base import BaseCommand, CommandError
from typing import Type
from django.db.models import Model, Count, F
from django.db import transaction

from ..config import get_config
from ..core.loader import get_migration, list_migrations, find_path


class SchemaMigrationCommandBase(BaseCommand):
    """Base class for schema migration commands."""
    
    model: Type[Model] = None  # Subclass sets this
    
    def get_config(self):
        """Get configuration for the model."""
        if not self.model:
            raise NotImplementedError("Subclass must set 'model' attribute")
        return get_config(self.model)
    
    def get_db_version(self, config) -> str | None:
        """Query database for most common schema_version."""
        versions = (
            self.model.objects
            .annotate(
                version=F(f"{config.document_field}__{config.version_field}"),
            )
            .values('version')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        if not versions:
            return None
        
        return versions[0]['version']


class MigrateCommandBase(SchemaMigrationCommandBase):
    """Base for migrate forward command."""
    
    def add_arguments(self, parser):
        parser.add_argument('migration_number', type=str)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, migration_number, dry_run=False, **options):
        """Migrate all documents to target migration."""
        config = self.get_config()
        current_version = self.get_db_version(config)
        
        migration = get_migration(config.migrations_package, migration_number)
        target_version = migration.SCHEMA_VERSION
        
        # Idempotency check
        if current_version == target_version:
            self.stdout.write(self.style.SUCCESS(
                f"Already at version {target_version}. No migration needed."
            ))
            return
        
        # Validate preconditions
        # ... (transformation logic)
        
        self.stdout.write(self.style.SUCCESS("Migration complete!"))


class RollbackCommandBase(SchemaMigrationCommandBase):
    """Base for rollback command."""
    # Similar pattern
    pass


class StatusCommandBase(SchemaMigrationCommandBase):
    """Base for status command."""
    # Similar pattern
    pass
```

### 6. Usage in Target App

**File**: `myapp/apps.py` (in user's project)

```python
from django.apps import AppConfig
from django_json_schema_migrations.config import MigrationConfig, register
from .models import MyDocument
from .schema import get_schema


class MyAppConfig(AppConfig):
    name = 'myapp'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        # Register this model for schema migrations
        register(MigrationConfig(
            model=MyDocument,
            document_field="content",
            version_field="schema_version",
            migrations_package="myapp.schema_migrations",
            schema_provider=get_schema,
        ))
```

**File**: `myapp/management/commands/migrate_documents.py`

```python
from django_json_schema_migrations.commands.base import MigrateCommandBase
from myapp.models import MyDocument


class Command(MigrateCommandBase):
    help = "Migrate MyDocument records to target schema version"
    model = MyDocument
```

---

## Phase-by-Phase Extraction Plan

### Phase 1: Abstraction Layer Design (4 hours)

**Deliverables**:
- `django_json_schema_migrations/config.py` — Configuration registry
- `django_json_schema_migrations/exceptions.py` — Custom exceptions
- Design document for mixin/inheritance patterns

**Tasks**:
1. Design configuration class with all pluggable points
2. Create registry mechanism
3. Design exception hierarchy
4. Document abstraction assumptions

**Exit criteria**:
- ✅ Configuration class can represent any model + schema
- ✅ All pluggable hooks clearly defined
- ✅ Mixin patterns designed
- ✅ Zero breaking changes to current questionnaires implementation

---

### Phase 2: Core Library Extraction (6 hours)

**Deliverables**:
- Extracted `core/loader.py`, `core/validator.py` (parameterized)
- Base command classes in `commands/base.py`
- Serializer mixin in `serializers/mixins.py`
- Full library structure with `__init__.py`, `apps.py`

**Tasks**:
1. Copy and adapt loader (add migrations_package parameter)
2. Copy and adapt validator (zero changes needed)
3. Create base command classes (inherit from questionnaires commands)
4. Create serializer mixin (wrap validate logic)
5. Create `AppConfig` with autodiscover of registered models
6. Write `__init__.py` exports

**Exit criteria**:
- ✅ Core library functions without questionnaires coupling
- ✅ All questionnaires-specific logic moved to base classes (inheritance)
- ✅ Configuration registry works
- ✅ 100% of current functionality preserved

---

### Phase 3: Plugin Integration & Packaging (4 hours)

**Deliverables**:
- `setup.py` / `pyproject.toml` configuration
- `MANIFEST.in` for package distribution
- `README.md` with quick start guide
- Integration tests showing usage in example app
- GitHub repo structure (README, LICENSE, CHANGELOG)

**Tasks**:
1. Create `setup.py` with dependencies (Django, jsonschema, etc.)
2. Add project metadata (version, author, license)
3. Create integration test app demonstrating usage
4. Write quick start guide
5. Set up GitHub actions for testing
6. Document release process

**Exit criteria**:
- ✅ Package installable via `pip install django-json-schema-migrations`
- ✅ Example app shows how to register and use
- ✅ All dependencies clearly listed
- ✅ Tests pass in CI/CD

---

### Phase 4: Testing & Documentation (6 hours)

**Deliverables**:
- Unit test suite for library (separate from questionnaires tests)
- Integration test suite
- Comprehensive documentation
- Migration guide for existing users

**Tasks**:
1. Extract questionnaires tests into library unit tests
2. Create integration test app with dummy models
3. Write user documentation:
   - Installation guide
   - Configuration guide
   - Writing migrations guide
   - API reference
   - FAQ
4. Write migration guide for questionnaires (how to upgrade)
5. Create architecture diagram

**Exit criteria**:
- ✅ 100+ test cases covering all public APIs
- ✅ Documentation complete and clear
- ✅ Example project included
- ✅ Release notes prepared

---

## Backward Compatibility Strategy

### For Current Questionnaires Implementation

**Approach**: Dual-mode support during transition

1. **Phase 1**: Extract library, questionnaires continues using local code
2. **Phase 2**: Create adapter layer in questionnaires that uses library
3. **Phase 3**: Deprecation period (2 releases) with warnings
4. **Phase 4**: Remove local code, fully migrate to library

**Code structure during Phase 2**:
```python
# questionnaires/schema_migrations_loader.py
# Adapter that wraps library calls with questionnaires defaults

from django_json_schema_migrations.core.loader import get_migration as lib_get_migration

def get_migration(migration_number: str):
    """Backward-compatible wrapper."""
    return lib_get_migration("questionnaires.schema_migrations", migration_number)

# All other functions similarly wrap library
```

**No breaking changes**:
- Command names unchanged
- API signatures unchanged
- Test imports unchanged (until Phase 4)

---

## Dependencies for Library

### Core Dependencies
- Django >= 5.0 (tested)
- jsonschema >= 4.0 (for JSON Schema validation)
- Python >= 3.11

### Optional Dependencies
- djangorestframework >= 3.14 (for serializer mixin)
- django-jsonform (for admin integration)

### Development Dependencies
- pytest >= 7.0
- pytest-django >= 4.0
- black, flake8, isort (code quality)

---

## Key Design Decisions

### 1. Configuration Registry vs Django App Registry
**Decision**: Custom registry tied to app config

**Rationale**:
- Migration discovery is app-specific, not Django-wide
- Each model can have different settings (field names, schema provider)
- Simpler than Django app registry for this use case

### 2. Mixin vs Decorator vs Callable
**Decision**: Provide mixin + manual hookpoint

**Rationale**:
- Mixin is standard DRF pattern (easy for Django developers)
- Manual hookpoint for advanced use cases (non-DRF)
- Flexibility without complexity

### 3. Command Names Parameterization
**Decision**: Command names set via class name in subclass

**Rationale**:
- Django convention: command name = module name
- Base classes are templates, not executable
- Each app provides concrete commands
- Simpler than configuration file

### 4. Library vs Django App
**Decision**: Full Django app (AppConfig, etc.)

**Rationale**:
- Can have `management/commands/` directory
- Can have models (for future audit trail)
- Follows Django conventions
- Easier installation (`INSTALLED_APPS`)

---

## Migration Path Examples

### Example 1: Questionnaires (Current)

**Before** (current):
```python
# questionnaires/apps.py - no setup needed
# Commands named: schema_migrate_questionnaire, etc.

# questionnaires/schema_migrations_loader.py
def get_migration(migration_number: str):
    # Load from questionnaires.schema_migrations
```

**After** (with library):
```python
# questionnaires/apps.py
from django_json_schema_migrations.config import register

class QuestionnaireConfig(AppConfig):
    def ready(self):
        register(MigrationConfig(model=Questionnaire, ...))

# questionnaires/management/commands/schema_migrate_questionnaire.py
class Command(MigrateCommandBase):
    model = Questionnaire
```

### Example 2: New App (Simple)

```python
# myapp/apps.py
class MyappConfig(AppConfig):
    def ready(self):
        from django_json_schema_migrations.config import register
        from .models import MyModel
        from .schema import get_schema
        
        register(MigrationConfig(
            model=MyModel,
            schema_provider=get_schema,
        ))

# myapp/management/commands/migrate_mymodel.py
from django_json_schema_migrations.commands.base import MigrateCommandBase
from myapp.models import MyModel

class Command(MigrateCommandBase):
    model = MyModel
```

---

## Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Extraction misses edge cases | Medium | High | Comprehensive test suite; parallel testing phase |
| Breaking changes in library | Low | High | Semantic versioning; deprecation period; change log |
| Adoption friction (too complex) | Medium | Medium | Excellent docs; example apps; quick start |
| Django version incompatibility | Low | Medium | Regular testing; version matrix in CI/CD |
| Performance regression | Low | Medium | Benchmarking; profiling tests |

**Mitigation strategy**:
- Keep questionnaires using library in parallel (alpha testing)
- Collect feedback from real usage before v1.0
- Semantic versioning (0.x.y during beta)
- Long deprecation period (6+ months)

---

## Success Criteria

✅ **Phase 1**: Configuration design complete and documented
✅ **Phase 2**: Library functions identically to current implementation (all 109 tests pass)
✅ **Phase 3**: Package installable and distributable via PyPI
✅ **Phase 4**: Comprehensive documentation with example apps
✅ **Overall**: 
- Zero breaking changes to questionnaires
- Other Django projects can use library independently
- Library has 100+ test cases
- Documentation exceeds Django conventions

---

## Future Enhancements (Post-v1.0)

1. **Admin integration**: Automatic admin command discovery
2. **Audit trail**: Optional table tracking all migrations
3. **Batch operations**: Scheduled migrations (run during off-hours)
4. **Schema diffing**: Show what changed between versions
5. **Rollback analytics**: Track failed rollbacks and reasons
6. **Multi-tenant support**: Isolate migrations by tenant
7. **Schema visualization**: GraphQL API for schema browser
8. **CI/CD integration**: Pre-deployment migration validation

---

## Conclusion

The schema migration framework is well-designed and thoroughly tested. Extraction as a library requires:
- **Abstraction of 3 coupling points** (model, schema provider, serializer)
- **Parameterization of 2 components** (loader, database queries)
- **Template inheritance for commands**

The architecture supports extraction cleanly with zero breaking changes. Estimated effort: **~20 hours**. Backward compatibility can be maintained for an indefinite period via adapter layer.
