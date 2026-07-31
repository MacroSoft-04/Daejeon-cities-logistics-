-- check if the data is clean
SELECT 
    COUNT(*) AS non_seoul_both_count
FROM clean_seoul_logi_total
WHERE 송_시 != '서울특별시' 
  AND 수_시 != '서울특별시';

WITH regional_summary AS (
    -- 1단계: 연도별, 권역별 물동량 1차 집계
    SELECT 
        YEAR,
        CASE 
            WHEN 송_시 IN ('경기도', '인천광역시') THEN '수도권 외곽 (인천·경기)'
            WHEN 송_시 = '대전광역시' THEN '대전'
            ELSE '기타 지방'
        END AS region_type,
        CASE 
            WHEN 송_시 IN ('경기도', '인천광역시') THEN 'Capital Area'
            WHEN 송_시 = '대전광역시' THEN 'Daejeon'
            ELSE 'Others'
        END AS region,
        SUM(TOTAL_QTY) AS total_qty
    FROM clean_seoul_logi_total
    WHERE 수_시 = '서울특별시' 
      AND 송_시 != '서울특별시'
    GROUP BY 
        YEAR,
        CASE 
            WHEN 송_시 IN ('경기도', '인천광역시') THEN '수도권 외곽 (인천·경기)'
            WHEN 송_시 = '대전광역시' THEN '대전'
            ELSE '기타 지방'
        END,
        CASE 
            WHEN 송_시 IN ('경기도', '인천광역시') THEN 'Capital Area'
            WHEN 송_시 = '대전광역시' THEN 'Daejeon'
            ELSE 'Others'
        END
)
-- 2단계: 연도별 총합을 구하여 비율(%) 계산
SELECT 
    YEAR,
    region_type,
    region,
    total_qty,
    -- 연도별 비율 계산 (소수점 2자리)
    ROUND(total_qty * 100.0 / SUM(total_qty) OVER (PARTITION BY YEAR), 2) AS ratio_pct
FROM regional_summary
ORDER BY YEAR, region_type;