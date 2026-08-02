WITH departure_data AS (
    -- 1. [Outbound] 충청권에서 다른 지역으로 출발하는 물동량
    -- (기준지: 충청권 출발지 / 상대지: 타지역 도착지)
    SELECT
        year,
        base_city,
        base_region_kr,
        base_region_en,
        target_city,
        target_region_kr,
        target_region_en,
        cargo_volume,
        '출발' AS direction
    FROM
        nlic_nt_fr_weight
    WHERE 
        base_region_kr = '충청권(대전제외)'
),
arrival_data AS (
    -- 2. [Inbound] 다른 지역에서 충청권으로 도착하는 물동량
    -- (기준지: 충청권 도착지 / 상대지: 타지역 출발지)
    -- ※ SELECT 순서를 departure_data와 100% 동일하게 맞춰줘야 합니다!
    SELECT
        year,
        target_city AS base_city,              -- [위치 2] 충청권 도시를 base_city로
        target_region_kr AS base_region_kr,    -- [위치 3] 충청권을 base_region_kr로
        target_region_en AS base_region_en,    -- [위치 4] 충청권 영문명을 base_region_en으로
        base_city AS target_city,              -- [위치 5] 타지역 도시를 target_city로
        base_region_kr AS target_region_kr,    -- [위치 6] 타지역 권역을 target_region_kr로
        base_region_en AS target_region_en,    -- [위치 7] 타지역 영문명을 target_region_en으로
        cargo_volume,
        '도착' AS direction
    FROM
        nlic_nt_fr_weight
    WHERE 
        target_region_kr = '충청권(대전제외)'
),
combined_data AS (
    SELECT * FROM departure_data
    UNION ALL
    SELECT * FROM arrival_data
),
aggregated_data AS (
    SELECT
        *,
        -- 연도 및 direction(출발/도착)별 총물동량 대비 비율(%)
        ROUND(
            (cargo_volume / SUM(cargo_volume) OVER (PARTITION BY year, direction)) * 100, 
            2
        ) AS ratio
    FROM
        combined_data
)
SELECT 
    year,
    base_city,
    base_region_kr,
    base_region_en,
    target_city,
    target_region_kr,
    target_region_en,
    direction,
    cargo_volume,
    ratio
FROM 
    aggregated_data
ORDER BY year, target_city, direction;