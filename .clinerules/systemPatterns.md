# System Patterns — battery-health-analytics

## Architecture Overview

### Core Design Philosophy
**Functional Core, Imperative Shell**
- Pure functions for all analytics logic (features, models, metrics)
- Imperative shell handles I/O, plotting, and side effects
- Clear separation between data processing and presentation

### Module Structure
```
src/bha/
├── features.py      # Pure feature extraction functions
├── models.py        # Degradation model implementations
├── metrics.py       # Evaluation and diagnostic functions
├── simulate.py      # Synthetic data generators
└── pipeline.py      # Orchestration and I/O handling
```

## Key Design Patterns

### 1. Data Flow Pipeline
```python
# Functional composition pattern
raw_data -> extract_features -> fit_model -> evaluate -> visualize
```

**Principles:**
- Each stage is a pure function (given same input, same output)
- No hidden state or side effects in core logic
- Easy to test, debug, and reason about

### 2. Physics-Constrained Models
```python
class SoHModel:
    def predict(self, features: Features) -> SoHPrediction:
        raw_prediction = self._raw_predict(features)
        return self._apply_physics_constraints(raw_prediction)
    
    def _apply_physics_constraints(self, prediction):
        # Enforce SoH ∈ [0,1] and monotonic decrease
        return isotonic_regression(np.clip(prediction, 0, 1))
```

**Key Constraints:**
- SoH bounded in [0, 1]
- Monotonic non-increasing (with small tolerance ε)
- Temperature/DoD effects follow Arrhenius-like scaling

### 3. Leakage Prevention Guards
```python
def time_split_validation(data: BatteryData, test_ratio: float = 0.2):
    """Strict time-based splits to prevent data leakage."""
    cutoff_time = data.time.quantile(1 - test_ratio)
    train = data[data.time <= cutoff_time]
    test = data[data.time > cutoff_time]
    
    # Guard: ensure no test data in training
    assert train.time.max() < test.time.min()
    return train, test
```

**Leakage Sources to Avoid:**
- Using future cycle data for "online" estimation
- Mixing test units into training data
- Features derived from full-cycle information when claiming partial-cycle capability

### 4. Statistical Validation Framework
```python
def validate_model_residuals(residuals: np.ndarray) -> ValidationReport:
    """Comprehensive residual analysis."""
    return ValidationReport(
        ljung_box_pvalue=ljung_box_test(residuals),
        normality_pvalue=shapiro_test(residuals),
        autocorr_coeffs=autocorrelation(residuals),
        heteroscedasticity_pvalue=breusch_pagan_test(residuals)
    )
```

**Statistical Requirements:**
- Residuals should be white noise (Ljung-Box p > 0.05)
- No correlation between residuals and inputs
- Homoscedastic errors (constant variance)

## Component Relationships

### Data Processing Chain
```
BatteryData -> FeatureExtractor -> ModelFitter -> Predictor -> Validator
     ↓              ↓                 ↓            ↓           ↓
  Pydantic      CC-CV slices    Physics-aware   SoH + CI   Diagnostics
  validation    + statistics     regression               + metrics
```

### Feature Extraction Pattern
```python
@dataclass
class CCCVFeatures:
    """Features extracted from CC-CV charge slice."""
    voltage_mean: float
    voltage_std: float
    current_mean: float
    charge_time: float
    accumulated_charge: float
    # ... more features
    
def extract_cccv_features(charge_slice: pd.DataFrame) -> CCCVFeatures:
    """Pure function: slice -> features."""
    return CCCVFeatures(
        voltage_mean=charge_slice.voltage.mean(),
        voltage_std=charge_slice.voltage.std(),
        # ... compute all features
    )
```

### Model Interface Pattern
```python
class DegradationModel(ABC):
    """Abstract base for all degradation models."""
    
    @abstractmethod
    def fit(self, features: Features, soh: np.ndarray) -> ModelParams:
        """Fit model parameters to training data."""
        pass
    
    @abstractmethod
    def predict(self, features: Features) -> SoHPrediction:
        """Predict SoH with uncertainty bounds."""
        pass
    
    @abstractmethod
    def equation(self) -> str:
        """Return model equation for documentation."""
        pass
```

## Critical Implementation Paths

### 1. Online SoH Estimation
```python
def estimate_soh_online(
    partial_charge_data: pd.DataFrame,
    model: DegradationModel,
    cycle_number: int
) -> SoHEstimate:
    """Estimate SoH from partial charge data only."""
    
    # Extract features from CC-CV slice (before full charge)
    features = extract_cccv_features(partial_charge_data)
    
    # Predict using fitted model
    prediction = model.predict(features)
    
    # Apply monotonicity constraint based on previous estimates
    constrained_soh = apply_monotonic_constraint(
        prediction.value, 
        previous_soh_history
    )
    
    return SoHEstimate(
        value=constrained_soh,
        confidence_interval=prediction.ci,
        cycle=cycle_number,
        features_used=features
    )
```

### 2. Counterfactual Analysis
```python
def simulate_usage_impact(
    base_model: DegradationModel,
    usage_scenarios: List[UsagePattern],
    time_horizon: int
) -> CounterfactualResults:
    """Compare degradation under different usage patterns."""
    
    results = {}
    for scenario in usage_scenarios:
        # Generate synthetic feature trajectory
        feature_trajectory = generate_feature_sequence(
            scenario, time_horizon
        )
        
        # Predict SoH evolution
        soh_trajectory = [
            base_model.predict(features).value 
            for features in feature_trajectory
        ]
        
        results[scenario.name] = soh_trajectory
    
    return CounterfactualResults(results)
```

### 3. Model Benchmarking Pipeline
```python
def benchmark_models(
    models: List[DegradationModel],
    datasets: List[BatteryDataset],
    cv_folds: int = 5
) -> BenchmarkResults:
    """Compare models across datasets with proper validation."""
    
    results = []
    for dataset in datasets:
        for model in models:
            # Time-based cross-validation
            cv_scores = time_series_cv(model, dataset, cv_folds)
            
            # Statistical validation
            residuals = compute_residuals(model, dataset)
            validation = validate_model_residuals(residuals)
            
            results.append(ModelResult(
                model_name=model.__class__.__name__,
                dataset_name=dataset.name,
                mae=cv_scores.mae,
                mape=cv_scores.mape,
                rmse=cv_scores.rmse,
                ljung_box_pvalue=validation.ljung_box_pvalue,
                # ... other metrics
            ))
    
    return BenchmarkResults(results)
```

## Error Handling Patterns

### Graceful Degradation
```python
def extract_features_safe(data: pd.DataFrame) -> Optional[Features]:
    """Feature extraction with graceful error handling."""
    try:
        return extract_cccv_features(data)
    except InsufficientDataError:
        logger.warning("Not enough data for feature extraction")
        return None
    except DataQualityError as e:
        logger.error(f"Data quality issue: {e}")
        return None
```

### Input Validation
```python
def validate_battery_data(data: pd.DataFrame) -> BatteryData:
    """Pydantic-based data validation."""
    required_columns = ['time', 'voltage', 'current', 'cycle']
    
    if not all(col in data.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {required_columns}")
    
    return BatteryData.parse_obj(data.to_dict('records'))
```

## Performance Considerations

### Computational Efficiency
- **Vectorized operations**: Use numpy/pandas for all numerical computations
- **Lazy evaluation**: Only compute features when needed
- **Caching**: Cache expensive computations (feature extraction, model fitting)

### Memory Management
- **Streaming processing**: Process large datasets in chunks
- **Feature selection**: Only extract relevant features for each model
- **Data cleanup**: Clear intermediate results after processing

## Testing Patterns

### Property-Based Testing
```python
@given(st.floats(min_value=0, max_value=1))
def test_soh_bounds(soh_value):
    """SoH should always be bounded in [0,1]."""
    model = PowerLawModel()
    features = generate_random_features()
    prediction = model.predict(features)
    assert 0 <= prediction.value <= 1
```

### Golden Dataset Testing
```python
def test_golden_dataset_performance():
    """Regression test on fixed dataset slice."""
    model = PowerLawModel()
    golden_data = load_golden_dataset("mit_sample_001")
    
    mae = evaluate_model(model, golden_data)
    assert mae <= 0.02, f"Performance regression: MAE={mae}"
```

### Synthetic Recovery Testing
```python
def test_parameter_recovery():
    """Model should recover known parameters from synthetic data."""
    true_params = {"a": 0.1, "b": 0.05}
    synthetic_data = generate_synthetic_degradation(true_params)
    
    model = PowerLawModel()
    fitted_params = model.fit(synthetic_data)
    
    assert abs(fitted_params.a - true_params["a"]) < 0.01
    assert abs(fitted_params.b - true_params["b"]) < 0.01
