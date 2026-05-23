def test_models_import() -> None:
    """Basic import sanity check."""
    from backend.app.models import ETF, OHLC, Position, StrategyParam, Trade
    from backend.app.models.etf import ETFCategory
    from backend.app.models.position import PositionStatus, TrendRegime
    from backend.app.models.trade import OrderStatus, TradeAction

    assert ETF.__tablename__ == "etf"
    assert OHLC.__tablename__ == "ohlc"
    assert Position.__tablename__ == "position"
    assert StrategyParam.__tablename__ == "strategy_params"
    assert Trade.__tablename__ == "trade"

    assert len(ETFCategory) == 4
    assert len(PositionStatus) == 2
    assert len(TrendRegime) == 3
    assert len(TradeAction) == 4
    assert len(OrderStatus) == 3


def test_settings() -> None:
    from backend.app.config import settings

    assert settings.postgres_user == "etf_compass"
    assert settings.redis_port == 6379
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.database_url_sync.startswith("postgresql://")
