import flet as ft
from data_processor import FinanceProcessor
from charts import (
    create_sunburst_view, create_sankey_view,
    create_big_spends_view, create_line_chart, create_bar_chart
)

def main(page: ft.Page):
    page.title = "MoneyLens - 智能财务分析助手"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 400
    page.window_height = 700

    processor = FinanceProcessor()
    privacy_mode = True
    selected_files = []
    current_view_mode = "monthly"  # "monthly" 或 "total"

    # 创建文件选择器
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # 帮助对话框
    help_dialog = ft.AlertDialog(
        title=ft.Text("📖 账单获取指南"),
        content=ft.Container(
            width=350,
            content=ft.Column([
                ft.Text("支付宝账单获取", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
                ft.Text("我的 → 账单 → 右上角··· → 开具交易流水证明 → 用于个人对账", size=12),
                ft.Divider(),
                ft.Text("微信账单获取", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600),
                ft.Text("我 → 服务 → 钱包 → 账单 → 常见问题 → 下载账单 → 用于个人对账", size=12),
                ft.Divider(),
                ft.Text("💡 技术特性", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("• Fuzzy-Match 自动去重\n• 时空滑动窗口算法\n• 多编码自动适配\n• 旭日图/桑葚图可视化", size=12),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            height=400,
        ),
        actions=[
            ft.TextButton("知道了", on_click=lambda e: setattr(help_dialog, "open", False) or page.update())
        ],
    )

    # 图表详情对话框
    chart_dialog = ft.AlertDialog(
        title=ft.Text(""),
        content=ft.Container(width=350, height=500),
        actions=[ft.TextButton("关闭", on_click=lambda e: setattr(chart_dialog, "open", False) or page.update())],
    )

    # UI 组件
    file_list_view = ft.Column(spacing=5, visible=False)
    loader_view = ft.Column([
        ft.ProgressRing(),
        ft.Text("正在分析数据...", size=14),
        ft.Text("正在运行特征识别算法", size=12, color=ft.colors.GREY_500)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, visible=False)

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

    def toggle_privacy(e):
        nonlocal privacy_mode
        privacy_mode = privacy_switch.value

    def show_help(e):
        page.dialog = help_dialog
        help_dialog.open = True
        page.update()

    def remove_file(filename):
        nonlocal selected_files
        selected_files = [f for f in selected_files if f['name'] != filename]
        file_list_view.controls = [c for c in file_list_view.controls
                                   if c.content.controls[1].value != filename]
        if not selected_files:
            file_list_view.visible = False
            analyze_btn.disabled = True
        page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal selected_files
        if e.files:
            selected_files = [{'name': f.name, 'path': f.path} for f in e.files]
            file_list_view.controls.clear()
            for f in e.files:
                file_list_view.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.DESCRIPTION, size=16),
                            ft.Text(f.name, size=12, expand=True),
                            ft.IconButton(
                                icon=ft.icons.CLOSE,
                                icon_size=16,
                                on_click=lambda _, fn=f.name: remove_file(fn)
                            )
                        ]),
                        bgcolor=ft.colors.GREY_200 if page.theme_mode == ft.ThemeMode.LIGHT else ft.colors.GREY_800,
                        border_radius=8,
                        padding=8
                    )
                )
            file_list_view.visible = True
            analyze_btn.disabled = False
            page.update()

    file_picker.on_result = on_file_picked

    def show_chart_detail(title: str, chart_data):
        """显示图表详情"""
        chart_dialog.title = ft.Text(title)

        if "旭日图" in title:
            if not chart_data:
                content = ft.Column([ft.Text("暂无数据", size=14, color=ft.colors.GREY_500)],
                                    alignment=ft.MainAxisAlignment.CENTER, expand=True)
            else:
                content = ft.Column([
                    ft.Text("主分类 → 子分类 → 金额", size=12, color=ft.colors.GREY_500),
                    ft.Divider(),
                ], spacing=10, scroll=ft.ScrollMode.AUTO)

                for main_cat, sub_data in chart_data.items():
                    main_total = sum(sub_data.values())
                    content.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.FOLDER, size=16, color=ft.colors.BLUE_400),
                                    ft.Text(f"{main_cat}", size=14, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.Text(f"¥{main_total:.0f}", size=13, color=ft.colors.BLUE_600),
                                ]),
                            ]),
                            margin=ft.margin.only(top=8)
                        )
                    )
                    for sub_cat, amount in sub_data.items():
                        percent = (amount / main_total * 100) if main_total > 0 else 0
                        content.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"  📄 {sub_cat}", size=12, expand=True),
                                    ft.Text(f"¥{amount:.0f}", size=12, color=ft.colors.GREEN_600),
                                    ft.Text(f"({percent:.0f}%)", size=10, color=ft.colors.GREY_500),
                                ]),
                                margin=ft.margin.only(left=15)
                            )
                        )
                    content.controls.append(ft.Divider(height=5, color=ft.colors.TRANSPARENT))
            chart_dialog.content = ft.Container(content=content, height=450)

        elif "桑葚图" in title or "资金流向" in title:
            if not chart_data:
                content = ft.Column([ft.Text("暂无数据", size=14, color=ft.colors.GREY_500)],
                                    alignment=ft.MainAxisAlignment.CENTER, expand=True)
            else:
                content = ft.Column([
                    ft.Text("平台 → 消费类别", size=12, color=ft.colors.GREY_500),
                    ft.Divider(),
                ], spacing=10, scroll=ft.ScrollMode.AUTO)

                for platform, categories in chart_data.items():
                    platform_total = sum(categories.values())
                    content.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.PHONE_ANDROID, size=16, color=ft.colors.ORANGE_400),
                                    ft.Text(f"{platform}", size=14, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.Text(f"¥{platform_total:.0f}", size=13, color=ft.colors.ORANGE_600),
                                ]),
                            ]),
                            margin=ft.margin.only(top=8)
                        )
                    )
                    for cat, amount in categories.items():
                        percent = (amount / platform_total * 100) if platform_total > 0 else 0
                        content.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(f"  → {cat}", size=12, expand=True),
                                    ft.Text(f"¥{amount:.0f}", size=12, color=ft.colors.GREEN_600),
                                    ft.Text(f"({percent:.0f}%)", size=10, color=ft.colors.GREY_500),
                                ]),
                                margin=ft.margin.only(left=15)
                            )
                        )
                    content.controls.append(ft.Divider(height=5, color=ft.colors.TRANSPARENT))
            chart_dialog.content = ft.Container(content=content, height=450)

        elif "大额支出" in title:
            if not chart_data:
                content = ft.Column([ft.Text("暂无大额支出（>100元）", size=14, color=ft.colors.GREY_500)],
                                    alignment=ft.MainAxisAlignment.CENTER, expand=True)
            else:
                content = ft.Column([
                    ft.Text(f"共 {len(chart_data)} 笔超过100元的支出", size=12, color=ft.colors.GREY_500),
                    ft.Divider(),
                ], spacing=10, scroll=ft.ScrollMode.AUTO)
                for item in chart_data:
                    content.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(item['date'], size=12, expand=True),
                                    ft.Text(f"¥{item['amount']:.0f}", size=14, weight=ft.FontWeight.BOLD,
                                            color=ft.colors.RED_500),
                                ]),
                                ft.Text(item['target'], size=11, color=ft.colors.GREY_600),
                                ft.Container(
                                    content=ft.Text(item['category'], size=10, color=ft.colors.BLUE_600),
                                    bgcolor=ft.colors.BLUE_50 if page.theme_mode == ft.ThemeMode.LIGHT else ft.colors.BLUE_900,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    border_radius=10,
                                ),
                            ], spacing=4),
                            border=ft.border.all(0.5, ft.colors.GREY_300),
                            border_radius=8,
                            padding=10,
                        )
                    )
            chart_dialog.content = ft.Container(content=content, height=450)

        elif "商家排行" in title:
            if not chart_data:
                content = ft.Column([ft.Text("暂无商家数据", size=14, color=ft.colors.GREY_500)],
                                    alignment=ft.MainAxisAlignment.CENTER, expand=True)
            else:
                content = ft.Column([
                    ft.Text("消费最多的商家", size=12, color=ft.colors.GREY_500),
                    ft.Divider(),
                ], spacing=8, scroll=ft.ScrollMode.AUTO)
                for i, (merchant, amount) in enumerate(chart_data.items(), 1):
                    content.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"{i}.", size=12, width=25, weight=ft.FontWeight.BOLD),
                                ft.Text(merchant, size=12, expand=True),
                                ft.Text(f"¥{amount:.0f}", size=12, weight=ft.FontWeight.BOLD,
                                        color=ft.colors.ORANGE_600),
                            ]),
                            padding=ft.padding.symmetric(vertical=4),
                            border=ft.border.only(bottom=ft.BorderSide(0.5, ft.colors.GREY_300)) if i < len(
                                chart_data) else None,
                        )
                    )
            chart_dialog.content = ft.Container(content=content, height=450)

        elif "月度趋势" in title:
            if not chart_data:
                content = ft.Column([ft.Text("暂无月度数据", size=14, color=ft.colors.GREY_500)],
                                    alignment=ft.MainAxisAlignment.CENTER, expand=True)
            else:
                values = list(chart_data.values())
                max_val = max(values) if values else 1
                content = ft.Column([
                    ft.Text("各月支出变化趋势", size=12, color=ft.colors.GREY_500),
                    ft.Divider(),
                ], spacing=10, scroll=ft.ScrollMode.AUTO)
                for month, amount in chart_data.items():
                    percent = (amount / max_val * 100) if max_val > 0 else 0
                    content.controls.append(
                        ft.Column([
                            ft.Row([
                                ft.Text(month, size=12, width=70),
                                ft.Text(f"¥{amount:.0f}", size=12, color=ft.colors.BLUE_600, width=80),
                                ft.Container(ft.ProgressBar(value=percent/100, height=8, color=ft.colors.BLUE_400), expand=True),
                            ]),
                        ], spacing=4)
                    )
            chart_dialog.content = ft.Container(content=content, height=450)

        elif "分类统计" in title:
            if not chart_data:
                content = ft.Column([ft.Text("暂无分类数据", size=14, color=ft.colors.GREY_500)],
                                    alignment=ft.MainAxisAlignment.CENTER, expand=True)
            else:
                total = sum(chart_data.values())
                content = ft.Column([
                    ft.Text(f"总计 ¥{total:.0f}", size=12, color=ft.colors.GREY_500),
                    ft.Divider(),
                ], spacing=10, scroll=ft.ScrollMode.AUTO)
                for cat, amount in chart_data.items():
                    percent = (amount / total * 100) if total > 0 else 0
                    content.controls.append(
                        ft.Column([
                            ft.Row([
                                ft.Text(cat, size=12, expand=True),
                                ft.Text(f"¥{amount:.0f}", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"({percent:.0f}%)", size=11, color=ft.colors.GREY_500),
                            ]),
                            ft.ProgressBar(value=percent / 100, height=8, color=ft.colors.BLUE_400),
                        ], spacing=4)
                    )
            chart_dialog.content = ft.Container(content=content, height=450)

        page.dialog = chart_dialog
        chart_dialog.open = True
        page.update()

    async def start_analysis(e):
        if not selected_files:
            return

        upload_area.visible = False
        file_list_view.visible = False
        privacy_switch.visible = False
        analyze_btn.visible = False
        loader_view.visible = True
        page.update()

        try:
            processor.clear_data()
            total_records = 0

            for file_info in selected_files:
                file_path = file_info['path']
                file_name = file_info['name']

                with open(file_path, 'rb') as f:
                    file_content = f.read()

                if '支付宝' in file_name or 'alipay' in file_name.lower():
                    count = processor.load_alipay(file_content, file_name)
                else:
                    count = processor.load_wechat(file_content, file_name)

                total_records += count
                print(f"已加载 {file_name}: {count} 条记录")

            if total_records == 0:
                show_error("未找到有效的支出数据，请检查账单格式")
                return

            success = processor.process_data(privacy_mode=privacy_mode)

            if not success:
                show_error("数据处理失败")
                return

            show_report()

        except Exception as err:
            import traceback
            traceback.print_exc()
            show_error(f"分析失败: {str(err)}")


    def show_error(message):
        loader_view.visible = False
        upload_area.visible = True
        file_list_view.visible = bool(selected_files)
        privacy_switch.visible = True
        analyze_btn.visible = True
        page.update()

        page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.colors.RED_500)
        page.snack_bar.open = True
        page.update()

    def toggle_view_mode(e):
        nonlocal current_view_mode
        if current_view_mode == "monthly":
            current_view_mode = "total"
        else:
            current_view_mode = "monthly"
        show_report()

    def show_report():
        """显示报告页面"""
        page.clean()

        # 获取数据
        if current_view_mode == "total":
            kpi = processor.get_total_kpi()
            monthly_trend = processor.get_monthly_trend()
            chart_data = processor.get_total_chart_data()
            is_total_view = True
        else:
            kpi = processor.get_current_kpi()
            monthly_trend = processor.get_monthly_trend()
            chart_data = processor.get_chart_data_for_month()
            is_total_view = False

        if not kpi:
            page.add(ft.Text("数据加载失败"))
            return

        all_months = processor.get_all_months()

        # 计算历史月均
        historical_avg = 3000.0
        if len(all_months) > 1 and not is_total_view:
            historical_total = 0
            for m in all_months:
                if m != processor.current_month:
                    month_data = processor.monthly_kpis.get(m, {})
                    historical_total += month_data.get('raw_total', 0)
            if len(all_months) - 1 > 0:
                historical_avg = historical_total / (len(all_months) - 1)

        survival_stats = processor.get_survival_stats(kpi['total_expense'], historical_avg)
        ai_insight = processor.generate_ai_insight(kpi, survival_stats, is_total=is_total_view)

        def go_back(e):
            page.clean()
            main(page)

        def on_month_change(e):
            if month_dropdown.value:
                processor.set_current_month(month_dropdown.value)
                show_report()

        back_btn = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=go_back)
        help_btn = ft.IconButton(icon=ft.icons.HELP_OUTLINE, on_click=show_help)
        theme_btn = ft.IconButton(icon=ft.icons.DARK_MODE, on_click=lambda e: toggle_theme(e) or show_report())

        # 视图切换按钮
        view_toggle = ft.SegmentedButton(
            selected={0 if not is_total_view else 1},
            on_change=lambda e: toggle_view_mode(e),
            segments=[
                ft.Segment(value=0, label=ft.Text("按月", size=12)),
                ft.Segment(value=1, label=ft.Text("总计", size=12)),
            ]
        )

        # 月份选择器
        month_dropdown = None

        if not is_total_view and all_months:
            month_dropdown = ft.Dropdown(
                width=120,
                value=processor.current_month,
                options=[ft.dropdown.Option(m) for m in all_months],
                on_change=on_month_change,
            )
            top_controls = ft.Row([back_btn, month_dropdown, view_toggle, help_btn, theme_btn],
                                  alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        else:
            top_controls = ft.Row([back_btn, view_toggle, help_btn, theme_btn],
                                  alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        card_bg = ft.colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.colors.GREY_800
        is_dark_mode = page.theme_mode == ft.ThemeMode.DARK

        # 标题
        title_text = "📊 总计财务报告" if is_total_view else f"📅 {processor.current_month} 财务报告"

        # KPI 卡片
        kpi_cards = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("💰 总支出" if is_total_view else "💰 本月支出", size=12, color=ft.colors.GREY_500),
                    ft.Text(f"¥{kpi['total_expense']:,.2f}", size=20, weight=ft.FontWeight.BOLD,
                            color=ft.colors.RED_500)
                ], spacing=5),
                padding=12, border_radius=12, bgcolor=card_bg, expand=True
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("🍚 恩格尔系数", size=12, color=ft.colors.GREY_500),
                    ft.Text(kpi['engle'], size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_500)
                ], spacing=5),
                padding=12, border_radius=12, bgcolor=card_bg, expand=True
            ),
        ], spacing=10)

        # 日均支出
        daily_avg_value = kpi['daily_avg']
        if isinstance(daily_avg_value, str):
            try:
                daily_avg_value = float(daily_avg_value.replace(',', ''))
            except:
                daily_avg_value = 0.0

        kpi_cards2 = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("📅 日均支出", size=12, color=ft.colors.GREY_500),
                    ft.Text(f"¥{daily_avg_value:.2f}", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_500)
                ], spacing=5),
                padding=12, border_radius=12, bgcolor=card_bg, expand=True
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("📊 交易笔数", size=12, color=ft.colors.GREY_500),
                    ft.Text(f"{kpi['transaction_count']}", size=20, weight=ft.FontWeight.BOLD,
                            color=ft.colors.ORANGE_500)
                ], spacing=5),
                padding=12, border_radius=12, bgcolor=card_bg, expand=True
            ),
        ], spacing=10)

        # 猫咪卡片
        mood_map = {"shocked": "🙀", "proud": "😻", "calm": "😼"}
        mood_emoji = mood_map.get(survival_stats['mood'], "😼")
        mood_color = ft.colors.RED_500 if survival_stats['mood'] == 'shocked' else (
            ft.colors.GREEN_500 if survival_stats['mood'] == 'proud' else ft.colors.BLUE_500)

        advice_text = ft.Column([
            ft.Text(ai_insight['summary'], size=14, weight=ft.FontWeight.BOLD, color=mood_color),
        ], spacing=5)

        for detail in ai_insight['details']:
            advice_text.controls.append(ft.Text(detail, size=12, color=ft.colors.GREY_600))

        cat_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(mood_emoji, size=48),
                    ft.Column([
                        ft.Text("AI猫猫理财官", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(ai_insight['persona'], size=12, color=ft.colors.GREY_500),
                    ], spacing=2),
                ]),
                ft.Divider(height=1),
                advice_text,
                ft.Divider(height=1),
                ft.Text(f"{'总计' if is_total_view else '本月'}支出 {kpi['total_expense']:.0f} 元", size=12),
                ft.Text(f"相当于搬砖 {survival_stats['work_hours']} 小时 ({survival_stats['work_days']}天)", size=12),
                ft.Text(f"可购买 {survival_stats['rice_jin']:.0f} 斤大米", size=12),
            ], spacing=8),
            padding=15, border_radius=15, bgcolor=card_bg
        )

        # 粮食卡片
        if is_total_view:
            rice_title = "🍚 粮食换算 (总计)"
            rice_desc = f"总计相当于 {survival_stats['rice_jin']:.0f} 斤大米"
        else:
            rice_title = "🍚 粮食换算"
            rice_desc = f"等价于 {survival_stats['rice_jin']:.0f} 斤大米"

        rice_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(rice_title, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{survival_stats['survival_days']}天口粮", size=12, color=ft.colors.GREEN_500),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=min(survival_stats['rice_jin'] / 1000, 1), color=ft.colors.GREEN_400, height=8),
                ft.Text(rice_desc, size=12),
                ft.Text(f"约 {survival_stats['rice_tons']} 吨 | {survival_stats['space_desc']}", size=11,
                        color=ft.colors.GREY_500),
            ], spacing=8),
            padding=15, border_radius=15, bgcolor=card_bg
        )

        # 分类统计预览
        category_items = []
        total = kpi['total_expense']
        for cat, amount in list(kpi['category_stats'].items())[:5]:
            percent = (amount / total * 100) if total > 0 else 0
            category_items.append(
                ft.Column([
                    ft.Row([
                        ft.Text(cat, size=12, expand=True),
                        ft.Text(f"¥{amount:.0f}", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(f"({percent:.0f}%)", size=10, color=ft.colors.GREY_500),
                    ]),
                    ft.ProgressBar(value=percent / 100, color=ft.colors.BLUE_400, height=6),
                ], spacing=4)
            )

        category_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📊 支出分类统计", size=14, weight=ft.FontWeight.BOLD),
                    ft.TextButton("查看全部",
                                  on_click=lambda _: show_chart_detail("📊 分类统计", kpi.get('category_stats', {}))),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Column(category_items, spacing=12),
            ], spacing=10),
            padding=15, border_radius=15, bgcolor=card_bg
        )

        # 图表区域
        chart_section = ft.Column([
            ft.Text("📈 详细分析图表", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            create_sunburst_view(chart_data.get('sunburst', {}), "📊 多级消费穿透图（旭日图）", is_dark_mode),
            create_sankey_view(chart_data.get('sankey', {}), "🔀 资金流向图（桑葚图）", is_dark_mode),
            create_big_spends_view(chart_data.get('big_spends', []), "💰 大额支出分析", is_dark_mode),
            create_line_chart(monthly_trend, "📈 月度支出趋势", is_dark_mode),
            create_bar_chart(kpi.get('merchant_stats', {}), "🏪 商家消费排行", ft.colors.ORANGE_400, is_dark_mode),
        ], spacing=10)

        # 添加所有组件
        page.add(
            top_controls,
            ft.Container(height=10),
            ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=5),
            kpi_cards,
            ft.Container(height=5),
            kpi_cards2,
            ft.Container(height=10),
            cat_card,
            ft.Container(height=10),
            rice_card,
            ft.Container(height=10),
            category_card,
            ft.Container(height=10),
            chart_section,
        )

    # 主视图组件
    upload_area = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.UPLOAD_FILE, size=48, color=ft.colors.BLUE_400),
            ft.Text("点击选择账单文件", size=14),
            ft.Text("支持微信/支付宝账单 (Excel/CSV)", size=12, color=ft.colors.GREY_500),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        width=float("inf"), height=180,
        bgcolor=ft.colors.BLUE_50 if page.theme_mode == ft.ThemeMode.LIGHT else ft.colors.BLUE_900,
        border_radius=20, padding=20, ink=True,
        on_click=lambda _: file_picker.pick_files(allow_multiple=True, allowed_extensions=["csv", "xlsx", "xls"])
    )

    privacy_switch = ft.Switch(label="🔒 隐私脱敏模式", value=True, on_change=toggle_privacy)

    analyze_btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.icons.ANALYTICS), ft.Text("开始 AI 智能识别")]),
        width=float("inf"), height=50, disabled=True,
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.BLUE_600,
                             shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=start_analysis
    )

    title = ft.Container(
        content=ft.Column([
            ft.Text("MoneyLens", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600),
            ft.Text("智能财务分析助手", size=16, color=ft.colors.GREY_600),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=20)
    )

    theme_btn = ft.IconButton(icon=ft.icons.DARK_MODE, on_click=toggle_theme)
    help_btn = ft.IconButton(icon=ft.icons.HELP_OUTLINE, on_click=show_help)
    top_bar = ft.Row([theme_btn, help_btn], alignment=ft.MainAxisAlignment.END)

    footer = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.SHIELD, size=14, color=ft.colors.GREY_500),
            ft.Text("采用 Fuzzy-Match 算法自动剔除重复冗余", size=11, color=ft.colors.GREY_500)
        ], alignment=ft.MainAxisAlignment.CENTER),
        margin=ft.margin.only(top=20, bottom=10)
    )

    page.add(
        top_bar,
        title,
        upload_area,
        file_list_view,
        privacy_switch,
        analyze_btn,
        loader_view,
        footer
    )


if __name__ == "__main__":
    ft.app(target=main)