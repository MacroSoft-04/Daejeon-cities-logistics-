-- Calculate regional cargo volumes and verify if the total percentage equals 100%
select 연도, 구분,
    SUM(CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN 물동량 ELSE 0 END) AS 수도권_물동량,
    SUM(CASE WHEN 대상지역 IN ('부산', '울산', '경남') THEN 물동량 ELSE 0 END) AS 영남권_물동량,
    SUM(CASE WHEN 대상지역 IN ('대전', '세종', '충남', '충북') THEN 물동량 ELSE 0 END) AS 충청권_물동량,
    SUM(CASE WHEN 대상지역 IN ('광주', '전남', '전북') THEN 물동량 ELSE 0 END) AS 호남권_물동량,
    SUM(CASE WHEN 대상지역 IN ('강원', '제주') THEN 물동량 ELSE 0 END) AS 기타_물동량,

    (
    ROUND(SUM(CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) +
    ROUND(SUM(CASE WHEN 대상지역 IN ('부산', '울산', '경남') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) +
    ROUND(SUM(CASE WHEN 대상지역 IN ('대전', '세종', '충남', '충북') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) +
    ROUND(SUM(CASE WHEN 대상지역 IN ('광주', '전남', '전북') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) + 
    ROUND(SUM(CASE WHEN 대상지역 IN ('강원', '제주') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) 
    ) AS verification_total_percentage
from data_logistics_cleaned
group by 연도, 구분
ORDER BY 연도, 구분 DESC;

-- find any target regions that are not included in the defined regions
select distinct 대상지역
from data_logistics_cleaned
where 대상지역 not in(
    '서울', '경기', '인천', 
    '부산', '울산', '경남', 
    '대전', '세종', '충남', '충북', 
    '광주', '전남', '전북', 
    '강원', '제주'
);

-- finally, calculate the 물동량 and percentage for each region
select 연도, 구분,
    SUM(CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN 물동량 ELSE 0 END) AS 수도권_물동량,
    SUM(CASE WHEN 대상지역 IN ('부산', '울산', '경남', '대구', '경북') THEN 물동량 ELSE 0 END) AS 영남권_물동량,
    SUM(CASE WHEN 대상지역 IN ('대전', '세종', '충남', '충북') THEN 물동량 ELSE 0 END) AS 충청권_물동량,
    SUM(CASE WHEN 대상지역 IN ('광주', '전남', '전북') THEN 물동량 ELSE 0 END) AS 호남권_물동량,
    SUM(CASE WHEN 대상지역 IN ('강원', '제주') THEN 물동량 ELSE 0 END) AS 기타_물동량,

    ROUND(SUM(CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) AS 수도권_비율,
    ROUND(SUM(CASE WHEN 대상지역 IN ('부산', '울산', '경남', '대구', '경북') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) AS 영남권_비율,
    ROUND(SUM(CASE WHEN 대상지역 IN ('대전', '세종', '충남', '충북') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) AS 충청권_비율,
    ROUND(SUM(CASE WHEN 대상지역 IN ('광주', '전남', '전북') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) AS 호남권_비율,
    ROUND(SUM(CASE WHEN 대상지역 IN ('강원', '제주') THEN 물동량 ELSE 0 END) / SUM(물동량) * 100, 2) AS 기타_비율
from data_logistics_cleaned
group by 연도, 구분
ORDER BY 연도, 구분 DESC;