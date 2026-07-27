select 연도, 
    SUM(CASE WHEN 구분 = '출발' THEN 물동량 ELSE 0 END) AS `총 출발량`, 
    SUM(CASE WHEN 구분 = '도착' THEN 물동량 ELSE 0 END) AS `총 도착량`
from `data_logistics_cleaned`
group by 연도;