import streamlit as st
import pandas as pd
import random
import os
import string
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

st.set_page_config(page_title="AI 應用規劃師 - 智能複習系統", layout="wide")

# ==========================================
# 檔案設定：隱藏帳號檔與歷史紀錄
# ==========================================
USER_FILE = ".users_secure.csv" 
HISTORY_FILE = "quiz_history.csv"

# ==========================================
# 讀取信箱機密設定 (支援 secrets.toml)
# ==========================================
try:
    SENDER_EMAIL = st.secrets["email"]["sender_email"]
    SENDER_PASSWORD = st.secrets["email"]["sender_password"]
except Exception:
    # 若找不到 secrets.toml，給予預設值防呆 (但會無法寄信)
    SENDER_EMAIL = "your_email@gmail.com"
    SENDER_PASSWORD = "your_app_password"

# --- 密碼加密函數 (SHA-256) ---
def hash_password(password):
    return hashlib.sha256(str(password).encode('utf-8')).hexdigest()

def send_registration_email(to_email, password):
    if SENDER_EMAIL == "your_email@gmail.com":
        return False, "尚未設定有效的寄件者信箱與密碼。"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = "【AI 應用規劃師】註冊成功通知"

    body = f"""
    歡迎加入 AI 應用規劃師 智能複習系統！
    
    您的登入帳號：{to_email}
    您的登入密碼：{password}
    
    請妥善保存您的密碼，祝您測驗順利！
    """
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "信件發送成功"
    except Exception as e:
        return False, str(e)

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# --- 帳號管理函數 ---
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE, dtype={"帳號": str, "密碼": str})
    else:
        return pd.DataFrame(columns=["帳號", "密碼"])

def save_user(username, password):
    df = load_users()
    hashed_pw = hash_password(password)
    new_user = pd.DataFrame([{"帳號": username, "密碼": hashed_pw}])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_FILE, index=False)

# 💡 新增：自動初始化預設帳號 (student / ipas8888)
def init_default_user():
    df = load_users()
    if "student" not in df["帳號"].values:
        hashed_pw = hash_password("ipas8888")
        new_user = pd.DataFrame([{"帳號": "student", "密碼": hashed_pw}])
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv(USER_FILE, index=False)

def load_all_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    else:
        return pd.DataFrame(columns=["帳號", "題幹", "答對次數", "答錯次數"])

def get_user_history(username):
    df = load_all_history()
    return df[df["帳號"] == username].copy()

# ==========================================
# 0. 啟動時自動建立預設帳號
# ==========================================
init_default_user()

# ==========================================
# 1. 系統狀態初始化
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'batch_id' not in st.session_state:
    st.session_state.batch_id = 0
if 'history_saved' not in st.session_state:
    st.session_state.history_saved = False

# ==========================================
# 2. 登入與註冊介面
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 考生登入系統")
    
    # 在登入頁面提示預設帳號
    st.info("💡 測試專用預設帳號：`student` ／ 密碼：`ipas8888`")
    
    tab_login, tab_register = st.tabs(["🔑 會員登入", "📝 註冊新帳號"])
    
    with tab_login:
        l_user = st.text_input("登入信箱 (或預設帳號)", key="login_user")
        l_pw = st.text_input("密碼", type="password", key="login_pw")
        if st.button("登入"):
            users_df = load_users()
            hashed_input_pw = hash_password(l_pw)
            match = users_df[(users_df["帳號"].astype(str) == str(l_user)) & (users_df["密碼"].astype(str) == str(hashed_input_pw))]
            
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.username = l_user
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤，若無帳號請先註冊。")

    with tab_register:
        r_user = st.text_input("輸入電子信箱 (將作為您的帳號)", key="reg_user")
        pwd_mode = st.radio("密碼設定方式", ["自行設定", "隨機產生"])
        
        if pwd_mode == "自行設定":
            r_pw = st.text_input("設定新密碼", type="password", key="reg_pw")
        else:
            r_pw = None
            st.info("💡 系統將隨機產生一組 8 碼密碼，並寄送至您的信箱。")

        if st.button("註冊"):
            if not r_user or "@" not in r_user or "." not in r_user:
                st.warning("⚠️ 請輸入有效的電子信箱格式！")
            else:
                users_df = load_users()
                if r_user in users_df["帳號"].values:
                    st.error("⚠️ 此帳號已被註冊過，請換一個或直接登入！")
                elif r_user == "student":
                    st.error("⚠️ 預設帳號名稱無法註冊！")
                else:
                    final_pw = r_pw if pwd_mode == "自行設定" else generate_random_password()
                    if not final_pw:
                        st.warning("⚠️ 密碼不能為空！")
                    else:
                        with st.spinner("建立帳號並寄送信件中..."):
                            success, msg = send_registration_email(r_user, final_pw)
                            if success:
                                save_user(r_user, final_pw)
                                st.success(f"✅ 註冊成功！系統已將密碼寄送至 `{r_user}`，請前往收信並切換到「會員登入」。")
                                st.balloons()
                            else:
                                st.error(f"❌ 註冊失敗！無法寄送信件。錯誤訊息：{msg}")
    st.stop()

# ==========================================
# 3. 讀取題庫與側邊欄
# ==========================================
try:
    full_df = pd.read_excel("ai_quiz.xlsx", engine="openpyxl")
    full_df['答案'] = full_df['答案'].astype(str).str.upper().str.strip()
except Exception as e:
    st.error("⚠️ 找不到 'ai_quiz.xlsx'，請檢查檔案路徑。")
    st.stop()

st.sidebar.title(f"👤 歡迎, {st.session_state.username}")
page = st.sidebar.radio("📌 選擇頁面", ["📝 模擬測驗", "📈 錯題統計"])
if st.sidebar.button("登出"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
st.sidebar.divider()

# ==========================================
# 頁面 A：模擬測驗
# ==========================================
if page == "📝 模擬測驗":
    st.sidebar.subheader("⚙️ 出題設定")
    
    def reset_exam_state():
        if "test_df" in st.session_state:
            del st.session_state.test_df
        st.session_state.submitted = False
        st.session_state.history_saved = False
        st.session_state.user_answers = {}
        st.session_state.batch_id += 1

    exam_mode = st.sidebar.radio("出題模式", ["隨機抽題", "🔥 錯題重練 (弱點強化)"], on_change=reset_exam_state)
    all_domains = ["全部領域"] + sorted(full_df['題庫領域'].unique().tolist())
    selected_domain = st.sidebar.selectbox("🎯 選擇考科領域", all_domains, on_change=reset_exam_state)

    if "test_df" not in st.session_state:
        user_history_df = get_user_history(st.session_state.username)
        
        if selected_domain == "全部領域":
            pool = full_df
        else:
            pool = full_df[full_df['題庫領域'] == selected_domain]

        if exam_mode == "🔥 錯題重練 (弱點強化)":
            merged_pool = pd.merge(pool, user_history_df[['題幹', '答錯次數']], on='題幹', how='left').fillna(0)
            wrong_pool = merged_pool[merged_pool['答錯次數'] > 0]
            
            if wrong_pool.empty:
                st.warning("🎉 太棒了！您在這個領域目前沒有錯題紀錄，為您切換為一般隨機抽題。")
                st.session_state.test_df = pool.sample(n=min(10, len(pool))).reset_index(drop=True)
            else:
                st.info(f"🔍 偵測到 {len(wrong_pool)} 題專屬錯題，正在從中抽題...")
                st.session_state.test_df = wrong_pool.sample(n=min(10, len(wrong_pool))).reset_index(drop=True)
        else:
            st.session_state.test_df = pool.sample(n=min(10, len(pool))).reset_index(drop=True)
            
        st.session_state.user_answers = {}

    test_df = st.session_state.test_df
    st.title(f"✍️ {exam_mode}：{selected_domain}")

    with st.form("exam_form"):
        for i, row in test_df.iterrows():
            st.subheader(f"第 {i+1} 題 【{row['題型']}】")
            st.info(row['題幹'])
            if row['題型'] != "是非題":
                st.markdown(f"**A:** {row.get('選項-A','')}\n\n**B:** {row.get('選項-B','')}\n\n**C:** {row.get('選項-C','')}\n\n**D:** {row.get('選項-D','')}")
            form_key = f"q_{st.session_state.batch_id}_{i}"
            if row['題型'] == "複選題":
                ans = st.multiselect("請選擇答案", ["A", "B", "C", "D"], key=form_key, disabled=st.session_state.submitted)
                st.session_state.user_answers[i] = "".join(sorted(ans))
            elif row['題型'] == "是非題":
                ans = st.radio("請判判断對錯", ["T", "F"], index=None, key=form_key, disabled=st.session_state.submitted)
                st.session_state.user_answers[i] = ans
            else:
                ans = st.radio("請選擇正確答案", ["A", "B", "C", "D"], index=None, key=form_key, disabled=st.session_state.submitted)
                st.session_state.user_answers[i] = ans
            st.divider()

        if st.form_submit_button("🏁 提交考卷"):
            st.session_state.submitted = True
            st.rerun()

    if st.session_state.submitted:
        st.header("📊 測驗結果")
        score = 0
        
        all_history_df = load_all_history()
        current_user = st.session_state.username
        
        for i, row in test_df.iterrows():
            u_ans = st.session_state.user_answers.get(i, "")
            c_ans = str(row['答案'])
            is_correct = (u_ans == c_ans)
            
            if is_correct:
                score += 1
                st.success(f"第 {i+1} 題：正確 ✅")
            else:
                st.error(f"第 {i+1} 題：錯誤 ❌")
                st.write(f"👉 您的答案：`{u_ans}` | 正確答案：`{c_ans}`")
                st.warning(f"💡 解析：{row.get('正確答案解釋', '無解析')}")
            
            if not st.session_state.history_saved:
                q_text = row['題幹']
                mask = (all_history_df['帳號'] == current_user) & (all_history_df['題幹'] == q_text)
                
                if mask.any():
                    idx = all_history_df[mask].index[0]
                    if is_correct:
                        all_history_df.at[idx, '答對次數'] += 1
                    else:
                        all_history_df.at[idx, '答錯次數'] += 1
                else:
                    new_row = {"帳號": current_user, "題幹": q_text, "答對次數": 1 if is_correct else 0, "答錯次數": 0 if is_correct else 1}
                    all_history_df = pd.concat([all_history_df, pd.DataFrame([new_row])], ignore_index=True)
            st.divider()

        if not st.session_state.history_saved:
            all_history_df.to_csv(HISTORY_FILE, index=False)
            st.session_state.history_saved = True

        st.metric("本次得分", f"{(score/len(test_df))*100:.0f} / 100")
        if st.button("🔄 重新挑戰新題目"):
            reset_exam_state()
            st.rerun()

# ==========================================
# 頁面 B：錯題統計 
# ==========================================
elif page == "📈 錯題統計":
    st.title(f"📈 {st.session_state.username} 的錯題分析")
    
    user_history_df = get_user_history(st.session_state.username)
    
    if user_history_df.empty:
        st.info("💡 您尚未有作答紀錄，趕快去測試一下吧！")
    else:
        user_history_df['總次數'] = user_history_df['答對次數'] + user_history_df['答錯次數']
        user_history_df['錯誤率(%)'] = (user_history_df['答錯次數'] / user_history_df['總次數'] * 100).round(1)
        wrong_df = user_history_df[user_history_df['答錯次數'] > 0].sort_values(by=['答錯次數', '錯誤率(%)'], ascending=[False, False])
        
        if wrong_df.empty:
            st.success("太強了！您目前的作答紀錄中沒有任何錯題 🎉")
        else:
            st.subheader("📊 錯題 Top 10")
            chart_data = wrong_df.head(10).copy()
            chart_data['題目'] = chart_data['題幹'].str.slice(0, 15) + "..."
            st.bar_chart(chart_data.set_index('題目')[['答錯次數', '答對次數']], color=["#ff4b4b", "#00cc96"])
            
            st.dataframe(wrong_df[['題幹', '答錯次數', '答對次數', '錯誤率(%)']].reset_index(drop=True), use_container_width=True)
