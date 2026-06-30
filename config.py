"""
config.py — 配置文件加载模块

职责：
  从 config.json 读取大模型配置，供 agent_controller 使用。
  用户只需编辑 config.json 中的 api_key 即可完成配置。
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "llm": {
        "api_key": "",
        "api_base": "https://api.deepseek.com",
        "model": "deepseek-chat",
    }
}


def load_config() -> dict:
    """
    加载配置文件 config.json。

    Returns:
        配置字典，文件不存在或格式错误时返回默认配置
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 确保关键字段存在
            if "llm" not in cfg:
                cfg["llm"] = {}
            for key in ["api_key", "api_base", "model"]:
                if key not in cfg["llm"]:
                    cfg["llm"][key] = DEFAULT_CONFIG["llm"][key]
            return cfg
    except (json.JSONDecodeError, OSError) as e:
        print(f"[config] 读取配置文件失败: {e}")

    return dict(DEFAULT_CONFIG)


def get_llm_config() -> dict:
    """快捷获取 LLM 配置部分。"""
    return load_config().get("llm", dict(DEFAULT_CONFIG["llm"]))
