import pandas as pd
import numpy as np
import pvlib
from pvlib import solarposition, irradiance, iam


class IrradianceModel:
    """倾斜面辐照度计算模型"""

    def __init__(self, latitude, longitude, altitude, tilt, azimuth, albedo=0.2):
        """
        初始化辐照度模型
        """
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.tilt = tilt
        self.azimuth = azimuth
        self.albedo = albedo

    def calculate_poa(self, weather_df):
        print("计算倾斜面辐照度(POA)...")

        # 1. 计算太阳位置
        solar_position = self._get_solar_position(weather_df)

        # 2. 计算倾斜面辐照度 
        poa_components = self._calculate_poa_components(
            weather_df,
            solar_position
        )

        # 3. 计算入射角(AOI)
        aoi = self._calculate_aoi(solar_position)

        # 4. 计算入射角修正系数(IAM) 
        iam_value = self._calculate_iam(aoi)

        # 5. 整合结果
        result_df = weather_df.copy()

        # 添加太阳位置
        result_df['solar_zenith'] = solar_position['apparent_zenith']
        result_df['solar_azimuth'] = solar_position['azimuth']

        # 添加POA组件
        result_df['poa_global'] = poa_components['poa_global']
        result_df['poa_direct'] = poa_components['poa_direct']
        result_df['poa_diffuse'] = poa_components['poa_diffuse']
        result_df['poa_sky_diffuse'] = poa_components['poa_sky_diffuse']
        result_df['poa_ground_diffuse'] = poa_components['poa_ground_diffuse']

        # 添加AOI和IAM
        result_df['aoi'] = aoi
        result_df['iam'] = iam_value

        # 计算有效POA (应用IAM损失)
        result_df['poa_effective'] = result_df['poa_global'] * result_df['iam']

        # 确保非负值
        result_df['poa_effective'] = result_df['poa_effective'].clip(lower=0)

        print(f"POA计算完成")
        print(f"  平均POA: {result_df['poa_global'].mean():.1f} W_per_m2")
        print(f"  最大POA: {result_df['poa_global'].max():.1f} W_per_m2")
        print(f"  平均IAM: {result_df['iam'].mean():.3f}")

        return result_df

    def _get_solar_position(self, weather_df):
        """
        计算太阳位置
        """
        solar_position = solarposition.get_solarposition(
            time=weather_df.index,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            temperature=weather_df['temp_air'],
        )

        return solar_position

    def _calculate_poa_components(self, weather_df, solar_position):
        """
        计算倾斜面辐照度各组件

        使用Perez天空漫射模型
        """
        # 提取DNI, DHI, GHI
        dni = weather_df['dni']
        dhi = weather_df['dhi']
        ghi = weather_df['ghi']

        # 计算地外辐照度
        dni_extra = irradiance.get_extra_radiation(weather_df.index)

        # 计算空气质量
        airmass = pvlib.atmosphere.get_relative_airmass(solar_position['apparent_zenith'])
        airmass_absolute = pvlib.atmosphere.get_absolute_airmass(airmass)

        # 使用Perez模型计算倾斜面总辐照度
        poa_irradiance = irradiance.get_total_irradiance(
            surface_tilt=self.tilt,
            surface_azimuth=self.azimuth,
            solar_zenith=solar_position['apparent_zenith'],
            solar_azimuth=solar_position['azimuth'],
            dni=dni,
            ghi=ghi,
            dhi=dhi,
            dni_extra=dni_extra,
            airmass=airmass_absolute,
            albedo=self.albedo,
            model='perez'  # Perez天空漫射模型
        )

        return poa_irradiance

    def _calculate_aoi(self, solar_position):
        """
        计算入射角(AOI - Angle of Incidence)

        """
        aoi = irradiance.aoi(
            surface_tilt=self.tilt,
            surface_azimuth=self.azimuth,
            solar_zenith=solar_position['apparent_zenith'],
            solar_azimuth=solar_position['azimuth']
        )

        return aoi

    def _calculate_iam(self, aoi):
        """
        计算入射角修正系数(IAM - Incidence Angle Modifier)

        使用Physical模型

        """
        iam_value = iam.physical(
            aoi=aoi,
            n=1.526,      # 玻璃折射率
            K=4.0,        # 消光系数
            L=0.002       # 玻璃厚度 2mm
        )

        # 处理无效值
        iam_value = iam_value.fillna(0)
        iam_value = iam_value.clip(lower=0, upper=1)

        return iam_value

    def get_annual_irradiance_summary(self, poa_df):
        """
        获取年度辐照度统计摘要

        """
        summary = {
            'annual_ghi_kwh_m2': poa_df['ghi'].sum() / 1000,  # kWh_per_m2
            'annual_poa_kwh_m2': poa_df['poa_global'].sum() / 1000,
            'annual_poa_effective_kwh_m2': poa_df['poa_effective'].sum() / 1000,
            'avg_daily_ghi_kwh_m2': poa_df['ghi'].sum() / 1000 / 365,
            'avg_daily_poa_kwh_m2': poa_df['poa_global'].sum() / 1000 / 365,
            'poa_to_ghi_ratio': poa_df['poa_global'].sum() / poa_df['ghi'].sum() if poa_df['ghi'].sum() > 0 else 0,
            'iam_loss_percent': (1 - poa_df['poa_effective'].sum() / poa_df['poa_global'].sum()) * 100 if poa_df['poa_global'].sum() > 0 else 0,
        }

        return summary
