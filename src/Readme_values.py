"""
====================================================================
* Purpose: recompute every number quoted in README 핵심 결과 3~9 in one run,
  so the README can be checked against data without opening each chart.
  Results 1 and 2 are produced by KITA_monthly_4 and TD_2.
* Data: data/processed/tradedata_2000_2025_4_added.csv (관세청)
        data/processed/kita_regional_{yearly,monthly}_4_added.csv (K-stat)
        data/processed/customs_sido_trade_daejeon.csv (관세청 시도별 API)
* Output: console, grouped by README section
====================================================================
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

DJ = "대전광역시"
NATION = "전국"
CHUNGNAM = "충청남도(세종특별자치시 포함)"
CHUNGBUK = "충청북도"
RANK_YEARS = 10
MIN_LOCAL_SHARE = 1.0


def header(title: str) -> None:
    print(f"\n---{title}---")


def section_shares(td: pd.DataFrame, region: str) -> pd.DataFrame:
    """Yearly section shares from summed amounts, averaged so each year counts equally."""
    yearly = (
        td[td["지역명"].eq(region)]
        .groupby(["기간", "부명약칭"])[["수출금액", "수입금액"]]
        .sum()
    )
    return (
        (yearly / yearly.groupby(level=0).transform("sum") * 100)
        .groupby(level=1)
        .mean()
    )


def result_3(recent: pd.DataFrame) -> None:
    header("3. Section shares (10-year average, %)")
    regions = {"대전": DJ, "전국": NATION, "충남": CHUNGNAM, "충북": CHUNGBUK}
    shares = {name: section_shares(recent, region) for name, region in regions.items()}
    sections = [
        "기계 및 전기기기",
        "조제식품류",
        "광학, 정밀, 의료기기",
        "광물성 생산품",
    ]
    for col in ("수출금액", "수입금액"):
        table = pd.DataFrame({name: s[col] for name, s in shares.items()}).reindex(
            sections
        )
        print(f"\n{col}\n{table.round(1).to_string()}")


def result_4(recent: pd.DataFrame) -> None:
    header("4. Chapters far above Daejeon's national share")
    dj = (
        recent[recent["지역명"].eq(DJ)]
        .groupby("류명약칭")[["수출금액", "수입금액"]]
        .sum()
    )
    nt = (
        recent[recent["지역명"].eq(NATION)]
        .groupby("류명약칭")[["수출금액", "수입금액"]]
        .sum()
    )
    for col in ("수출금액", "수입금액"):
        print(
            f"Daejeon share of national {col}: {dj[col].sum() / nt[col].sum() * 100:.2f}%"
        )
    profile = pd.DataFrame(
        {
            "대전_수출중": dj["수출금액"] / dj["수출금액"].sum() * 100,
            "전국대비_수출": dj["수출금액"] / nt["수출금액"] * 100,
            "대전_수입중": dj["수입금액"] / dj["수입금액"].sum() * 100,
            "전국대비_수입": dj["수입금액"] / nt["수입금액"] * 100,
        }
    )
    # Only chapters that matter inside Daejeon; a high national share on a
    # negligible chapter is not a finding.
    big = profile[
        profile["대전_수출중"].ge(MIN_LOCAL_SHARE)
        | profile["대전_수입중"].ge(MIN_LOCAL_SHARE)
    ]
    top = (
        big["전국대비_수출"]
        .nlargest(5)
        .index.union(big["전국대비_수입"].nlargest(5).index)
    )
    print(
        profile.loc[top]
        .sort_values("전국대비_수출", ascending=False)
        .round(1)
        .to_string()
    )


def result_5(td: pd.DataFrame) -> None:
    header("5. Transport exports and aircraft share")
    t = td[td["지역명"].eq(DJ) & td["부명약칭"].eq("수송기기")]
    by_chapter = t.pivot_table(
        index="기간", columns="류명약칭", values="수출금액", aggfunc="sum"
    )
    out = pd.DataFrame(
        {
            "수송기기_수출_백만": by_chapter.sum(axis=1) / 1_000,
            "항공기_비중%": by_chapter["항공기"] / by_chapter.sum(axis=1) * 100,
            "항공기_신고건수": t[t["류명약칭"].eq("항공기")]
            .groupby("기간")["수출건수"]
            .sum(),
        }
    )
    print(out.loc[out.index.max() - RANK_YEARS + 1 :].round(0).to_string())


def result_6(last_full_year: int) -> None:
    header("6. Declarations and value per declaration (API)")
    api = pd.read_csv(DATA_DIR / "customs_sido_trade_daejeon.csv").set_index("연도")
    # The API also returns the current partial year, which would understate everything.
    api = api.loc[:last_full_year]
    first, last = api.index.min(), api.index.max()
    for flow, prefix in (("수출", "exp"), ("수입", "imp")):
        count, value = api[f"{prefix}Cnt"], api[f"{prefix}UsdAmt"]
        per = value * 1_000 / count
        print(
            f"{flow}: count {count[first]:,} -> {count[last]:,} ({(count[last] / count[first] - 1) * 100:+.1f}%), "
            f"value {(value[last] / value[first] - 1) * 100:+.1f}%, "
            f"per declaration {per[first]:,.0f} -> {per[last]:,.0f} USD ({(per[last] / per[first] - 1) * 100:+.1f}%)"
        )


def result_7(recent: pd.DataFrame) -> None:
    header("7. Optical/precision/medical share of imports (%)")
    dj, nt = section_shares(recent, DJ), section_shares(recent, NATION)
    sec = "광학, 정밀, 의료기기"
    print(
        f"Daejeon {dj.loc[sec, '수입금액']:.1f}, national {nt.loc[sec, '수입금액']:.1f}"
    )


def result_8() -> None:
    header("8. Export weight and unit value (K-stat)")
    yearly = pd.read_csv(DATA_DIR / "kita_regional_yearly_4_added.csv")
    yearly = yearly[yearly["연도"].le(2025)]
    last = yearly["연도"].max()
    before, after = [int(last) - 7, int(last) - 6], [
        int(last) - 2,
        int(last) - 1,
        int(last),
    ]
    print(f"before = {before}, after = {after}")
    for region in ("대전", "전국"):
        r = yearly[yearly["지역명"].eq(region)].set_index("연도")
        for col in ("수출중량_천톤", "수출단가_USD_kg", "수출액_백만불"):
            b, a = r.loc[before, col].mean(), r.loc[after, col].mean()
            print(f"{region} {col}: {b:,.1f} -> {a:,.1f} ({(a / b - 1) * 100:+.0f}%)")
    pivot = yearly.pivot_table(
        index="연도", columns="지역명", values=["수출단가_USD_kg", "수입단가_USD_kg"]
    )
    ratio = pivot["수출단가_USD_kg"]["대전"] / pivot["수출단가_USD_kg"]["전국"]
    print("\nDaejeon / national export unit value:")
    print(ratio.round(2).to_string())
    print(
        f"\nImport unit value {last}: Daejeon {pivot['수입단가_USD_kg']['대전'][last]:.1f}, "
        f"national {pivot['수입단가_USD_kg']['전국'][last]:.1f}"
    )


def result_9() -> None:
    header("9. Monthly index (yearly monthly mean = 100)")
    monthly = pd.read_csv(
        DATA_DIR / "kita_regional_monthly_4_added.csv", parse_dates=["연월"]
    )
    dj = monthly[monthly["지역명"].eq("대전") & monthly["연도"].le(2025)].copy()
    dj["월"] = dj["연월"].dt.month
    for col in ("수출액_백만불", "수입액_백만불"):
        idx = dj[col] / dj.groupby("연도")[col].transform("mean") * 100
        print(col, idx.groupby(dj["월"]).mean().round(0).astype(int).to_dict())


def inorganic_chemicals(td: pd.DataFrame) -> None:
    header("3 (bullet). Inorganic chemical imports")
    dj = td[td["지역명"].eq(DJ)]
    total = dj.groupby("기간")["수입금액"].sum()
    inorg = dj[dj["류명약칭"].eq("무기화학품")].groupby("기간")["수입금액"].sum()
    out = pd.DataFrame({"백만USD": inorg / 1_000, "전체수입중%": inorg / total * 100})
    print(out.loc[out.index.max() - RANK_YEARS + 1 :].round(1).to_string())


if __name__ == "__main__":
    td = pd.read_csv(DATA_DIR / "tradedata_2000_2025_4_added.csv")
    recent = td[td["기간"].gt(td["기간"].max() - RANK_YEARS)]
    result_3(recent)
    inorganic_chemicals(td)
    result_4(recent)
    result_5(td)
    result_6(int(td["기간"].max()))
    result_7(recent)
    result_8()
    result_9()
