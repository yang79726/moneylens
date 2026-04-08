# -*- coding: utf-8 -*-
"""
MoneyLens 财务分析器 - 生存成本转换模块
功能：将金额换算为体力、粮食和猫咪评价，提供“生理性”消费感知。
"""
import pandas as pd


# 这是一个独立的工具函数，专门负责从原始数据中切分出月份统计
def extract_monthly_kpis(all_data_df):
    if all_data_df.empty:
        return {}

    df = all_data_df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['month_str'] = df['date'].dt.strftime('%Y-%m')

    monthly_dict = {}
    for month, group in df.groupby('month_str'):
        # 1. 基础数据清洗（保留原功能）
        group['type_final'] = group['type_final'].astype(str).str.strip()
        group['main_category'] = group['main_category'].astype(str).str.strip()

        # 2. 筛选支出并计算总额（保留原功能）
        exp_df = group[group['type_final'] == '支出']
        total_exp = exp_df['amount_abs'].sum()

        # 3. 计算恩格尔系数（保留原功能）
        food_exp = exp_df[exp_df['main_category'] == '餐饮美食']['amount_abs'].sum()
        engle_val = (food_exp / total_exp * 100) if total_exp > 0 else 0

        # --- 新增功能 A：深夜消费分析 ---
        # 提取小时数，判断是否在 22:00 - 04:00 之间
        group['hour'] = group['date'].dt.hour
        night_exp_count = len(group[(group['hour'] >= 22) | (group['hour'] <= 4)])
        # 如果深夜消费单数占比超过 20%，标记为深夜活跃
        is_night_owl = night_exp_count > (len(group) * 0.2)

        # --- 新增功能 B：消费画像判定 ---
        if engle_val > 60:
            persona_type = '食堂战神'
        elif is_night_owl:
            persona_type = '深夜购物狂'
        elif total_exp > 5000:  # 这里的 5000 可以根据你的实际高消费定义修改
            persona_type = '精致利己'
        else:
            persona_type = '稳健派'

        # 4. 计算天数（保留原功能）
        days = max((group['date'].max() - group['date'].min()).days + 1, 1)

        # 5. 更新字典（在原有基础上增加 persona_type）
        monthly_dict[month] = {
            "total_expense": f"{total_exp:,.2f}",
            "daily_avg": f"{(total_exp / days):,.2f}",
            "engle": f"{engle_val:.1f}%",
            "raw_total": total_exp,
            "raw_daily": total_exp / days,
            # 新增传出字段
            "persona_type": persona_type,
            "is_night_owl": is_night_owl
        }
    return monthly_dict

class LifeCostConverter:
    def __init__(self, total_expense_str, monthly_avg=3000.0):
        """
        :param total_expense_str: 传入来自 cost.py 的格式化字符串，如 "3,500.50"
        :param monthly_avg: 月度平均支出参考值，用于判定猫咪情绪
        """
        # 1. 字符串清洗与安全转换
        try:
            # 移除逗号并转为浮点数
            clean_val = str(total_expense_str).replace(',', '').strip()
            self.total = float(clean_val)
        except (ValueError, AttributeError):
            self.total = 0.0
            print(f"Converter Warning: 无法解析金额 '{total_expense_str}'，已设为 0")

        # 2. 设定换算常数 (已按要求调整)
        self.avg = float(monthly_avg) if monthly_avg > 0 else 3000.0
        self.RICE_PRICE = 2.6  # 大米单价：2.6元/斤
        self.MANUAL_LABOR_RATE = 20.0  # 搬砖价格：20.0元/小时

    def get_stats(self):
        """执行所有换算逻辑并返回给前端模板的字典"""

        # --- A. 体力投影 (搬砖) ---
        work_hours = self.total / self.MANUAL_LABOR_RATE
        work_days = work_hours / 8.0  # 假设每天标准体力劳动 8 小时

        # --- B. 物质投影 (粮食) ---
        rice_jin = self.total / self.RICE_PRICE
        rice_tons = rice_jin / 2000.0  # 1吨 = 2000斤
        # 假设一人一天消耗 1 斤粮，计算生存天数
        survival_days = int(rice_jin)

        # --- C. 情绪投影 (猫咪评价) ---
        # 计算当前支出与均值的比例
        ratio = self.total / self.avg
        ratio_pct = round((ratio - 1) * 100, 1)

        if ratio > 1.2:  # 高出均值 20%
            mood = "shocked"
        elif ratio < 0.8:  # 低于均值 20%
            mood = "proud"
        else:
            mood = "calm"

        # --- D. 空间感描述 ---
        if rice_jin <= 0:
            space_desc = "粮仓空空如也"
        elif rice_jin < 50:
            space_desc = "约 1 袋标准大米"
        elif rice_jin < 500:
            space_desc = f"约 {round(rice_jin / 50, 1)} 袋大米"
        elif rice_jin < 2000:
            space_desc = "足以堆满实验室的一面墙"
        else:
            space_desc = "足以装满一辆小型皮卡车"

        return {
            "total_raw": self.total,
            "work_hours": round(work_hours, 1),
            "work_days": round(work_days, 1),
            "rice_jin": round(rice_jin, 1),
            "rice_tons": round(rice_tons, 2),
            "survival_days": survival_days,
            "space_desc": space_desc,
            "mood": mood,
            "ratio_pct": ratio_pct,
            "avg_ref": self.avg
        }


# 测试代码 (直接运行此文件可查看效果)
if __name__ == "__main__":
    # 模拟从 cost.py 传出的带逗号字符串
    test_amount = "4,200.00"
    test_avg = 3000.0

    conv = LifeCostConverter(test_amount, test_avg)
    res = conv.get_stats()

    print(f"--- 生存审计测试 ---")
    print(f"总支出: {res['total_raw']} 元")
    print(f"搬砖时长: {res['work_hours']} 小时 ({res['work_days']} 天)")
    print(f"等价粮食: {res['rice_jin']} 斤 ({res['rice_tons']} 吨)")
    print(f"猫咪情绪: {res['mood']} (涨幅: {res['ratio_pct']}%)")