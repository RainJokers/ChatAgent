"""
app.py — 智能聊天助手 Agent 主界面（Streamlit）

职责：
  提供 Web 交互界面，展示对话、快捷按钮、任务面板和诊断信息。
  实现观察者模式中的界面更新部分。
"""

import streamlit as st

from agent_controller import AgentController


# ─── 页面配置 ─────────────────────────────────────────────
st.set_page_config(
    page_title="智能聊天助手 Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 自定义 CSS 样式 ──────────────────────────────────────
st.markdown("""
<style>
    /* 主标题 */
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }
    /* 聊天消息 */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: flex-start;
        gap: 0.8rem;
    }
    .user-message {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        border: 1px solid #a5b4fc;
    }
    .agent-message {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #86efac;
    }
    .message-avatar {
        font-size: 1.8rem;
        line-height: 1;
        flex-shrink: 0;
    }
    .message-content {
        flex: 1;
        line-height: 1.6;
    }
    .message-meta {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.3rem;
    }
    /* 快捷按钮 */
    .quick-btn {
        display: inline-block;
        margin: 0.2rem;
    }
    /* 侧边栏 */
    .sidebar-section {
        padding: 0.5rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 0.8rem;
    }
    .sidebar-section:last-child {
        border-bottom: none;
    }
    /* 诊断面板 */
    .diagnostic-panel {
        background: #f3f4f6;
        border-radius: 8px;
        padding: 0.8rem;
        font-size: 0.85rem;
        font-family: 'Courier New', monospace;
        margin-top: 0.5rem;
    }
    /* Streamlit 覆盖 */
    .stButton button {
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        padding: 0.3rem 1rem !important;
    }
    .stTextInput input {
        border-radius: 24px !important;
        padding: 0.6rem 1.2rem !important;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─── 初始化 Session State ─────────────────────────────────
def init_session_state():
    """初始化 Streamlit 会话状态。"""
    if "agent" not in st.session_state:
        st.session_state.agent = AgentController()
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "你好！我是你的智能聊天助手 Agent 🤖\n\n我可以帮你：\n- 💬 自由聊天\n- 📖 回答知识性问题\n- 📋 记录待办任务\n- 😊 感知你的情绪\n\n有什么想聊的吗？"}
        ]
    if "diagnostic" not in st.session_state:
        st.session_state.diagnostic = None


init_session_state()

# ─── 侧边栏 ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 Agent 控制面板")

    # — 任务面板 —
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("#### 📋 待办任务")

    agent = st.session_state.agent
    tasks = agent.task_manager.get_pending_tasks()

    if tasks:
        for task in tasks:
            if st.button(f"✅ {task['description']}",
                         key=f"complete_{task['id']}",
                         help="标记完成",
                         use_container_width=True):
                agent.task_manager.complete_task(task["id"])
                st.rerun()
    else:
        st.info("🎉 暂无待办任务")
    st.markdown("</div>", unsafe_allow_html=True)

    # — 快捷按钮 —
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ 快捷指令")

    quick_actions = [
        ("💬 打招呼", "你好！"),
        ("📖 查知识", "告诉我什么是设计模式"),
        ("📋 记任务", "提醒我明天下午3点开会"),
        ("😊 分享心情", "今天心情很好！"),
        ("😞 倾诉烦恼", "最近压力好大，很累"),
        ("🗑️ 清空对话", "__clear__"),
    ]

    for label, cmd in quick_actions:
        if st.button(label, key=f"quick_{cmd}", use_container_width=True):
            if cmd == "__clear__":
                st.session_state.messages = [
                    {"role": "assistant", "content": "对话已清空！有什么想聊的吗？😊"}
                ]
                agent.clear_history()
                st.session_state.diagnostic = None
                st.rerun()
            else:
                # 直接处理快捷消息（绕过输入框，避免 session_state 冲突）
                st.session_state.messages.append({"role": "user", "content": cmd})
                with st.spinner("🤖 Agent 思考中..."):
                    result = agent.process_message(cmd)
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})
                st.session_state.diagnostic = agent.get_diagnostic_info(result)
                event_msg = agent.ui_observer.get_last_event_message()
                if event_msg:
                    st.toast(event_msg)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # — 系统状态 —
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("#### 📊 系统状态")
    st.markdown(f"- 对话轮次：{len(agent.conversation_history)}")
    st.markdown(f"- 待办任务：{len(tasks)}")
    llm_status = "🧠 大模型" if agent.llm_enabled else "📋 规则策略"
    st.markdown(f"- 回复模式：{llm_status}")
    st.markdown("</div>", unsafe_allow_html=True)

    # — 诊断信息 —
    if st.session_state.diagnostic:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.markdown("#### 🔬 诊断信息")
        st.markdown(f"<div class='diagnostic-panel'>{st.session_state.diagnostic}</div>",
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ─── 主界面 ───────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 智能聊天助手 Agent</h1>
    <p>管道-过滤器 + 分层架构 · 策略模式 · 观察者模式</p>
</div>
""", unsafe_allow_html=True)

# — 聊天记录 —
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-avatar">👤</div>
                <div class="message-content">
                    <strong>你</strong>
                    <p style="margin: 0.3rem 0;">{msg['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message agent-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <strong>Agent</strong>
                    <p style="margin: 0.3rem 0;">{msg['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

# — 聊天输入框（按 Enter 发送，自动清空） —
user_input = st.chat_input("输入你想说的话，按 Enter 发送...")

# — 处理输入 —
if user_input:
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 处理消息
    with st.spinner("🤖 Agent 思考中..."):
        result = agent.process_message(user_input)

    # 添加 Agent 回复
    st.session_state.messages.append({"role": "assistant", "content": result["response"]})

    # 保存诊断信息
    st.session_state.diagnostic = agent.get_diagnostic_info(result)

    # 检查是否有观察者事件
    event_msg = agent.ui_observer.get_last_event_message()
    if event_msg:
        st.toast(event_msg)

    st.rerun()

# — 底部留白 —
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
