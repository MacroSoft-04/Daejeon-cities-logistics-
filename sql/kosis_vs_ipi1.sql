/*
====================================================================
* Author: Minseo Kim
* Data Sources: 
    - KOSIS 시도/산업별 광공업 생산지수(2018~2026)
    - https://www.kosis.or.kr/kosis/kosis/main.do?page=main&menuNo=1000
    - kosis_ipi_clean2.csv
* organise data by region (including National aggregate)
* Output: data/kosis_org_ipi.csv
====================================================================
*/

WITH base_mapped AS (
    SELECT
        yr AS `year`,                   -- year 컬럼명 매핑 수정
        날짜 AS `date`,
        산업별 AS industry,
        region AS region_kr,
        region_en, 
        avg_index, 
        index_share_pct
    FROM kosis_ipi_clean2
    WHERE 산업별 = '총지수'               -- 총지수만 필터링
),
nationwide AS (
    -- 권역별 지수를 비중(index_share_pct) 기반으로 가중평균하여 전국 지표 산출
    SELECT
        `year`,
        `date`,
        industry,
        '전국' AS region_kr,
        'Nationwide' AS region_en,
        ROUND(SUM(avg_index * index_share_pct) / SUM(index_share_pct), 2) AS avg_index,
        ROUND(SUM(index_share_pct), 2) AS index_share_pct
    FROM base_mapped
    GROUP BY `year`, `date`, industry
),
combined AS (
    -- 권역별 데이터와 전국 데이터 결합
    SELECT * FROM base_mapped
    UNION ALL
    SELECT * FROM nationwide
)
SELECT
    `year`,
    `date`,
    industry,
    region_kr,
    region_en,
    avg_index,
    index_share_pct
FROM combined
ORDER BY 
    `year`, 
    `date`, 
    -- 전국 데이터를 가장 상단에 조회하도록 정렬 (선택사항)
    CASE WHEN region_kr = '전국' THEN 0 ELSE 1 END,
    region_kr;