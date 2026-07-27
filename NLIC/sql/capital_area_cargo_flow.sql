WITH departure_data AS (
    -- 1. [Outbound] Freight volume originating from Capital Region (Includes internal moves)
    SELECT
        연도 AS year,
        '수도권' AS base_region,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            ELSE 대상지역 
        END AS target_region,
        '출발' AS flow_type,
        물동량 AS cargo_volume
    FROM
        data_logistics_total_national
    WHERE
        기준지역 IN ('서울', '경기', '인천')
),
arrival_data AS (
    -- 2. [Inbound] Freight volume destined for Capital Region (Includes internal moves)
    SELECT
        연도 AS year,
        '수도권' AS base_region,
        CASE 
            WHEN 기준지역 IN ('서울', '경기', '인천') THEN '수도권'
            ELSE 기준지역 
        END AS target_region,
        '도착' AS flow_type,
        물동량 AS cargo_volume
    FROM
        data_logistics_total_national
    WHERE
        대상지역 IN ('서울', '경기', '인천')
),
combined_data AS (
    -- Combine outbound and inbound dataset
    SELECT * FROM departure_data
    UNION ALL
    SELECT * FROM arrival_data
)
SELECT
    year,
    base_region,   -- 'Capital Region'
    target_region, -- Partner region (e.g., Gangwon, Gyeongnam, Capital Region)
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