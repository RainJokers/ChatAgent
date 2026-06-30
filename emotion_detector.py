"""
emotion_detector.py — 情绪检测模块

职责：
  基于关键词和规则检测用户输入文本中的情绪倾向。
  返回情绪类型：positive（积极）/ neutral（中性）/ negative（消极）。
  检测结果影响后续回复的语气风格。
"""

import re


class EmotionDetector:
    """情绪检测器，分析文本中的情感倾向。"""

    # 积极情绪关键词
    POSITIVE_WORDS = {
        "开心", "高兴", "快乐", "兴奋", "棒", "好", "喜欢", "爱",
        "幸福", "满意", "赞", "厉害", "优秀", "哈哈", "嘻嘻",
        "太好了", "nice", "great", "amazing", "wonderful", "excellent",
        "good", "happy", "love", "perfect", "超棒", "真棒", "不错",
    }

    # 消极情绪关键词
    NEGATIVE_WORDS = {
        "难过", "伤心", "生气", "郁闷", "烦", "焦虑", "压力", "累",
        "疲惫", "孤单", "孤独", "失望", " frustrated", "讨厌",
        "恶心", "糟糕", "差", "恨", "哭", "叹气", "烦人",
        "sad", "angry", "upset", "depressed", "terrible", "horrible",
        "bad", "hate", "tired", "stressed", "难受", "痛苦",
    }

    # 情绪强化词（出现时提高权重）
    INTENSIFIERS = {"很", "非常", "特别", "极其", "太", "超级", "真的", "实在", "太", "十分"}

    def __init__(self):
        # 缓存结果以提高性能
        self._cache: dict[str, str] = {}

    def detect(self, text: str) -> str:
        """
        检测文本情绪倾向。

        Args:
            text: 用户输入文本

        Returns:
            情绪类型：positive / neutral / negative
        """
        if not text or not text.strip():
            return "neutral"

        # 检查缓存
        cache_key = text.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        text_lower = text.lower()

        # 计算情绪得分
        positive_score = self._count_matches(text_lower, self.POSITIVE_WORDS)
        negative_score = self._count_matches(text_lower, self.NEGATIVE_WORDS)

        # 考虑强化词
        intensifier_count = self._count_matches(text_lower, self.INTENSIFIERS)
        if intensifier_count > 0:
            positive_score *= 1.3
            negative_score *= 1.3

        # 情绪符号检测
        if ":)" in text or ":D" in text or ":-)" in text:
            positive_score += 1
        if ":(" in text or ":'(" in text or ":-(" in text:
            negative_score += 1

        # 判断最终情绪
        if positive_score > negative_score:
            result = "positive"
        elif negative_score > positive_score:
            result = "negative"
        else:
            result = "neutral"

        # 存入缓存
        self._cache[cache_key] = result
        return result

    def _count_matches(self, text: str, word_set: set) -> int:
        """统计文本中匹配关键词的数量。"""
        count = 0
        for word in word_set:
            # 使用单词边界匹配，避免部分匹配
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            count += len(pattern.findall(text))
        return count

    def get_emotion_label(self, emotion: str) -> str:
        """返回情绪的中文标签。"""
        labels = {
            "positive": "😊 积极",
            "neutral": "😐 中性",
            "negative": "😞 消极",
        }
        return labels.get(emotion, "😐 中性")
