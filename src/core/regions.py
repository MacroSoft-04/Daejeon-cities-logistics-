"""Region keys shared by the KITA and 관세청 pipelines and the chart scripts."""

# 관세청 uses full names; KITA and the comparison codebook already use these short ones.
SIDO_SHORT = {
    "광주광역시": "광주",
    "대구광역시": "대구",
    "대전광역시": "대전",
    "부산광역시": "부산",
    "세종특별자치시": "세종",
    "충청남도": "충남",
    "충청북도": "충북",
}

COMBINED = "충남(세종 포함)"
COMBINED_SOURCE_NAME = "충청남도(세종특별자치시 포함)"
COMBINED_PARTS = ["충남", "세종"]

SCALE_GROUP = ["광주", "대구", "부산"]
ADJACENT_GROUP = ["충남", "충북", "세종"]
ADJACENT_CONSISTENT = [COMBINED, "충북"]

# 세종 launched 2012-07, so KITA's first full year without 연기군 in 충남 is 2013;
# from then on both sources put 충남 on today's boundary.
FIRST_COMMON_BOUNDARY_YEAR = 2013


def adjacent_regions(first_year):
    """Side by side when both sources agree on 충남; the combined series otherwise."""
    if first_year >= FIRST_COMMON_BOUNDARY_YEAR:
        return ADJACENT_GROUP
    return ADJACENT_CONSISTENT
