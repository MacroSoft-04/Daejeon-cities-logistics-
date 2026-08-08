WITH yearly_vol AS (
    -- 1. 지역/유형/품목/연도별 물동량 집계 및 전년 대비 증감량(GAP) 계산
    SELECT 
        region_kr,
        region_en,
        flow_type,
        commodity,
        year,
        SUM(cargo_volume) AS cargo_vol,
        -- 이전 연도 추출 (연도 기준 정렬)
        LAG(year) OVER (
            PARTITION BY region_kr, flow_type, commodity 
            ORDER BY year
        ) AS prev_year,
        -- 전년 대비 물동량 증감(GAP) 계산
        SUM(cargo_volume) - LAG(SUM(cargo_volume)) OVER (
            PARTITION BY region_kr, flow_type, commodity 
            ORDER BY year
        ) AS gap_vol
    FROM nlictr_com_cat
    WHERE year IN (2020, 2021, 2022, 2023)
      AND region_kr IN ('충청권(대전제외)', '수도권', '대전시')
      AND flow_type <> '합계'
      AND commodity_category = '원자재 및 기초소재'
    GROUP BY region_kr, region_en, flow_type, commodity, year
),
target_rank AS (
    -- 2. 21-22년 증감량(ABS) 기준 Top 2 품목 순위 추출
    SELECT 
        region_kr,
        flow_type,
        commodity,
        ROW_NUMBER() OVER (
            PARTITION BY region_kr, flow_type 
            ORDER BY SUM(ABS(gap_vol))/3.0 DESC
        ) AS rank_num
    FROM yearly_vol
    GROUP BY region_kr, flow_type, commodity
)
SELECT 
    y.region_kr,
    y.region_en,
    y.flow_type,
    y.commodity,
    t.rank_num,
    y.year,
    y.cargo_vol,
    CASE 
        WHEN y.prev_year IS NOT NULL THEN CONCAT(y.prev_year, ' - ', y.year)
        ELSE '기준연도'
    END AS gap_period,
    y.gap_vol
FROM yearly_vol y
INNER JOIN target_rank t
    ON y.region_kr = t.region_kr
   AND y.flow_type = t.flow_type
   AND y.commodity = t.commodity
WHERE t.rank_num <= 4
ORDER BY y.region_kr, y.flow_type, t.rank_num, y.year;