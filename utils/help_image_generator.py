"""
帮助图片生成器 - 将帮助文本转换为美观的图片
"""

import os
import io
import base64
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


class HelpImageGenerator:
    """生成帮助图片"""

    # 颜色配置 - 温暖的渐变配色
    BG_START_COLOR = (60, 30, 20)  # 深橙红色
    BG_END_COLOR = (45, 25, 20)  # 深棕色

    CARD_BG_COLOR = (70, 45, 35, 150)  # 半透明暖色卡片背景（更透明）
    CARD_BORDER_COLOR = (200, 120, 60, 120)  # 金橙色边框（半透明）

    TITLE_COLOR = (255, 220, 150)  # 金黄色标题
    SUBTITLE_COLOR = (255, 180, 130)  # 珊瑚色副标题
    TEXT_COLOR = (250, 240, 220)  # 温暖米色文本
    COMMAND_COLOR = (255, 220, 100)  # 金色命令
    ACCENT_COLOR = (255, 140, 60)  # 暖橙色强调

    # 装饰色
    GLOW_COLOR = (255, 200, 100, 100)  # 金色光晕
    SHADOW_COLOR = (20, 10, 5, 120)  # 暖色阴影

    # 字体大小 - 增大
    TITLE_SIZE = 48
    SUBTITLE_SIZE = 32
    TEXT_SIZE = 26
    SMALL_SIZE = 22

    # 间距 - 调整为横屏布局
    PADDING = 60
    CARD_PADDING = 20
    LINE_SPACING = 8
    SECTION_SPACING = 25
    CARD_RADIUS = 15  # 圆角半径
    COLUMN_SPACING = 40  # 列间距

    # 背景图片配置
    BACKGROUND_IMAGE = "background.png"  # 背景图片文件名(放在 utils 文件夹)
    BACKGROUND_OPACITY = 0.3  # 背景图片透明度(0.0-1.0)

    @staticmethod
    def _get_font(size: int) -> ImageFont.FreeTypeFont:
        """获取字体"""
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "C:/Windows/Fonts/msyh.ttc",
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size)
                    test_bbox = font.getbbox("测试")
                    if test_bbox[2] - test_bbox[0] > 0:
                        return font
                except Exception:
                    continue

        raise RuntimeError("未找到可用的中文字体")

    @staticmethod
    def _draw_rounded_rectangle(draw: ImageDraw.ImageDraw, coords: tuple, radius: int, fill: tuple, outline: tuple = None, width: int = 2):
        """绘制圆角矩形"""
        x1, y1, x2, y2 = coords

        # 绘制主体
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)

        # 四个圆角
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)

        # 绘制边框
        if outline:
            draw.arc([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=outline, width=width)
            draw.arc([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=outline, width=width)
            draw.arc([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=outline, width=width)
            draw.arc([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=outline, width=width)
            draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
            draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
            draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
            draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)

    @staticmethod
    def _create_gradient_background(width: int, height: int) -> Image.Image:
        """创建渐变背景（支持背景图片）"""
        # 尝试加载背景图片
        bg_image_path = os.path.join(os.path.dirname(__file__), HelpImageGenerator.BACKGROUND_IMAGE)

        if os.path.exists(bg_image_path):
            try:
                # 加载背景图片
                bg_img = Image.open(bg_image_path).convert('RGB')

                # 缩放背景图片以适应目标尺寸（保持宽高比，裁剪多余部分）
                bg_ratio = bg_img.width / bg_img.height
                target_ratio = width / height

                if bg_ratio > target_ratio:
                    # 背景图更宽，按高度缩放
                    new_height = height
                    new_width = int(height * bg_ratio)
                else:
                    # 背景图更高，按宽度缩放
                    new_width = width
                    new_height = int(width / bg_ratio)

                bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 居中裁剪
                left = (new_width - width) // 2
                top = (new_height - height) // 2
                bg_img = bg_img.crop((left, top, left + width, top + height))

                # 应用透明度（通过叠加半透明的纯色层）
                overlay = Image.new('RGB', (width, height), HelpImageGenerator.BG_START_COLOR)
                opacity = int(255 * (1 - HelpImageGenerator.BACKGROUND_OPACITY))
                overlay.putalpha(opacity)

                # 创建带alpha通道的背景图
                bg_img_rgba = bg_img.convert('RGBA')
                overlay_rgba = Image.new('RGBA', (width, height), HelpImageGenerator.BG_START_COLOR + (opacity,))

                # 叠加
                result = Image.alpha_composite(bg_img_rgba, overlay_rgba)

                # 在上面叠加渐变效果（增强层次感）
                gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                gradient_draw = ImageDraw.Draw(gradient)

                for y in range(height):
                    r1, g1, b1 = HelpImageGenerator.BG_START_COLOR
                    r2, g2, b2 = HelpImageGenerator.BG_END_COLOR
                    ratio = y / height
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    alpha = int(80 * ratio)  # 渐变透明度
                    gradient_draw.line([(0, y), (width, y)], fill=(r, g, b, alpha))

                result = Image.alpha_composite(result, gradient)
                return result.convert('RGB')

            except Exception as e:
                # 加载失败，降级到纯渐变
                pass

        # 没有背景图或加载失败，使用纯渐变背景
        base = Image.new('RGB', (width, height), HelpImageGenerator.BG_START_COLOR)

        for y in range(height):
            r1, g1, b1 = HelpImageGenerator.BG_START_COLOR
            r2, g2, b2 = HelpImageGenerator.BG_END_COLOR

            ratio = y / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)

            draw = ImageDraw.Draw(base)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        return base

    @staticmethod
    def _wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list:
        """文本自动换行"""
        lines = []
        for line in text.split('\n'):
            if not line:
                lines.append('')
                continue

            current_line = ''
            for char in line:
                test_line = current_line + char
                bbox = font.getbbox(test_line)
                w = bbox[2] - bbox[0]

                if w <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = char

            if current_line:
                lines.append(current_line)

        return lines

    @staticmethod
    def generate_status_image(title: str, content_dict: dict, width: int = 1920) -> Tuple[bytes, str]:
        """生成状态图片（键值对显示 - 横屏双列布局 - 动态高度）"""
        font_title = HelpImageGenerator._get_font(HelpImageGenerator.TITLE_SIZE)
        font_subtitle = HelpImageGenerator._get_font(HelpImageGenerator.SUBTITLE_SIZE)
        font_text = HelpImageGenerator._get_font(HelpImageGenerator.TEXT_SIZE)

        # 第一步：计算所需高度
        num_columns = 2
        column_width = (width - HelpImageGenerator.PADDING * 2 - HelpImageGenerator.COLUMN_SPACING * (num_columns - 1)) // num_columns
        max_text_width = column_width - HelpImageGenerator.CARD_PADDING * 2

        # 计算标题区域高度
        title_bbox = font_title.getbbox(title)
        header_height = HelpImageGenerator.PADDING + (title_bbox[3] - title_bbox[1]) + 15 + 10 + HelpImageGenerator.SECTION_SPACING + 10

        # 分配sections到各列并计算每列高度
        sections_list = list(content_dict.items())
        sections_per_column = (len(sections_list) + num_columns - 1) // num_columns
        columns = [sections_list[i:i + sections_per_column] for i in range(0, len(sections_list), sections_per_column)]

        max_column_height = 0
        for column_sections in columns:
            column_height = 0
            for section_title, items in column_sections:
                card_height = HelpImageGenerator.CARD_PADDING
                subtitle_bbox = font_subtitle.getbbox(section_title)
                card_height += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                for key, value in items.items():
                    text_line = f"{key}: {value}"
                    wrapped_lines = HelpImageGenerator._wrap_text(text_line, max_text_width, font_text)
                    for _ in wrapped_lines:
                        text_bbox = font_text.getbbox('A')
                        card_height += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                card_height += HelpImageGenerator.CARD_PADDING
                column_height += card_height + HelpImageGenerator.SECTION_SPACING

            max_column_height = max(max_column_height, column_height)

        # 计算总高度
        height = header_height + max_column_height + HelpImageGenerator.PADDING

        # 第二步：创建图片
        # 创建渐变背景
        img = HelpImageGenerator._create_gradient_background(width, height)

        # 创建RGBA层用于半透明元素
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw = ImageDraw.Draw(img)

        # 绘制标题区域
        y = HelpImageGenerator.PADDING

        # 标题光晕
        glow_radius = 60
        for i in range(3):
            alpha = int(HelpImageGenerator.GLOW_COLOR[3] * (1 - i / 3))
            r, g, b = HelpImageGenerator.GLOW_COLOR[:3]
            draw_overlay.ellipse(
                [width//2 - glow_radius, y - glow_radius//2,
                 width//2 + glow_radius, y + glow_radius//2],
                fill=(r, g, b, alpha)
            )

        # 绘制主标题
        title_bbox = font_title.getbbox(title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, y), title, fill=HelpImageGenerator.TITLE_COLOR, font=font_title)
        y += (title_bbox[3] - title_bbox[1]) + 15

        # 装饰线
        line_y = y + 10
        draw.line([(width//2 - 100, line_y), (width//2 + 100, line_y)],
                  fill=HelpImageGenerator.ACCENT_COLOR, width=3)
        y += HelpImageGenerator.SECTION_SPACING + 10

        # 双列布局
        num_columns = 2
        column_width = (width - HelpImageGenerator.PADDING * 2 - HelpImageGenerator.COLUMN_SPACING * (num_columns - 1)) // num_columns
        max_text_width = column_width - HelpImageGenerator.CARD_PADDING * 2

        # 分配sections到各列
        sections_list = list(content_dict.items())
        sections_per_column = (len(sections_list) + num_columns - 1) // num_columns
        columns = [sections_list[i:i + sections_per_column] for i in range(0, len(sections_list), sections_per_column)]

        # 绘制各列
        start_y = y
        for col_idx, column_sections in enumerate(columns):
            x_offset = HelpImageGenerator.PADDING + col_idx * (column_width + HelpImageGenerator.COLUMN_SPACING)
            y = start_y

            for section_title, items in column_sections:
                # 计算卡片高度
                card_height = HelpImageGenerator.CARD_PADDING
                subtitle_bbox = font_subtitle.getbbox(section_title)
                card_height += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                for key, value in items.items():
                    text_line = f"{key}: {value}"
                    wrapped_lines = HelpImageGenerator._wrap_text(text_line, max_text_width, font_text)
                    for _ in wrapped_lines:
                        text_bbox = font_text.getbbox('A')
                        card_height += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                card_height += HelpImageGenerator.CARD_PADDING

                # 绘制卡片阴影
                shadow_offset = 4
                HelpImageGenerator._draw_rounded_rectangle(
                    draw_overlay,
                    (x_offset + shadow_offset,
                     y + shadow_offset,
                     x_offset + column_width + shadow_offset,
                     y + card_height + shadow_offset),
                    HelpImageGenerator.CARD_RADIUS,
                    fill=HelpImageGenerator.SHADOW_COLOR
                )

                # 绘制卡片背景
                HelpImageGenerator._draw_rounded_rectangle(
                    draw_overlay,
                    (x_offset, y,
                     x_offset + column_width, y + card_height),
                    HelpImageGenerator.CARD_RADIUS,
                    fill=HelpImageGenerator.CARD_BG_COLOR,
                    outline=HelpImageGenerator.CARD_BORDER_COLOR,
                    width=2
                )

                # 合并overlay到主图
                img.paste(overlay, (0, 0), overlay)
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw_overlay = ImageDraw.Draw(overlay)

                # 绘制章节标题
                card_y = y + HelpImageGenerator.CARD_PADDING
                draw.text(
                    (x_offset + HelpImageGenerator.CARD_PADDING, card_y),
                    f"▸ {section_title}",
                    fill=HelpImageGenerator.SUBTITLE_COLOR,
                    font=font_subtitle
                )
                card_y += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                # 绘制内容
                for key, value in items.items():
                    text_line = f"{key}: {value}"
                    wrapped_lines = HelpImageGenerator._wrap_text(text_line, max_text_width, font_text)
                    for wrapped_line in wrapped_lines:
                        draw.text(
                            (x_offset + HelpImageGenerator.CARD_PADDING + 15, card_y),
                            wrapped_line,
                            fill=HelpImageGenerator.TEXT_COLOR,
                            font=font_text
                        )
                        text_bbox = font_text.getbbox('A')
                        card_y += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                y += card_height + HelpImageGenerator.SECTION_SPACING

        # 最终合并overlay
        img.paste(overlay, (0, 0), overlay)

        # 转换为字节和base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_bytes, img_base64

    @staticmethod
    def generate_list_image(title: str, sections: list, width: int = 1920) -> Tuple[bytes, str]:
        """生成列表图片（横屏双列布局 - 动态高度）"""
        font_title = HelpImageGenerator._get_font(HelpImageGenerator.TITLE_SIZE)
        font_subtitle = HelpImageGenerator._get_font(HelpImageGenerator.SUBTITLE_SIZE)
        font_text = HelpImageGenerator._get_font(HelpImageGenerator.TEXT_SIZE)

        # 第一步：计算所需高度
        num_columns = 2
        column_width = (width - HelpImageGenerator.PADDING * 2 - HelpImageGenerator.COLUMN_SPACING * (num_columns - 1)) // num_columns
        max_text_width = column_width - HelpImageGenerator.CARD_PADDING * 2

        # 计算标题区域高度
        title_bbox = font_title.getbbox(title)
        header_height = HelpImageGenerator.PADDING + (title_bbox[3] - title_bbox[1]) + 15 + 10 + HelpImageGenerator.SECTION_SPACING + 10

        # 分配sections到各列并计算每列高度
        sections_per_column = (len(sections) + num_columns - 1) // num_columns
        columns = [sections[i:i + sections_per_column] for i in range(0, len(sections), sections_per_column)]

        max_column_height = 0
        for column_sections in columns:
            column_height = 0
            for section_title, items in column_sections:
                card_height = HelpImageGenerator.CARD_PADDING
                subtitle_bbox = font_subtitle.getbbox(section_title)
                card_height += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                for item in items:
                    wrapped_lines = HelpImageGenerator._wrap_text(str(item), max_text_width, font_text)
                    for _ in wrapped_lines:
                        text_bbox = font_text.getbbox('A')
                        card_height += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                card_height += HelpImageGenerator.CARD_PADDING
                column_height += card_height + HelpImageGenerator.SECTION_SPACING

            max_column_height = max(max_column_height, column_height)

        # 计算总高度
        height = header_height + max_column_height + HelpImageGenerator.PADDING

        # 第二步：创建图片
        # 创建渐变背景
        img = HelpImageGenerator._create_gradient_background(width, height)

        # 创建RGBA层用于半透明元素
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw = ImageDraw.Draw(img)

        # 绘制标题区域
        y = HelpImageGenerator.PADDING

        # 标题光晕
        glow_radius = 60
        for i in range(3):
            alpha = int(HelpImageGenerator.GLOW_COLOR[3] * (1 - i / 3))
            r, g, b = HelpImageGenerator.GLOW_COLOR[:3]
            draw_overlay.ellipse(
                [width//2 - glow_radius, y - glow_radius//2,
                 width//2 + glow_radius, y + glow_radius//2],
                fill=(r, g, b, alpha)
            )

        # 绘制主标题
        title_bbox = font_title.getbbox(title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, y), title, fill=HelpImageGenerator.TITLE_COLOR, font=font_title)
        y += (title_bbox[3] - title_bbox[1]) + 15

        # 装饰线
        line_y = y + 10
        draw.line([(width//2 - 100, line_y), (width//2 + 100, line_y)],
                  fill=HelpImageGenerator.ACCENT_COLOR, width=3)
        y += HelpImageGenerator.SECTION_SPACING + 10

        # 双列布局
        num_columns = 2
        column_width = (width - HelpImageGenerator.PADDING * 2 - HelpImageGenerator.COLUMN_SPACING * (num_columns - 1)) // num_columns
        max_text_width = column_width - HelpImageGenerator.CARD_PADDING * 2

        # 分配sections到各列
        sections_per_column = (len(sections) + num_columns - 1) // num_columns
        columns = [sections[i:i + sections_per_column] for i in range(0, len(sections), sections_per_column)]

        # 绘制各列
        start_y = y
        for col_idx, column_sections in enumerate(columns):
            x_offset = HelpImageGenerator.PADDING + col_idx * (column_width + HelpImageGenerator.COLUMN_SPACING)
            y = start_y

            for section_title, items in column_sections:
                # 计算卡片高度
                card_height = HelpImageGenerator.CARD_PADDING
                subtitle_bbox = font_subtitle.getbbox(section_title)
                card_height += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                for item in items:
                    wrapped_lines = HelpImageGenerator._wrap_text(str(item), max_text_width, font_text)
                    for _ in wrapped_lines:
                        text_bbox = font_text.getbbox('A')
                        card_height += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                card_height += HelpImageGenerator.CARD_PADDING

                # 绘制卡片阴影
                shadow_offset = 4
                HelpImageGenerator._draw_rounded_rectangle(
                    draw_overlay,
                    (x_offset + shadow_offset,
                     y + shadow_offset,
                     x_offset + column_width + shadow_offset,
                     y + card_height + shadow_offset),
                    HelpImageGenerator.CARD_RADIUS,
                    fill=HelpImageGenerator.SHADOW_COLOR
                )

                # 绘制卡片背景
                HelpImageGenerator._draw_rounded_rectangle(
                    draw_overlay,
                    (x_offset, y,
                     x_offset + column_width, y + card_height),
                    HelpImageGenerator.CARD_RADIUS,
                    fill=HelpImageGenerator.CARD_BG_COLOR,
                    outline=HelpImageGenerator.CARD_BORDER_COLOR,
                    width=2
                )

                # 合并overlay到主图
                img.paste(overlay, (0, 0), overlay)
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw_overlay = ImageDraw.Draw(overlay)

                # 绘制章节标题
                card_y = y + HelpImageGenerator.CARD_PADDING
                draw.text(
                    (x_offset + HelpImageGenerator.CARD_PADDING, card_y),
                    f"▸ {section_title}",
                    fill=HelpImageGenerator.SUBTITLE_COLOR,
                    font=font_subtitle
                )
                card_y += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                # 绘制内容
                for item in items:
                    wrapped_lines = HelpImageGenerator._wrap_text(str(item), max_text_width, font_text)
                    for wrapped_line in wrapped_lines:
                        draw.text(
                            (x_offset + HelpImageGenerator.CARD_PADDING + 15, card_y),
                            wrapped_line,
                            fill=HelpImageGenerator.TEXT_COLOR,
                            font=font_text
                        )
                        text_bbox = font_text.getbbox('A')
                        card_y += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                y += card_height + HelpImageGenerator.SECTION_SPACING

        # 最终合并overlay
        img.paste(overlay, (0, 0), overlay)

        # 转换为字节和base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_bytes, img_base64

    @staticmethod
    def generate_help_image(title: str, sections: list, width: int = 1920) -> Tuple[bytes, str]:
        """生成帮助图片（横屏双列布局 - 动态高度）"""
        font_title = HelpImageGenerator._get_font(HelpImageGenerator.TITLE_SIZE)
        font_subtitle = HelpImageGenerator._get_font(HelpImageGenerator.SUBTITLE_SIZE)
        font_text = HelpImageGenerator._get_font(HelpImageGenerator.TEXT_SIZE)

        # 第一步：计算所需高度
        num_columns = 2
        column_width = (width - HelpImageGenerator.PADDING * 2 - HelpImageGenerator.COLUMN_SPACING * (num_columns - 1)) // num_columns
        max_text_width = column_width - HelpImageGenerator.CARD_PADDING * 2

        # 计算标题区域高度
        title_bbox = font_title.getbbox(title)
        header_height = HelpImageGenerator.PADDING + (title_bbox[3] - title_bbox[1]) + 15 + 10 + HelpImageGenerator.SECTION_SPACING + 10

        # 分配sections到各列并计算每列高度
        sections_per_column = (len(sections) + num_columns - 1) // num_columns
        columns = [sections[i:i + sections_per_column] for i in range(0, len(sections), sections_per_column)]

        max_column_height = 0
        for column_sections in columns:
            column_height = 0
            for section_title, content_lines in column_sections:
                card_height = HelpImageGenerator.CARD_PADDING
                subtitle_bbox = font_subtitle.getbbox(section_title)
                card_height += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                for line in content_lines:
                    wrapped_lines = HelpImageGenerator._wrap_text(line, max_text_width, font_text)
                    for _ in wrapped_lines:
                        text_bbox = font_text.getbbox('A')
                        card_height += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                card_height += HelpImageGenerator.CARD_PADDING
                column_height += card_height + HelpImageGenerator.SECTION_SPACING

            max_column_height = max(max_column_height, column_height)

        # 计算总高度
        height = header_height + max_column_height + HelpImageGenerator.PADDING

        # 第二步：创建图片
        # 创建渐变背景
        img = HelpImageGenerator._create_gradient_background(width, height)

        # 创建RGBA层用于半透明元素
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw = ImageDraw.Draw(img)

        # 绘制标题区域装饰
        y = HelpImageGenerator.PADDING

        # 标题光晕效果
        glow_radius = 60
        for i in range(3):
            alpha = int(HelpImageGenerator.GLOW_COLOR[3] * (1 - i / 3))
            r, g, b = HelpImageGenerator.GLOW_COLOR[:3]
            draw_overlay.ellipse(
                [width//2 - glow_radius, y - glow_radius//2,
                 width//2 + glow_radius, y + glow_radius//2],
                fill=(r, g, b, alpha)
            )

        # 绘制主标题
        title_bbox = font_title.getbbox(title)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, y), title, fill=HelpImageGenerator.TITLE_COLOR, font=font_title)
        y += (title_bbox[3] - title_bbox[1]) + 15

        # 装饰线
        line_y = y + 10
        draw.line([(width//2 - 100, line_y), (width//2 + 100, line_y)],
                  fill=HelpImageGenerator.ACCENT_COLOR, width=3)
        y += HelpImageGenerator.SECTION_SPACING + 10

        # 双列布局
        num_columns = 2
        column_width = (width - HelpImageGenerator.PADDING * 2 - HelpImageGenerator.COLUMN_SPACING * (num_columns - 1)) // num_columns
        max_text_width = column_width - HelpImageGenerator.CARD_PADDING * 2

        # 分配sections到各列（尽量平均）
        sections_per_column = (len(sections) + num_columns - 1) // num_columns
        columns = [sections[i:i + sections_per_column] for i in range(0, len(sections), sections_per_column)]

        # 绘制各列
        start_y = y
        for col_idx, column_sections in enumerate(columns):
            x_offset = HelpImageGenerator.PADDING + col_idx * (column_width + HelpImageGenerator.COLUMN_SPACING)
            y = start_y

            for section_title, content_lines in column_sections:
                # 计算卡片高度
                card_height = HelpImageGenerator.CARD_PADDING
                subtitle_bbox = font_subtitle.getbbox(section_title)
                card_height += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                for line in content_lines:
                    wrapped_lines = HelpImageGenerator._wrap_text(line, max_text_width, font_text)
                    for _ in wrapped_lines:
                        text_bbox = font_text.getbbox('A')
                        card_height += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                card_height += HelpImageGenerator.CARD_PADDING

                # 绘制卡片阴影
                shadow_offset = 4
                HelpImageGenerator._draw_rounded_rectangle(
                    draw_overlay,
                    (x_offset + shadow_offset,
                     y + shadow_offset,
                     x_offset + column_width + shadow_offset,
                     y + card_height + shadow_offset),
                    HelpImageGenerator.CARD_RADIUS,
                    fill=HelpImageGenerator.SHADOW_COLOR
                )

                # 绘制卡片背景
                HelpImageGenerator._draw_rounded_rectangle(
                    draw_overlay,
                    (x_offset, y,
                     x_offset + column_width, y + card_height),
                    HelpImageGenerator.CARD_RADIUS,
                    fill=HelpImageGenerator.CARD_BG_COLOR,
                    outline=HelpImageGenerator.CARD_BORDER_COLOR,
                    width=2
                )

                # 合并overlay到主图
                img.paste(overlay, (0, 0), overlay)
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw_overlay = ImageDraw.Draw(overlay)

                # 绘制章节标题
                card_y = y + HelpImageGenerator.CARD_PADDING
                draw.text(
                    (x_offset + HelpImageGenerator.CARD_PADDING, card_y),
                    f"▸ {section_title}",
                    fill=HelpImageGenerator.SUBTITLE_COLOR,
                    font=font_subtitle
                )
                card_y += (subtitle_bbox[3] - subtitle_bbox[1]) + HelpImageGenerator.LINE_SPACING + 5

                # 绘制内容
                for line in content_lines:
                    wrapped_lines = HelpImageGenerator._wrap_text(line, max_text_width, font_text)
                    for wrapped_line in wrapped_lines:
                        if wrapped_line.strip().startswith('/'):
                            color = HelpImageGenerator.COMMAND_COLOR
                        else:
                            color = HelpImageGenerator.TEXT_COLOR

                        draw.text(
                            (x_offset + HelpImageGenerator.CARD_PADDING + 15, card_y),
                            wrapped_line,
                            fill=color,
                            font=font_text
                        )
                        text_bbox = font_text.getbbox('A')
                        card_y += (text_bbox[3] - text_bbox[1]) + HelpImageGenerator.LINE_SPACING

                y += card_height + HelpImageGenerator.SECTION_SPACING

        # 最终合并overlay
        img.paste(overlay, (0, 0), overlay)

        # 转换为字节和base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        return img_bytes, img_base64
