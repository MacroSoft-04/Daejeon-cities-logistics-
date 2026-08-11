SELECT
    LPAD(HS코드, 2, '0') AS hs_chapter,
    품목명 AS product_name
FROM tradedata_dj_2020_2026_raw



WITH prep_data AS (
    -- 1단계: HS 코드를 2자리 문자열(hs_chapter)로 정규화
    SELECT 
        기간 AS year
        , 지역 AS region
        , LPAD(HS코드, 2, '0') AS hs_chapter
        , 수출금액 AS sales
    FROM tradedata_dj_2020_2026_raw
),
mapped_section AS (
    -- 2단계: hs_chapter 기준 HS Section(부) 번호 매핑
    SELECT 
        year
        , hs_chapter
        , sales
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
    FROM prep_data
),
final_section AS (
    -- 3단계: HS Section 코드 기준 한글 명칭 매핑
    SELECT 
        year
        , hs_section
        , CASE 
            WHEN hs_section = '01' THEN '동물 및 동물성 생산품'
            WHEN hs_section = '02' THEN '식물성 생산품'
            WHEN hs_section = '03' THEN '동식물성 유지류'
            WHEN hs_section = '04' THEN '조제식품류'
            WHEN hs_section = '05' THEN '광물성 생산품'
            WHEN hs_section = '06' THEN '화학공업 제품'
            WHEN hs_section = '07' THEN '플라스틱 및 고무 제품'
            WHEN hs_section = '08' THEN '가죽 및 모피 제품'
            WHEN hs_section = '09' THEN '목재 및 목재 제품'
            WHEN hs_section = '10' THEN '펄프 및 종이 제품'
            WHEN hs_section = '11' THEN '섬유 및 섬유 제품'
            WHEN hs_section = '12' THEN '신발, 모자, 우산 등'
            WHEN hs_section = '13' THEN '석재, 유리 및 도자기'
            WHEN hs_section = '14' THEN '귀금속 및 보석류'
            WHEN hs_section = '15' THEN '비금속 및 그 제품'
            WHEN hs_section = '16' THEN '기계 및 전기기기'
            WHEN hs_section = '17' THEN '수송기기'
            WHEN hs_section = '18' THEN '광학, 정밀, 의료기기'
            WHEN hs_section = '19' THEN '무기 및 탄약'
            WHEN hs_section = '20' THEN '잡품(가구, 장난감 등)'
            ELSE '특수품 및 기타'
          END AS section_name
        , hs_chapter
        , sales
    FROM mapped_section
)

SELECT * FROM final_section;