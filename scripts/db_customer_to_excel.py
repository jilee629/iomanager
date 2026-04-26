#!/usr/bin/env -S uv run python

import sqlite3
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

def export_db_to_excel(db_path):
    try:
        # 1. DB 연결
        conn = sqlite3.connect(db_path)

        # 2. 실행할 SQL 쿼리
        query = """
        SELECT 
            C.phone_number AS "전화번호",
            C.visit_count AS "총방문횟수",
            C.last_visit_at AS "최근방문일",
            T.name AS "패스이름",
            P.remaining_count AS "남은횟수",
            P.expires_on AS "만료일"
        FROM iomanager_app_customer AS C
        LEFT JOIN iomanager_app_customerpass AS P ON C.id = P.customer_id
        LEFT JOIN iomanager_app_passtemplate AS T ON P.template_id = T.id
        WHERE P.remaining_count > 0;
        """

        # 3. Pandas를 사용하여 쿼리 결과를 데이터프레임으로 변환
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("조회된 데이터가 없습니다.")
            return

        # 4. 파일명 생성 (예: customer_report_20231027.xlsx)
        current_date = datetime.now().strftime("%Y%m%d")
        excel_filename = f"customer_report_{current_date}.xlsx"

        # 5. 엑셀로 저장 (index=False는 행 번호를 제외함)
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        
        print(f"성공! 엑셀 파일이 생성되었습니다: {excel_filename}")
        return excel_filename

    except Exception as e:
        print(f"오류 발생: {e}")
    
    finally:
        if conn:
            conn.close()

# 실행
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    db_file = os.path.join(BASE_DIR, 'db.sqlite3')
    saved_file = export_db_to_excel(db_file)
