"""
task_manager.py — 任务管理模块

职责：
  管理用户创建的待办任务，支持任务的增删查改。
  实现观察者模式中的 Subject（主题），当任务变化时通知所有观察者。
  数据持久化到 JSON 文件。
"""

import json
import os
import threading
from datetime import datetime
from typing import Callable


# ─── 观察者模式：观察者接口 ────────────────────────────────
class Observer:
    """观察者接口，所有观察者需实现 update 方法。"""

    def update(self, event_type: str, data: any):
        """
        当被观察对象状态变化时调用。

        Args:
            event_type: 事件类型（如 "task_added", "task_completed"）
            data: 事件相关数据
        """
        raise NotImplementedError


class Subject:
    """主题（被观察者）基类，管理观察者注册与通知。"""

    def __init__(self):
        self._observers: list[Observer] = []
        self._lock = threading.Lock()

    def attach(self, observer: Observer) -> None:
        """注册观察者。"""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """移除观察者。"""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def notify(self, event_type: str, data: any) -> None:
        """通知所有注册的观察者。"""
        with self._lock:
            observers = list(self._observers)
        for observer in observers:
            try:
                observer.update(event_type, data)
            except Exception as e:
                print(f"[Subject] 通知观察者失败: {e}")


# ─── 任务管理器 ──────────────────────────────────────────
class TaskManager(Subject):
    """任务管理器，实现观察者模式 Subject，管理待办任务的增删查改。"""

    def __init__(self, data_dir: str = "data"):
        super().__init__()
        self.data_dir = data_dir
        self.tasks_file = os.path.join(data_dir, "tasks.json")
        self._tasks: list[dict] = []
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        """从 JSON 文件加载任务数据。"""
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                self._tasks = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._tasks = []

    def _save(self) -> None:
        """将任务数据保存到 JSON 文件（线程安全、无冗余文件系统调用）。"""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(self._tasks, f, ensure_ascii=False, indent=2)

    def add_task(self, description: str) -> dict:
        """
        添加新任务。

        Args:
            description: 任务描述

        Returns:
            创建的任务字典
        """
        task = {
            "id": len(self._tasks) + 1,
            "description": description,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False,
        }
        with self._lock:
            self._tasks.append(task)
            self._save()

        self.notify("task_added", task)
        return task

    def complete_task(self, task_id: int) -> bool:
        """
        完成任务。

        Args:
            task_id: 任务 ID

        Returns:
            是否成功完成
        """
        task = None
        with self._lock:
            for t in self._tasks:
                if t["id"] == task_id:
                    t["completed"] = True
                    self._save()
                    task = t
                    break
        # notify 必须在锁外调用，否则与 Subject.notify() 的 self._lock 形成死锁
        if task:
            self.notify("task_completed", task)
            return True
        return False

    def delete_task(self, task_id: int) -> bool:
        """
        删除任务。

        Args:
            task_id: 任务 ID

        Returns:
            是否成功删除
        """
        deleted = None
        with self._lock:
            for i, task in enumerate(self._tasks):
                if task["id"] == task_id:
                    deleted = self._tasks.pop(i)
                    self._save()
                    break
        if deleted:
            self.notify("task_deleted", deleted)
            return True
        return False

    def get_all_tasks(self) -> list[dict]:
        """获取所有任务列表。"""
        with self._lock:
            return list(self._tasks)

    def get_pending_tasks(self) -> list[dict]:
        """获取未完成的任务列表。"""
        with self._lock:
            return [t for t in self._tasks if not t["completed"]]

    def get_task_summary(self) -> str:
        """返回任务摘要文本。"""
        pending = self.get_pending_tasks()
        if not pending:
            return "📋 当前没有待办任务，一切轻松！"
        summary = "📋 **你的待办任务清单：**\n"
        for i, task in enumerate(pending, 1):
            summary += f"{i}. {task['description']}（创建于 {task['created_at']}）\n"
        return summary.strip()

    def parse_task_from_text(self, text: str) -> str:
        """
        从文本中解析任务描述。

        Args:
            text: 用户输入文本

        Returns:
            提取的任务描述
        """
        # 移除常见前缀
        prefixes = ["提醒我", "记下", "记住", "帮我记", "安排", "提醒"]
        for prefix in prefixes:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
        return text.strip()
