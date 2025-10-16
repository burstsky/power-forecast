# 系统损失参数 
LOSSES = {
    # 环境相关损失
    'soiling': 0.02,             # 灰层/污染损失
    'shading': 0.00,             # 阴影损失
    'snow': 0.00,                # 积雪损失 

    # 系统组件损失
    'mismatch': 0.02,            # 组件失配损失
    'wiring': 0.02,              # 线损 (直流侧)
    'connections': 0.005,        # 接头/接插件损失

    # 组件特性损失
    'lid': 0.015,                # 光致衰减 
    'nameplate_rating': 0.01,    # 铭牌功率误差
    'age': 0.00,                 # 老化损失

    # 系统可用性
    'availability': 0.01,        # 系统可用性损失 (维护/故障停机)
}

# 损失类型中文名称映射
LOSS_NAMES = {
    'soiling': '灰层污染损失',
    'shading': '阴影遮挡损失',
    'snow': '积雪覆盖损失',
    'mismatch': '组件失配损失',
    'wiring': '直流线损',
    'connections': '接头连接损失',
    'lid': '光致衰减',
    'nameplate_rating': '铭牌功率误差',
    'age': '老化损失',
    'availability': '系统可用性损失',
}


def get_total_dc_loss():
    """
    计算总直流侧损失系数
    """
    remaining_efficiency = 1.0

    for loss_name, loss_value in LOSSES.items():
        remaining_efficiency *= (1 - loss_value)

    total_loss = 1 - remaining_efficiency
    return total_loss


def get_loss_breakdown():
    """
    获取损失分解字典
    """
    breakdown = {}
    for key, value in LOSSES.items():
        if value > 0:  # 只包含非零损失
            breakdown[LOSS_NAMES[key]] = value
    return breakdown


def apply_dc_losses(dc_power):
    """
    对直流功率应用所有损失
    """
    return dc_power * (1 - get_total_dc_loss())


# 预计算总损失
TOTAL_DC_LOSS = get_total_dc_loss()
SYSTEM_EFFICIENCY = 1 - TOTAL_DC_LOSS
