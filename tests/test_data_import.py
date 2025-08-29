import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from battery_health.multi_aging_exp.data_import import (
    import_datafile,
    timestamp_to_seconds,
    find_files,
    SensorDataNotFound
)


class TestDataImport:
    """Test suite for data_import module"""

    def test_timestamp_to_seconds_valid_format(self):
        """Test timestamp conversion with valid format"""
        timestamps = pd.Series(['00:01:30.500', '00:02:45.250', '01:00:00.000'])
        result = timestamp_to_seconds(timestamps)
        expected = np.array([90.5, 165.25, 3600.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_timestamp_to_seconds_invalid_format(self):
        """Test timestamp conversion with invalid format"""
        timestamps = pd.Series(['invalid', 'format', 'data'])
        result = timestamp_to_seconds(timestamps)
        assert result is None

    def test_import_datafile_valid_csv(self):
        """Test importing a valid CSV file"""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('run_time,voltage,current\n')
            f.write('00:01:30.500,3.7,1.2\n')
            f.write('00:02:45.250,3.6,1.1\n')
            temp_file = Path(f.name)
        
        try:
            df = import_datafile(temp_file)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert 'run_time' in df.columns
            assert 'voltage' in df.columns
            assert 'current' in df.columns
            # Check that timestamp was converted to seconds
            assert df.run_time.iloc[0] == 90.5
            assert df.run_time.iloc[1] == 165.25
        finally:
            os.unlink(temp_file)

    def test_import_datafile_empty_csv(self):
        """Test importing an empty CSV file raises SensorDataNotFound"""
        # Create a temporary empty CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('run_time,voltage,current\n')  # Header only
            temp_file = Path(f.name)
        
        try:
            with pytest.raises(SensorDataNotFound):
                import_datafile(temp_file)
        finally:
            os.unlink(temp_file)

    def test_import_datafile_numeric_runtime(self):
        """Test importing CSV with numeric run_time (no conversion needed)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('run_time,voltage,current\n')
            f.write('90.5,3.7,1.2\n')
            f.write('165.25,3.6,1.1\n')
            temp_file = Path(f.name)
        
        try:
            df = import_datafile(temp_file)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            # Should remain as numeric values
            assert df.run_time.iloc[0] == 90.5
            assert df.run_time.iloc[1] == 165.25
        finally:
            os.unlink(temp_file)

    def test_find_files_structure(self):
        """Test find_files function with mock directory structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            study_dir = Path(temp_dir)
            stage_dir = study_dir / "Stage_1"
            stage_dir.mkdir()
            
            # Create some test files
            test_files = [
                "data_aging01_01_test.csv",
                "data_aging01_01_another.csv",
                "data_aging02_01_test.csv"
            ]
            
            for filename in test_files:
                (stage_dir / filename).touch()
            
            # Test finding files
            files = find_files(study_dir, stage=1, aging_type="aging", tp=1, cell=1)
            assert len(files) == 2  # Should find 2 files matching pattern
            assert all(f.suffix == '.csv' for f in files)
            assert all('aging01_01' in f.name for f in files)


def test_simple_addition():
    """Simple test to verify pytest is working"""
    assert 1 + 1 == 2


def test_numpy_array():
    """Simple test with numpy to verify dependencies"""
    arr = np.array([1, 2, 3])
    assert len(arr) == 3
    assert arr.sum() == 6


def test_pandas_dataframe():
    """Simple test with pandas to verify dependencies"""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    assert len(df) == 3
    assert list(df.columns) == ['a', 'b']
