WITH mapped_data AS ( 
    SELECT
        연도 AS year,
        품목 AS commodity,
        지역 AS city,
        구분 AS flow_type,
        물동량_톤 AS cargo_volume,
        -- 1. Commodity Category (English)
        CASE 
            -- 1. 농축수산물 및 신선식품 (Agriculture & Fresh Food)
            WHEN 품목 IN ('농산물', '축산물', '수산물', '임산물') 
                THEN '농축수산물 및 신선식품'

            -- 2. 소비재 및 생활용품 (Consumer Goods & Retail)
            WHEN 품목 IN (
                '음식료품', '담배제품', '섬유제품; 의복제외', 
                '의복, 의복 액세서리 및 모피제품', '가죽, 가방 및 신발제품', 
                '인쇄 및 기록매체'
            ) THEN '소비재 및 생활용품'

            -- 3. 원자재 및 기초소재 (Raw & Intermediate Materials)
            WHEN 품목 IN (
                '석탄광물', '석회석광물', '비금속광물', '비금속 광물제품',
                '제1차 금속 제품', '코크스, 연탄 및 석유정제품', '화합물 및 화학제품',
                '고무제품 및 플라스틱 제품', '목재 및 나무제품(가구제외)', '펄프, 종이 및 종이제품'
            ) THEN '원자재 및 기초소재'

            -- 4. 기계·전지·기계장비 (Machinery & Advanced Industry)
            WHEN 품목 IN (
                '전자부품, 컴퓨터, 영상, 음향 및 통신장비', '전기장비 제품', 
                '의료,정밀,광학기기및시계', '자동차 및 트레일러', '기타운송 장비', 
                '기타기계 및 장비제조품', '금속가공 제품:기계 및 가구제외', '가구 제품'
            ) THEN '제조업 및 장비'

            -- 5. 순환 자원 (Recycled Materials)
            WHEN 품목 LIKE '%재생재료%' 
                THEN '재생재료'

            -- 6. 기타 (Unclassified)
            ELSE '기타 화물'
        END AS commodity_category
    FROM nlictr_cargo_2019_2023
)
SELECT 
    *,
    -- 3. Region Category (Korean)
    CASE 
        WHEN city = '대전' THEN '대전시'
        WHEN city IN ('서울', '경기', '인천') THEN '수도권'
        WHEN city IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
        WHEN city IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
        WHEN city IN ('광주', '전북', '전남') THEN '호남권'
        ELSE '기타'
    END AS region_kr,

    -- 4. Region Category (English)
    CASE 
        WHEN city = '대전' THEN 'Daejeon'
        WHEN city IN ('서울', '경기', '인천') THEN 'Capital Area'
        WHEN city IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
        WHEN city IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
        WHEN city IN ('광주', '전북', '전남') THEN 'Honam'
        ELSE 'Others'
    END AS region_en
FROM mapped_data;