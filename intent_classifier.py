"""
intent_classifier.py — 意图识别模块

职责：
  基于关键词规则匹配，识别用户输入的意图类型。
  支持 4 类意图：small_talk（闲聊）、knowledge_query（知识查询）、
  task_creation（任务创建）、emotion_sharing（情绪倾诉）。

  采用管道-过滤器风格中的第一个过滤器。
"""

import json
import os
from typing import Optional


class IntentClassifier:
    """意图分类器，基于关键词规则匹配识别用户意图。"""

    INTENTS = ["small_talk", "knowledge_query", "task_creation", "emotion_sharing"]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.rules_file = os.path.join(data_dir, "intent_rules.json")
        self._rules: dict[str, dict] = {}
        self._load_rules()

    def _load_rules(self) -> None:
        """从 JSON 文件加载意图规则。"""
        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                self._rules = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[IntentClassifier] 加载规则失败: {e}")
            self._rules = {}

    def classify(self, text: str) -> str:
        """
        对用户输入进行意图分类。

        Args:
            text: 用户输入的文本

        Returns:
            意图类型字符串：small_talk / knowledge_query / task_creation / emotion_sharing
        """
        if not text or not text.strip():
            return "small_talk"

        text_lower = text.lower().strip()

        # 按优先级依次检查各意图的关键词
        for intent in ["task_creation", "knowledge_query", "emotion_sharing", "small_talk"]:
            rule = self._rules.get(intent)
            if not rule:
                continue
            keywords = rule.get("keywords", [])
            for keyword in keywords:
                if keyword in text_lower:
                    return intent

        # 默认返回闲聊
        return "small_talk"

    def get_intent_description(self, intent: str) -> str:
        """返回意图的中文描述。"""
        descriptions = {
            "small_talk": "闲聊对话",
            "knowledge_query": "知识查询",
            "task_creation": "任务创建",
            "emotion_sharing": "情绪倾诉",
        }
        return descriptions.get(intent, "未知意图")
