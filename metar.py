"""
Author: cg8-5712
Date: 2025-04-20
Version: 1.0.0
License: GPL-3.0
LastEditTime: 2025-04-20 16:30:00
Title: METAR/TAF Weather Query Plugin
Description: This plugin allows users to query METAR and TAF weather
             reports for airports using their ICAO codes.
             The results can be displayed in either text or image format.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple
from bs4 import BeautifulSoup
import requests

@dataclass
class MetarInfo:
    """METAR 数据模型"""
    station_code: str
    metar_info: dict
    taf_periods: list

    @staticmethod
    async def get_weather_info(station_code: str) -> Tuple[dict, list]:
        """获取天气数据"""
        url = f"https://aviationweather.gov/api/data/metar?ids={station_code}&format=html&taf=true"

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except requests.Timeout:
            return None, "请求超时"
        except requests.RequestException as e:
            return None, f"请求失败: {e}"

        if response.status_code != 200:
            return None, "获取数据失败"

        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', class_='decoded')

        if not tables:
            return None, "未找到天气数据"

        # 解析 METAR 数据
        metar_info = {}
        metar_data = tables[0]
        for row in metar_data.find_all('tr'):
            label = row.find('span', class_='leftLabel') or row.find('span', class_='leftData')
            if label:
                key = label.text.strip(':')
                value = row.find_all('td')[-1].text.strip()
                metar_info[key] = value

        # 解析 TAF 数据
        taf_periods = []
        if len(tables) > 1:
            taf_data = tables[1]
            taf_periods = MetarInfo._parse_taf_data(taf_data)

        return metar_info, taf_periods

    @staticmethod
    def _parse_taf_data(taf_data) -> list:
        """解析TAF数据"""
        taf_periods = []
        current_period = {}
        for row in taf_data.find_all('tr'):
            label = (row.find('span', class_='leftLabel') or
                     row.find('span', class_='leftData') or
                     row.find('span', class_='leftWxData'))
            if label:
                key = label.text.strip(':')
                value = row.find_all('td')[-1].text.strip()

                if key == 'Forecast period':
                    if current_period:
                        taf_periods.append(current_period)
                        current_period = {}
                    current_period['period'] = value
                elif key == 'Text':
                    current_period['raw_text'] = value
                elif key == 'Forecast type':
                    current_period['type'] = value
                elif key in ['Winds', 'Visibility', 'Clouds',
                             'Weather', 'Temperature', 'Ceiling']:
                    current_period[key.lower()] = value

        if current_period:
            taf_periods.append(current_period)

        return taf_periods

    def format_text_output(self) -> str:
        """格式化文本输出"""
        output = f"""== {self.station_code} 气象报文 ==
报文时间: {self.metar_info.get('Conditions at', 'N/A')}
原始报文: {self.metar_info.get('Text', 'N/A')}

温度: {self.metar_info.get('Temperature', 'N/A')}
露点: {self.metar_info.get('Dewpoint', 'N/A')}
气压: {self.metar_info.get('Pressure (altimeter)', 'N/A')}
风向风速: {self.metar_info.get('Winds', 'N/A')}
能见度: {self.metar_info.get('Visibility', 'N/A')}
云层: {self.metar_info.get('Clouds', 'N/A')}

== 预报信息 =="""

        for period in self.taf_periods:
            output += f"""
预报时段: {period.get('period', 'N/A')}
原始报文: {period.get('raw_text', 'N/A')}
预报类型: {period.get('type', 'N/A')}
风向风速: {period.get('winds', 'N/A')}
能见度: {period.get('visibility', 'N/A')}
云层: {period.get('clouds', 'N/A')}
天气现象: {period.get('weather', 'N/A')}
温度: {period.get('temperature', 'N/A')}
云底高: {period.get('ceiling', 'N/A')}"""

        return output

    def prepare_template_data(self) -> dict:
        """准备模板数据"""
        metar_rows = []
        for label, key in [
            ("报文时间", "Conditions at"),
            ("原始报文", "Text"),
            ("温度", "Temperature"),
            ("露点", "Dewpoint"),
            ("气压", "Pressure (altimeter)"),
            ("风向风速", "Winds"),
            ("能见度", "Visibility"),
            ("云层", "Clouds")
        ]:
            metar_rows.append({
                "label": label,
                "value": self.metar_info.get(key, "N/A")
            })

        taf_periods = []
        for period in self.taf_periods:
            rows = []
            for label, key in [
                ("原始报文", "raw_text"),
                ("预报类型", "type"),
                ("风向风速", "winds"),
                ("能见度", "visibility"),
                ("云层", "clouds"),
                ("天气现象", "weather"),
                ("温度", "temperature"),
                ("云底高", "ceiling")
            ]:
                rows.append({
                    "label": label,
                    "value": period.get(key, "N/A")
                })

            taf_periods.append({
                "period": period.get("period", "N/A"),
                "rows": rows
            })

        return {
            "station_code": self.station_code,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metar_rows": metar_rows,
            "taf_periods": taf_periods
        }
