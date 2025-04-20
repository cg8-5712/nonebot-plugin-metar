"""
Author: cg8-5712
Date: 2025-04-20
Version: 1.0.0
License: GPL-3.0
LastEditTime: 2025-04-20 16:30:00
Title: METAR/TAF Weather Query Plugin
Description: This plugin allows users to query METAR and TAF weather reports
             for airports using their ICAO codes.
             The results can be displayed in either text or image format.
"""

from nonebot import on_command
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from nonebot_plugin_htmlrender import template_to_pic
from nonebot_plugin_alconna import At, Text

from zhenxun.configs.path_config import TEMPLATE_PATH
from zhenxun.utils.message import MessageUtils
from .metar import MetarInfo

__plugin_meta__ = PluginMetadata(
    name="航空天气查询",
    description="查询机场 METAR/TAF 天气报告",
    usage="""
    指令:
        @机器人 wea [机场ICAO代码]: 以图片形式显示
        @机器人 wea [机场ICAO代码] --raw: 以文字形式显示
    """,
)

WeatherCommand = on_command("wea", rule=to_me(), priority=5, block=True)


@WeatherCommand.handle()
async def handle_weather(event: GroupMessageEvent, args=CommandArg()):
    """
    This function handles the weather command.
    It retrieves METAR and TAF weather reports for the specified airport ICAO code.
    The results can be displayed in either text or image format.
    """
    args = args.extract_plain_text().strip().split()
    if not args:
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text("请提供机场 ICAO 代码")
        ]).send(reply_to=True)
        return

    station_code = args[0].upper()
    show_raw = len(args) > 1 and args[1] == "--raw"

    # 获取天气数据
    metar_info, taf_periods = await MetarInfo.get_weather_info(station_code)
    if isinstance(taf_periods, str):  # 错误信息
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text(taf_periods)
        ]).send(reply_to=True)
        return

    weather_data = MetarInfo(station_code, metar_info, taf_periods)

    if show_raw:
        text_output = weather_data.format_text_output()
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            Text(text_output)
        ]).send(reply_to=True)
    else:
        template_data = weather_data.prepare_template_data()
        image = await template_to_pic(
            template_path=str(
                (TEMPLATE_PATH / "aviation" / "metar").absolute()),
            template_name="main.html",
            templates=template_data,
            pages={
                "viewport": {"width": 800, "height": 600},
                "base_url": f"file://{TEMPLATE_PATH}"
            },
            wait=2
        )
        await MessageUtils.build_message([
            At(flag="user", target=str(event.user_id)),
            image
        ]).send(reply_to=True)
