"""
冷却时间管理器
"""

import time
from typing import Dict, Optional, Tuple
from src.common.logger import get_logger

logger = get_logger("dt_cooldown")


class CooldownManager:
    """动作冷却管理器"""

    # 存储冷却状态 {user_id_chat_id_action: timestamp}
    _cooldowns: Dict[str, float] = {}

    @staticmethod
    def check_cooldown(
        user_id: str,
        chat_id: str,
        action_name: str,
        cooldown_seconds: int
    ) -> Tuple[bool, Optional[int]]:
        """
        检查动作是否在冷却中
        返回: (是否可用, 剩余冷却时间秒数)
        """
        if cooldown_seconds <= 0:
            return True, None  # 无冷却限制

        key = f"{user_id}_{chat_id}_{action_name}"
        last_use = CooldownManager._cooldowns.get(key, 0)

        time_passed = time.time() - last_use
        remaining = cooldown_seconds - time_passed

        if remaining > 0:
            # 还在冷却中
            return False, int(remaining)
        else:
            # 冷却已结束
            return True, None

    @staticmethod
    def set_cooldown(user_id: str, chat_id: str, action_name: str):
        """设置动作冷却"""
        key = f"{user_id}_{chat_id}_{action_name}"
        CooldownManager._cooldowns[key] = time.time()
        logger.debug(f"设置冷却: {key}")

    @staticmethod
    def clear_cooldown(user_id: str, chat_id: str, action_name: str):
        """清除动作冷却"""
        key = f"{user_id}_{chat_id}_{action_name}"
        if key in CooldownManager._cooldowns:
            del CooldownManager._cooldowns[key]
            logger.debug(f"清除冷却: {key}")

    @staticmethod
    def format_time(seconds: int) -> str:
        """格式化剩余时间"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒" if secs > 0 else f"{minutes}分"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}小时{minutes}分"
            else:
                return f"{hours}小时"

    @staticmethod
    def cleanup_expired(max_age_seconds: int = 86400):
        """清理过期的冷却记录（默认1天）"""
        now = time.time()
        expired_keys = [
            key for key, timestamp in CooldownManager._cooldowns.items()
            if now - timestamp > max_age_seconds
        ]
        for key in expired_keys:
            del CooldownManager._cooldowns[key]
        if expired_keys:
            logger.info(f"清理过期冷却记录: {len(expired_keys)}个")
