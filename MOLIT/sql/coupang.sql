SELECT 
    YEAR,
    CASE 
        WHEN LEFT(SIDO, 2) IN ('서울', '경기', '인천') THEN '수도권'
        ELSE SIDO
    END AS SIDO_GROUP,
    COMPANY_NAME_CLEAN AS COMPANY_NAME,
    COUNT(*) AS REGISTRATION_COUNT
FROM 
    `processed_wh_info`
WHERE 
    COMPANY_NAME_CLEAN LIKE '%쿠팡%'
GROUP BY 
    YEAR, 
    CASE 
        WHEN LEFT(SIDO, 2) IN ('서울', '경기', '인천') THEN '수도권'
        ELSE SIDO
    END,
    COMPANY_NAME_CLEAN
ORDER BY 
    YEAR ASC, 
    SIDO_GROUP ASC;