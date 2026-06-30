"""
response_strategies.py — 回复生成策略（策略模式）

职责：
  定义抽象策略接口和多种具体策略类，分别对应不同意图的回复生成。
  包括规则策略（原有关键词模板）和大模型策略（接入 LLM API）。

  架构要点：
  - 新增意图只需新增策略类并注册到 STRATEGY_MAP
  - LLM 策略调用失败时自动回退到规则策略
  - 通过 configure_llm() 动态启用/关闭 LLM
"""

import random
import json
from typing import Optional

from knowledge_base import KnowledgeBase
from task_manager import TaskManager
from conversation_history import ConversationHistory


# ─── 抽象策略接口 ──────────────────────────────────────────
class ResponseStrategy:
    """回复生成策略的抽象基类。"""

    def generate(self, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager,
                 intent: str = "") -> str:
        """
        生成回复。

        Args:
            user_input: 用户输入文本
            emotion: 检测到的情绪
            history: 对话历史
            knowledge_base: 知识库
            task_manager: 任务管理器
            intent: 识别到的意图

        Returns:
            生成的回复文本
        """
        raise NotImplementedError


# ─── 具体策略：闲聊 ──────────────────────────────────────
class SmallTalkStrategy(ResponseStrategy):
    """闲聊意图的回复策略。"""

    def __init__(self):
        self._greetings = [
            "你好呀！有什么我可以帮你的吗？😊",
            "嗨！很高兴见到你~ 想聊些什么呢？",
            "哈喽！今天想聊点什么呢？",
            "嗨嗨~ 我在这儿呢！",
        ]
        self._farewells = [
            "再见！期待下次聊天~ 👋",
            "拜拜！有需要随时找我哦~",
            "下次见！祝你愉快 😊",
            "再见啦，保持联系！",
        ]
        self._thanks = [
            "不客气！很高兴能帮到你 😊",
            "不用谢，举手之劳 ~",
            "应该的！有什么需要随时说~",
            "别客气，能帮到你就好！",
        ]
        self._about_self = [
            "我是你的智能聊天助手 Agent！我可以和你聊天、回答知识性问题、帮你记录任务，还能感知你的情绪哦~ 😊",
            "我是一个智能对话 Agent，用 Python 实现，采用了管道-过滤器加分层架构的混合风格！",
            "我叫 Agent，是你的 AI 小助手。我会聊天、查知识、记任务，还能感知情绪呢！",
        ]
        self._default_responses = [
            "嗯嗯，我在听呢，继续说说~",
            "原来如此，很有意思！",
            "好的呢，还有什么想聊的吗？",
            "明白了~ 我想听听更多！",
            "嗯！你说得对~",
            "说的有道理！",
        ]

    def generate(self, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager,
                 intent: str = "") -> str:
        user_lower = user_input.lower().strip()

        # 问候类
        if any(w in user_lower for w in ["你好", "嗨", "哈喽", "hi", "hello", "在吗"]):
            return random.choice(self._greetings)

        # 告别类
        if any(w in user_lower for w in ["再见", "拜拜", "下次见"]):
            return random.choice(self._farewells)

        # 感谢类
        if any(w in user_lower for w in ["谢谢", "感谢", "多谢"]):
            return random.choice(self._thanks)

        # 询问 Agent 身份
        if any(w in user_lower for w in ["你是谁", "你叫什么", "你是什么"]):
            return random.choice(self._about_self)

        # 根据情绪调整
        if emotion == "positive":
            return random.choice([
                "听起来你心情不错呢！真替你开心 😊",
                "好棒的感觉！继续保持好心情哦~",
                "看你心情这么好，我也开心！有什么好事分享一下？",
            ])
        elif emotion == "negative":
            return random.choice([
                "听起来你心情不太好… 有什么想聊聊的吗？",
                "别担心，我在这里陪着你呢 🙂",
                "每个人都会有不开心的时候，需要我帮你做点什么吗？",
            ])

        # 默认回复
        return random.choice(self._default_responses)


# ─── 具体策略：知识查询 ──────────────────────────────────
class KnowledgeQueryStrategy(ResponseStrategy):
    """知识查询意图的回复策略。"""

    def generate(self, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager,
                 intent: str = "") -> str:
        # 先查知识库
        answer = knowledge_base.query(user_input)
        if answer:
            return f"📖 **我知道这个！**\n\n{answer}"

        # 没找到则给提示
        topics = knowledge_base.get_all_topics()
        topics_str = "、".join(topics)
        return (
            f"🤔 关于这个问题，我目前的知识库中还没有收录哦。\n\n"
            f"不过我可以回答以下话题：\n{topics_str}\n\n"
            f"你可以输入「告诉我 + 话题」来查询相关知识！"
        )


# ─── 具体策略：任务创建 ──────────────────────────────────
class TaskCreationStrategy(ResponseStrategy):
    """任务创建意图的回复策略。"""

    def generate(self, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager,
                 intent: str = "") -> str:
        description = task_manager.parse_task_from_text(user_input)
        if not description:
            return "好的，请告诉我需要记录什么任务？例如「提醒我明天开会」"

        task = task_manager.add_task(description)
        pending_count = len(task_manager.get_pending_tasks())
        return (
            f"✅ **任务已记录！**\n\n"
            f"📌 任务：{description}\n"
            f"🕐 创建时间：{task['created_at']}\n\n"
            f"你目前共有 {pending_count} 个待办任务。"
        )


# ─── 具体策略：情绪倾诉 ──────────────────────────────────
class EmotionSharingStrategy(ResponseStrategy):
    """情绪倾诉意图的回复策略。"""

    def generate(self, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager,
                 intent: str = "") -> str:
        if emotion == "positive":
            return (
                "😊 **感受到你的好心情了！**\n\n"
                "分享快乐会让快乐加倍！要不要把这份好心情也传递给别人呢？\n"
                "如果你有什么开心的事，我很乐意听你多聊聊~"
            )
        elif emotion == "negative":
            return (
                "😞 **感受到你有些烦恼了…**\n\n"
                "没关系的，有什么不开心的事都可以跟我说说。\n"
                "有时候把心里话说出来，就会感觉轻松很多。\n\n"
                "💡 要不要我帮你记录一个待办，或者分散一下注意力？"
            )
        else:
            return (
                "🤗 **我感受到你在分享心情！**\n\n"
                "无论是什么样的话题，我都很愿意倾听。\n"
                "你想多聊聊你的感受吗？"
            )


# ─── LLM 策略 ──────────────────────────────────────────────
class LLMStrategy(ResponseStrategy):
    """
    大模型回复策略。

    通过 OpenAI 兼容接口调用大模型生成自然回复。
    集成意图识别、情绪检测、知识检索、对话历史等信息到 Prompt 中。
    API 调用失败时自动回退到对应的规则策略。
    """

    # 默认配置
    DEFAULT_API_BASE = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.api_base: str = self.DEFAULT_API_BASE
        self.model: str = self.DEFAULT_MODEL
        self.enabled: bool = False
        self._client = None
        # 规则策略作为 fallback
        self._fallback_map: dict[str, ResponseStrategy] = {
            "small_talk": SmallTalkStrategy(),
            "knowledge_query": KnowledgeQueryStrategy(),
            "task_creation": TaskCreationStrategy(),
            "emotion_sharing": EmotionSharingStrategy(),
        }

    def configure(self, api_key: str, api_base: str = None, model: str = None) -> None:
        """
        配置 LLM 连接参数。

        Args:
            api_key: API 密钥
            api_base: API 地址（默认 DeepSeek）
            model: 模型名称（默认 deepseek-chat）
        """
        self.api_key = api_key
        if api_base:
            self.api_base = api_base
        if model:
            self.model = model
        self.enabled = bool(api_key and api_key.strip())
        if self.enabled:
            self._client = None  # 延迟初始化

    def disable(self) -> None:
        """关闭 LLM 模式，回退到规则策略。"""
        self.enabled = False
        self.api_key = None
        self._client = None

    @property
    def is_configured(self) -> bool:
        """是否已配置并可用的 LLM。"""
        return self.enabled and bool(self.api_key)

    def _get_client(self):
        """延迟初始化 OpenAI 客户端。"""
        if self._client is None and self.is_configured:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                )
            except ImportError:
                raise ImportError(
                    "请安装 openai 库：pip install openai"
                )
        return self._client

    def _build_system_prompt(self, intent: str, emotion: str,
                              user_input: str,
                              knowledge_result: Optional[str],
                              task_context: Optional[str]) -> str:
        """构建系统提示词，融入管道处理结果。"""
        intent_desc = {
            "small_talk": "闲聊对话",
            "knowledge_query": "知识查询",
            "task_creation": "任务创建",
            "emotion_sharing": "情绪倾诉",
        }.get(intent, "闲聊对话")

        emotion_desc = {
            "positive": "用户情绪积极 😊",
            "neutral": "用户情绪中性 😐",
            "negative": "用户情绪消极 😞",
        }.get(emotion, "用户情绪中性")

        prompt = f"""你是一个智能聊天助手 Agent，采用管道-过滤器 + 分层架构实现。

【当前对话上下文】
- 识别意图：{intent_desc}
- 用户情绪：{emotion_desc}

【回复要求】
1. 根据识别到的意图和情绪进行回复
2. 语气自然友好，适当使用 emoji
3. 回复简洁明了，一般不超过 200 字"""

        if knowledge_result:
            prompt += f"\n\n【知识库匹配结果】\n{knowledge_result}\n(请基于此知识进行回答，如果用户问的是相关知识，可以用更自然的语言解释)"

        if task_context:
            prompt += f"\n\n【任务上下文】\n{task_context}"

        prompt += "\n\n请直接回复用户，不要输出思考过程。"
        return prompt

    def generate(self, user_input: str, emotion: str,
                 history: ConversationHistory,
                 knowledge_base: KnowledgeBase,
                 task_manager: TaskManager,
                 intent: str = "") -> str:
        intent = intent or "small_talk"

        # ─── 知识查询优先命中知识库，未命中再调大模型 ─────
        if intent == "knowledge_query":
            answer = knowledge_base.query(user_input)
            if answer:
                return f"📖 **我知道这个！**\n\n{answer}"

        # 如果 LLM 未启用，回退到规则策略
        if not self.is_configured:
            return self._fallback(user_input, emotion, history,
                                  knowledge_base, task_manager, intent)

        # 任务创建：实际调用 add_task 记录任务，再让 LLM 生成确认回复
        task_context = None
        created_task = None
        if intent == "task_creation":
            description = task_manager.parse_task_from_text(user_input)
            if description:
                created_task = task_manager.add_task(description)
                pending = len(task_manager.get_pending_tasks())
                task_context = (
                    f"用户想要创建任务：{description}\n"
                    f"任务已创建成功！当前共有 {pending} 个待办任务。"
                )

        # 构建消息
        try:
            client = self._get_client()
            if client is None:
                return self._fallback(user_input, emotion, history,
                                      knowledge_base, task_manager, intent)

            messages = [
                {"role": "system", "content": self._build_system_prompt(
                    intent, emotion, user_input, None, task_context
                )},
            ]

            # 添加上下文历史（最近 4 轮）
            recent = history.get_history()[-4:] if len(history) > 4 else history.get_history()
            for turn in recent:
                messages.append({"role": "user", "content": turn["user"]})
                messages.append({"role": "assistant", "content": turn["agent"]})

            # 当前用户输入
            messages.append({"role": "user", "content": user_input})

            # 调用 API
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                timeout=15,
            )

            response = completion.choices[0].message.content
            if response:
                return response

        except Exception as e:
            print(f"[LLMStrategy] API 调用失败，回退到规则策略: {e}")

        # 回退
        return self._fallback(user_input, emotion, history,
                              knowledge_base, task_manager, intent)

    def _fallback(self, user_input: str, emotion: str,
                  history: ConversationHistory,
                  knowledge_base: KnowledgeBase,
                  task_manager: TaskManager,
                  intent: str) -> str:
        """回退到对应的规则策略。"""
        strategy = self._fallback_map.get(intent, self._fallback_map["small_talk"])
        return strategy.generate(user_input, emotion, history,
                                  knowledge_base, task_manager)


# ─── 策略映射 ────────────────────────────────────────────
STRATEGY_MAP: dict[str, ResponseStrategy] = {
    "small_talk": SmallTalkStrategy(),
    "knowledge_query": KnowledgeQueryStrategy(),
    "task_creation": TaskCreationStrategy(),
    "emotion_sharing": EmotionSharingStrategy(),
    "__llm__": LLMStrategy(),  # 特殊 key，由控制器动态启用
}
