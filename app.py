import streamlit as st
import pandas as pd
import random
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
# 增加一個 batch_id，用來強制清空所有輸入元件的狀態
if 'batch_id' not in st.session_state:
    st.session_state.batch_id = 0

# ==========================================
# 2. 登入介面
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 考生登入系統")
    user = st.text_input("帳號", value="student")
    pw = st.text_input("密碼", type="password", value="ipas123")
    if st.button("開始考試"):
        if user == "student" and pw == "ipas123":
            st.session_state.logged_in = True
            st.session_state.end_time = datetime.now() + timedelta(minutes=90)
            st.rerun()
        else:
            st.error("❌ 帳號或密碼錯誤")
    st.stop()

# ==========================================
# 3. 讀取與篩選題庫
# ==========================================
try:
    full_df = pd.read_excel("ai_quiz.xlsx", engine="openpyxl")
    full_df['答案'] = full_df['答案'].astype(str).str.upper().str.strip()
except Exception as e:
    st.error("⚠️ 找不到 'ai_quiz.xlsx'，請檢查檔案路徑。")
    st.stop()

# 側邊欄：領域選擇
all_domains = ["全部領域"] + sorted(full_df['題庫領域'].unique().tolist())
selected_domain = st.sidebar.selectbox("🎯 選擇考科領域", all_domains)

# 抽題邏輯
if "test_df" not in st.session_state:
    if selected_domain == "全部領域":
        pool = full_df
    else:
        pool = full_df[full_df['題庫領域'] == selected_domain]
    
    st.session_state.test_df = pool.sample(n=min(10, len(pool))).reset_index(drop=True)
    st.session_state.user_answers = {}

test_df = st.session_state.test_df

# ==========================================
# 4. 考試介面
# ==========================================
st.title(f"✍️ 模擬測驗：{selected_domain}")

with st.form("exam_form"):
    for i, row in test_df.iterrows():
        st.subheader(f"第 {i+1} 題 【{row['題型']}】")
        st.info(row['題幹'])
        
        q_type = row['題型']
        # 這裡決定選項的 Label
        opts_labels = ["A", "B", "C", "D"]
        
        # 顯示選項詳細內容 (解決重複出現 A 的問題)
        if q_type != "是非題":
            st.markdown(f"**A:** {row.get('選項-A','')}")
            st.markdown(f"**B:** {row.get('選項-B','')}")
            st.markdown(f"**C:** {row.get('選項-C','')}")
            st.markdown(f"**D:** {row.get('選項-D','')}")

        # 使用 batch_id 確保每次重新練習時 key 都是全新的，進而清空答案
        form_key = f"q_{st.session_state.batch_id}_{i}"

        if q_type == "複選題":
            # 複選題：使用 multiselect
            ans = st.multiselect("請選擇答案 (多選)", opts_labels, key=form_key, disabled=st.session_state.submitted)
            st.session_state.user_answers[i] = "".join(sorted(ans))
        elif q_type == "是非題":
            # 是非題：標籤改為 T / F
            ans = st.radio("請判斷對錯", ["T", "F"], index=None, key=form_key, disabled=st.session_state.submitted)
            st.session_state.user_answers[i] = ans
        else:
            # 單選題
            ans = st.radio("請選擇正確答案", opts_labels, index=None, key=form_key, disabled=st.session_state.submitted)
            st.session_state.user_answers[i] = ans
        
        st.divider()

    submit_btn = st.form_submit_button("🏁 提交考卷")
    if submit_btn:
        st.session_state.submitted = True
        st.rerun()

# ==========================================
# 5. 結果顯示與解析
# ==========================================
if st.session_state.submitted:
    st.header("📊 測驗結果")
    score = 0
    
    for i, row in test_df.iterrows():
        u_ans = st.session_state.user_answers.get(i, "")
        c_ans = str(row['答案'])
        
        if u_ans == c_ans:
            score += 1
            st.success(f"第 {i+1} 題：正確 ✅")
        else:
            st.error(f"第 {i+1} 題：錯誤 ❌")
            st.write(f"👉 您的答案：`{u_ans}` | 正確答案：`{c_ans}`")
            st.warning(f"💡 解析：{row.get('正確答案解釋', '無解析')}")
        st.divider()

    st.balloons()
    st.metric("總分", f"{(score/len(test_df))*100:.0f} / 100")

    # 重新練習按鈕：更新 batch_id 來清空所有元件狀態
    if st.button("🔄 再練 10 題 (清空並重新抽題)"):
        st.session_state.batch_id += 1 # 關鍵：改變 key 讓元件重置
        st.session_state.submitted = False
        if "test_df" in st.session_state:
            del st.session_state.test_df
        st.rerun()
