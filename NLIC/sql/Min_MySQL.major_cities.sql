SELECT 
    CASE 
        WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
        WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
    END AS 권역,
    대상지역 AS 도시명,
    SUM(물동량) AS 총_도착_물동량
FROM data_logistics_cleaned
WHERE 구분 = '도착'
    AND 대상지역 IN ('서울', '경기', '인천', '대전', '세종', '충북', '충남')
GROUP BY 권역, 대상지역
-- -- Group by regions first, then sort by logistic volume in descending order within each region
ORDER BY 권역 DESC, 총_도착_물동량 DESC; 

SELECT 
    CASE 
        WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
        WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
    END AS 권역,
    대상지역 AS 도시명,
    SUM(물동량) AS 총_출발_물동량
FROM data_logistics_cleaned
WHERE 구분 = '출발'
  AND 대상지역 IN ('대전', '세종', '충북', '충남', '부산', '대구', '울산', '경북', '경남')
GROUP BY 권역, 대상지역
-- Group by regions first, then sort by logistic volume in descending order within each region
ORDER BY 권역 DESC, 총_출발_물동량 DESC;
