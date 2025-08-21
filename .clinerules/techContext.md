# Tech Context — battery-health-analytics

## Technology Stack

### Core Analytics (Python)
- **numpy**: Numerical computations, array operations
- **pandas**: Data manipulation, time series handling
- **scipy**: Statistical functions, optimization, signal processing
- **statsmodels**: Statistical tests (Ljung-Box), time series analysis
- **scikit-learn**: Regression models, preprocessing, validation

### Optional ML Extensions
- **jax**: For future PINN implementations (physics-informed neural networks)
- **pytorch**: Alternative for neural network models if needed
- **Note**: Heavy ML frameworks only added when justified by specific use cases

### Web Dashboard
- **SvelteKit**: Primary choice for frontend framework
  - Lightweight, fast, excellent developer experience
  - Built-in routing, SSR capabilities
  - Alternative: Next.js if React ecosystem preferred
- **Vega-Lite**: Declarative visualization grammar
  - Grammar of graphics approach (preferred over imperative plotting)
  - JSON-based chart specifications
  - Alternative: Observable Plot
- **FastAPI**: Minimal backend (only if needed)
  - Type-safe API endpoints
  - Automatic OpenAPI documentation
  - Used sparingly - prefer client-side processing when possible

### Data Validation & Contracts
- **pydantic**: Data models, validation, serialization
  - Type-safe data structures
  - Automatic validation of battery data schemas
  - Clear error messages for data quality issues

### Testing Framework
- **pytest**: Primary testing framework
  - Fixtures for test data setup
  - Parametrized tests for multiple datasets
  - Coverage reporting
- **hypothesis**: Property-based testing
  - Generate random test cases
  - Test invariants and edge cases
  - Particularly useful for numerical stability

### Code Quality Tools
- **ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **black**: Code formatter for consistent style
- **mypy**: Static type checking
- **pre-commit**: Git hooks for automated quality checks

### Development Environment
- **pyproject.toml**: Modern Python packaging
- **GitHub Actions**: CI/CD pipeline
  - Unit tests on every push
  - Slow/golden dataset tests nightly
  - Automated linting and formatting checks

## Development Setup

### Project Structure
```
battery-health-analytics/
├── pyproject.toml           # Dependencies, build config
├── README.md               # Project documentation
├── LICENSE.txt             # Open source license
├── .gitignore             # Git ignore patterns
├── .clinerules/           # Cline memory bank
├── src/
│   └── bha/               # Main package (battery health analytics)
│       ├── __init__.py
│       ├── features.py    # Feature extraction
│       ├── models.py      # Degradation models
│       ├── metrics.py     # Evaluation metrics
│       ├── simulate.py    # Synthetic data generation
│       └── pipeline.py    # Orchestration
├── tests/
│   ├── test_features.py   # Feature extraction tests
│   ├── test_leakage.py    # Data leakage prevention
│   ├── test_system_id.py  # Parameter recovery tests
│   ├── test_monotonicity.py # Physics constraint tests
│   └── test_golden.py     # Regression tests
├── data/
│   └── golden/            # Small reference datasets
├── notebooks/
│   └── 01_benchmarks.ipynb # Analysis and figures
└── dashboard/             # Web application
    ├── package.json
    ├── src/
    └── static/
```

### Package Management
- **pip**: Standard Python package installer
- **pip-tools**: For dependency pinning and management
- **Virtual environments**: Isolated development environments

### Current Package Structure
**Note**: Existing code uses `battery_health` package name in `src/battery_health/`
- May need to refactor to `bha` for consistency with project brief
- Current modules: `multi_aging_exp/` with `feature_extraction.py` and `data_import.py`

## Dependencies

### Core Requirements
```toml
[project]
dependencies = [
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scipy>=1.10.0",
    "statsmodels>=0.14.0",
    "scikit-learn>=1.3.0",
    "pydantic>=2.0.0",
]
```

### Development Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "hypothesis>=6.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
    "pre-commit>=3.0.0",
]
```

### Dashboard Dependencies
```json
{
  "dependencies": {
    "@sveltejs/kit": "^1.0.0",
    "vega-lite": "^5.0.0",
    "vega-embed": "^6.0.0"
  }
}
```

## Technical Constraints

### Performance Requirements
- **Feature extraction**: < 1 second per battery cycle
- **Model fitting**: < 30 seconds for typical dataset
- **Dashboard loading**: < 2 seconds for initial view
- **Memory usage**: Handle datasets up to 1GB in memory

### Compatibility
- **Python**: 3.9+ (for modern type hints)
- **Node.js**: 18+ (for SvelteKit)
- **Browsers**: Modern browsers with ES2020 support

### Data Formats
- **Input**: CSV, HDF5, or Parquet files
- **Schema**: Standardized battery cycling data format
- **Output**: JSON for API responses, PNG/SVG for plots

## Development Workflows

### Local Development
```bash
# Setup
make setup          # Install dependencies, setup pre-commit
make test           # Run test suite
make lint           # Run linting and formatting
make demo           # Start dashboard locally

# Development cycle
make test-watch     # Continuous testing during development
make format         # Format code
make type-check     # Run mypy
```

### Testing Strategy
- **Unit tests**: Fast, isolated, no external dependencies
- **Integration tests**: Test component interactions
- **Property-based tests**: Use hypothesis for edge cases
- **Golden dataset tests**: Regression tests on fixed data
- **Performance tests**: Ensure speed requirements met

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -e .[dev]
      - run: pytest
      - run: ruff check
      - run: black --check .
      - run: mypy src/
```

## Data Management

### Dataset Handling
- **Small datasets**: Include directly in repo (`data/golden/`)
- **Large datasets**: Use DVC or download scripts
- **Data validation**: Pydantic schemas for all inputs
- **Caching**: Cache processed features to avoid recomputation

### File Organization
```
data/
├── golden/                 # Small reference datasets (< 10MB)
│   ├── mit_sample_001.csv
│   └── hust_sample_001.csv
├── cache/                  # Processed features cache
└── downloads/              # Large datasets (gitignored)
```

## Visualization Architecture

### Chart Specifications
- **Vega-Lite JSON**: Declarative chart definitions
- **Reusable templates**: Common chart patterns as functions
- **Interactive features**: Brushing, linking, filtering

### Dashboard Architecture
```
dashboard/
├── src/
│   ├── lib/
│   │   ├── charts/         # Vega-Lite chart components
│   │   ├── data/           # Data loading utilities
│   │   └── stores/         # Svelte stores for state
│   ├── routes/
│   │   ├── +page.svelte    # Main dashboard
│   │   └── api/            # API endpoints (if needed)
│   └── app.html
└── static/                 # Static assets
```

## Security Considerations

### Data Privacy
- No sensitive battery data in public repos
- Anonymized datasets only
- Clear data usage policies

### Code Security
- Dependency scanning with GitHub Dependabot
- No hardcoded secrets or API keys
- Input validation for all user data

## Performance Optimization

### Computational Efficiency
- **Vectorization**: Use numpy operations over Python loops
- **Lazy loading**: Load data only when needed
- **Caching**: Cache expensive computations
- **Profiling**: Regular performance monitoring

### Memory Management
- **Chunked processing**: Handle large datasets in batches
- **Memory profiling**: Monitor memory usage patterns
- **Garbage collection**: Explicit cleanup of large objects

## Future Technical Considerations

### Scalability
- **Distributed computing**: Dask for larger datasets
- **Cloud deployment**: Docker containers for reproducible environments
- **API scaling**: FastAPI with async support

### Advanced Features
- **Real-time processing**: Streaming data pipelines
- **Model serving**: MLOps pipeline for model deployment
- **Advanced visualization**: 3D plots, animation for time series
