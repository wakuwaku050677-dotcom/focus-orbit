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
# シート名（間違えないように！）
SHEET_NAME = "focus_orbit_db"

@st.cache_resource
def get_gspread_client():
    # Secretsから辞書として読み込む
    key_dict = dict(st.secrets["gcp_service_account"])
    
    # 秘密鍵の改行コード修正（エラー回避）
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
        st.error(f"エラー：スプレッドシート '{SHEET_NAME}' が見つかりません。共有設定と名前を確認してください。")
        st.stop()

# データの読み書き関数
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
    """データをスプレッドシートに追加する"""
    sheet = get_sheet()
    
    # タイムスタンプを追加
    data_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # スプレッドシートのヘッダーがなければ作成（初回のみ）
    try:
        header = sheet.row_values(1)
        if not header:
            header = list(data_dict.keys())
            sheet.append_row(header)
    except:
        pass
        
    # 現在のヘッダーに合わせて値を並べる
    header = sheet.row_values(1)
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
        period = st.text_input("期間", placeholder="例：2026/01/05 〜 2026/02/15")
        not_to_do = st.text_area("除外リスト（やらないこと）", placeholder="例：YouTubeを見ない、ダラダラSNSしない")
        if_then = st.text_area("If-Thenルール", placeholder="例：朝起きたら → すぐにPCを開く")
        reward = st.text_input("6週間後のご褒美", placeholder="例：美味しいお寿司！")
        
        if st.form_submit_button("宣言を更新する"):
            # 設定用の特別なログとして保存
            save_log({
                "type": "setup",
                "user": user_name,
                "goal": goal,
                "period": period,
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
        w_date = st.date_input("振り返り日", datetime.now())
        q1 = st.text_area("1. 事実と感情（何をした？どう感じた？）")
        q2 = st.text_area("2. 目標進捗（理想に近づいている？）")
        q3 = st.text_area("3. 環境評価（ツールや場所は適切？）")
        q4 = st.text_area("4. リソース活用（AIや体験を活かせた？）")
        q5 = st.text_area("5. 次週の仮説（来週の実験と対策は？）")
        
        if st.form_submit_button("週次レビューを保存"):
            save_log({
                "type": "weekly",
                "user": user_name,
                "date": str(w_date),
                "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5
            })

# --- Tab 4: ダッシュボード ---
with tab4:
    st.header("📊 Orbit Dashboard")
    
    # データを読み込み
    df = load_data()
    
    if not df.empty:
        # 自分のデータだけ抽出
        my_df = df[df["user"] == user_name]
        
        # 最新の宣言を表示
        setup_df = my_df[my_df["type"] == "setup"]
        if not setup_df.empty:
            last_setup = setup_df.iloc[-1]
            st.success(f"🏆 目標：{last_setup.get('goal', '未設定')}")
            st.warning(f"⛔ 禁止：{last_setup.get('not_to_do', '未設定')}")
        
        # 履歴表示
        st.subheader("📝 最近の記録")
        display_cols = ["date", "type", "memo", "if_then_ok"]
        # 存在する列だけ表示
        existing_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[existing_cols].sort_index(ascending=False))
        
        # 励ましメッセージ
        st.divider()
        st.caption("🤖 Message from Control Tower:")
        import random
        msgs = [
            "飽きは変化の兆しだ。恐れるな。",
            "ナメるな、俺の工夫。",
            "0から1より、1を育てろ。",
            "感情は羅針盤だ。無視するな。",
            "書くことは、考えることだ。"
        ]
        st.write(f"**「{random.choice(msgs)}」**")
    else:
        st.info("まだデータがありません。「宣言・設計」タブから入力を始めましょう！")
