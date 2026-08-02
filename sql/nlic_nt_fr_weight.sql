WITH base_mapped AS (
    -- 1. [출발 데이터] 기준지역이 출발지가 되고, 대상지역이 도착지가 됨
    SELECT
        연도 AS year,
        '출발' AS flow_type,
        기준지역 AS base_city,
        대상지역 AS target_city,
        물동량 AS cargo_volume
    FROM nlic_raw_nt_logi_total

    UNION ALL

    -- 2. [도착 데이터] 대상지역이 기준(도착지)이 되고, 기준지역이 상대 출발지가 됨
    SELECT
        연도 AS year,
        '도착' AS flow_type,
        대상지역 AS base_city,   -- 도착지 관점에서는 대상지역이 기준이 됨
        기준지역 AS target_city, -- 도착지 관점에서는 기준지역이 상대 지역이 됨
        물동량 AS cargo_volume
    FROM nlic_raw_nt_logi_total
),
mapped_data AS (
    SELECT
        *, -- [수정 1] flow_type 컬럼 직접 선택
        
        -- 기준지역 권역 매핑
        CASE 
            WHEN base_city = '대전' THEN '대전시'
            WHEN base_city IN ('서울', '경기', '인천') THEN '수도권'
            WHEN base_city IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
            WHEN base_city IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN base_city IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS base_region_kr,

        CASE 
            WHEN base_city = '대전' THEN 'Daejeon'
            WHEN base_city IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN base_city IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
            WHEN base_city IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN base_city IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS base_region_en,

        -- 대상지역 권역 매핑
        CASE 
            WHEN target_city = '대전' THEN '대전시'
            WHEN target_city IN ('서울', '경기', '인천') THEN '수도권'
            WHEN target_city IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
            WHEN target_city IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN target_city IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS target_region_kr,

        CASE 
            WHEN target_city = '대전' THEN 'Daejeon'
            WHEN target_city IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN target_city IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
            WHEN target_city IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN target_city IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS target_region_en
    FROM base_mapped
    WHERE flow_type = '출발' -- [핵심] 출발 데이터만 필터링
)
SELECT 
    year, base_city, base_region_en,  base_region_kr, 
    target_city, target_region_en,target_region_kr, cargo_volume,
    
    CASE 
        WHEN base_region_kr = target_region_kr THEN '권역 내'
        ELSE '권역 간'
    END AS logistics_type
FROM mapped_data;
