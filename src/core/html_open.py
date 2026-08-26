import webbrowser
import pandas as pd

# 1. summary.csv 파일 읽기
df = pd.read_csv("national_summary.csv")

# 2. DataFrame을 HTML 표로 변환하여 summary.html 저장
df.to_html("national_summary.html", index=False)

# 3. 변환된 HTML 파일 브라우저로 실행
webbrowser.open("national_summary.html")
