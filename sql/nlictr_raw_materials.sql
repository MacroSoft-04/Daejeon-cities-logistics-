WITH base_data AS (
    SELECT
        region_kr,
        region_en,
        flow_type,
        commodity,
        -- 연도별 물동량 집계
        SUM(CASE WHEN year = 2020 THEN cargo_volume ELSE 0 END) AS vol_2020,
        SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) AS vol_2021,
        SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) AS vol_2022,
        SUM(CASE WHEN year = 2023 THEN cargo_volume ELSE 0 END) AS vol_2023,
        
        -- 연도별 증감량 계산
        SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2020 THEN cargo_volume ELSE 0 END) AS gap_20_21_vol,
        SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) AS gap_21_22_vol,
        SUM(CASE WHEN year = 2023 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) AS gap_22_23_vol
    FROM 
        nlictr_com_cat
    WHERE   
        year IN (2020, 2021, 2022, 2023)
        AND region_kr IN ('충청권(대전제외)', '수도권', '대전시')
        AND flow_type <> '합계'
        AND commodity_category = '원자재 및 기초소재'
    GROUP BY 
        region_kr, 
        region_en,
        flow_type,
        commodity  -- [수정] 품목별 집계를 위한 GROUP BY 추가
),
ranked_data AS (
    SELECT 
        *,
        -- region_kr, flow_type 그룹별로 gap_21_22_vol 절댓값 기준 내림차순 순위 부여
        ROW_NUMBER() OVER (
            PARTITION BY region_kr, flow_type 
            ORDER BY ABS(gap_21_22_vol) DESC
        ) AS rank_num
    FROM 
        base_data
)
SELECT 
    region_kr,
    region_en,
    flow_type,
    commodity,  -- [수정] commodity_category 대신 실제 품목명 출력
    vol_2020,
    vol_2021,
    vol_2022,
    vol_2023,
    gap_20_21_vol,
    gap_21_22_vol,
    gap_22_23_vol,
    rank_num
FROM 
    ranked_data
WHERE 
    rank_num <= 5 
ORDER BY 
    region_kr, 
    flow_type, 
    rank_num;