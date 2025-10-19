"""
确认管理器 - 处理需要二次确认的操作
"""

import time
from typing import Dict, Optional, Tuple
from src.common.logger import get_logger

logger = get_logger("dt_confirmation")


class ConfirmationManager:
    """确认状态管理器"""

    # 存储待确认的操作 {user_id_chat_id: {action, timestamp, data}}
    _pending_confirmations: Dict[str, Dict] = {}

    # 确认超时时间（秒）
    CONFIRMATION_TIMEOUT = 60

    @staticmethod
    def create_confirmation(
        user_id: str,
        chat_id: str,
        action_type: str,
        action_data: Optional[Dict] = None
    ) -> str:
        """
        创建待确认操作
        返回: 确认键
        """
        key = f"{user_id}_{chat_id}"
        ConfirmationManager._pending_confirmations[key] = {
            "action_type": action_type,
            "timestamp": time.time(),
            "data": action_data or {}
        }
        logger.info(f"创建确认: {key} -> {action_type}")
        return key

    @staticmethod
    def check_confirmation(user_id: str, chat_id: str, expected_type: str) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否有待确认的操作
        返回: (是否匹配, 操作数据)
        """
        key = f"{user_id}_{chat_id}"

        if key not in ConfirmationManager._pending_confirmations:
            return False, None

        confirmation = ConfirmationManager._pending_confirmations[key]

        # 检查是否超时
        if time.time() - confirmation["timestamp"] > ConfirmationManager.CONFIRMATION_TIMEOUT:
            del ConfirmationManager._pending_confirmations[key]
            logger.info(f"确认超时: {key}")
            return False, None

        # 检查类型是否匹配
        if confirmation["action_type"] != expected_type:
            return False, None

        # 匹配成功，删除确认状态并返回数据
        data = confirmation["data"]
        del ConfirmationManager._pending_confirmations[key]
        logger.info(f"确认成功: {key} -> {expected_type}")
        return True, data

    @staticmethod
    def cancel_confirmation(user_id: str, chat_id: str):
        """取消待确认操作"""
        key = f"{user_id}_{chat_id}"
        if key in ConfirmationManager._pending_confirmations:
            del ConfirmationManager._pending_confirmations[key]
            logger.info(f"取消确认: {key}")

    @staticmethod
    def cleanup_expired():
        """清理过期的确认"""
        now = time.time()
        expired_keys = [
            key for key, conf in ConfirmationManager._pending_confirmations.items()
            if now - conf["timestamp"] > ConfirmationManager.CONFIRMATION_TIMEOUT
        ]
        for key in expired_keys:
            del ConfirmationManager._pending_confirmations[key]
        if expired_keys:
            logger.info(f"清理过期确认: {len(expired_keys)}个")
