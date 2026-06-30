"""
knowledge_base.py — 知识库模块

职责：
  加载和管理内置知识库（JSON 文件），提供知识检索功能。
  支持关键词匹配查找事实性知识。
"""

import json
import os
from typing import Optional


class KnowledgeBase:
    """知识库类，负责加载和检索事实性知识。"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.knowledge_file = os.path.join(data_dir, "knowledge_base.json")
        self._facts: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """从 JSON 文件加载知识库数据。"""
        try:
            with open(self.knowledge_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._facts = data.get("facts", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[KnowledgeBase] 加载知识库失败: {e}")
            self._facts = {}

    def query(self, text: str) -> Optional[str]:
        """
        根据用户输入文本检索相关知识。

        Args:
            text: 用户输入文本

        Returns:
            匹配的知识内容，如未找到返回 None
        """
        text_lower = text.lower()
        for keyword, answer in self._facts.items():
            if keyword in text_lower:
                return answer
        return None

    def get_all_topics(self) -> list[str]:
        """返回知识库中所有主题列表。"""
        return list(self._facts.keys())

    def reload(self) -> None:
        """重新加载知识库（支持热更新）。"""
        self._load()
