WITH category AS (
    SELECT DISTINCT 
        commodity
    FROM nlictr_com_cat
    WHERE commodity_category = '원자재 및 기초소재'
),
item AS (
    SELECT DISTINCT 
        commodity
    FROM nlictr_raw_meterial_detail
)

-- 1. LEFT JOIN (nlictr_com_cat 기준)
SELECT 
    c.commodity AS cat_commodity,
    i.commodity AS item_commodity,
    CASE 
        WHEN i.commodity IS NOT NULL THEN '매칭 (양쪽 존재)'
        ELSE 'nlictr_com_cat 에만 존재'
    END AS match_status
FROM category c
LEFT JOIN item i
    ON c.commodity = i.commodity

