WITH base_gap AS (
    SELECT 
        CASE 
            WHEN target_city IN ('서울', '경기', '인천') THEN '수도권'
            ELSE target_city
        END AS target_city,
        target_region_kr,
        target_region_en,
        direction,
        SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) AS vol_2021,
        SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) AS vol_2022,
        SUM(CASE WHEN year = 2023 THEN cargo_volume ELSE 0 END) AS vol_2023,
        SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) AS gap_22_21_vol,
        SUM(CASE WHEN year = 2023 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) AS gap_23_22_vol
    FROM 
        nlic_chung_cargo_flow
    WHERE 
        year IN (2021, 2022, 2023)
    GROUP BY 
        CASE 
            WHEN target_city IN ('서울', '경기', '인천') THEN '수도권'
            ELSE target_city
        END,
        target_region_kr,
        target_region_en,
        direction
),
ranked_gap AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY direction ORDER BY ABS(gap_22_21_vol) DESC) AS rank_22_21,
        ROW_NUMBER() OVER (PARTITION BY direction ORDER BY ABS(gap_23_22_vol) DESC) AS rank_23_22
    FROM base_gap
)

-- [1] 2021 -> 2022 변동 분석
SELECT 
    '2021-2022' AS period_type,
    direction,
    CASE WHEN rank_22_21 <= 5 THEN target_city ELSE '기타 (10개 지자체)' END AS target_city,
    CASE WHEN rank_22_21 <= 5 THEN target_region_kr ELSE '기타' END AS region,
    CASE WHEN rank_22_21 <= 5 THEN target_city ELSE 'Others (10 Local Govs)' END AS city_en,
    CASE WHEN rank_22_21 <= 5 THEN target_region_en ELSE 'Others' END AS region_en,
    SUM(vol_2021) AS vol_start,
    SUM(vol_2022) AS vol_end,
    SUM(gap_22_21_vol) AS gap_vol
FROM ranked_gap
GROUP BY 
    direction,
    CASE WHEN rank_22_21 <= 5 THEN target_city ELSE '기타 (10개 지자체)' END,
    CASE WHEN rank_22_21 <= 5 THEN target_region_kr ELSE '기타' END,
    CASE WHEN rank_22_21 <= 5 THEN target_city ELSE 'Others (10 Local Govs)' END,
    CASE WHEN rank_22_21 <= 5 THEN target_region_en ELSE 'Others' END

UNION ALL

-- [2] 2022 -> 2023 변동 분석
SELECT 
    '2022-2023' AS period_type,
    direction,
    CASE WHEN rank_23_22 <= 5 THEN target_city ELSE '기타 (10개 지자체)' END AS target_city,
    CASE WHEN rank_23_22 <= 5 THEN target_region_kr ELSE '기타' END AS region,
    CASE WHEN rank_23_22 <= 5 THEN target_city ELSE 'Others (10 Local Govs)' END AS city_en,
    CASE WHEN rank_23_22 <= 5 THEN target_region_en ELSE 'Others' END AS region_en,
    SUM(vol_2022) AS vol_start,
    SUM(vol_2023) AS vol_end,
    SUM(gap_23_22_vol) AS gap_vol
FROM ranked_gap
GROUP BY 
    direction,
    CASE WHEN rank_23_22 <= 5 THEN target_city ELSE '기타 (10개 지자체)' END,
    CASE WHEN rank_23_22 <= 5 THEN target_region_kr ELSE '기타' END,
    CASE WHEN rank_23_22 <= 5 THEN target_city ELSE 'Others (10 Local Govs)' END,
    CASE WHEN rank_23_22 <= 5 THEN target_region_en ELSE 'Others' END

ORDER BY 
    period_type ASC,
    direction ASC, 
    ABS(gap_vol) DESC;