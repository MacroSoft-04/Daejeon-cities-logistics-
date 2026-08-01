/*
====================================================================
* Author: Minseo Kim
* Data Sources: 
    - KOSIS 시도/산업별 광공업 생산지수(2018~2026)
    - https://www.kosis.or.kr/kosis/kosis/main.do?page=main&menuNo=1000
    - kosis_ipi_clean2.csv
* organise data by region
* Output: data/kosis_org_ipi.csv
====================================================================
*/

SELECT 
    *
FROM kosis_ipi_clean2
WHERE 산업별 = '총지수'                 -- 총지수만 필터링
