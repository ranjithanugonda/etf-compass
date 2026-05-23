"""Seed the database with the 21 approved ETFs and default strategy params."""

from backend.app.db import async_session
from backend.app.models.etf import ETF, ETFCategory
from backend.app.models.strategy_params import StrategyParam

ETFS_RAW: list[dict[str, object]] = [
    {"s": "METALIETF", "n": "Nifty Metal ETF", "c": ETFCategory.COMMODITIES,
     "a": "Nippon", "e": "Metal & mining stocks", "b": 1.36, "atr": 13.0},
    {"s": "OILETF", "n": "Nifty Oil & Gas ETF", "c": ETFCategory.COMMODITIES,
     "a": "Nippon", "e": "Oil & energy sector", "b": 1.09, "atr": 6.0},
    {"s": "GOLDIETF", "n": "Gold ETF", "c": ETFCategory.COMMODITIES,
     "a": "Nippon", "e": "Physical gold", "b": -0.06, "atr": 13.0},
    {"s": "SILVERIETF", "n": "Silver ETF", "c": ETFCategory.COMMODITIES,
     "a": "ICICI Pru", "e": "Physical silver", "b": 0.2, "atr": 23.0},
    # Sectoral
    {"s": "FMCGIETF", "n": "Nifty FMCG ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "FMCG sector", "b": 0.6, "atr": 6.0},
    {"s": "PHARMABEES", "n": "Nifty Pharma ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "Pharmaceutical sector", "b": 0.78, "atr": 10.0},
    {"s": "CPSEETF", "n": "CPSE ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "PSU companies", "b": 1.16, "atr": 8.0},
    {"s": "MODEFENSE", "n": "Nifty India Defence ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "Defence & aerospace", "b": 1.2, "atr": 9.0},
    {"s": "MOREALTY", "n": "Nifty Realty ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "Real estate sector", "b": 1.56, "atr": 7.0},
    {"s": "ITBEES", "n": "Nifty IT ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "IT services", "b": 1.17, "atr": 10.0},
    {"s": "AUTOBEES", "n": "Nifty Auto ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "Automobile sector", "b": 1.18, "atr": 6.0},
    {"s": "PSUBNKBEES", "n": "Nifty PSU Bank ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "PSU banking stocks", "b": 1.16, "atr": 9.0},
    {"s": "BANKBEES", "n": "Nifty Bank ETF", "c": ETFCategory.SECTORAL,
     "a": "Nippon", "e": "Banking sector", "b": 0.94, "atr": 4.0},
    # Indian Market Index
    {"s": "MIDCAETF", "n": "Nifty Midcap 150 ETF", "c": ETFCategory.INDIAN_INDEX,
     "a": "ICICI Pru", "e": "Indian mid-cap stocks", "b": 1.17, "atr": 7.0},
    {"s": "HDFCSML250", "n": "Nifty Smallcap 250 ETF", "c": ETFCategory.INDIAN_INDEX,
     "a": "HDFC MF", "e": "Indian small-cap stocks", "b": 1.18, "atr": 5.0},
    {"s": "JUNIORBEES", "n": "Nifty Next 50 ETF", "c": ETFCategory.INDIAN_INDEX,
     "a": "Nippon", "e": "Emerging large caps", "b": 1.17, "atr": 5.0},
    {"s": "SENEXIETF", "n": "Sensex ETF", "c": ETFCategory.INDIAN_INDEX,
     "a": "ICICI Pru", "e": "BSE Sensex", "b": 0.98, "atr": 4.0},
    {"s": "NIFTYIETF", "n": "Nifty 50 ETF", "c": ETFCategory.INDIAN_INDEX,
     "a": "ICICI Pru", "e": "Nifty 50", "b": 1.0, "atr": 5.0},
    # International Market Index
    {"s": "HNGSNGBEES", "n": "Hang Seng ETF", "c": ETFCategory.INTERNATIONAL,
     "a": "Nippon", "e": "Hong Kong equities", "b": 0.61, "atr": 7.0},
    {"s": "MAFANG", "n": "NYSE FANG+ ETF", "c": ETFCategory.INTERNATIONAL,
     "a": "Motilal Oswal", "e": "US technology leaders", "b": 0.64, "atr": 3.0},
    {"s": "MON100", "n": "Nasdaq 100 ETF", "c": ETFCategory.INTERNATIONAL,
     "a": "Motilal Oswal", "e": "US Nasdaq 100", "b": 0.9, "atr": 7.0},
]

APPROVED_ETFS: list[dict[str, object]] = [
    {
        "symbol": e["s"], "name": e["n"], "category": e["c"],
        "amc": e["a"], "underlying_exposure": e["e"],
        "beta": e["b"], "atr": e["atr"],
    }
    for e in ETFS_RAW
]

# Shorter keys for strategy params to avoid line-length issues
STRATEGY_SEEDS = [
    ("total_corpus", 15_000_000, "Total capital corpus (INR)"),
    ("initial_tranche", 300_000, "First tranche size (INR, 2% of corpus)"),
    ("second_tranche", 200_000, "Second tranche size (INR, 1.33% of corpus)"),
    ("third_tranche", 150_000, "Third tranche size (INR, 1% of corpus)"),
    ("addon_tranche", 100_000, "Fourth+ add-on tranche size (INR, 0.66%)"),
    ("max_position_size", 1_250_000, "Max position per ETF (INR, 8.33% of corpus)"),
    ("max_tranches", 9, "Max tranches per position"),
    ("profit_target_pct", 5.0, "Profit target exit % over WAC"),
    ("time_stop_months", 4, "Time exit months from entry"),
    ("addon_threshold_pct", 2.5, "Price decline % for add-on trigger"),
    ("addon_duration_days", 7, "Add-on window (days)"),
    ("pullback_weekly_pct", 2.5, "Weekly pullback threshold %"),
    ("pullback_weekly_days", 5, "Weekly pullback lookback days"),
    ("pullback_monthly_pct", 5.0, "Monthly pullback threshold %"),
    ("pullback_monthly_days", 21, "Monthly pullback lookback days"),
]

DEFAULT_STRATEGY_PARAMS: list[dict[str, object]] = [
    {"param_name": name, "param_value": value, "description": desc}
    for name, value, desc in STRATEGY_SEEDS
]


async def seed_etfs() -> None:
    async with async_session() as session:
        for etf_data in APPROVED_ETFS:
            existing = await session.get(ETF, etf_data["symbol"])
            if existing is None:
                session.add(ETF(**etf_data))
        await session.commit()
        print(f"Seeded {len(APPROVED_ETFS)} ETFs.")


async def seed_strategy_params() -> None:
    async with async_session() as session:
        from sqlalchemy import select
        for param_data in DEFAULT_STRATEGY_PARAMS:
            result = await session.execute(
                select(StrategyParam).where(StrategyParam.param_name == param_data["param_name"])
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                session.add(StrategyParam(**param_data))
        await session.commit()
        print(f"Seeded {len(DEFAULT_STRATEGY_PARAMS)} strategy params.")


async def main() -> None:
    await seed_etfs()
    await seed_strategy_params()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
