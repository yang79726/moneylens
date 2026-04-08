import pandas as pd
import io
import re
from typing import List, Dict, Any, Tuple
from converters import LifeCostConverter, extract_monthly_kpis


class FinanceProcessor:
    """移动端财务数据处理类"""

    def __init__(self):
        self.all_data = pd.DataFrame()
        self.all_months = []  # 存储所有可用月份
        self.current_month = None  # 当前选中的月份
        self.monthly_kpis = {}  # 存储所有月份的KPI
        self.category_mapping = {
            '交通出行': {
                '高铁火车': ['铁路', '12306', '高铁', '中铁', '火车票'],
                '打车租车': ['滴滴', '打车', '高德', '曹操', 'T3', '出租车'],
                '公交地铁': ['地铁', '公交', '轨道交通', '公共交通'],
                '共享单车': ['共享单车', '哈啰', '美团单车', '青桔'],
                '自驾车费': ['加油站', '油费', '停车费', 'ETC']
            },
            '网购消费': {
                '京东': ['京东', 'JD.COM'],
                '淘宝天猫': ['淘宝', '天猫', '闲鱼', 'Tmall'],
                '拼多多': ['拼多多', 'Pinduoduo'],
                '其他电商': ['唯品会', '得物', '小红书', '苏宁易购']
            },
            '餐饮美食': {
                '外卖点餐': ['美团外卖', '饿了么', '外卖'],
                '甜品饮品': ['蜜雪冰城', '瑞幸', '星巴克', '奶茶', '咖啡'],
                '快餐简餐': ['肯德基', '麦当劳', '德克士', '汉堡'],
                '中餐正餐': ['饭店', '餐厅', '酒楼', '餐馆', '火锅'],
                '便利零食': ['便利店', '超市', '零食', '小卖部']
            },
            '休闲娱乐': {
                '游戏充值': ['游戏充值', 'Steam', '米哈游'],
                '会员订阅': ['视频会员', 'Bilibili', '腾讯视频', '爱奇艺'],
                '电影演出': ['电影票', '电影院', '演出', '演唱会']
            },
            '生活服务': {
                '通讯缴费': ['话费', '充值', '电信', '移动', '联通'],
                '水电燃气': ['电费', '水费', '燃气费', '物业费'],
                '服饰鞋包': ['服装', '鞋子', '包包', '配饰'],
                '美容美发': ['理发', '美容', '美甲']
            },
            '教育培训': {
                '学校缴费': ['兰州大学', '大学', '学校', '学费'],
                '在线课程': ['课程', '培训', '教育', '学习'],
                '书籍文具': ['书店', '图书', '教材', '文具']
            },
            '医疗健康': {
                '医院药店': ['医院', '药店', '医疗', '健康', '体检'],
                '保健用品': ['保健品', '医疗器械', '口罩']
            }
        }

    def _classify(self, text: str) -> Tuple[str, str]:
        """智能分类"""
        text_lower = text.lower()

        if '兰州大学' in text:
            return '教育培训', '学校缴费'
        if '爱回收' in text:
            return '生活服务', '维修回收'

        for main_cat, sub_dict in self.category_mapping.items():
            for sub_cat, keywords in sub_dict.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        return main_cat, sub_cat

        return '其他', '未分类'

    def load_alipay(self, file_content: bytes, filename: str) -> int:
        """加载支付宝账单"""
        try:
            content = None
            for enc in ['gbk', 'utf-8-sig', 'utf-8', 'gb18030']:
                try:
                    content = file_content.decode(enc)
                    break
                except:
                    continue

            if not content:
                return 0

            lines = content.splitlines()
            records = []
            header_found = False
            header_index = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if '交易时间' in line and '金额' in line:
                    header_found = True
                    header_cols = [c.strip() for c in line.split(',')]
                    for i, col in enumerate(header_cols):
                        header_index[col] = i
                    continue

                if header_found and ',' in line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= len(header_index):
                        try:
                            tp = parts[header_index.get('收/支', header_index.get('收支', -1))]
                            if tp != '支出':
                                continue

                            amount_str = parts[header_index.get('金额', -1)]
                            amount_val = float(re.sub(r"[^\d.-]", "", amount_str))

                            records.append({
                                'time': parts[header_index.get('交易时间', 0)],
                                'target': parts[header_index.get('交易对方', 1)] if len(parts) > 1 else '',
                                'product': parts[header_index.get('商品说明', 2)] if len(parts) > 2 else '',
                                'amount': amount_val,
                                'type': tp,
                                'platform': '支付宝'
                            })
                        except (ValueError, KeyError, IndexError):
                            continue

            if records:
                new_df = pd.DataFrame(records)
                self.all_data = pd.concat([self.all_data, new_df], ignore_index=True)
                return len(records)
            return 0
        except Exception as e:
            print(f"支付宝解析错误: {e}")
            return 0

    def load_wechat(self, file_content: bytes, filename: str) -> int:
        """加载微信账单 - 智能定位表头"""
        try:
            df = None
            try:
                xl = pd.ExcelFile(io.BytesIO(file_content))
                sheet = xl.sheet_names[0]

                temp_df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet, header=None)

                header_row = -1
                for idx, row in temp_df.iterrows():
                    row_str = ' '.join([str(cell) for cell in row.values if pd.notna(cell)])
                    if '交易时间' in row_str and '金额' in row_str:
                        header_row = idx
                        break

                if header_row >= 0:
                    df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet, skiprows=header_row)
                else:
                    df = pd.read_excel(io.BytesIO(file_content), skiprows=16)
            except Exception as e:
                print(f"Excel读取尝试失败: {e}")
                content = file_content.decode('utf-8-sig')
                lines = content.splitlines()
                header_line = 0
                for i, line in enumerate(lines):
                    if '交易时间' in line and '金额' in line:
                        header_line = i
                        break
                df = pd.read_csv(io.StringIO(content), skiprows=header_line)

            if df is None or df.empty:
                return 0

            df.columns = df.columns.str.strip()

            time_col = next((c for c in df.columns if '时间' in c), None)
            type_col = next((c for c in df.columns if '收/支' in c or '收支' in c), None)
            amount_col = next((c for c in df.columns if '金额' in c), None)
            target_col = next((c for c in df.columns if '对方' in c), None)
            product_col = next((c for c in df.columns if '商品' in c), None)

            if not all([time_col, type_col, amount_col]):
                return 0

            records = []
            for _, row in df.iterrows():
                type_val = str(row[type_col]).strip()
                if '支出' not in type_val:
                    continue

                raw_amt = str(row[amount_col])
                clean_amt = raw_amt.replace('￥', '').replace('¥', '').replace(',', '').strip()

                try:
                    amount_val = float(clean_amt)
                except:
                    nums = re.findall(r"[-+]?\d*\.\d+|\d+", clean_amt)
                    if nums:
                        amount_val = float(nums[0])
                    else:
                        continue

                records.append({
                    'time': row[time_col],
                    'target': str(row.get(target_col, '未知')) if target_col else '未知',
                    'product': str(row.get(product_col, '')) if product_col else '',
                    'amount': amount_val,
                    'type': '支出',
                    'platform': '微信'
                })

            if records:
                new_df = pd.DataFrame(records)
                self.all_data = pd.concat([self.all_data, new_df], ignore_index=True)
                return len(records)
            return 0
        except Exception as e:
            print(f"微信解析错误: {e}")
            return 0

    def process_data(self, privacy_mode: bool = False) -> bool:
        """处理数据并返回是否成功"""
        if self.all_data.empty:
            return False

        # 时间处理
        self.all_data['time'] = pd.to_datetime(self.all_data['time'], errors='coerce')
        self.all_data = self.all_data.dropna(subset=['time'])
        self.all_data['date'] = self.all_data['time'].dt.date
        self.all_data['amount_abs'] = self.all_data['amount'].abs()

        # 添加 type_final 列
        self.all_data['type_final'] = '支出'

        # 去重
        self.all_data = self.all_data.drop_duplicates(subset=['time', 'target', 'amount_abs'])

        # 分类
        def apply_classify(row):
            text = f"{row['target']}{row['product']}"
            return self._classify(text)

        classifications = self.all_data.apply(apply_classify, axis=1)
        self.all_data['main_category'] = [c[0] for c in classifications]
        self.all_data['sub_category'] = [c[1] for c in classifications]

        # 脱敏
        if privacy_mode:
            self.all_data['target_display'] = self.all_data['target'].apply(
                lambda x: str(x)[0] + '**' if len(str(x)) > 1 else '**'
            )
        else:
            self.all_data['target_display'] = self.all_data['target']

        self.all_data['year_month'] = self.all_data['time'].dt.strftime('%Y-%m')

        # 计算所有月份的KPI
        self.monthly_kpis = extract_monthly_kpis(self.all_data)
        self.all_months = sorted(self.monthly_kpis.keys(), reverse=True)

        if self.all_months:
            self.current_month = self.all_months[0]

        return True

    def get_total_kpi(self) -> Dict[str, Any]:
        """获取总计KPI（所有月份汇总）"""
        if self.all_data.empty:
            return {}

        total_expense = self.all_data['amount_abs'].sum()

        # 计算总天数
        date_min = self.all_data['date'].min()
        date_max = self.all_data['date'].max()
        total_days = (date_max - date_min).days + 1 if date_min and date_max else 1

        # 计算恩格尔系数
        food_expense = self.all_data[self.all_data['main_category'] == '餐饮美食']['amount_abs'].sum()
        engle = (food_expense / total_expense * 100) if total_expense > 0 else 0

        # 分类统计
        category_stats = self.all_data.groupby('main_category')['amount_abs'].sum().sort_values(
            ascending=False).to_dict()
        category_stats = {k: float(v) for k, v in category_stats.items()}

        # 月度趋势
        monthly_trend = self.all_data.groupby('year_month')['amount_abs'].sum().sort_index().to_dict()
        monthly_trend = {k: float(v) for k, v in monthly_trend.items()}

        # 商家排行
        merchant_stats = self.all_data.groupby('target_display')['amount_abs'].sum().sort_values(ascending=False).head(
            15).to_dict()
        merchant_stats = {k: float(v) for k, v in merchant_stats.items()}

        # 平台统计
        platform_stats = self.all_data.groupby('platform')['amount_abs'].sum().to_dict()
        platform_stats = {k: float(v) for k, v in platform_stats.items()}

        # 消费画像（基于总计）
        night_count = len(self.all_data[(self.all_data['time'].dt.hour >= 22) | (self.all_data['time'].dt.hour <= 4)])
        is_night_owl = night_count > len(self.all_data) * 0.2

        if engle > 60:
            persona_type = '食堂战神'
        elif is_night_owl:
            persona_type = '深夜购物狂'
        elif total_expense > 5000:
            persona_type = '精致利己'
        else:
            persona_type = '稳健派'

        # 计算日均（返回数字，不是字符串）
        daily_avg = total_expense / total_days if total_days > 0 else 0

        return {
            'total_expense': float(total_expense),
            'total_expense_str': f"{total_expense:,.2f}",
            'daily_avg': daily_avg,  # 改为数字
            'daily_avg_str': f"{daily_avg:.2f}",  # 字符串版本
            'engle': f"{engle:.1f}%",
            'transaction_count': len(self.all_data),
            'max_spend': float(self.all_data['amount_abs'].max()),
            'category_stats': category_stats,
            'monthly_trend': monthly_trend,
            'merchant_stats': merchant_stats,
            'platform_stats': platform_stats,
            'persona_type': persona_type,
            'is_night_owl': is_night_owl,
            'total_days': total_days
        }

    def get_current_kpi(self) -> Dict[str, Any]:
        """获取当前选中月份的KPI"""
        if not self.current_month or self.current_month not in self.monthly_kpis:
            return {}

        month_kpi = self.monthly_kpis[self.current_month]
        total_expense = month_kpi['raw_total']

        current_df = self.all_data[self.all_data['year_month'] == self.current_month]

        category_stats = current_df.groupby('main_category')['amount_abs'].sum().sort_values(ascending=False).to_dict()
        merchant_stats = current_df.groupby('target_display')['amount_abs'].sum().sort_values(ascending=False).head(
            10).to_dict()

        return {
            'total_expense': float(total_expense),
            'total_expense_str': month_kpi['total_expense'],
            'daily_avg': month_kpi['daily_avg'],
            'engle': month_kpi['engle'],
            'transaction_count': int(len(current_df)),
            'max_spend': float(current_df['amount_abs'].max()) if not current_df.empty else 0,
            'category_stats': {k: float(v) for k, v in category_stats.items()},
            'merchant_stats': {k: float(v) for k, v in merchant_stats.items()},
            'persona_type': month_kpi['persona_type'],
            'is_night_owl': month_kpi.get('is_night_owl', False)
        }

    def get_chart_data_for_month(self, month: str = None) -> Dict[str, Any]:
        """获取指定月份的图表数据"""
        if self.all_data.empty:
            return {}

        target_month = month or self.current_month
        if not target_month:
            return {}

        expense_df = self.all_data[self.all_data['year_month'] == target_month]

        if expense_df.empty:
            return {}

        # 1. 旭日图数据
        sunburst_data = {}
        for main_cat in expense_df['main_category'].unique():
            main_df = expense_df[expense_df['main_category'] == main_cat]
            sunburst_data[main_cat] = {}
            for sub_cat in main_df['sub_category'].unique():
                sub_df = main_df[main_df['sub_category'] == sub_cat]
                sunburst_data[main_cat][sub_cat] = round(float(sub_df['amount_abs'].sum()), 2)

        # 2. 桑葚图数据
        sankey_data = {}
        for platform in expense_df['platform'].unique():
            platform_df = expense_df[expense_df['platform'] == platform]
            sankey_data[platform] = {}
            for cat in platform_df['main_category'].unique():
                cat_df = platform_df[platform_df['main_category'] == cat]
                sankey_data[platform][cat] = round(float(cat_df['amount_abs'].sum()), 2)

        # 3. 大额支出数据
        big_spends = expense_df[expense_df['amount_abs'] > 100].sort_values('amount_abs', ascending=False).head(20)
        big_spends_list = []
        for _, row in big_spends.iterrows():
            big_spends_list.append({
                'date': row['time'].strftime('%Y-%m-%d') if pd.notna(row['time']) else '未知',
                'amount': round(float(row['amount_abs']), 2),
                'target': row['target_display'],
                'category': f"{row['main_category']}/{row['sub_category']}"
            })

        # 4. 商家排行
        merchant_top = expense_df.groupby('target_display')['amount_abs'].sum().sort_values(ascending=False).head(
            15).to_dict()
        merchant_top = {k: float(v) for k, v in merchant_top.items()}

        return {
            'sunburst': sunburst_data,
            'sankey': sankey_data,
            'big_spends': big_spends_list,
            'merchant_top': merchant_top
        }

    def get_total_chart_data(self) -> Dict[str, Any]:
        """获取总计的图表数据"""
        if self.all_data.empty:
            return {}

        expense_df = self.all_data

        # 1. 旭日图数据
        sunburst_data = {}
        for main_cat in expense_df['main_category'].unique():
            main_df = expense_df[expense_df['main_category'] == main_cat]
            sunburst_data[main_cat] = {}
            for sub_cat in main_df['sub_category'].unique():
                sub_df = main_df[main_df['sub_category'] == sub_cat]
                sunburst_data[main_cat][sub_cat] = round(float(sub_df['amount_abs'].sum()), 2)

        # 2. 桑葚图数据
        sankey_data = {}
        for platform in expense_df['platform'].unique():
            platform_df = expense_df[expense_df['platform'] == platform]
            sankey_data[platform] = {}
            for cat in platform_df['main_category'].unique():
                cat_df = platform_df[platform_df['main_category'] == cat]
                sankey_data[platform][cat] = round(float(cat_df['amount_abs'].sum()), 2)

        # 3. 大额支出数据
        big_spends = expense_df[expense_df['amount_abs'] > 100].sort_values('amount_abs', ascending=False).head(20)
        big_spends_list = []
        for _, row in big_spends.iterrows():
            big_spends_list.append({
                'date': row['time'].strftime('%Y-%m-%d') if pd.notna(row['time']) else '未知',
                'amount': round(float(row['amount_abs']), 2),
                'target': row['target_display'],
                'category': f"{row['main_category']}/{row['sub_category']}"
            })

        # 4. 商家排行
        merchant_top = expense_df.groupby('target_display')['amount_abs'].sum().sort_values(ascending=False).head(
            15).to_dict()
        merchant_top = {k: float(v) for k, v in merchant_top.items()}

        return {
            'sunburst': sunburst_data,
            'sankey': sankey_data,
            'big_spends': big_spends_list,
            'merchant_top': merchant_top
        }

    def get_monthly_trend(self) -> Dict[str, Any]:
        """获取月度趋势数据"""
        if self.all_data.empty:
            return {}

        trend = self.all_data.groupby('year_month')['amount_abs'].sum().sort_index().to_dict()
        return {k: float(v) for k, v in trend.items()}

    def get_survival_stats(self, total_expense: float, monthly_avg: float = 3000.0) -> Dict[str, Any]:
        """获取生存统计"""
        expense_str = f"{total_expense:,.2f}"
        converter = LifeCostConverter(expense_str, monthly_avg)
        return converter.get_stats()

    def generate_ai_insight(self, kpi: Dict[str, Any], survival: Dict[str, Any], is_total: bool = False) -> Dict[
        str, Any]:
        """生成AI猫猫理财官建议"""
        total = kpi['total_expense']
        persona = kpi['persona_type']
        engle_val = float(kpi['engle'].replace('%', '')) if isinstance(kpi['engle'], str) else kpi['engle']
        is_night = kpi.get('is_night_owl', False)

        # 根据视图模式设置时间描述
        time_desc = "总计" if is_total else "本月"

        details = []

        # 画像吐槽
        if persona == '深夜购物狂':
            details.append("🌙 深夜守望者：凌晨的订单是感性的冲动，早上的账单是理性的痛苦。猫咪怀疑你是在梦游剁手！")
        elif persona == '食堂战神':
            details.append("🛡️ 食堂战神：恩格尔系数极高，你是在用胃支撑学校的基建吗？多吃鱼少吃草，喵~")
        elif persona == '精致利己':
            details.append("💅 精致利己：你在非刚需上的投入不菲，猫咪觉得你更爱面子而不是肚子。")
        elif persona == '稳健派':
            details.append("😼 稳健派：消费理性，支出在猫掌掌控之中，搬砖人继续加油。")

        # 消费炸弹（总计模式阈值调高）
        if is_total:
            if total > 15000:
                details.append("💣 消费炸弹：总支出已突破15000元警戒线，猫咪理财官受到了惊吓！")
            elif total < 5000:
                details.append("💰 省钱达人：总支出控制得很好，猫咪为你点赞！")
        else:
            if total > 4500:
                details.append("💣 消费炸弹：本月支出已突破警戒线，猫咪理财官受到了惊吓！")
            elif total < 1500:
                details.append("💰 省钱达人：本月支出控制得很好，猫咪为你点赞！")

        # 恩格尔系数吐槽
        if engle_val > 60:
            details.append("🍚 粮食警告：恩格尔系数过高，你是在吃土吗？")
        elif engle_val < 20 and total > 1000:
            details.append("🍽️ 品质生活：恩格尔系数较低，生活品质不错~")

        # 深夜消费
        if is_night:
            details.append("🌃 夜猫子：深夜消费活跃，早点睡觉能省不少钱！")

        # 粮食投影
        rice_jin = survival.get('rice_jin', 0)
        if rice_jin > 3000:
            details.append(f"🍚 粮食警告：你总共挥霍了 {rice_jin:.0f} 斤大米，够全村流浪猫吃一个月了！")
        elif rice_jin > 1000:
            details.append(f"🍚 粮食警告：你这段时间挥霍了 {rice_jin:.0f} 斤大米，够流浪猫吃一周了！")

        if not details:
            details.append("表现平平，没有惊喜也没有惊吓。乖乖去赚小鱼干吧。")

        # 核心评价
        ratio = survival.get('ratio_pct', 0)
        if is_total:
            if ratio > 30:
                summary = f"震惊！"
            elif ratio < -15:
                summary = f"欣慰！"
            else:
                summary = "情绪稳定。总支出还在猫掌掌控之中，搬砖人继续加油。"
        else:
            if ratio > 20:
                summary = f"震惊！本月支出超出平均基准线 {ratio:.0f}%！"
            elif ratio < -10:
                summary = f"欣慰！本月成功比平时节省了 {abs(ratio):.0f}%！"
            else:
                summary = "情绪稳定。支出还在猫掌掌控之中，搬砖人继续加油。"

        return {
            "persona": persona,
            "summary": summary,
            "details": details
        }

    def get_all_months(self) -> List[str]:
        """获取所有月份列表"""
        return self.all_months

    def set_current_month(self, month: str):
        """设置当前月份"""
        if month in self.monthly_kpis:
            self.current_month = month

    def clear_data(self):
        self.all_data = pd.DataFrame()
        self.all_months = []
        self.current_month = None
        self.monthly_kpis = {}