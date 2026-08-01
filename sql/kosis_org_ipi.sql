/*
====================================================================
* Author: Minseo Kim
* Data Sources: 
    - KOSIS 시도/산업별 광공업 생산지수(2018~2026)
    - https://www.kosis.or.kr/kosis/kosis/main.do?page=main&menuNo=1000
* organise data by region
* Output: data/kosis_org_ipi.csv
====================================================================
*/

WITH base_data AS (
    SELECT 
        날짜,
        YEAR(날짜) AS yr,
        MONTH(날짜) AS mth,
        시도별,
        산업별,
        항목,
        지수,
        -- 1. 대전을 독립 권역으로 분리한 권역 매핑 (한글)
        CASE 
            WHEN 시도별 LIKE '%대전%' THEN '대전'
            WHEN 시도별 REGEXP '서울|경기|인천|수도권' THEN '수도권'
            WHEN 시도별 REGEXP '세종|충북|충남|충청' THEN '충청권'
            WHEN 시도별 REGEXP '부산|대구|울산|경북|경남|경상' THEN '영남권'
            WHEN 시도별 REGEXP '광주|전북|전남|전라' THEN '호남권'
        ELSE '기타'
    END AS region,  
        
        -- 2. 권역 매핑 (영문)
        CASE 
            WHEN 시도별 LIKE '%대전%' THEN 'Daejeon'
            WHEN 시도별 REGEXP '서울|경기|인천|수도권' THEN 'Capital Area'
            WHEN 시도별 REGEXP '세종|충북|충남|충청' THEN 'Chungcheong'
            WHEN 시도별 REGEXP '부산|대구|울산|경북|경남|경상' THEN 'Yeongnam'
            WHEN 시도별 REGEXP '광주|전북|전남|전라' THEN 'Honam'
            ELSE 'Others'
        END AS region_en
    FROM kosis_ipi_clean
    WHERE 항목 LIKE '%계절조정%' -- 계절조정 지수만 선택
),

-- 권역별 월간/연간 평균 지수 집계
region_aggregated AS (
    SELECT 
        yr,
        mth,
        날짜,
        산업별,
        region,
        region_en,
        ROUND(AVG(지수), 2) AS avg_index
    FROM base_data
    GROUP BY yr, mth, 날짜, 산업별, region, region_en
)

-- 최종 추출: 권역별 지수 및 전체 대비 비중(비율) 산출
SELECT 
    yr,
    mth,
    날짜,
    산업별,
    region,
    region_en,
    avg_index,
    -- 같은 시점(날짜)/산업 내에서 해당 권역 지수가 차지하는 비중(%)
    ROUND(
        (avg_index / SUM(avg_index) OVER (PARTITION BY 날짜, 산업별)) * 100, 2
    ) AS index_share_pct
FROM region_aggregated
ORDER BY 날짜, 산업별, region;
