-- [한 번에 검증하기] UNION ALL을 활용한 일괄 결과 출력
SELECT 
    '1. ratio 합계 최소/최대값 (99.9~100.1 이면 정상)' AS check_item,
    CONCAT('Min: ', MIN(sum_ratio), '% / Max: ', MAX(sum_ratio), '%') AS check_result
FROM (
    SELECT year, direction, ROUND(SUM(ratio), 2) AS sum_ratio
    FROM nlic_chung_cargo_flow
    GROUP BY year, direction
) t1

UNION ALL

SELECT 
    '2. NULL 또는 0 이하 물동량 행 수 (제주 제외, 0이어야 정상)' AS check_item,
    CAST(COUNT(*) AS CHAR) AS check_result
FROM nlic_chung_cargo_flow
WHERE (cargo_volume IS NULL OR cargo_volume <= 0)
  AND base_city <> '제주'
  AND target_city <> '제주'

UNION ALL

SELECT 
    '3. 충청->충청 내부 이동 데이터 건수 (출발/도착 각 1회씩)' AS check_item,
    CAST(COUNT(*) AS CHAR) AS check_result  -- ✅ 불필요한 base_city, target_city 및 Trailing Comma 제거
FROM nlic_chung_cargo_flow
WHERE base_region_kr = '충청권(대전제외)' 
  AND target_region_kr = '충청권(대전제외)';


-- detailed internal movement data for Chungcheong region
SELECT 
    year,
    direction,
    COUNT(*) AS internal_row_count,               -- 충청 내 이동 데이터 행 수
    COUNT(DISTINCT base_city) AS unique_base_cities, -- 출발 시군구 수 (중복제거)
    COUNT(DISTINCT target_city) AS unique_target_cities, -- 도착 시군구 수 (중복제거)
    SUM(cargo_volume) AS total_internal_volume    -- 충청 내 총 물동량
FROM nlic_chung_cargo_flow
WHERE base_region_kr = '충청권(대전제외)' 
  AND target_region_kr = '충청권(대전제외)'
GROUP BY year, direction
ORDER BY year, direction;