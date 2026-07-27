SELECT 
    year, 
    flow_type,
    
    -- [Volume]
    SUM(CASE WHEN target_region IN ('수도권') THEN total_cargo_volume ELSE 0 END) AS Capital_Area_vol,
    SUM(CASE WHEN target_region IN ('부산', '울산', '경남', '대구', '경북') THEN total_cargo_volume ELSE 0 END) AS Yeongnam_vol,
    SUM(CASE WHEN target_region IN ('대전', '세종', '충남', '충북') THEN total_cargo_volume ELSE 0 END) AS Chungcheong_vol,
    SUM(CASE WHEN target_region IN ('광주', '전남', '전북') THEN total_cargo_volume ELSE 0 END) AS Honam_vol,
    SUM(CASE WHEN target_region IN ('강원', '제주') THEN total_cargo_volume ELSE 0 END) AS Others_vol,

    -- [Ratio (%)]
    ROUND(SUM(CASE WHEN target_region IN ('수도권') THEN total_cargo_volume ELSE 0 END) * 100.0 / NULLIF(SUM(total_cargo_volume), 0), 2) AS Capital_Area_ratio,
    ROUND(SUM(CASE WHEN target_region IN ('부산', '울산', '경남', '대구', '경북') THEN total_cargo_volume ELSE 0 END) * 100.0 / NULLIF(SUM(total_cargo_volume), 0), 2) AS Yeongnam_ratio,
    ROUND(SUM(CASE WHEN target_region IN ('대전', '세종', '충남', '충북') THEN total_cargo_volume ELSE 0 END) * 100.0 / NULLIF(SUM(total_cargo_volume), 0), 2) AS Chungcheong_ratio,
    ROUND(SUM(CASE WHEN target_region IN ('광주', '전남', '전북') THEN total_cargo_volume ELSE 0 END) * 100.0 / NULLIF(SUM(total_cargo_volume), 0), 2) AS Honam_ratio,
    ROUND(SUM(CASE WHEN target_region IN ('강원', '제주') THEN total_cargo_volume ELSE 0 END) * 100.0 / NULLIF(SUM(total_cargo_volume), 0), 2) AS Others_ratio,

    -- [total]
    SUM(total_cargo_volume) AS total_cargo_volume

FROM capital_city
GROUP BY year, flow_type
ORDER BY year ASC, flow_type DESC;