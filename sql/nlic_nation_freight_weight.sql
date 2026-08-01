WITH base_mapped AS (
    -- 1. [출발 데이터] 기준지역이 출발지가 되고, 대상지역이 도착지가 됨
    SELECT
        연도,
        '출발' AS flow_type,
        기준지역 AS base_region,
        대상지역 AS target_region,
        물동량
    FROM nlic_raw_nt_logi_total

    UNION ALL

    -- 2. [도착 데이터] 대상지역이 기준(도착지)이 되고, 기준지역이 상대 출발지가 됨
    SELECT
        연도,
        '도착' AS flow_type,
        대상지역 AS base_region,  -- 도착지 관점에서는 대상지역이 기준이 됨
        기준지역 AS target_region, -- 도착지 관점에서는 기준지역이 상대 지역이 됨
        물동량
    FROM nlic_raw_nt_logi_total
),
mapped_data AS (
    SELECT
        연도,
        flow_type AS 구분,
        
        -- 기준지역 권역 매핑
        CASE 
            WHEN base_region = '대전' THEN '대전시'
            WHEN base_region IN ('서울', '경기', '인천') THEN '수도권'
            WHEN base_region IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
            WHEN base_region IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN base_region IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS base_city_kr,

        CASE 
            WHEN base_region = '대전' THEN 'Daejeon'
            WHEN base_region IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN base_region IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
            WHEN base_region IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN base_region IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS base_city_en,

        -- 대상지역 권역 매핑
        CASE 
            WHEN target_region = '대전' THEN '대전시'
            WHEN target_region IN ('서울', '경기', '인천') THEN '수도권'
            WHEN target_region IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
            WHEN target_region IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN target_region IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS target_city_kr,

        CASE 
            WHEN target_region = '대전' THEN 'Daejeon'
            WHEN target_region IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN target_region IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
            WHEN target_region IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN target_region IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS target_city_en,
        물동량
    FROM base_mapped
)
SELECT 
    연도,
    base_city_kr,
    base_city_en,
    target_city_kr,
    target_city_en,
    구분,
    CASE 
        WHEN base_city_kr = target_city_kr THEN '권역 내'
        ELSE '권역 간'
    END AS logistics_type,
    SUM(물동량) AS 물동량
FROM mapped_data
GROUP BY
    연도,
    base_city_kr,
    base_city_en,
    target_city_kr,
    target_city_en,
    구분;