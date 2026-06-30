"""
response_generator.py — 回复生成器

职责：
  作为策略模式中的 Context（上下文），持有策略引用，
  根据意图选择对应的策略生成回复。
  是管道-过滤器风格的第二个过滤器。
"""

from typing import Optional

from response_strategies import STRATEGY_MAP, ResponseStrategy
from knowledge_base import KnowledgeBase
from task_manager import TaskManager
from conversation_history import ConversationHistory


class ResponseGenerator:
    """回复生成器，根据意图选择并执行对应的回复策略。"""

    def __init__(self):
        self._strategies: dict[str, ResponseStrategy] = STRATEGY_MAP

    def generate(self, intent: str, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager) -> str:
        """
        根据意图类型选择策略并生成回复。

        Args:
            intent: 意图类型
            user_input: 用户输入
            emotion: 检测到的情绪
            history: 对话历史
            knowledge_base: 知识库
            task_manager: 任务管理器

        Returns:
            生成的回复文本
        """
        strategy = self._strategies.get(intent)
        if strategy is None:
            # 默认使用闲聊策略
            strategy = self._strategies.get("small_talk")

        response = strategy.generate(user_input, emotion, history,
                                      knowledge_base, task_manager,
                                      intent=intent)
        return response

    def register_strategy(self, intent: str, strategy: ResponseStrategy) -> None:
        """
        注册新的策略（扩展点）。

        Args:
            intent: 意图类型
            strategy: 策略实例
        """
        self._strategies[intent] = strategy
