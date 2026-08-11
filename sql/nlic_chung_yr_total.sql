/*
====================================================================
* Author: Minseo Kim
* Data Sources: 
    - NLIC 물류통계(2018~2026)
    - data_logistics_total_national.csv
* organise data by region
* Output: data/nlic_chung_regional_cargo_flow.csv
====================================================================
*/

WITH departure_data AS (
    -- 1. [Outbound] 충청권에서 다른 지역으로 나가는 물동량
    -- 기준지 = 충청권(출발), 상대지 = 타지역(도착)
    SELECT
        year,
        base_region_kr,
        base_region_en,
        target_region_kr,
        target_region_en,
        SUM(cargo_volume) AS cargo_volume,
        '출발' AS flow_type
    FROM
        nlic_nt_fr_weight
    WHERE 
        base_region_kr = '충청권(대전제외)'
    GROUP BY
        year, base_region_kr, base_region_en, target_region_kr, target_region_en
),
arrival_data AS (
    -- 2. [Inbound] 다른 지역에서 충청권으로 들어오는 물동량
    -- 기준지 = 충청권(도착), 상대지 = 타지역(출발)
    -- ※ 원본의 target(도착지)을 '기준지' 위치로, base(출발지)를 '상대지' 위치로 스왑(Swap)하여 기준을 고정
    SELECT
        year,
        target_region_kr AS base_region_kr,
        target_region_en AS base_region_en,
        base_region_kr AS target_region_kr,
        base_region_en AS target_region_en,
        SUM(cargo_volume) AS cargo_volume,
        '도착' AS flow_type
    FROM
        nlic_nt_fr_weight
    WHERE 
        target_region_kr = '충청권(대전제외)'
    GROUP BY
        year, target_region_kr, target_region_en, base_region_kr, base_region_en
),
combined_data AS (
    SELECT * FROM departure_data
    UNION ALL
    SELECT * FROM arrival_data
),
aggregated_data AS (
    SELECT
        *,
        -- 연도 및 flow_type(출발/도착)별 총물동량 대비 비율(%)
        ROUND(
            (cargo_volume / SUM(cargo_volume) OVER (PARTITION BY year, flow_type)) * 100, 
            2
        ) AS ratio
    FROM
        combined_data
)
SELECT 
    year,
    base_region_kr,
    base_region_en,
    target_region_kr,
    target_region_en,
    flow_type,
    cargo_volume,
    ratio
FROM 
    aggregated_data
ORDER BY year, flow_type;