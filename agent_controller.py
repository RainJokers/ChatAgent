"""
agent_controller.py — 核心控制器（管道-过滤器 + 分层架构混合）

职责：
  作为交互层与决策层之间的核心控制器，编排整个处理流程：
    用户输入 → 意图识别 → 情绪检测 → 回复生成 → 输出
  同时维护各模块实例和对话状态。

  架构说明：
  - 管道-过滤器风格：每个处理步骤是一个过滤器，数据沿管道流动
  - 分层架构风格：交互层(UI) → 决策层(Controller) → 数据层(存储)
"""

import os
import time
from typing import Optional

from config import get_llm_config
from intent_classifier import IntentClassifier
from emotion_detector import EmotionDetector
from response_generator import ResponseGenerator
from response_strategies import LLMStrategy, STRATEGY_MAP
from knowledge_base import KnowledgeBase
from task_manager import TaskManager, Observer
from conversation_history import ConversationHistory


# ─── 观察者模式：界面更新观察者 ────────────────────────────
class UIObserver(Observer):
    """界面观察者，监听任务变化并更新 UI 状态。"""

    def __init__(self):
        self.last_event: Optional[dict] = None

    def update(self, event_type: str, data: any) -> None:
        self.last_event = {
            "type": event_type,
            "data": data,
            "message": self._format_message(event_type, data),
        }

    def _format_message(self, event_type: str, data: any) -> str:
        messages = {
            "task_added": f"📌 新任务已创建：{data.get('description', '')}",
            "task_completed": f"✅ 任务已完成：{data.get('description', '')}",
            "task_deleted": f"🗑️ 任务已删除：{data.get('description', '')}",
        }
        return messages.get(event_type, f"事件: {event_type}")

    def get_last_event_message(self) -> Optional[str]:
        """获取最近一次事件的消息。"""
        if self.last_event:
            return self.last_event["message"]
        return None

    def clear_event(self) -> None:
        """清空最近事件。"""
        self.last_event = None


class AgentController:
    """
    Agent 核心控制器。

    负责整个对话处理管道的编排：
    [输入] → 意图识别 → 情绪检测 → 回复生成 → [输出]
    """

    def __init__(self, data_dir: str = "data"):
        # 初始化各模块（数据层）
        self.data_dir = data_dir
        self.knowledge_base = KnowledgeBase(data_dir)
        self.task_manager = TaskManager(data_dir)
        self.conversation_history = ConversationHistory(max_turns=20)

        # 初始化过滤器（决策层）
        self.intent_classifier = IntentClassifier(data_dir)
        self.emotion_detector = EmotionDetector()
        self.response_generator = ResponseGenerator()

        # 观察者
        self.ui_observer = UIObserver()
        self.task_manager.attach(self.ui_observer)

        # LLM 配置（从环境变量自动加载）
        self._llm_strategy: LLMStrategy = STRATEGY_MAP.get("__llm__")  # type: ignore
        self._llm_enabled = False
        self._auto_configure_llm()

    def _auto_configure_llm(self) -> None:
        """
        自动配置 LLM，优先级：
          1. config.json（推荐）
          2. 环境变量 LLM_API_KEY / LLM_API_BASE / LLM_MODEL
        """
        # 优先从 config.json 读取
        cfg = get_llm_config()
        api_key = cfg.get("api_key", "") or os.environ.get("LLM_API_KEY", "")
        if api_key:
            api_base = cfg.get("api_base", "") or os.environ.get("LLM_API_BASE", "https://api.deepseek.com")
            model = cfg.get("model", "") or os.environ.get("LLM_MODEL", "deepseek-chat")
            self.configure_llm(api_key, api_base, model)

    def process_message(self, user_input: str) -> dict:
        """
        处理用户消息（管道-过滤器风格）。

        处理流程：
          1. 意图识别过滤器
          2. 情绪检测过滤器
          3. 回复生成过滤器
          4. 对话记录存储

        Args:
            user_input: 用户输入文本

        Returns:
            包含处理结果的字典：
            {
                "response": str,       # Agent 回复
                "intent": str,         # 识别到的意图
                "emotion": str,        # 检测到的情绪
                "processing_time": float,  # 处理时间(秒)
            }
        """
        start_time = time.time()

        # ─── 过滤器 1：意图识别 ─────────────────
        intent = self.intent_classifier.classify(user_input)

        # ─── 过滤器 2：情绪检测 ─────────────────
        emotion = self.emotion_detector.detect(user_input)

        # ─── 过滤器 3：回复生成 ─────────────────
        response = self.response_generator.generate(
            intent=intent,
            user_input=user_input,
            emotion=emotion,
            history=self.conversation_history,
            knowledge_base=self.knowledge_base,
            task_manager=self.task_manager,
        )

        # ─── 记录对话历史 ──────────────────────
        self.conversation_history.add_turn(
            user_input=user_input,
            agent_response=response,
            intent=intent,
            emotion=emotion,
        )

        processing_time = time.time() - start_time

        return {
            "response": response,
            "intent": intent,
            "emotion": emotion,
            "processing_time": round(processing_time, 3),
        }

    def get_diagnostic_info(self, result: dict) -> str:
        """返回处理诊断信息（用于调试和展示）。"""
        intent_label = self.intent_classifier.get_intent_description(result["intent"])
        emotion_label = self.emotion_detector.get_emotion_label(result["emotion"])
        mode = "🧠 大模型" if self._llm_enabled else "📋 规则策略"
        return (
            f"🔍 **处理诊断**\n"
            f"├ 识别意图：{intent_label}\n"
            f"├ 检测情绪：{emotion_label}\n"
            f"├ 回复模式：{mode}\n"
            f"└ 处理耗时：{result['processing_time']:.2f}s"
        )

    # ─── LLM 配置接口 ─────────────────────────────────────
    def configure_llm(self, api_key: str, api_base: str = None, model: str = None) -> None:
        """
        配置并启用大模型。
        启用后，所有意图的回复生成都交由 LLMStrategy 处理（自带规则回退）。

        Args:
            api_key: API 密钥
            api_base: API 地址（默认 DeepSeek）
            model: 模型名称
        """
        if self._llm_strategy:
            self._llm_strategy.configure(api_key, api_base, model)
            self._llm_enabled = self._llm_strategy.is_configured
            if self._llm_enabled:
                # 让 ResponseGenerator 的所有意图都用 LLM 策略
                for intent in ["small_talk", "knowledge_query", "task_creation", "emotion_sharing"]:
                    self.response_generator._strategies[intent] = self._llm_strategy

    def disable_llm(self) -> None:
        """关闭大模型，回退到规则策略。"""
        if self._llm_strategy:
            self._llm_strategy.disable()
        self._llm_enabled = False
        # 恢复规则策略
        from response_strategies import SmallTalkStrategy, KnowledgeQueryStrategy, \
            TaskCreationStrategy, EmotionSharingStrategy
        self.response_generator._strategies["small_talk"] = SmallTalkStrategy()
        self.response_generator._strategies["knowledge_query"] = KnowledgeQueryStrategy()
        self.response_generator._strategies["task_creation"] = TaskCreationStrategy()
        self.response_generator._strategies["emotion_sharing"] = EmotionSharingStrategy()

    @property
    def llm_enabled(self) -> bool:
        """LLM 是否已启用。"""
        return self._llm_enabled

    @property
    def llm_config(self) -> dict:
        """当前 LLM 配置信息。"""
        if self._llm_strategy:
            return {
                "enabled": self._llm_strategy.is_configured,
                "api_base": self._llm_strategy.api_base,
                "model": self._llm_strategy.model,
                "has_key": bool(self._llm_strategy.api_key),
            }
        return {"enabled": False}

    def get_task_summary(self) -> str:
        """获取任务摘要。"""
        return self.task_manager.get_task_summary()

    def clear_history(self) -> None:
        """清空对话历史。"""
        self.conversation_history.clear()
