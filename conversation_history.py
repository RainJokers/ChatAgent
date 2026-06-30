"""
conversation_history.py — 对话历史模块

职责：
  管理多轮对话上下文，保存对话记录，支持上下文摘要。
  为多轮记忆提供数据支持。
"""

from datetime import datetime
from typing import Optional


class ConversationHistory:
    """对话历史管理器，保存并管理多轮对话上下文。"""

    def __init__(self, max_turns: int = 20):
        """
        初始化对话历史管理器。

        Args:
            max_turns: 最大保留对话轮数，默认 20 轮
        """
        self.max_turns = max_turns
        self._history: list[dict] = []

    def add_turn(self, user_input: str, agent_response: str,
                 intent: str = "", emotion: str = "") -> None:
        """
        添加一轮对话。

        Args:
            user_input: 用户输入
            agent_response: Agent 回复
            intent: 识别到的意图
            emotion: 检测到的情绪
        """
        turn = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "agent": agent_response,
            "intent": intent,
            "emotion": emotion,
        }
        self._history.append(turn)

        # 超出最大轮数则移除最早的
        if len(self._history) > self.max_turns:
            self._history.pop(0)

    def get_history(self) -> list[dict]:
        """获取完整对话历史。"""
        return list(self._history)

    def get_recent_context(self, n: int = 5) -> str:
        """
        获取最近的对话上下文文本。

        Args:
            n: 最近几轮对话

        Returns:
            格式化的上下文文本
        """
        recent = self._history[-n:] if len(self._history) > n else self._history
        if not recent:
            return ""

        context = ""
        for turn in recent:
            context += f"用户: {turn['user']}\n"
            context += f"Agent: {turn['agent']}\n"
        return context.strip()

    def get_last_user_input(self) -> Optional[str]:
        """获取用户最近一次输入。"""
        if self._history:
            return self._history[-1]["user"]
        return None

    def get_last_agent_response(self) -> Optional[str]:
        """获取 Agent 最近一次回复。"""
        if self._history:
            return self._history[-1]["agent"]
        return None

    def clear(self) -> None:
        """清空对话历史。"""
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
