import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time

# ---------------------------------------------------------
# 🔒 セキュリティ設定
# ---------------------------------------------------------
SIMPLE_PASSWORD = "focus2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 Login Required")
        password = st.text_input("パスワードを入力", type="password")
        if st.button("ログイン"):
            if password == SIMPLE_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
        st.stop()

check_password()

# ---------------------------------------------------------
# 🛠️ Googleスプレッドシート接続設定（ID指名版）
# ---------------------------------------------------------

# 👇👇👇 ここにコピーしたIDを貼ってください！ 👇👇👇
SHEET_ID = "1_voruG0wDD6TqhiXo1OE8RNNBM9N2zomPR0hWAV2apM"
# 👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆

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
        # ここを open_by_key に変更しました
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"エラー：スプレッドシートが開けません。IDと共有設定を確認してください。\n詳細: {e}")
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
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_dict["timestamp"] = now_str
    
    try:
        header = sheet.row_values(1)
        if not header:
            header = list(data_dict.keys())
            sheet.append_row(header)
    except:
        pass
        
    header = sheet.row_values(1)
    row = []
    for col in header:
        row.append(data_dict.get(col, ""))

    sheet.append_row(row)
    st.toast("✅ 記録しました！")
    time.sleep(1)
    st.rerun()

# ---------------------------------------------------------
# 🚀 アプリ本体
# ---------------------------------------------------------
st.set_page_config(page_title="Couple's Focus Orbit", page_icon="🪐")

st.title("🪐 Couple's Focus Orbit")
st.caption("6週間集中プロジェクト管制室")

# サイドバー
st.sidebar.header("👤 Pilot")
user_name = st.sidebar.radio("操縦士を選択", ["阿部", "あや"])

# タブ
tab1, tab2, tab3, tab4 = st.tabs(["🎯 宣言", "✅ 日次", "🔄 週次", "📊 グラフ"])

# --- Tab 1: 宣言と設計 ---
with tab1:
    st.header("🎯 Project Setup")
    
    # 接続確認リンク
    try:
        sheet = get_sheet()
        st.success(f"🔗 接続中のシートを確認 👉 [クリック]({sheet.url})")
    except:
        pass

    st.info("この6週間、何に命を燃やす？")
    
    with st.form("setup_form"):
        goal = st.text_input("たった一つの目標", placeholder="例：毎日4コマ漫画投稿")
        
        d_start = datetime.now().date()
        d_end = d_start + timedelta(weeks=6)
        
        st.write("期間設定")
        period_tuple = st.date_input("カレンダー選択", value=(d_start, d_end))
        
        not_to_do = st.text_area("除外リスト", placeholder="例：YouTubeを見ない")
        if_then = st.text_area("If-Thenルール", placeholder="例：朝起きたらPCを開く")
        reward = st.text_input("6週間後のご褒美", placeholder="例：お寿司")
        
        if st.form_submit_button("宣言を更新"):
            p_str = str(period_tuple)
            if isinstance(period_tuple, tuple) and len(period_tuple) == 2:
                p_str = f"{period_tuple[0]} 〜 {period_tuple[1]}"

            save_log({
                "type": "setup",
                "user": user_name,
                "goal": goal,
                "period": p_str,
                "not_to_do": not_to_do,
                "if_then": if_then,
                "reward": reward
            })

# --- Tab 2: 日々の運行 ---
with tab2:
    st.header("✅ Daily Check")
    st.write(f"今日の {user_name} の記録")
    
    with st.form("daily_form"):
        date = st.date_input("日付", datetime.now())
        check_if = st.checkbox("If-Thenルールを守れた？")
        check_ex = st.checkbox("除外リストに勝った？")
        memo = st.text_area("一言メモ", placeholder="感情・気づき...")
        
        if st.form_submit_button("日報を送信"):
            save_log({
                "type": "daily",
                "user": user_name,
                "date": str(date),
                "if_then_ok": "Yes" if check_if else "No",
                "exclusion_ok": "Yes" if check_ex else "No",
                "memo": memo
            })

# --- Tab 3: 週次メンテナンス ---
with tab3:
    st.header("🔄 Weekly Review")
    
    with st.form("weekly_form"):
        w_date = st.date_input("振り返り日", datetime.now())
        q1 = st.text_area("1. 事実と感情")
        q2 = st.text_area("2. 目標進捗")
        q3 = st.text_area("3. 環境評価")
        q4 = st.text_area("4. リソース活用")
        q5 = st.text_area("5. 次週の仮説")
        
        if st.form_submit_button("保存する"):
            save_log({
                "type": "weekly",
                "user": user_name,
                "date": str(w_date),
                "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5
            })

# --- Tab 4: ダッシュボード ---
with tab4:
    st.header("📊 Orbit Dashboard")
    
    df = load_data()
    
    if not df.empty:
        my_df = df[df["user"] == user_name]
        
        # 1. 宣言内容
        setup_df = my_df[my_df["type"] == "setup"]
        if not setup_df.empty:
            last = setup_df.iloc[-1]
            g_text = last.get('goal', '未設定')
            n_text = last.get('not_to_do', '未設定')
            r_text = last.get('reward', '未設定')
            p_text = last.get('period', '未設定')

            c1, c2 = st.columns(2)
            c1.success(f"🏆 目標：{g_text}")
            c2.warning(f"⛔ 禁止：{n_text}")
            st.info(f"🎁 ご褒美：{r_text}")
            st.caption(f"📅 期間：{p_text}")
            st.divider()
        
        # 2. グラフ化
        st.subheader("📈 日々の達成記録")
        daily_df = my_df[my_df["type"] == "daily"].copy()
        
        has_date = "date" in daily_df.columns
        has_ok = "if_then_ok" in daily_df.columns

        if not daily_df.empty and has_date and has_ok:
            try:
                daily_df["date"] = pd.to_datetime(daily_df["date"])
                daily_df = daily_df.sort_values("date")
                daily_df["達成"] = daily_df["if_then_ok"].apply(lambda x: 1 if x == "Yes" else 0)
                daily_df["日付"] = daily_df["date"].dt.strftime('%m/%d')
                st.bar_chart(daily_df, x="日付", y="達成", color="#00aa00")
            except:
                st.caption("データ収集中...")
        else:
            st.caption("データが集まるとここにグラフが表示されます。")

        # 3. 履歴リスト
        st.subheader("📝 最近の記録")
        cols = ["date", "type", "memo", "if_then_ok"]
        show_cols = [c for c in cols if c in df.columns]
        st.dataframe(df[show_cols].sort_index(ascending=False))
        
        st.divider()
        import random
        msgs = ["飽きは変化の兆しだ。", "ナメるな、俺の工夫。", "0から1より、1を育てろ。", "感情は羅針盤だ。", "書くことは、考えることだ。"]
        st.write(f"**「{random.choice(msgs)}」**")

    else:
        st.info("データがありません。「宣言」タブから入力を！")
