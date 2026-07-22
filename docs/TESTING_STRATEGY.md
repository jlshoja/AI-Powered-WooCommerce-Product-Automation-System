# Testing Strategy

## Test Pyramid

```
        E2E (0)          ← Not implemented yet
       /      \
   Integration (0)       ← Not implemented yet
      /          \
   Unit (46)      Unit (46)     ← Current: 46 unit tests
```

## Current Coverage

| Module | Tests | Status |
|--------|-------|--------|
| AI Client/Manager | 7 | ✅ |
| Automation (BatchImporter, Scheduler, Tracker) | 5 | ✅ |
| Excel Parser (Reader) | 5 | ✅ |
| Image Manager | 7 | ✅ |
| Validator | 11 | ✅ |
| WooCommerce Client | 9 | ✅ |
| **Total** | **46** | ✅ |

## Test Conventions

### Naming
- Files: `test_<module>.py`
- Functions: `test_<feature>_<scenario>`
- Fixtures: lowercase, descriptive

### Fixtures
```python
# conftest.py or module-level
@pytest.fixture
def client():
    return WooCommerceClient(...)

@pytest.fixture
def product():
    return Product(...)  # minimal valid product
```

### Mocking
- Mock external APIs (WC, OpenAI, HTTP)
- Use `unittest.mock.patch` on the client method
- Don't mock internal logic

## Test Categories

### Unit Tests (Current)
- Isolated, fast, no external dependencies
- Mock all I/O: WC API, OpenAI, file system, HTTP
- Run on every commit

### Integration Tests (Planned)
- Real WC test instance (Docker)
- Real OpenAI (or mock server (or cached responses)
- Real Excel files
- Run nightly

### E2E Tests (Planned)
- Full pipeline: Excel → Import → WC
- Verify products in WC admin
- Run on release candidates

## Test Data

### Fixtures
- Use factory functions for test products
- Minimal valid data only
- Parametrize for edge cases

```python
def make_product(sku="TEST001", **overrides):
    base = { "id": "1", "post_title": "Test", "sku": sku, ... }
    return Product(**{**base, **overrides})
```

### Excel Test Files
- `output/Product_Master.xlsx` - current test file
- Future: Generate temp Excel in `tmp_path` fixture

## Running Tests

```bash
# All
pytest

# Module
pytest tests/test_ai/

# Keyword
pytest -k "seo"

# Coverage
pytest --cov=src --cov-report=term-missing

# CI mode (strict)
pytest -x --strict-markers --strict-config
```

## CI Pipeline (Planned)

```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: mypy src/
      - run: pytest --cov=src --cov-fail-under=80
```

## Gaps & Roadmap

| Gap | Priority | Plan |
|-----|----------|------|
| No integration tests | High | Docker WC + test script |
| No E2E tests | Medium | Playwright or manual script |
| No property-based testing | Low | Hypothesis for validator |
| No performance tests | Low | Locust for batch import |
| No mutation testing | Low | mutmut |

## Quality Gates

| Metric | Target |
|--------|--------|
| Unit test pass | 100% |
| Coverage (unit) | ≥80% |
| Ruff | 0 errors |
| Mypy | 0 errors |
| No secrets in code | Verified |