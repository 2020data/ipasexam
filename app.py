import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# 頁面基本設定
st.set_page_config(page_title="AI 應用規劃師 - 模擬考系統", layout="wide")

# ==========================================
# 1. 系統狀態初始化
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# ==========================================
# 2. 登入介面 (未登入時顯示)
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 考生登入系統")
    st.info("請輸入帳號密碼以開始測驗。")
    
    user = st.text_input("帳號 (預設: student)")
    pw = st.text_input("密碼 (預設: ipas123)", type="password")
    
    if st.button("開始考試"):
        if user == "student" and pw == "ipas123":
            st.session_state.logged_in = True
            # 設定考試時間為 90 分鐘
            st.session_state.end_time = datetime.now() + timedelta(minutes=90)
            st.rerun() # 成功後重整頁面
        else:
            st.error("❌ 帳號或密碼錯誤")
            
    # ⚠️ 核心防呆：如果還沒登入，程式執行到這裡就會停止，不會畫出下面的考卷
    st.stop() 

# ==========================================
# 3. 考試主程式 (已登入才會執行到這裡)
# ==========================================

# 側邊欄：登出與計時器
st.sidebar.title("⏳ 考試資訊")
if st.sidebar.button("🚪 登出系統"):
    st.session_state.logged_in = False
    st.session_state.submitted = False
    if "test_df" in st.session_state:
        del st.session_state.test_df
    st.rerun()

# 讀取題庫
try:
    full_df = pd.read_excel("ai_quiz.xlsx", engine="openpyxl")
except Exception as e:
    st.error("⚠️ 系統錯誤：找不到題庫檔案 'ai_quiz.xlsx'。")
    st.info("請確認檔案與 app.py 放在同一個資料夾，並且安裝了 openpyxl 套件。")
    st.stop()

# 隨機抽取 10 題並鎖定
if "test_df" not in st.session_state:
    st.session_state.test_df = full_df.sample(n=min(10, len(full_df))).reset_index(drop=True)
    st.session_state.user_answers = {}

test_df = st.session_state.test_df

# 計算剩餘時間
remaining = st.session_state.end_time - datetime.now()
seconds_left = int(remaining.total_seconds())

if seconds_left <= 0 and not st.session_state.submitted:
    st.session_state.submitted = True
    st.sidebar.error("⏰ 時間到！系統已自動交卷。")
    st.rerun()

if not st.session_state.submitted:
    mins, secs = divmod(max(0, seconds_left), 60)
    st.sidebar.metric("剩餘時間", f"{mins:02d}:{secs:02d}")

# 考試畫面渲染
st.title("🚀 AI 應用規劃師 - 隨機 10 題測驗")
st.write("請仔細閱讀題目，完成後至頁面最下方點擊「提交考卷」。")

with st.form("exam_form"):
    for i, row in test_df.iterrows():
        st.write(f"### 第 {i+1} 題 ({row['題型']})")
        st.info(row['題幹'])
        
        # 處理選項
        opts = ["A", "B", "C", "D"] if row['題型'] != "是非題" else ["T", "F"]
        if row['題型'] != "是非題":
            st.write(f"(A) {row.get('選項-A', '')}  \n(B) {row.get('選項-B', '')}  \n(C) {row.get('選項-C', '')}  \n(D) {row.get('選項-D', '')}")
        
        # 保留作答紀錄
        prev_ans = st.session_state.user_answers.get(i)
        idx = opts.index(prev_ans) if prev_ans in opts else None
        
        ans = st.radio(f"請選擇答案 (Q{i+1})", opts, index=idx, key=f"q_{i}", disabled=st.session_state.submitted)
        st.session_state.user_answers[i] = ans
        st.divider()
    
    # 提交按鈕
    submit_btn = st.form_submit_button("🏁 提交考卷", disabled=st.session_state.submitted)
    if submit_btn and not st.session_state.submitted:
        st.session_state.submitted = True
        st.rerun()

# ==========================================
# 4. 顯示成績與解析
# ==========================================
if st.session_state.submitted:
    st.header("📊 評分報告")
    score = 0
    
    for i, row in test_df.iterrows():
        u_ans = st.session_state.user_answers.get(i)
        c_ans = str(row['答案']).strip().upper()
        
        if u_ans == c_ans:
            score += 1
            st.success(f"第 {i+1} 題：正確 ✅ (您的答案: {u_ans})")
        else:
            st.error(f"第 {i+1} 題：錯誤 ❌ (您的答案: {u_ans}, 正確答案: {c_ans})")
            st.warning(f"💡 解析：{row.get('正確答案解釋', '無解析')}")
    
    final_score = (score / len(test_df)) * 100
    st.metric("本輪最終得分", f"{final_score:.0f} / 100")
    
    if st.button("🔄 再練 10 題 (產生新題目)"):
        del st.session_state.test_df
        st.session_state.user_answers = {}
        st.session_state.submitted = False
        st.session_state.end_time = datetime.now() + timedelta(minutes=90)
        st.rerun()
