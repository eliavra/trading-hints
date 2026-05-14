import pytest
import pandas as pd
import numpy as np
from data import _compute_fear_greed, _perf_at_offset, SECTORS
from models import Signal

def test_compute_fear_greed():
    # Test extreme high (Greed)
    # The _compute_fear_greed function handles raw percentages and counts.
    # SMA20=85, SMA50=85, SMA200=80, NHNL=50, VOL=1.5 -> Score should be 100
    score_high = _compute_fear_greed(85, 85, 80, 50, 1.5)
    assert score_high == 100.0
    
    # Test extreme low (Fear)
    score_low = _compute_fear_greed(20, 30, 40, -50, 0.5)
    assert score_low == 0.0
    
    # Test neutral
    score_neutral = _compute_fear_greed(52.5, 57.5, 60, 0, 1.0)
    assert score_neutral == 50.0

def test_compute_perf_at_offset():
    s = pd.Series([100, 110, 121]) # 10% increases
    # _perf_at_offset(close, offset)
    assert round(_perf_at_offset(s, 1), 4) == 0.1000
    assert round(_perf_at_offset(s, 2), 4) == 0.2100
    assert _perf_at_offset(s, 5) == 0.0 # Not enough data

if __name__ == "__main__":
    pytest.main([__file__])
