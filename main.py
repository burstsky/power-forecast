import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.pv_simulator import PVSimulator
from src.utils.exporter import export_simulation_results
from src.config.system_params import LOCATION, SYSTEM, MODULE, INVERTER
from src.config.loss_params import LOSSES




def main():
    # 记录开始时间
    start_time = time.time()

    try:
        # 步骤1: 创建仿真器
        simulator = PVSimulator(
            location_params=LOCATION,
            system_params=SYSTEM,
            module_params=MODULE,
            inverter_params=INVERTER,
            loss_params=LOSSES
        )

        # 步骤2: 运行仿真
        print("\n开始运行仿真...")
        results_df = simulator.run_simulation()

        # 步骤3: 导出Excel
        print("导出结果...")

        # 生成文件名 (带时间戳)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"pv_generation_suzhou_1MW_{timestamp}.xlsx"
        output_path = os.path.join("output", output_filename)

        # 确保输出目录存在
        os.makedirs("output", exist_ok=True)

        # 导出
        export_simulation_results(results_df, simulator, output_path)

        # 计算耗时
        elapsed_time = time.time() - start_time

        # 打印完成信息
        print("仿真完成!")
        print(f"总耗时: {elapsed_time:.1f} 秒")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
