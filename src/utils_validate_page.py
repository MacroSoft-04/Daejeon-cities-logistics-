"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - find and validate selectors for the site crawling
* Input:
    - https://tradedata.go.kr/cts/index.do#
* Output:
    - tradedata_crawl.py
* Scope:        기간·대상·제외 범위와 그 이유
* Notes:        코드만 봐서는 알 수 없는 것
====================================================================
"""


def validate_selectors(selectors):
    print(f"\n<validate selectors>")
    for name, get_locator in selectors.items():
        locator = get_locator()

        is_visible = any(locator.nth(i).is_visible() for i in range(locator.count()))

        print(f"{name}: {is_visible}")


def find_hoverable_element(selectors):
    print(f"\n<find hoverable elemnt>")
    for name, get_locator in selectors.items():
        locator = get_locator()

        for i in range(locator.count()):
            element = locator.nth(i)

            if not element.is_visible():
                continue

            try:
                element.hover(timeout=1000)

                print(f"{name}: True")
                return element

            except Exception:
                continue
        print(f"{name}: False")

    raise RuntimeError("No visible and hoverable element was found.")
