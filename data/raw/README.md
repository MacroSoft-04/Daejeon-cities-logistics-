# 원본 데이터 저장소

| 파일 | 출처 | 조회 조건 | 받은 날짜 | 저장소 포함 | post-process |
|---|---|---|---|---|---|
| tradedata_dj_20.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| tradedata_dj_21.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| tradedata_dj_22.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| tradedata_dj_23.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| tradedata_dj_24.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| tradedata_dj_25.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| tradedata_dj_26.csv | 관세청 무역통계 tradedata.go.kr | 지역별 실적 > 대전 > HS 부/류 | 2026-08-12 | O | tradedata_dj_2020_2026.csv |
| nlic_od_matrix_2022.csv | NLIC 전국화물통행실태조사 홈페이지 | 물류통계 > 내륙화물통계 > 도로 > O/D별 수송실적 | 2022-08-14 | O | nlic_od_long_2022.csv |
| nlic_commodity_matrix_2022.csv | NLIC 전국화물통행실태조사 홈페이지 | 물류통계 > 내륙화물통계 > 도로 > 품목별 화물수송실적 | 2022-08-14 | O | nlic_commodity_long_2022.csv |
| 시도·산업별_사업체수__종사자수_및_매출액_’20___20260815082431.csv | KOSIS 국가통계포털 kosis.kr | 국내통계 > 주제별 통계 > 경제일반/경기 > 전국 사업체 조사 > 등록기반 > 11차 개정 > 시도·산업별 사업체수, 종사자수 및 매출액(’20~ )| 2022-08-14 | O | estab_survey_daejeon_long.csv |
| 시도_시군구__산업분류별_주요지표_10명_이상__20260814140423.csv | KOSIS 국가통계포털 kosis.kr | 국내통계 > 주제별 통계 > 광업/제조업 > 광업제조업조사 > 산업편 > 11차 산업분류 개정 > 시도(시군구)/산업분류별 주요지표(10명 이상)| 2022-08-14 | O | mining_mfg_by_sido_long.csv |

- 전국사업체조사: 2020년은 조사 시기가 상이(6~7월/35일 vs 2~3월/25일)하여 제외
- 광업제조업조사: 2020년은 경제총조사 실시연도로 조사 주체가 달라 제외

### 단년도 기준의 타당성

도입부 차트(09)는 2024년 단일 연도 기준이다. 단년도 노이즈 여부를
확인한 결과 제조업 격차의 표준편차는 0.19%p, 선정 산업 집합은 4년
평균 기준과 완전히 일치했다.

재현: `python src/validation.py gap_stability`