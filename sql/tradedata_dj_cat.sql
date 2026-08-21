SELECT
    LPAD(HS코드, 2, '0') AS hs_chapter,
    품목명 AS product_name
FROM tradedata_dj_2020_2025_raw

WITH prep AS (
    SELECT
        기간                          AS year
        , LPAD(HS코드, 2, '0')        AS hs_chapter
        , 품목명                       AS product_name
        , 수출건수                     AS export_cnt
        , 수출금액                     AS export_usd
        , 수입건수                     AS import_cnt
        , 수입금액                     AS import_usd
        , 무역수지                     AS balance
    FROM tradedata_dj_2020_2025_raw
),
sectioned AS (
    SELECT
        *
        , CASE
            WHEN hs_chapter BETWEEN '01' AND '05' THEN '01'
            WHEN hs_chapter BETWEEN '06' AND '14' THEN '02'
            WHEN hs_chapter = '15'                THEN '03'
            WHEN hs_chapter BETWEEN '16' AND '24' THEN '04'
            WHEN hs_chapter BETWEEN '25' AND '27' THEN '05'
            WHEN hs_chapter BETWEEN '28' AND '38' THEN '06'
            WHEN hs_chapter BETWEEN '39' AND '40' THEN '07'
            WHEN hs_chapter BETWEEN '41' AND '43' THEN '08'
            WHEN hs_chapter BETWEEN '44' AND '46' THEN '09'
            WHEN hs_chapter BETWEEN '47' AND '49' THEN '10'
            WHEN hs_chapter BETWEEN '50' AND '63' THEN '11'
            WHEN hs_chapter BETWEEN '64' AND '67' THEN '12'
            WHEN hs_chapter BETWEEN '68' AND '70' THEN '13'
            WHEN hs_chapter = '71'                THEN '14'
            WHEN hs_chapter BETWEEN '72' AND '83' THEN '15'
            WHEN hs_chapter BETWEEN '84' AND '85' THEN '16'
            WHEN hs_chapter BETWEEN '86' AND '89' THEN '17'
            WHEN hs_chapter BETWEEN '90' AND '92' THEN '18'
            WHEN hs_chapter = '93'                THEN '19'
            WHEN hs_chapter BETWEEN '94' AND '96' THEN '20'
            ELSE '21'
          END AS hs_section
    FROM prep
),
named AS(
    SELECT
    *
    , CASE hs_section
        WHEN '01' THEN '동물 및 동물성 생산품'
        WHEN '02' THEN '식물성 생산품'
        WHEN '03' THEN '동식물성 유지류'
        WHEN '04' THEN '조제식품류'
        WHEN '05' THEN '광물성 생산품'
        WHEN '06' THEN '화학공업 제품'
        WHEN '07' THEN '플라스틱 및 고무 제품'
        WHEN '08' THEN '가죽 및 모피 제품'
        WHEN '09' THEN '목재 및 목재 제품'
        WHEN '10' THEN '펄프 및 종이 제품'
        WHEN '11' THEN '섬유 및 섬유 제품'
        WHEN '12' THEN '신발, 모자, 우산 등'
        WHEN '13' THEN '석재, 유리 및 도자기'
        WHEN '14' THEN '귀금속 및 보석류'
        WHEN '15' THEN '비금속 및 그 제품'
        WHEN '16' THEN '기계 및 전기기기'
        WHEN '17' THEN '수송기기'
        WHEN '18' THEN '광학, 정밀, 의료기기'
        WHEN '19' THEN '무기 및 탄약'
        WHEN '20' THEN '잡품(가구, 장난감 등)'
        ELSE '특수품 및 기타'
      END AS section_name
FROM sectioned)
SELECT
    year,
    hs_section,
    section_name,
    hs_chapter,
    product_name,
    export_cnt,
    export_usd,
    ROUND(export_usd * 100.0 / SUM(export_usd) OVER (PARTITION BY year), 2) AS export_ratio,
    import_cnt,
    import_usd,
    ROUND(import_usd * 100.0 / SUM(import_usd) OVER (PARTITION BY year), 2) AS import_ratio,
    balance
FROM named;
