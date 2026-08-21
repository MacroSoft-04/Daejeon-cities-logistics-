-- ====================================================================
-- Author: Minseo Kim
-- Source: tradedata_dj_2020_2025 (관세청 무역통계, HS 부/류별 수출입)
-- Output: year x [기계 및 전기기기 | 수송기기 | 기타] with export/import
--         totals, shares, and the label material for the 기타 bucket.
-- ====================================================================

WITH base_data AS (
    SELECT
        year,
        section_name AS orig_section,
        CASE
            WHEN section_name IN ('기계 및 전기기기', '수송기기') THEN section_name
            ELSE '기타'
        END AS section_name,
        SUM(export_usd) AS export_usd,
        SUM(import_usd) AS import_usd
    FROM tradedata_dj_2020_2025
    GROUP BY year, section_name
),

ranked_data AS (
    -- Rank and count within the collapsed group so the chart legend can name
    -- what the 기타 bucket holds without re-reading the ungrouped source.
    SELECT
        year,
        orig_section,
        section_name,
        export_usd,
        import_usd,
        ROW_NUMBER() OVER (
            PARTITION BY year, section_name
            ORDER BY export_usd DESC
        ) AS sub_rank,
        COUNT(*) OVER (
            PARTITION BY year, section_name
        ) AS sub_section_count
    FROM base_data
),

aggregated_data AS (
    SELECT
        year,
        section_name,
        SUM(export_usd) AS export_usd,
        SUM(import_usd) AS import_usd,
        MAX(CASE WHEN section_name = '기타' THEN sub_section_count END) AS other_section_count,
        MAX(CASE WHEN section_name = '기타' AND sub_rank = 1 THEN orig_section END) AS other_top_section
    FROM ranked_data
    GROUP BY year, section_name
)

SELECT
    year,
    section_name,
    export_usd,
    import_usd,
    export_usd - import_usd AS balance_usd,
    -- Exports and imports are shared against their own yearly totals; a single
    -- combined denominator would make each side look smaller than it is.
    ROUND(export_usd * 100.0 / SUM(export_usd) OVER (PARTITION BY year), 2) AS export_ratio,
    ROUND(import_usd * 100.0 / SUM(import_usd) OVER (PARTITION BY year), 2) AS import_ratio,
    other_section_count,
    other_top_section
FROM aggregated_data
ORDER BY
    year ASC,
    CASE WHEN section_name = '기타' THEN 1 ELSE 0 END ASC,
    export_ratio DESC;