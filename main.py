from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import random
import json
import os
from datetime import datetime

@register("basics", "Tsuki", "一些基础功能的插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.tarot_data = None  # type: dict | None
        self.tarot_cards = None  # type: list[str] | None

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        # 预加载 tarot.json，便于 jrrp 使用
        try:
            base_dir = os.path.dirname(__file__)
            tarot_path = os.path.join(base_dir, "tarot.json")
            with open(tarot_path, "r", encoding="utf-8") as f:
                self.tarot_data = json.load(f)
                # 固定顺序，确保在不同环境中也可复现
                self.tarot_cards = sorted(self.tarot_data.keys())
            logger.info("[basics] Tarot 数据加载完成，共 %d 张牌", len(self.tarot_cards))
        except Exception as e:
            self.tarot_data = None
            self.tarot_cards = None
            logger.error("[basics] Tarot 数据加载失败：%s", e)
    
    @filter.command("jrrp")
    async def today_luck(self, event: AstrMessageEvent):
        """今日人品，结果为 0~100 的整数，每天固定"""
        user_id = str(event.get_sender_id())
        today = datetime.now().strftime('%Y-%m-%d')
        # 使用局部随机数生成器，避免污染全局随机状态
        rng_luck = random.Random(today + user_id)
        luck = rng_luck.randint(0, 100)
        user_name = event.get_sender_name()
        # Tarot 抽牌（每日对每个用户固定）
        tarot_text = ""
        if self.tarot_data and self.tarot_cards:
            rng_tarot = random.Random(f"{today}-{user_id}-tarot")
            card = rng_tarot.choice(self.tarot_cards)
            orientation_key = rng_tarot.choice(["upright", "reversed"])  # 50% 正/逆位
            orientation_zh = "正位" if orientation_key == "upright" else "逆位"
            reading = self.tarot_data.get(card, {}).get(orientation_key)
            if reading:
                tarot_text = (
                    f"\n\n今日塔罗：{card}（{orientation_zh}）\n"
                    f"- 核心：{reading.get('core', '—')}\n"
                    f"- 感情：{reading.get('love', '—')}\n"
                    f"- 事业：{reading.get('career', '—')}\n"
                    f"- 建议：{reading.get('advice', '—')}"
                )
            else:
                tarot_text = "\n\n今日塔罗：数据缺失，稍后再试。"
        else:
            tarot_text = "\n\n今日塔罗：未找到 tarot.json，已跳过占卜。"

        yield event.plain_result(f"{user_name} 的今日人品是：{luck} 🍀" + tarot_text)

    @filter.command("roll")
    async def roll_dice(self, event: AstrMessageEvent):
        """掷骰子，支持格式：/roll [面数]，默认 6 面"""
        parts = event.message_str.strip().split()
        try:
            sides = int(parts[1]) if len(parts) > 1 else 6
            if sides <= 1:
                raise ValueError()
        except ValueError:
            yield event.plain_result("🎲 请输入正确的骰子面数（如：/roll 或 /roll 20）")
            return

        result = random.randint(1, sides)
        yield event.plain_result(f"你掷出了一个 {sides} 面骰子，点数为：{result} 🎲")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
