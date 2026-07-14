-- 2022 cargo volume
SELECT 
    CASE 
        WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
        WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
        WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
        WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
        ELSE '기타'
    END AS 권역,
    대상지역 AS 도시명,
    구분,
    물동량
FROM data_logistics_cleaned
WHERE 연도 = '2022';

-- 2023 cargo volume
SELECT 
    CASE 
        WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
        WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
        WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
        WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
        ELSE '기타'
    END AS 권역,
    대상지역 AS 도시명,
    구분,
    물동량
FROM data_logistics_cleaned
WHERE 연도 = '2023';

