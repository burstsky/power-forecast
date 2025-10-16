import pandas as pd
import numpy as np
import pvlib


class TemperatureModel:
    """光伏组件温度计算模型"""

    def __init__(self, mounting_type='roof_mounted', model='faiman'):
        """
        初始化温度模型
        """
        self.mounting_type = mounting_type
        self.model = model
        self.params = self._get_temperature_model_params()

    def _get_temperature_model_params(self):
        """
        获取温度模型参数

        """
        if self.model == 'faiman':
            # Faiman模型参数
            if self.mounting_type == 'roof_mounted':
                # 贴装彩钢瓦: 散热条件差
                params = {
                    'u0': 29.0,  # 对流热传导系数 (W_per_m2K)
                    'u1': 1.0,   # 风速系数 (W/(m2K·(m/s)))
                }
            elif self.mounting_type == 'open_rack':
                # 标准开放式支架
                params = {
                    'u0': 25.0,
                    'u1': 6.84,
                }
            else:
                # 绝缘背板
                params = {
                    'u0': 26.0,
                    'u1': 1.2,
                }

        elif self.model == 'pvsyst':
            # PVsyst模型参数
            if self.mounting_type == 'roof_mounted':
                params = {
                    'u_c': 29.0,  # 常数热损失系数
                    'u_v': 0.0,   # 风速相关系数
                }
            else:
                params = {
                    'u_c': 25.0,
                    'u_v': 1.2,
                }

        else:
            # 默认使用Faiman开放式参数
            params = {
                'u0': 25.0,
                'u1': 6.84,
            }

        return params

    def calculate_cell_temperature(self, poa_global, temp_air, wind_speed):
        """
        计算光伏组件工作温度

        """
        print(f"正在计算组件温度 (模型: {self.model}, 安装: {self.mounting_type})...")

        if self.model == 'faiman':
            # Faiman模型
            cell_temp = pvlib.temperature.faiman(
                poa_global=poa_global,
                temp_air=temp_air,
                wind_speed=wind_speed,
                u0=self.params['u0'],
                u1=self.params['u1']
            )

        elif self.model == 'pvsyst':
            # PVsyst模型
            cell_temp = pvlib.temperature.pvsyst_cell(
                poa_global=poa_global,
                temp_air=temp_air,
                wind_speed=wind_speed,
                u_c=self.params['u_c'],
                u_v=self.params['u_v']
            )

        else:

            noct = 50 if self.mounting_type == 'roof_mounted' else 45
            cell_temp = temp_air + (noct - 20) / 800 * poa_global

        # 后处理
        # 1. 夜间处理: POA=0时, 组件温度=环境温度
        cell_temp = pd.Series(np.where(poa_global <= 0, temp_air, cell_temp), index=poa_global.index)

        # 2. 确保组件温度 >= 环境温度
        cell_temp = pd.Series(np.maximum(cell_temp, temp_air), index=poa_global.index)

        # 3. 物理合理性检查
        cell_temp = cell_temp.clip(lower=-40, upper=85)  # 组件工作温度范围

        print(f"[OK] 温度计算完成")
        print(f"  环境温度范围: {temp_air.min():.1f}C ~ {temp_air.max():.1f}C")
        print(f"  组件温度范围: {cell_temp.min():.1f}C ~ {cell_temp.max():.1f}C")
        print(f"  平均温升: {(cell_temp - temp_air).mean():.1f}C")
        print(f"  最大温升: {(cell_temp - temp_air).max():.1f}C")

        return cell_temp

    def get_temperature_statistics(self, cell_temp, temp_air, poa_global):
        """
        获取温度统计信息

        """
        # 只统计白天数据 (POA > 10 W_per_m2)
        daytime_mask = poa_global > 10

        stats = {
            'avg_ambient_temp': temp_air.mean(),
            'avg_cell_temp': cell_temp.mean(),
            'avg_cell_temp_daytime': cell_temp[daytime_mask].mean(),
            'max_cell_temp': cell_temp.max(),
            'min_cell_temp': cell_temp.min(),
            'avg_temperature_rise': (cell_temp - temp_air).mean(),
            'avg_temperature_rise_daytime': (cell_temp[daytime_mask] - temp_air[daytime_mask]).mean(),
            'max_temperature_rise': (cell_temp - temp_air).max(),
            'hours_above_25C': (cell_temp > 25).sum(),
            'hours_above_45C': (cell_temp > 45).sum(),
            'hours_above_65C': (cell_temp > 65).sum(),
        }

        return stats

    def estimate_temperature_loss(self, cell_temp, temp_ref=25, gamma_pmp=-0.0035):
        """
        估算温度导致的功率损失

        """
        # 温度损失系数
        temp_coefficient = 1 + gamma_pmp * (cell_temp - temp_ref)

        temp_coefficient = temp_coefficient.clip(lower=0.5, upper=1.1)

        return temp_coefficient
