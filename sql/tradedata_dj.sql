SELECT *,
    ROW_NUMBER() OVER (
            PARTITION BY region_kr, flow_type 
            ORDER BY ABS(gap_21_22_vol) DESC
        ) AS rank_numSUBSTRING_INDEX(SUBSTRING_INDEX(기간, '-', 1), '.', 1) AS 연도,

FROM tradedata_dj_2020_2026;