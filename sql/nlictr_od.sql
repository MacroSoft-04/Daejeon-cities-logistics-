WITH base AS(
    SELECT 
    *,
    ROW_NUMBER() OVER (
            PARTITION BY 연도
            ORDER BY 물동량_톤 DESC
        ) AS rank_num
    FROM nlictr_od_cargo_2019_2023
)
SELECT *
    FROM base
    WHERE rank_num < 4;