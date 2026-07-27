WITH base_data AS (
    SELECT
        연도 AS year,
        -- Set baseline region to 'Capital Region'
        '수도권' AS base_region,    
        CASE 
            WHEN 기준지역 IN ('서울', '경기', '인천') THEN 
                CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권' ELSE 대상지역 END
            ELSE 
                CASE WHEN 기준지역 IN ('서울', '경기', '인천') THEN '수도권' ELSE 기준지역 END
        END AS target_region,
        CASE 
            WHEN 기준지역 IN ('서울', '경기', '인천') THEN '출발'
            ELSE '도착'
        END AS flow_type,
        물동량 AS cargo_volume
    FROM
        data_logistics_total_national
    WHERE
        기준지역 IN ('서울', '경기', '인천')
        OR 대상지역 IN ('서울', '경기', '인천')
)
SELECT
    year,
    base_region,   -- Always '수도권' (Capital Region)
    target_region, -- Partner region (e.g., Gangwon, Gyeongnam, Capital Region)
    flow_type,     -- Flow direction (Departure / Arrival)
    SUM(cargo_volume) AS total_cargo_volume
FROM
    base_data
GROUP BY
    year,
    flow_type,
    base_region,
    target_region
ORDER BY
    year ASC,
    flow_type ASC,
    target_region ASC;