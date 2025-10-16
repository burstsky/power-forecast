import pandas as pd
import numpy as np
import pvlib
from datetime import datetime

from src.data.weather_fetcher import PVGISWeatherFetcher
from src.models.irradiance import IrradianceModel
from src.models.temperature import TemperatureModel
from src.models.losses import SystemLosses

class PVSimulator:
    """光伏系统仿真器"""
    def __init__(self, location_params, system_params, module_params, inverter_params, loss_params):

        self.location = location_params
        self.system = system_params
        self.module = module_params
        self.inverter = inverter_params
        self.loss_params = loss_params

        # 初始化子模块
        self.weather_fetcher = PVGISWeatherFetcher(
            latitude=location_params['latitude'],
            longitude=location_params['longitude'],
            altitude=location_params['altitude']
        )

        self.irradiance_model = IrradianceModel(
            latitude=location_params['latitude'],
            longitude=location_params['longitude'],
            altitude=location_params['altitude'],
            tilt=system_params['tilt'],
            azimuth=system_params['azimuth'],
            albedo=system_params['albedo']
        )

        self.temperature_model = TemperatureModel(
            mounting_type=system_params['mounting_type'],
            model='faiman'
        )

        self.loss_model = SystemLosses(loss_params)

    def run_simulation(self):
        print(f"地点: {self.location['name']}")
        print(f"装机容量: {self.system['capacity_kw']} kW")
        print(f"倾角: {self.system['tilt']}度, 方位角: {self.system['azimuth']}度")

        # 步骤1: 获取气象数据
        print("\n[1/7] 获取气象数据...")
        weather_df = self.weather_fetcher.fetch_tmy_data()

        # 步骤2: 计算POA辐照度
        print("\n[2/7] 计算倾斜面辐照度...")
        poa_df = self.irradiance_model.calculate_poa(weather_df)

        # 步骤3: 计算组件温度
        print("\n[3/7] 计算组件温度...")
        cell_temp = self.temperature_model.calculate_cell_temperature(
            poa_global=poa_df['poa_global'],
            temp_air=poa_df['temp_air'],
            wind_speed=poa_df['wind_speed']
        )
        poa_df['cell_temp'] = cell_temp

        # 步骤4: 计算DC功率
        print("\n[4/7] 计算直流功率...")
        dc_power = self._calculate_dc_power(
            poa_effective=poa_df['poa_effective'],
            cell_temp=poa_df['cell_temp']
        )
        poa_df['dc_power_kw'] = dc_power

        # 步骤5: 应用系统损失
        print("\n[5/7] 应用系统损失...")
        dc_power_after_loss = self.loss_model.apply_all_losses(dc_power)
        poa_df['dc_power_after_loss_kw'] = dc_power_after_loss
        print(f"  系统直流效率: {self.loss_model.get_system_efficiency()*100:.2f}%")
        print(f"  总损失: {self.loss_model.get_total_loss_percentage():.2f}%")

        # 步骤6: 计算AC功率
        print("\n[6/7] 计算交流功率...")
        ac_power = self._calculate_ac_power(dc_power_after_loss)
        poa_df['ac_power_kw'] = ac_power

        # 步骤7: 计算发电量
        print("\n[7/7] 计算发电量...")
        poa_df['energy_kwh'] = ac_power  

        # 整理结果DataFrame
        results_df = self._format_results(poa_df)

        return results_df

    def _calculate_dc_power(self, poa_effective, cell_temp):
        """计算直流功率"""
        pdc0 = self.system['capacity_kw']
        gamma_pdc = self.module['gamma_pmp']
        temp_ref = self.module['T_ref']

        dc_power = pvlib.pvsystem.pvwatts_dc(
            effective_irradiance=poa_effective,
            temp_cell=cell_temp,
            pdc0=pdc0,
            gamma_pdc=gamma_pdc,
            temp_ref=temp_ref
        )

        return dc_power.clip(lower=0)

    def _calculate_ac_power(self, dc_power):
        """计算交流功率"""
        pdc0 = self.inverter['pdc0']
        eta_inv_nom = self.inverter['eta_inv_nom']
        eta_inv_ref = self.inverter.get('eta_inv_ref', 0.9637)

        ac_power = pvlib.inverter.pvwatts(
            pdc=dc_power,
            pdc0=pdc0,
            eta_inv_nom=eta_inv_nom,
            eta_inv_ref=eta_inv_ref
        )

        pac_max = self.inverter['pac0']
        return ac_power.clip(lower=0, upper=pac_max)

    def _format_results(self, poa_df):
        """
        格式化结果DataFrame - 只保留必要的列
        """
        # 只选择必要的输出列
        output_columns = ['energy_kwh']
        
        results_df = poa_df[output_columns].copy()
        
        # 重置索引,将datetime变为列
        results_df = results_df.reset_index()
        
        results_df['energy_kwh'] = results_df['energy_kwh'].fillna(0)
        
        return results_df

if __name__ == '__main__':
    from src.config.system_params import LOCATION, SYSTEM, MODULE, INVERTER
    from src.config.loss_params import LOSSES

    # 创建仿真器
    simulator = PVSimulator(LOCATION, SYSTEM, MODULE, INVERTER, LOSSES)

    # 运行仿真
    results = simulator.run_simulation()

    # 显示结果预览
    print("\n结果数据预览:")
    print(results.head(10))

    # 月度统计
    monthly_summary = simulator.get_monthly_summary(results)
    print("\n月度统计:")
    print(monthly_summary)
