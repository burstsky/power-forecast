import pandas as pd
import numpy as np


class SystemLosses:
    """系统损失模型"""

    def __init__(self, loss_params):
        self.loss_params = loss_params

    def apply_all_losses(self, dc_power):
        """
        对直流功率应用所有系统损失
        """
        power_after_loss = dc_power.copy() if isinstance(dc_power, pd.Series) else dc_power

        # 依次应用各项损失
        for loss_name, loss_value in self.loss_params.items():
            if loss_value > 0:
                power_after_loss = power_after_loss * (1 - loss_value)

        return power_after_loss

    def get_total_loss_factor(self):
        """
        计算总损失系数

        """
        retention_factor = 1.0
        for loss_value in self.loss_params.values():
            retention_factor *= (1 - loss_value)
        return retention_factor

    def get_total_loss_percentage(self):
        """
        获取总损失百分比
        """
        return (1 - self.get_total_loss_factor()) * 100

    def get_loss_breakdown(self, dc_power_series):
        """
        计算损失分解 (各项损失的绝对值)

        """
        breakdown = {}
        cumulative_power = dc_power_series.copy()

        for loss_name, loss_percentage in self.loss_params.items():
            if loss_percentage > 0:
                # 计算该项损失的绝对量
                loss_power = cumulative_power * loss_percentage
                loss_energy_kwh = loss_power.sum()

                breakdown[loss_name] = {
                    'percentage': loss_percentage * 100,  # 转为百分比
                    'energy_loss_kwh': loss_energy_kwh,
                }

                # 更新累积功率
                cumulative_power = cumulative_power * (1 - loss_percentage)

        # 添加总计
        total_loss_energy = dc_power_series.sum() - cumulative_power.sum()
        breakdown['total'] = {
            'percentage': self.get_total_loss_percentage(),
            'energy_loss_kwh': total_loss_energy,
        }

        return breakdown

    def get_loss_breakdown_summary(self, dc_power_series):
        """
        获取损失分解
        """
        from src.config.loss_params import LOSS_NAMES

        breakdown = self.get_loss_breakdown(dc_power_series)

        # 构建DataFrame
        data = []
        for loss_key, loss_data in breakdown.items():
            if loss_key == 'total':
                continue
            row = {
                '损失类型': LOSS_NAMES.get(loss_key, loss_key),
                '损失比例(%)': f"{loss_data['percentage']:.2f}",
                '年度损失电量(kWh)': f"{loss_data['energy_loss_kwh']:.0f}",
            }
            data.append(row)

        # 添加总计行
        if 'total' in breakdown:
            data.append({
                '损失类型': '总计',
                '损失比例(%)': f"{breakdown['total']['percentage']:.2f}",
                '年度损失电量(kWh)': f"{breakdown['total']['energy_loss_kwh']:.0f}",
            })

        df = pd.DataFrame(data)
        return df

    def apply_individual_loss(self, power, loss_name):
        """
        应用单项损失
        """
        if loss_name not in self.loss_params:
            raise ValueError(f"未知的损失类型: {loss_name}")

        loss_value = self.loss_params[loss_name]
        return power * (1 - loss_value)

    def get_system_efficiency(self):
        """
        获取系统直流效率 
        """
        return self.get_total_loss_factor()

    def estimate_annual_loss_impact(self, dc_energy_annual_kwh):
        """
        估算年度损失影响
        """
        total_loss_factor = self.get_total_loss_factor()
        final_energy = dc_energy_annual_kwh * total_loss_factor
        total_loss_energy = dc_energy_annual_kwh - final_energy

        impact = {
            'original_dc_energy_kwh': dc_energy_annual_kwh,
            'total_loss_energy_kwh': total_loss_energy,
            'final_dc_energy_kwh': final_energy,
            'total_loss_percentage': self.get_total_loss_percentage(),
            'system_efficiency': total_loss_factor * 100,
        }

        return impact
