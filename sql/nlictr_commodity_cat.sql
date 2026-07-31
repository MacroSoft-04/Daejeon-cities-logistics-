WITH mapped_data AS ( 
    SELECT
        *,
        -- 1. Commodity Category (English)
        CASE 
            WHEN 품목 IN (
                '음식료품', '섬유제품; 의복제외', '의복, 의복 액세서리 및 모피제품', 
                '가죽, 가방 및 신발제품', '가구 제품', '기타제품', '인쇄 및 기록매체'
            ) THEN 'Consumer & E-Commerce'

            WHEN 품목 IN (
                '농산물', '축산물', '수산물', '임산물'
            ) THEN 'Agriculture & Fresh Food'

            WHEN 품목 IN (
                '비금속 광물제품', '비금속광물', '석탄광물', '석회석광물', 
                '제1차 금속 제품', '코크스, 연탄 및 석유정제품', '화합물 및 화학제품'
            ) THEN 'Heavy Industry & Raw Materials'

            WHEN 품목 IN (
                '전자부품, 컴퓨터, 영상, 음향 및 통신장비', '전기장비 제품', 
                '의료,정밀,광학기기및시계', '자동차 및 트레일러', '기타운송 장비', 
                '기타기계 및 장비제조품', '금속가공 제품:기계 및 가구제외', 
                '고무제품 및 플라스틱 제품', '목재 및 나무제품(가구제외)', '펄프, 종이 및 종이제품'
            ) THEN 'Manufacturing & Equipment'

            WHEN 품목 LIKE '%재생재료%' THEN 'Recycled Materials'
            
            ELSE 'Other Bulk Cargo'
        END AS commodity_cat_en,

        -- 2. Commodity Category (Korean)
        CASE 
            WHEN 품목 IN (
                '음식료품', '섬유제품; 의복제외', '의복, 의복 액세서리 및 모피제품', 
                '가죽, 가방 및 신발제품', '가구 제품', '기타제품', '인쇄 및 기록매체'
            ) THEN '소비재 및 이커머스'

            WHEN 품목 IN (
                '농산물', '축산물', '수산물', '임산물'
            ) THEN '농축수산물 및 신선식품'

            WHEN 품목 IN (
                '비금속 광물제품', '비금속광물', '석탄광물', '석회석광물', 
                '제1차 금속 제품', '코크스, 연탄 및 석유정제품', '화합물 및 화학제품'
            ) THEN '중화학 및 원자재'

            WHEN 품목 IN (
                '전자부품, 컴퓨터, 영상, 음향 및 통신장비', '전기장비 제품', 
                '의료,정밀,광학기기및시계', '자동차 및 트레일러', '기타운송 장비', 
                '기타기계 및 장비제조품', '금속가공 제품:기계 및 가구제외', 
                '고무제품 및 플라스틱 제품', '목재 및 나무제품(가구제외)', '펄프, 종이 및 종이제품'
            ) THEN '제조업 및 장비'

            WHEN 품목 LIKE '%재생재료%' THEN '재생재료'
            
            ELSE '기타 화물'
        END AS commodity_cat_kr
    FROM nlic_cargo_2019_2023
)
SELECT 
    *,
    -- 3. Region Category (Korean)
    CASE 
        WHEN 지역 = '대전' THEN '대전시'
        WHEN 지역 IN ('서울', '경기', '인천') THEN '수도권'
        WHEN 지역 IN ('세종', '충북', '충남') THEN '충청권(대전제외)'
        WHEN 지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
        WHEN 지역 IN ('광주', '전북', '전남') THEN '호남권'
        ELSE '기타'
    END AS region_kr,

    -- 4. Region Category (English)
    CASE 
        WHEN 지역 = '대전' THEN 'Daejeon'
        WHEN 지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
        WHEN 지역 IN ('세종', '충북', '충남') THEN 'Chungcheong(excl. DJ)'
        WHEN 지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
        WHEN 지역 IN ('광주', '전북', '전남') THEN 'Honam'
        ELSE 'Others'
    END AS region_en
FROM mapped_data;