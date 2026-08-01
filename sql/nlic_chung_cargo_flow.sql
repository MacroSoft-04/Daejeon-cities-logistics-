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
    -- 1. [Outbound] Freight volume originating from Chungcheong Region (Excluding Daejeon)
    SELECT
        연도 AS year,
        '충청권(대전제외)' AS base_region,
        CASE 
            WHEN 대상지역 IN ('세종', '충남', '충북') THEN '충청권(대전제외)' -- 👈 쉼표 제거 및 컬럼명(대상지역) 수정
            ELSE 대상지역 
        END AS target_region,
        '출발' AS flow_type,
        물동량 AS cargo_volume
    FROM
        data_logistics_total_national
    WHERE
        기준지역 IN ('세종', '충남', '충북')
),
arrival_data AS (
    -- 2. [Inbound] Freight volume destined for Chungcheong Region (Excluding Daejeon)
    SELECT
        연도 AS year,
        '충청권(대전제외)' AS base_region,
        CASE 
            WHEN 기준지역 IN ('세종', '충남', '충북') THEN '충청권(대전제외)' -- 👈 쉼표 제거
            ELSE 기준지역 
        END AS target_region,
        '도착' AS flow_type,
        물동량 AS cargo_volume
    FROM
        data_logistics_total_national
    WHERE
        대상지역 IN ('세종', '충남', '충북')
),
combined_data AS (
    -- Combine outbound and inbound dataset
    SELECT * FROM departure_data
    UNION ALL
    SELECT * FROM arrival_data
)
SELECT
    year,
    base_region,   -- 'Chungcheong Region (Excluding Daejeon)'
    target_region, -- Partner region
    flow_type,     -- Flow direction ('Departure' / 'Arrival')
    SUM(cargo_volume) AS total_cargo_volume
FROM
    combined_data
GROUP BY
    year,
    base_region,
    target_region,
    flow_type
ORDER BY
    year ASC,
    flow_type ASC,
    target_region ASC;