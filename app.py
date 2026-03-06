import streamlit as st
import pandas as pd

# 頁面配置
st.set_page_config(page_title="AI 應用規劃師 - 在線模擬考", layout="wide")

# --- 1. 登入系統邏輯 ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 考生登入系統")
        user = st.text_input("帳號 (預設: student)")
        pw = st.text_input("密碼 (預設: ipas123)", type="password")
        if st.button("進入考試"):
            if user == "student" and pw == "ipas123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("帳號或密碼錯誤，請重新輸入。")
        return False
    return True

# --- 2. 核心考試功能 ---
def run_exam():
    st.sidebar.title("📝 考試資訊")
    st.sidebar.info("科目：AI 應用規劃師\n題數：100 題\n及格分數：70 分")
    
    if st.sidebar.button("登出"):
        st.session_state.logged_in = False
        st.rerun()

    # 讀取題庫
    try:
        df = pd.read_excel("ai_quiz.xlsx")
    except Exception as e:
        st.error(f"找不到題庫檔案 ai_quiz.xlsx，請確認檔案路徑。錯誤: {e}")
        return

    # 初始化 session state 存儲答案與提交狀態
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    st.title("🚀 AI 應用規劃師模擬考試")
    st.write("請認真閱讀題目並選出正確答案，完成後點擊底部的「提交考卷」。")

    # 顯示題目
    for i, row in df.iterrows():
        st.markdown(f"#### 第 {i+1} 題：{row['題型']}")
        st.write(row['題幹'])
        
        # 處理選項
        if row['題型'] == "是非題":
            options = ["T", "F"]
        else:
            options = ["A", "B", "C", "D"]
            # 格式化顯示選項內容
            opt_labels = {
                "A": f"A: {row['選項-A']}",
                "B": f"B: {row['選項-B']}",
                "C": f"C: {row['選項-C']}",
                "D": f"D: {row['選項-D']}"
            }
        
        # 記錄使用者選擇
        user_choice = st.radio(
            f"選擇您的答案 (Q{i+1}):",
            options,
            index=None,
            key=f"q_{i}",
            format_func=lambda x: opt_labels[x] if row['題型'] != "是非題" else x,
            disabled=st.session_state.submitted
        )
        st.session_state.user_answers[i] = user_choice
        st.divider()

    # 提交考卷
    if not st.session_state.submitted:
        if st.button("🏁 提交考卷並計算分數"):
            st.session_state.submitted = True
            st.rerun()

    # 3. 評分與解析顯示
    if st.session_state.submitted:
        st.header("🎯 考試結果報告")
        score = 0
        wrong_questions = []

        for i, row in df.iterrows():
            correct_ans = str(row['答案']).strip().upper()
            user_ans = st.session_state.user_answers.get(i)

            if user_ans == correct_ans:
                score += 1
            else:
                wrong_questions.append({
                    "no": i+1,
                    "q": row['題幹'],
                    "user": user_ans,
                    "correct": correct_ans,
                    "reason": row['正確答案解釋']
                })

        final_score = (score / len(df)) * 100
        
        # 顯示總分儀表板
        col1, col2 = st.columns(2)
        col1.metric("最終得分", f"{final_score:.1f} 分")
        col2.metric("答對題數", f"{score} / {len(df)}")

        if final_score >= 70:
            st.balloons()
            st.success("🎉 恭喜！您已通過模擬測驗！")
        else:
            st.warning("⚠️ 尚未及格，請複習以下錯題。")

        # 錯題解析區
        if wrong_questions:
            with st.expander("🔍 查看錯題解析", expanded=True):
                for w in wrong_questions:
                    st.error(f"**第 {w['no']} 題：{w['q']}**")
                    st.write(f"❌ 您的答案：{w['user']} | ✅ 正確答案：{w['correct']}")
                    st.info(f"💡 解析：{w['reason']}")
                    st.divider()

        if st.button("🔄 重新挑戰一次"):
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.rerun()

# 啟動系統
if check_login():
    run_exam()