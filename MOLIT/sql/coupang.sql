SELECT 
    YEAR,
    CASE 
        WHEN LEFT(SIDO, 2) IN ('서울', '경기', '인천') THEN '수도권'
        ELSE '기타'
    END AS SIDO_GROUP,
    COUNT(*) AS REGISTRATION_COUNT
FROM 
    `processed_wh_info`
WHERE 
    COMPANY_NAME_CLEAN LIKE '%쿠팡%'
GROUP BY 
    1, 2
ORDER BY 
    1 ASC, 2 ASC;