"""Trade balance summaries shared by charts and the README tables."""

import pandas as pd

MILLION = 1_000


def yearly_balance(df: pd.DataFrame, regions: dict[str, str]) -> pd.DataFrame:
    """Yearly balance per region, in million USD and as % of total trade.
    The rate makes a single city and the whole country comparable."""
    rows = []
    for name in regions:
        yearly = (
            df[df["지역명"].eq(name)]
            .groupby("기간")[["수출금액", "수입금액", "무역수지"]]
            .sum()
        )
        rows.append(
            pd.DataFrame(
                {
                    "지역": name,
                    "무역수지_백만불": yearly["무역수지"] / MILLION,
                    "교역액대비_수지율": yearly["무역수지"]
                    / (yearly["수출금액"] + yearly["수입금액"])
                    * 100,
                }
            )
        )
    return pd.concat(rows).reset_index(names="연도")


def longest_surplus_start(balance: pd.Series) -> int:
    """First year of the longest run of surplus years. Finding the turning
    point from data keeps the period table right if the data are updated."""
    surplus = balance.gt(0)
    run_id = surplus.ne(surplus.shift()).cumsum()
    runs = balance[surplus].groupby(run_id[surplus]).apply(lambda s: s.index)
    return int(max(runs, key=len).min())


def describe(balance: pd.Series) -> str:
    deficit = balance[balance.lt(0)].index.tolist()
    surplus = balance[balance.gt(0)].index.tolist()
    if not deficit:
        return "매년 흑자"
    if not surplus:
        return "매년 적자"
    if len(deficit) <= len(surplus):
        return f"{', '.join(map(str, deficit))}년 적자"
    small = ", ".join(f"{y}년 {balance[y]:+,.0f}백만 USD" for y in surplus)
    return f"적자 (흑자: {small})"


def period_table(yearly: pd.DataFrame, focus: str) -> pd.DataFrame:
    """Split the years at the focus region's longest surplus run and describe
    every region in each period."""
    wide = yearly.pivot(index="연도", columns="지역", values="무역수지_백만불")
    split = longest_surplus_start(wide[focus])
    first, last = wide.index.min(), wide.index.max()
    periods = {
        f"{first}~{split - 1}": wide.loc[: split - 1],
        f"{split}~{last}": wide.loc[split:],
    }
    return pd.DataFrame(
        {
            "구간": list(periods),
            **{
                region: [describe(p[region]) for p in periods.values()]
                for region in wide.columns
            },
        }
    )
