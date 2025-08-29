import pytest
from battery_health.multi_aging_exp.data_import import timestamp_to_seconds
import pandas as pd
import numpy as np


def test_now_fixed():
    """This test is now fixed after seeing the failure"""
    # Fixed the expected value based on the test failure output
    timestamps = pd.Series(['00:01:30.500'])
    result = timestamp_to_seconds(timestamps)
    # Corrected expected value: 1 minute 30.5 seconds = 90.5 seconds
    expected = np.array([90.5])
    np.testing.assert_array_almost_equal(result, expected)


def test_edge_case_empty_series():
    """Test with empty pandas series"""
    timestamps = pd.Series([])
    result = timestamp_to_seconds(timestamps)
    expected = np.array([])
    np.testing.assert_array_equal(result, expected)
