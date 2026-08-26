from utils_html import get_html
from pathlib import Path

base_dir = Path(".")
save_dir = base_dir / "data/raw"
save_dir.mkdir(parents=True, exist_ok=True)
target_path = save_dir / "kita_monthly_data.xls"


def kita_download_action(page):
    page.evaluate("""
        var input = document.getElementById('site_area_code') || document.querySelector('input[type="text"]');
        if (input) { input.value = '30'; }
    """)
    page.select_option("select[name='s_term_gb']", "M")
    page.select_option("select[name='s_monthsum_gb']", "1")
    page.select_option("select[name='s_measure']", "1000")

    page.evaluate("doSearchReset();")
    page.wait_for_timeout(3000)
    page.evaluate("if (window.mySheet1) { mySheet1.ShowTreeLevel(-1); }")
    page.wait_for_timeout(1500)

    with page.expect_download() as download_info:
        page.locator("a[title='엑셀다운']").click()

    download = download_info.value
    download.save_as(target_path)
    print(f"Downloaded successfully to {target_path}")


html_content = get_html(
    url="https://stat.kita.net/stat/kts/prod/ProdWholeDetailPopup.screen",
    referer_url="https://stat.kita.net",
    action_callback=kita_download_action,
)
