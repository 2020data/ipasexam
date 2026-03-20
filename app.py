import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 頁面基本設定
st.set_page_config(page_title="AI 應用規劃師 - 專業模擬考", layout="wide")

# ==========================================
# 1. 系統狀態初始化
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

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
# 3. 資料讀取與篩選
# ==========================================
try:
    full_df = pd.read_excel("ai_quiz.xlsx", engine="openpyxl")
    # 確保答案欄位是字串並轉大寫
    full_df['答案'] = full_df['答案'].astype(str).str.upper().str.strip()
except Exception as e:
    st.error(f"⚠️ 讀取題庫失敗：{e}")
    st.stop()

# 側邊欄：功能設定
st.sidebar.title("🛠️ 考試設定")

# 領域篩選器
all_domains = ["全部領域"] + sorted(full_df['題庫領域'].unique().tolist())
selected_domain = st.sidebar.selectbox("選擇考試領域", all_domains)

# 如果更換領域，清除目前的題目重新抽題
if "current_domain" not in st.session_state or st.session_state.current_domain != selected_domain:
    st.session_state.current_domain = selected_domain
    if "test_df" in st.session_state:
        del st.session_state.test_df
        st.session_state.user_answers = {}
        st.session_state.submitted = False

# 抽題邏輯
if "test_df" not in st.session_state:
    if selected_domain == "全部領域":
        pool = full_df
    else:
        pool = full_df[full_df['題庫領域'] == selected_domain]
    
    st.session_state.test_df = pool.sample(n=min(10, len(pool))).reset_index(drop=True)

test_df = st.session_state.test_df

# ==========================================
# 4. 考試畫面
# ==========================================
st.title(f"🚀 AI 應用規劃師 - {selected_domain} (10題)")

with st.form("exam_form"):
    for i, row in test_df.iterrows():
        st.write(f"### 第 {i+1} 題 | 【{row['題型']}】")
        st.info(f"**[{row['題庫領域']}]** {row['題幹']}")
        
        q_type = row['題型']
        options = ["A", "B", "C", "D"]
        
        # 顯示選項內容
        if q_type != "是非題":
            st.write(f"(A) {row.get('選項-A', '')}  \n(B) {row.get('選項-B', '')}  \n(C) {row.get('選項-C', '')}  \n(D) {row.get('選項-D', '')}")
        
        # 根據題型提供不同的輸入組件
        if q_type == "複選題":
            # 複選題使用 multiselect
            ans = st.multiselect(f"請選擇答案 (多選) - Q{i+1}", options, key=f"q_{i}", disabled=st.session_state.submitted)
            # 將選中的 list 轉為字串排序，例如 ['B', 'A'] -> 'AB'
            st.session_state.user_answers[i] = "".join(sorted(ans))
        
        elif q_type == "是非題":
            ans = st.radio(f"請選擇 (O/X) - Q{i+1}", ["T", "F"], index=None, key=f"q_{i}", disabled=st.session_state.submitted)
            st.session_state.user_answers[i] = ans
            
        else: # 單選題
            ans = st.radio(f"請選擇答案 (單選) - Q{i+1}", options, index=None, key=f"q_{i}", disabled=st.session_state.submitted)
            st.session_state.user_answers[i] = ans
            
        st.divider()

    submit_btn = st.form_submit_button("🏁 提交考卷")
    if submit_btn:
        st.session_state.submitted = True
        st.rerun()

# ==========================================
# 5. 成績結算與詳細解析
# ==========================================
if st.session_state.submitted:
    st.header("📊 評分報告與解析")
    score = 0
    
    for i, row in test_df.iterrows():
        u_ans = st.session_state.user_answers.get(i, "")
        c_ans = str(row['答案']) # 正確答案
        
        # 判斷邏輯：複選題需字串完全符合 (例如 "ABC" == "ABC")
        is_correct = (u_ans == c_ans)
        
        if is_correct:
            score += 1
            st.success(f"✅ 第 {i+1} 題 正確！")
        else:
            st.error(f"❌ 第 {i+1} 題 錯誤")
            
        # 顯示詳細對照表
        cols = st.columns(2)
        cols[0].write(f"**您的答案：** `{u_ans if u_ans else '未作答'}`")
        cols[1].write(f"**正確答案：** `{c_ans}`")
        
        with st.expander(f"查看第 {i+1} 題解析"):
            st.write(f"**解析：** {row.get('正確答案解釋', '暫無詳細解析。')}")
        st.divider()

    # 計算總分
    final_score = (score / len(test_df)) * 100
    st.sidebar.metric("最終得分", f"{final_score:.0f} 分")
    
    if st.button("🔄 重新練習 (換一組題目)"):
        del st.session_state.test_df
        st.session_state.user_answers = {}
        st.session_state.submitted = False
        st.rerun()
