import requests
import pandas as pd
import json
from datetime import datetime
import pytz


class PVGISWeatherFetcher:
    """PVGIS气象数据获取器"""

    def __init__(self, latitude, longitude, altitude=0):
        """
        初始化PVGIS数据获取器

        Args:
            latitude (float): 纬度 (度N)
            longitude (float): 经度 (度E)
            altitude (int): 海拔高度 (m), 默认0
        """
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.base_url = "https://re.jrc.ec.europa.eu/api/v5_2"

    def fetch_tmy_data(self, startyear=2005, endyear=2020):
        """
        获取典型气象年(TMY)数据
        """
        print(f"正在从PVGIS获取气象数据...")
        print(f"位置: 纬度{self.latitude}度N, 经度{self.longitude}度E, 海拔{self.altitude}m")

        # 构建API请求URL
        endpoint = f"{self.base_url}/tmy"
        params = {
            'lat': self.latitude,
            'lon': self.longitude,
            'startyear': startyear,
            'endyear': endyear,
            'outputformat': 'json'
        }

        try:
            # 发送GET请求
            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()

            # 提取小时数据
            if 'outputs' in data and 'tmy_hourly' in data['outputs']:
                hourly_data = data['outputs']['tmy_hourly']
                df = self._parse_tmy_data(hourly_data)
                print(f"成功获取 {len(df)} 小时气象数据")
                
                # 数据验证
                validation = self.validate_data(df)
                print(f"  数据完整性: {'通过' if validation['is_complete'] else '失败'}")
                print(f"  物理合理性: {'通过' if validation['is_physically_valid'] else '失败'}")
                
                if not validation['is_complete'] or not validation['is_physically_valid']:
                    print(" 数据验证发现问题，请检查数据质量")
                
                return df
            else:
                raise Exception("PVGIS响应格式错误: 未找到tmy_hourly数据")

        except requests.exceptions.RequestException as e:
            raise Exception(f"PVGIS API请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失败: {str(e)}")

    def _parse_tmy_data(self, hourly_data):
        """
        解析PVGIS TMY数据
        """
        # 转换为DataFrame
        df = pd.DataFrame(hourly_data)

        # 构建时间戳
        # PVGIS格式: time(UTC): YYYYMMDDHHMM
        df['datetime'] = pd.to_datetime(df['time(UTC)'], format='%Y%m%d:%H%M')

        # 转换为目标时区 (Asia/Shanghai = UTC+8)
        df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')

        # 重命名列 (PVGIS列名 -> 标准列名)
        column_mapping = {
            'G(h)': 'ghi',           # 全局水平辐照度 (W_per_m2)
            'Gb(n)': 'dni',          # 直射法向辐照度 (W_per_m2)
            'Gd(h)': 'dhi',          # 漫射水平辐照度 (W_per_m2)
            'T2m': 'temp_air',       # 2米高度气温 (C)
            'WS10m': 'wind_speed',   # 10米高度风速 (m/s)
            'RH': 'relative_humidity',  # 相对湿度 (%)
            'SP': 'pressure',        # 地表气压 (Pa)
        }

        df = df.rename(columns=column_mapping)

        # 选择需要的列
        output_columns = ['datetime', 'ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']

        # 添加可选列(如果存在)
        if 'relative_humidity' in df.columns:
            output_columns.append('relative_humidity')
        if 'pressure' in df.columns:
            output_columns.append('pressure')

        df = df[output_columns]

        # 数据类型转换
        for col in ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 处理缺失值
        df = df.fillna(0)

        # 设置datetime为索引
        df = df.set_index('datetime')

        # 确保数据按时间排序
        df = df.sort_index()

        return df

    def validate_data(self, df):
        """
        验证气象数据的完整性和合理性
        """
        validation = {
            'total_hours': len(df),
            'expected_hours': 8760,
            'missing_values': df.isnull().sum().to_dict(),
            'data_range': {
                'ghi': (df['ghi'].min(), df['ghi'].max()),
                'dni': (df['dni'].min(), df['dni'].max()),
                'dhi': (df['dhi'].min(), df['dhi'].max()),
                'temp_air': (df['temp_air'].min(), df['temp_air'].max()),
                'wind_speed': (df['wind_speed'].min(), df['wind_speed'].max()),
            },
            'negative_irradiance': (df[['ghi', 'dni', 'dhi']] < 0).sum().to_dict(),
        }

        # 检查完整性
        validation['is_complete'] = (validation['total_hours'] == 8760)

        # 检查物理合理性
        validation['is_physically_valid'] = all([
            validation['negative_irradiance']['ghi'] == 0,
            validation['negative_irradiance']['dni'] == 0,
            validation['negative_irradiance']['dhi'] == 0,
        ])

        return validation


if __name__ == '__main__':
    print("PVGIS气象数据获取测试")

    # 创建获取器
    fetcher = PVGISWeatherFetcher(
        latitude=31.30,
        longitude=120.62,
        altitude=5
    )

    # 获取数据
    try:
        weather_df = fetcher.fetch_tmy_data()

        print("\n数据预览:")
        print(weather_df.head(10))

        print("\n数据统计:")
        print(weather_df.describe())

        # 验证数据
        validation = fetcher.validate_data(weather_df)
        print("\n数据验证:")
        print(f"  总小时数: {validation['total_hours']}")
        print(f"  数据完整: {validation['is_complete']}")
        print(f"  物理合理: {validation['is_physically_valid']}")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
