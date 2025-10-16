# 地理位置参数
LOCATION = {
    'latitude': 31.30,           # 苏州纬度 (度N)
    'longitude': 120.62,         # 苏州经度 (度E)
    'altitude': 5,               # 海拔高度 (m)
    'timezone': 'Asia/Shanghai', # 时区
    'name': '苏州'
}

# 系统配置参数
SYSTEM = {
    'capacity_kw': 1000,         # 装机容量 (kW)
    'area_m2': 5000,             # 安装面积 (m²)
    'tilt': 3,                   # 倾角 (度)
    'azimuth': 180,              # 方位角 (度) - 正南180度
    'albedo': 0.2,               # 地面反照率
    'mounting_type': 'roof_mounted',  # 安装类型: 贴装彩钢瓦
}

# 光伏组件参数
MODULE = {
    # 基本参数
    'name': 'Standard 545W Mono-Si',
    'technology': 'mono-Si',
    'pmp': 545,                  # 最大功率 (W)
    'vmp': 41.5,                 # 最大功率点电压 (V)
    'imp': 13.13,                # 最大功率点电流 (A)
    'voc': 49.7,                 # 开路电压 (V)
    'isc': 13.95,                # 短路电流 (A)

    # 温度系数
    'alpha_sc': 0.0005,          # 短路电流温度系数 (%/C)
    'beta_voc': -0.0029,         # 开路电压温度系数 (%/C)
    'gamma_pmp': -0.0035,        # 功率温度系数 (%/C)

    # 工作条件
    'T_noct': 50,                # 标称工作温度 (C)
    'T_ref': 25,                 # 参考温度 (C)
    'G_ref': 1000,               # 参考辐照度 

    # 物理参数
    'area': 2.0,                 # 单块组件面积 (m²)
    'cells_in_series': 144,      # 串联电池片数

    # 光伏板结构 (五层)
    'structure': {
        'layer_1': 'Tempered Glass (3.2mm)',
        'layer_2': 'EVA',
        'layer_3': 'Cells (Mono-Si)',
        'layer_4': 'EVA',
        'layer_5': 'Triplo-layer Back Sheet'
    }
}

# 计算组件数量
MODULE['quantity'] = int(SYSTEM['capacity_kw'] * 1000 / MODULE['pmp'])

# 逆变器参数 (集中式)
INVERTER = {
    'type': 'central',           # 类型: 集中式
    'name': 'Central Inverter 1000kW',
    'pdc0': 1000,                # 额定直流输入功率 (kW)
    'pac0': 1000,                # 额定交流输出功率 (kW)
    'eta_inv_nom': 0.98,         # 额定效率 (欧洲效率)
    'eta_inv_ref': 0.9637,       # 参考效率
    'pdc_min': 50,               # 最小启动功率 (kW)
    'pdc_max': 1050,             # 最大直流输入功率 (kW)
    'vdc_min': 450,              # 最小直流电压 (V)
    'vdc_max': 1000,             # 最大直流电压 (V)
    'vdc_nom': 700,              # 额定直流电压 (V)
    'mppt_low': 500,             # MPPT下限 (V)
    'mppt_high': 850,            # MPPT上限 (V)
    'quantity': 1                # 逆变器数量
}

# 温度模型参数
TEMPERATURE_MODEL = {
    'model': 'faiman',
    'u0': 29.0,                  # 对流热传导系数
    'u1': 0.0,                   # 风速系数 
}

# 入射角损失模型参数
IAM_MODEL = {
    'model': 'physical',
    'n': 1.526,                  # 玻璃折射率
    'K': 4.0,                    # 消光系数
    'L': 0.002,                  # 玻璃厚度 2mm
}
