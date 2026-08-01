/*
====================================================================
* Author: Minseo Kim
* Data Sources: 
    - NLIC 물류통계(2018~2026)
    - data_logistics_total_national.csv
* organise data by region
* Output: data/nlic_chung_cargo_flow.csv
====================================================================
*/

WITH departure_data AS (
    -- 1. [Outbound] 충청권 출발 데이터 중, 원본 구분도 '출발'인 행만 추출
    SELECT
        연도 AS year,
        '충청권(대전제외)' AS base_city_kr,
        'Chungcheong(excl. DJ)' AS base_city_en,
        target_city_kr AS partner_city_kr,
        target_city_en AS partner_city_en,
        물동량 AS cargo_volume,
        '출발' AS direction
    FROM
        nlic_nt_freight_weight
    WHERE 
        base_city_kr = '충청권(대전제외)'
        AND 구분 = '출발'  -- [핵심] 원본 데이터의 '출발' 행만 필터링!
),
arrival_data AS (
    -- 2. [Inbound] 충청권 도착 데이터 중, 원본 구분도 '도착'인 행만 추출
    SELECT
        연도 AS year,
        '충청권(대전제외)' AS base_city_kr,
        'Chungcheong(excl. DJ)' AS base_city_en,
        base_city_kr AS partner_city_kr,
        base_city_en AS partner_city_en,
        물동량 AS cargo_volume,
        '도착' AS direction
    FROM
        nlic_nt_freight_weight
    WHERE 
        target_city_kr = '충청권(대전제외)'
        AND 구분 = '도착'  -- [핵심] 원본 데이터의 '도착' 행만 필터링!
),
combined_data AS (
    SELECT * FROM departure_data
    UNION ALL
    SELECT * FROM arrival_data
),
aggregated_data AS (
    SELECT
        *,
        -- 연도/방향별 비율(%) 계산
        ROUND(
            (cargo_volume / SUM(cargo_volume) OVER (PARTITION BY year, direction)) * 100, 
            2
        ) AS ratio
    FROM
        combined_data
)
-- 최종 결과 출력
SELECT 
    year,
    base_city_kr,
    base_city_en,
    partner_city_kr,
    partner_city_en,
    cargo_volume,
    direction,
    ratio
FROM 
    aggregated_data
ORDER BY year, partner_city_kr, direction;