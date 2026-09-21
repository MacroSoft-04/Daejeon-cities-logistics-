/*
====================================================================
* Author:   Minseo Kim
* Purpose:  Verify the 류 -> 부 mapping before it is joined, since a
*           range join fails silently in both directions.
* Input:    data/processed/tradedata_2000_2025_cleaned.csv
*           data/processed/codebook_hs_section.csv
* Output:   Query results only. Both should return 0 rows.
* Scope:    Validates the 류코드 values present in the cleaned file,
*           not the codebook on its own. Sections with no chapters and
*           reversed ranges (류_시작 > 류_끝) are out of scope because
*           the join never reaches them.
* Notes:    Query 1 catches gaps: an unmapped 류 gets a NULL 부코드 from
*           the LEFT JOIN in tradedata_section.sql, which no error
*           surfaces. 
            Query 2 catches overlaps: a 류 inside two ranges
*           is emitted twice, inflating row counts and skewing the
*           수출비중/수입비중 denominators.
*
*           Run manually after either the codebook or the cleaned file
*           changes. 류코드, 류_시작, 류_끝 are all bigint, so no LPAD
*           or CAST is needed for the comparison.
====================================================================
*/

-- 1) Chapters in the data with no section (should return 0 rows).
SELECT DISTINCT t.류코드, t.품목명
FROM tradedata_2000_2025_cleaned t
WHERE NOT EXISTS (
    SELECT 1 FROM codebook_hs_section m
    WHERE t.류코드 BETWEEN m.류_시작 AND m.류_끝
);

-- 2) Chapters matched by more than one section, i.e. overlapping ranges (should return 0 rows).
SELECT c.류코드, COUNT(*) AS 류코드_개수
FROM (SELECT DISTINCT 류코드 FROM tradedata_2000_2025_cleaned) c
JOIN codebook_hs_section m
  ON c.류코드 BETWEEN m.류_시작 AND m.류_끝
GROUP BY c.류코드
HAVING COUNT(*) > 1;