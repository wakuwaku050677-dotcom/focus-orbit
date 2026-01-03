import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time

# ---------------------------------------------------------
# 🔒 セキュリティ設定（簡易パスワード）
# ---------------------------------------------------------
SIMPLE_PASSWORD = "focus2026"

def check_password():
    """パスワード認証機能"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 Login Required")
        password = st.text_input("パスワードを入力してください", type="password")
        if st.button("ログイン"):
            if password == SIMPLE_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
        st.stop()  # 認証されるまでここでストップ

# 認証チェック実行
check_password()

# ---------------------------------------------------------
# 🛠️ Googleスプレッドシート接続設定
# ---------------------------------------------------------
SHEET_NAME = "focus_orbit_db"

@st.cache_resource
def get_gspread_client():
    key_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in key_dict:
        key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)
    return client

def get_sheet():
    client = get_gspread_client()
    try:
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except gspread.SpreadsheetNotFound:
        st.error(f"エラー：スプレッドシート '{SHEET_NAME}' が見つかりません。")
        st.stop()

def load_data():
    sheet = get_sheet()
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
             return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()

def save_log(data_dict):
    sheet = get_sheet()
    data_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        header = sheet.row_values(1)
        if not header:
            header = list(data_dict.keys())
            sheet.append_row(header)
    except:
        pass
        
    header = sheet.row_values(1)
    # 不足しているカラムがあれば追加（柔軟性確保）
    for col in data_dict.keys():
        if col not in header:
            pass

    row = [data_dict.get(col, "") for col in header]
    sheet.append_row(row)
    st.toast("✅ 記録しました！")
    time.sleep(1)
    st.rerun()

# ---------------------------------------------------------
# 🚀 アプリ本体：Couple's Focus Orbit
# ---------------------------------------------------------
st.set_page_config(page_title="Couple's Focus Orbit", page_icon="🪐")

st.title("🪐 Couple's Focus Orbit")
st.caption("6週間集中プロジェクト管制室")

# サイドバー：ユーザー選択
st.sidebar.header("👤 Pilot")
user_name = st.sidebar.radio("操縦士を選択", ["阿部", "あや"])

# タブ構成
tab1, tab2, tab3, tab4 = st.tabs(["🎯 宣言・設計", "✅ 日々の運行", "🔄 週次メンテ", "📊 ダッシュボード"])

# --- Tab 1: 宣言と設計 ---
with tab1:
    st.header("🎯 Project Setup")
    st.info("この6週間、何に命を燃やす？")
    
    with st.form("setup_form"):
        goal = st.text_input("たった一つの目標", placeholder="例：毎日インスタに4コマ漫画投稿")
        
        # 変更点：カレンダー入力に変更
        # デフォルト期間（今日から6週間）
        default_start = datetime.now().date()
        default_end = default_start + timedelta(weeks=6)
        
        st.write("期間設定（開始日と終了日を選択）")
        period_tuple = st.date_input(
            "カレンダー",
            value=(default_start, default_end),
            help="カレンダーで開始日と終了日をクリックしてください"
        )
        
        not_to_do = st.text_area("除外リスト（やらないこと）", placeholder="例：YouTubeを見ない、ダラダラSNSしない")
        if_then = st.text_area("If-Thenルール", placeholder="例：朝起きたら → すぐにPCを開く")
        reward = st.text_input("6週間後のご褒美", placeholder="例：美味しいお寿司！")
        
        if st.form_submit_button("宣言を更新する"):
            # 期間を文字列に変換
            if isinstance(period_tuple, tuple) and len(period_tuple) == 2:
                period_str = f"{period_tuple[0]} 〜 {period_tuple[1]}"
            elif isinstance(period_tuple, tuple) and len(period_tuple) == 1:
                period_str = f"{period_tuple[0]} 〜 (未定)"
            else:
                period_str = str(period_tuple)

            save_log({
                "type": "setup",
                "user": user_name,
                "goal": goal,
                "period": period_str,
                "not_to_do": not_to_do,
                "if_then": if_then,
                "reward": reward
            })

# --- Tab 2: 日々の運行 ---
with tab2:
    st.header("✅ Daily Check")
    st.write(f"今日の {user_name} の運行記録")
    
    with st.form("daily_form"):
        date = st.date_input("日付", datetime.now())
        check_if_then = st.checkbox("If-Thenルールを守れた？")
        check_exclusion = st.checkbox("除外リスト（誘惑）に勝った？")
        memo = st.text_area("一言メモ（感情・気づき）", placeholder="今日はここが辛かった、逆にここが良かった...")
        
        if st.form_submit_button("日報を送信"):
            save_log({
                "type": "daily",
                "user": user_name,
                "date": str(date),
                "if_then_ok": "Yes" if check_if_then else "No",
                "exclusion_ok": "Yes" if check_exclusion else "No",
                "memo": memo
            })

# --- Tab 3: 週次メンテナンス ---
with tab3:
    st.header("🔄 Weekly Review")
    st.write("1週間を振り返り、軌道を修正する")
    
    with st.form("weekly_form"):
        w_date = st.date_input("振り返り日",
