from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Signal(Enum):
    OVERBOUGHT = "OVERBOUGHT"
    OVERSOLD = "OVERSOLD"
    CAUTION = "CAUTION"
    NEUTRAL = "NEUTRAL"
    HOT = "HOT"
    COLD = "COLD"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    FLAT = "FLAT"
    RED_LIGHT = "RED LIGHT"
    GREEN_LIGHT = "GREEN LIGHT"
    STRONG_BULL = "STRONG BULL"
    WEAK_BEAR = "WEAK / BEAR"
    HEALTHY = "HEALTHY"
    EUPHORIA = "EUPHORIA"
    FEAR = "FEAR"
    CAUTIOUS_BULL = "CAUTIOUS BULL"
    DIVERGENCE = "DIVERGENCE"
    BUYING = "BUYING"
    SELLING = "SELLING"


@dataclass
class BreadthIndicator:
    name: str
    value: float | str
    signal: Signal
    action: str
    description: str = ""


@dataclass
class MarketBreadth:
    pct_above_sma20: float
    pct_above_sma50: float
    pct_above_sma200: float
    new_highs_lows: int
    high_low_ratio: float
    volume_breadth_ratio: float
    fear_greed_score: float
    vix: float = 0.0
    vix_3m: float = 0.0
    vix_6m: float = 0.0
    mcclellan_osc: float = 0.0
    spy_atr_pct: float = 0.0
    ad_data: dict[str, dict] = field(default_factory=dict)
    indicators: list[BreadthIndicator] = field(default_factory=list)


@dataclass
class SectorData:
    name: str
    etf: str
    price: float
    sma20: float
    pct_vs_sma20: float
    signal: Signal
    perf_day: float = 0.0
    perf_1w: float = 0.0
    perf_2w: float = 0.0
    perf_3w: float = 0.0


@dataclass
class SeasonalityRow:
    period: int
    label: str
    avg_return: float
    win_rate: float
    std_dev: float
    min_return: float
    max_return: float


@dataclass
class SeasonalityResult:
    ticker: str
    monthly: list[SeasonalityRow] = field(default_factory=list)
    weekly: list[SeasonalityRow] = field(default_factory=list)
    current_month: str = ""
    signal: Signal = Signal.FLAT
