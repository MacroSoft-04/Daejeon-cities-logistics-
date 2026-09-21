/*
====================================================================
* Author:   Minseo Kim
* Purpose:  Attach an HS 부 (section) to each 류 row and compute
*           export/import shares by 지역 and 기간.
* Input:    data/processed/tradedata_2000_2025_cleaned.csv
*           data/processed/codebook_hs_section.csv
* Output:   Query result (not written to disk)
* Scope:    2000-2025, 7 regions
* Notes:    Shares are computed within each 지역-기간 group, not across
*           regions. Rows flagged 원자료없음 = True are zero-filled,
*           so they are not real zeros.
====================================================================
*/

SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name IN ('codebook_hs_section', 'tradedata_2000_2025_cleaned')
  AND column_name IN ('부코드', '류코드', '류_시작', '류_끝');

WITH sectioned AS (
    -- LEFT JOIN instead of CASE ... ELSE: an unmapped chapter surfaces as NULL
    -- rather than being silently absorbed into a catch-all section.
    SELECT
        t.*
        , m.부코드
        , m.부명_약칭
        , m.부명_공식
    FROM tradedata_2000_2025_cleaned t
    LEFT JOIN codebook_hs_section m
        -- CAST first: if HS코드 is ever loaded as an integer, '1' must become '01'.
        ON t.류코드 BETWEEN m.류_시작 AND m.류_끝
)
SELECT
        지역, 기간
    , LPAD(CAST(부코드 AS CHAR), 2, '0') AS 부코드 
    , 부명_약칭 AS 부명약칭
    , 부명_공식
    , LPAD(CAST(류코드 AS CHAR), 2, '0') AS 류코드
    , 품목약칭_TRASS AS 류명약칭
    , 품목명 AS 류명_공식
    , 수출건수, 수출금액
    -- Partition by 지역 as well: a 기간-only window would give each chapter's
    -- share of all seven regions combined.
    , ROUND(수출금액 * 100.0
            / NULLIF(SUM(수출금액) OVER (PARTITION BY 지역, 기간), 0), 2) AS 수출비중
    , 수입건수, 수입금액
    ,ROUND(수입금액 * 100.0
            / NULLIF(SUM(수입금액) OVER (PARTITION BY 지역, 기간), 0), 2) AS 수입비중
    , 무역수지, 원자료없음
FROM sectioned
ORDER BY 지역, 기간, 류코드;