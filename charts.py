import flet as ft
from typing import Dict, List, Any


def create_sunburst_view(data: Dict, title: str, is_dark: bool = False) -> ft.Container:
    """创建旭日图风格的层级视图"""
    bg_color = ft.colors.GREY_900 if is_dark else ft.colors.WHITE

    if not data:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("暂无数据", size=13, color=ft.colors.GREY_500),
            ], spacing=10),
            padding=15, border_radius=15, bgcolor=bg_color,
        )

    content_items = []
    for main_cat, sub_data in data.items():
        main_total = sum(sub_data.values())
        if main_total == 0:  # 跳过总金额为0的分类
            continue

        content_items.append(
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.icons.FOLDER, size=18, color=ft.colors.BLUE_400),
                    ft.Text(main_cat, size=14, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(f"¥{main_total:.0f}", size=13, color=ft.colors.BLUE_600),
                ]),
                subtitle=ft.Text(f"{len(sub_data)}个子分类", size=11),
                controls=[
                    ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(sub_cat, size=12, expand=True),
                                    ft.Text(f"¥{amount:.0f}", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"({(amount / main_total * 100):.0f}%)", size=11, color=ft.colors.GREY_500),
                                ]),
                                ft.ProgressBar(value=amount / main_total if main_total > 0 else 0, height=4,
                                               color=ft.colors.GREEN_400),
                            ], spacing=4),
                            padding=ft.padding.only(left=20, top=8, right=10, bottom=8),
                        )
                        for sub_cat, amount in sub_data.items()
                    ], spacing=5)
                ]
            )
        )

    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(content_items, spacing=5, scroll=ft.ScrollMode.AUTO),
        ], spacing=10),
        padding=15, border_radius=15, bgcolor=bg_color,
    )


def create_sankey_view(data: Dict, title: str, is_dark: bool = False) -> ft.Container:
    """创建桑葚图风格的流向视图"""
    bg_color = ft.colors.GREY_900 if is_dark else ft.colors.WHITE

    if not data:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("暂无数据", size=13, color=ft.colors.GREY_500),
            ], spacing=10),
            padding=15, border_radius=15, bgcolor=bg_color,
        )

    content_items = []
    for platform, categories in data.items():
        platform_total = sum(categories.values())
        if platform_total == 0:  # 跳过总金额为0的平台
            continue

        content_items.append(
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.icons.PHONE_ANDROID, size=18, color=ft.colors.ORANGE_400),
                    ft.Text(platform, size=14, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(f"¥{platform_total:.0f}", size=13, color=ft.colors.ORANGE_600),
                ]),
                subtitle=ft.Text(f"流向{len(categories)}个类别", size=11),
                controls=[
                    ft.Column([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.ARROW_FORWARD, size=14, color=ft.colors.GREY_400),
                                ft.Text(cat, size=12, expand=True),
                                ft.Text(f"¥{amount:.0f}", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(f"({(amount / platform_total * 100):.0f}%)", size=11, color=ft.colors.GREY_500),
                            ], spacing=8),
                            padding=ft.padding.only(left=20, top=6, right=10, bottom=6),
                        )
                        for cat, amount in categories.items()
                    ], spacing=5)
                ]
            )
        )

    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(content_items, spacing=5, scroll=ft.ScrollMode.AUTO),
        ], spacing=10),
        padding=15, border_radius=15, bgcolor=bg_color,
    )


def create_big_spends_view(big_spends: List[Dict], title: str, is_dark: bool = False) -> ft.Container:
    """创建大额支出视图"""
    bg_color = ft.colors.GREY_900 if is_dark else ft.colors.WHITE
    item_bg = ft.colors.GREY_100 if is_dark else ft.colors.GREY_50

    if not big_spends:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("暂无大额支出（>100元）", size=13, color=ft.colors.GREY_500),
            ], spacing=10),
            padding=15, border_radius=15, bgcolor=bg_color,
        )

    items = []
    for item in big_spends[:15]:
        items.append(
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(item['date'], size=11, color=ft.colors.GREY_600),
                        ft.Text(item['target'], size=12, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(item['category'], size=10),
                            bgcolor=ft.colors.BLUE_50,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=10,
                        ),
                    ], spacing=3, expand=True),
                    ft.Text(f"¥{item['amount']:.0f}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_500),
                ], spacing=10),
                padding=10,
                bgcolor=item_bg,
                border_radius=10,
                margin=ft.margin.only(bottom=5),
            )
        )

    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO, height=400),
        ], spacing=10),
        padding=15, border_radius=15, bgcolor=bg_color,
    )


def create_line_chart(data: Dict[str, float], title: str, is_dark: bool = False) -> ft.Container:
    """创建折线图（用进度条模拟）"""
    bg_color = ft.colors.GREY_900 if is_dark else ft.colors.WHITE

    if not data:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("暂无数据", size=13, color=ft.colors.GREY_500),
            ], spacing=10),
            padding=15, border_radius=15, bgcolor=bg_color,
        )

    values = list(data.values())
    max_val = max(values) if values else 1

    items = []
    for month, amount in data.items():
        percent = (amount / max_val * 100) if max_val > 0 else 0
        items.append(
            ft.Column([
                ft.Row([
                    ft.Text(month, size=11, width=70),
                    ft.Text(f"¥{amount:.0f}", size=11, color=ft.colors.BLUE_600, width=80),
                    ft.ProgressBar(value=percent / 100, height=8, color=ft.colors.BLUE_400, expand=True),
                ]),
            ], spacing=4)
        )

    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(items, spacing=8, scroll=ft.ScrollMode.AUTO, height=300),
        ], spacing=10),
        padding=15, border_radius=15, bgcolor=bg_color,
    )


def create_bar_chart(data: Dict[str, float], title: str, color: str, is_dark: bool = False) -> ft.Container:
    """创建条形图"""
    bg_color = ft.colors.GREY_900 if is_dark else ft.colors.WHITE

    if not data:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("暂无数据", size=13, color=ft.colors.GREY_500),
            ], spacing=10),
            padding=15, border_radius=15, bgcolor=bg_color,
        )

    max_value = max(data.values()) if data else 1

    items = []
    for name, value in list(data.items())[:10]:
        percent = (value / max_value * 100) if max_value > 0 else 0
        items.append(
            ft.Column([
                ft.Row([
                    ft.Text(name, size=11, expand=True),
                    ft.Text(f"¥{value:.0f}", size=11, weight=ft.FontWeight.BOLD),
                ]),
                ft.ProgressBar(value=percent / 100, height=8, color=color),
            ], spacing=4)
        )

    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(items, spacing=12, scroll=ft.ScrollMode.AUTO, height=350),
        ], spacing=10),
        padding=15, border_radius=15, bgcolor=bg_color,
    )