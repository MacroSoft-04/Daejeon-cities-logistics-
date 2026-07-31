WITH mapped_data AS ( 
    SELECT
        *,
        -- 대전시만 단독 분리, 나머지는 권역으로 결합
        CASE 
            WHEN 기준지역 = '대전' THEN '대전시'
            WHEN 기준지역 IN ('서울', '경기', '인천') THEN '수도권'
            WHEN 기준지역 IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
            WHEN 기준지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN 기준지역 IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS base_city_kr,

        CASE 
            WHEN 기준지역 = '대전' THEN 'Daejeon'
            WHEN 기준지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN 기준지역 IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
            WHEN 기준지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN 기준지역 IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS base_city_en,

        CASE 
            WHEN 대상지역 = '대전' THEN '대전시'
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            WHEN 대상지역 IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS target_city_kr,

        CASE 
            WHEN 대상지역 = '대전' THEN 'Daejeon'
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN 대상지역 IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS target_city_en
    FROM data_logistics_total_national
)
SELECT 
    연도,
    base_city_kr,
    base_city_en,
    target_city_kr,
    target_city_en,
    CASE 
        WHEN base_city_kr = target_city_kr THEN '권역 내'
        ELSE '권역 간'
    END AS logistics_type,
    물동량
FROM mapped_data;