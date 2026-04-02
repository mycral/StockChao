# -*- coding: utf-8 -*-
"""
K线查看器和选股工具
基于PySide6 + Matplotlib
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 必须最先设置 Matplotlib 后端（必须在任何 matplotlib 导入之前）
import matplotlib
matplotlib.use('QtAgg')

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import DB_PATH
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QPushButton,
    QComboBox, QTabWidget, QDateEdit, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QSplitter, QMessageBox, QHeaderView, QAbstractItemView,
    QDialog, QDialogButtonBox, QCompleter
)
from PySide6.QtCore import Qt, QDate, QStringListModel
from PySide6.QtGui import QFont, QColor

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 导入技能管理器
from skills.skill_manager import SkillManager

def get_pinyin_initials(name):
    """获取中文名字的拼音首字母"""
    try:
        import pypinyin
        # 获取完整拼音
        pinyin_list = pypinyin.pinyin(name, style=pypinyin.Style.NORMAL)
        # 取每个字拼音的首字母
        return ''.join([c[0][0].upper() if c and c[0] else '' for c in pinyin_list])
    except ImportError:
        return ''
    except Exception:
        return ''


def has_pinyin_match(name, keyword):
    """检查名字的拼音首字母是否匹配关键词"""
    if not name or not keyword:
        return False
    # 移除空格
    name_clean = name.replace(' ', '').replace('*', '')
    pinyin = get_pinyin_initials(name_clean)
    keyword_upper = keyword.upper()
    # 检查拼音首字母是否以关键词开头
    return pinyin.startswith(keyword_upper)


class KLineChart(FigureCanvas):
    """K线图组件（K线 + 成交量）"""

    def __init__(self, parent=None, width=5, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1e1e1e')
        # 使用GridSpec将图分为两部分：上方K线(70%)，下方成交量(20%)
        self.gs = self.fig.add_gridspec(2, 1, height_ratios=[7, 3], hspace=0.1)
        self.axes = self.fig.add_subplot(self.gs[0])
        self.vol_axes = self.fig.add_subplot(self.gs[1], sharex=self.axes)
        self._apply_dark_axes_style()
        super().__init__(self.fig)
        self.setParent(parent)

    def _apply_dark_axes_style(self):
        """深色主题样式"""
        for ax in [self.axes, self.vol_axes]:
            ax.set_facecolor('#252526')
            ax.tick_params(colors='#a0a0a0', labelsize=8)
            ax.xaxis.label.set_color('#808080')
            ax.yaxis.label.set_color('#808080')
            for spine in ax.spines.values():
                spine.set_color('#3c3c3c')
            ax.title.set_color('#e0e0e0')

    def plot_kline(self, df, ts_code, name):
        """绘制K线图和成交量（深色主题）"""
        self.axes.clear()
        self.vol_axes.clear()
        self._apply_dark_axes_style()

        if df is None or len(df) == 0:
            self.axes.text(0.5, 0.5, '无数据', ha='center', va='center', color='#808080')
            self.draw()
            return

        # 转换日期格式
        df = df.copy()
        df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

        # 截取最近250个交易日（约一年）
        if len(df) > 250:
            df = df.tail(250)

        # 深色主题颜色
        up_color = '#ff4444'      # 红色（上涨）
        down_color = '#00b050'    # 绿色（下跌）
        grid_color = '#3c3c3c'

        # 绘制K线
        for idx, row in df.iterrows():
            date = row['date']
            open_price = row['open']
            close_price = row['close']
            high_price = row['high']
            low_price = row['low']

            if close_price >= open_price:
                color = up_color
                body_height = close_price - open_price
                body_bottom = open_price
                facecolor = color
            else:
                color = down_color
                body_height = open_price - close_price
                body_bottom = close_price
                facecolor = color

            # 绘制上下影线
            self.axes.plot([date, date], [low_price, high_price], color=color, linewidth=0.8)
            # 绘制实体
            rect = plt.Rectangle(
                (mdates.date2num(date) - 0.3, body_bottom),
                0.6,
                body_height if body_height > 0 else 0.1,
                linewidth=0.8,
                edgecolor=color,
                facecolor=facecolor
            )
            self.axes.add_patch(rect)

        # K线设置
        self.axes.set_title(f'{name} ({ts_code})', fontsize=11, fontweight='bold', color='#e0e0e0')
        self.axes.set_ylabel('价格', color='#a0a0a0')
        self.axes.grid(True, alpha=0.3, color=grid_color)
        self.axes.tick_params(labelbottom=False)
        for label in self.axes.get_xticklabels():
            label.set_color('#808080')
        for label in self.axes.get_yticklabels():
            label.set_color('#808080')

        # 绘制成交量柱状图
        colors = []
        for idx, row in df.iterrows():
            if row['close'] >= row['open']:
                colors.append(up_color)
            else:
                colors.append(down_color)

        self.vol_axes.bar(df['date'], df['vol'] / 10000, color=colors, width=0.6)
        self.vol_axes.set_ylabel('成交量(万手)', color='#a0a0a0')
        self.vol_axes.set_xlabel('日期', color='#a0a0a0')
        self.vol_axes.grid(True, alpha=0.3, color=grid_color)
        for label in self.vol_axes.get_xticklabels():
            label.set_color('#808080')
        for label in self.vol_axes.get_yticklabels():
            label.set_color('#808080')
        self.vol_axes.grid(True, alpha=0.3)

        # 设置x轴日期格式（只在成交量图显示）
        self.vol_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        self.vol_axes.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        self.fig.autofmt_xdate(rotation=45)

        self.draw()

        # 绑定点击事件
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        self.draw()

    def on_click(self, event):
        """点击K线获取详情"""
        if event.inaxes != self.axes:
            return
        print(f"点击位置: x={event.xdata}, y={event.ydata}")

    def plot_minute(self, df, ts_code, name):
        """绘制分时图（深色主题）

        Args:
            df: DataFrame，包含 trade_time, open, high, low, close, vol 列
            ts_code: 股票代码
            name: 股票名称
        """
        self.axes.clear()
        self.vol_axes.clear()
        self._apply_dark_axes_style()

        if df is None or len(df) == 0:
            self.axes.text(0.5, 0.5, '无分时数据', ha='center', va='center', color='#808080')
            self.draw()
            return

        df = df.copy()

        # 解析时间（兼容多种列名）
        time_col = None
        for col in ['trade_time', '时间', 'day']:
            if col in df.columns:
                time_col = col
                break

        if time_col is None:
            self.axes.text(0.5, 0.5, '时间字段缺失', ha='center', va='center')
            self.draw()
            return

        df['time'] = pd.to_datetime(df[time_col], format='%Y-%m-%d %H:%M:%S')

        # 解析成交量（兼容多种列名）
        vol_col = 'vol' if 'vol' in df.columns else ('volume' if 'volume' in df.columns else None)

        # 截取最近数据（分时数据量大）
        if len(df) > 500:
            df = df.tail(500)

        # 深色主题颜色
        up_color = '#ff4444'
        down_color = '#00b050'
        line_color = '#0078d4'
        avg_color = '#ff9800'
        grid_color = '#3c3c3c'

        # 绘制分时线（价格）
        self.axes.plot(df['time'], df['close'], color=line_color, linewidth=1.0)
        self.axes.fill_between(df['time'], df['close'].min(), df['close'],
                               color=line_color, alpha=0.1)

        # 计算均价线（简单均线）
        if 'open' in df.columns:
            df['avg'] = df['close'].rolling(window=10, min_periods=1).mean()
            self.axes.plot(df['time'], df['avg'], color=avg_color, linewidth=0.8,
                           linestyle='--', label='均价')

        # 设置
        self.axes.set_title(f'{name} ({ts_code})', fontsize=11, fontweight='bold', color='#e0e0e0')
        self.axes.set_ylabel('价格', color='#a0a0a0')
        self.axes.grid(True, alpha=0.3, color=grid_color)
        self.axes.tick_params(labelbottom=False)
        self.axes.spines['top'].set_color(grid_color)
        self.axes.spines['right'].set_color(grid_color)
        self.axes.spines['bottom'].set_color(grid_color)
        self.axes.spines['left'].set_color(grid_color)
        for label in self.axes.get_xticklabels():
            label.set_color('#808080')
        for label in self.axes.get_yticklabels():
            label.set_color('#808080')

        # 成交量柱状图
        colors = []
        for _, row in df.iterrows():
            if row['close'] >= (row['open'] if 'open' in df.columns else row['close']):
                colors.append(up_color)
            else:
                colors.append(down_color)

        if vol_col:
            self.vol_axes.bar(df['time'], df[vol_col] / 10000, color=colors, width=0.0003)
        self.vol_axes.set_ylabel('成交量(万手)', color='#a0a0a0')
        self.vol_axes.set_xlabel('时间', color='#a0a0a0')
        self.vol_axes.grid(True, alpha=0.3, color=grid_color)
        self.vol_axes.spines['top'].set_color(grid_color)
        self.vol_axes.spines['right'].set_color(grid_color)
        self.vol_axes.spines['bottom'].set_color(grid_color)
        self.vol_axes.spines['left'].set_color(grid_color)
        for label in self.vol_axes.get_xticklabels():
            label.set_color('#808080')
        for label in self.vol_axes.get_yticklabels():
            label.set_color('#808080')

        # 时间格式
        self.vol_axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.vol_axes.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
        self.fig.autofmt_xdate(rotation=45)

        self.draw()


class StockSelector:
    """选股器"""

    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def screen_stocks(self, conditions):
        """
        选股条件:
        conditions = {
            'pe_min': None, 'pe_max': None,      # 市盈率范围
            'pb_min': None, 'pb_max': None,       # 市净率范围
            'turnover_rate_min': None,            # 最小换手率
            'total_mv_max': None,                 # 最大总市值（亿）
            'industry': None,                     # 行业
            'market': None,                       # 市场
            'price_min': None, 'price_max': None, # 价格范围
        }
        """
        conn = self.get_connection()

        # 构建SQL查询
        sql = """
            SELECT DISTINCT
                b.ts_code, b.symbol, b.name, b.industry, b.market,
                d.trade_date, d.close as price,
                db.pe, db.pb, db.turnover_rate, db.total_mv, db.circ_mv
            FROM stock_basic b
            INNER JOIN daily d ON b.ts_code = d.ts_code
            INNER JOIN daily_basic db ON b.ts_code = db.ts_code AND d.trade_date = db.trade_date
            WHERE 1=1
        """
        params = []

        # 获取最新日期的数据
        latest_date_sql = """
            SELECT MAX(trade_date) FROM daily
        """
        cursor = conn.execute(latest_date_sql)
        latest_date = cursor.fetchone()[0]
        if latest_date:
            sql += " AND d.trade_date = ?"
            params.append(latest_date)
            sql += " AND db.trade_date = ?"
            params.append(latest_date)

        # 市盈率筛选
        if conditions.get('pe_max') is not None:
            sql += " AND (db.pe IS NOT NULL AND db.pe <= ?)"
            params.append(conditions['pe_max'])

        if conditions.get('pe_min') is not None:
            sql += " AND (db.pe IS NOT NULL AND db.pe >= ?)"
            params.append(conditions['pe_min'])

        # 市净率筛选
        if conditions.get('pb_max') is not None:
            sql += " AND (db.pb IS NOT NULL AND db.pb <= ?)"
            params.append(conditions['pb_max'])

        if conditions.get('pb_min') is not None:
            sql += " AND (db.pb IS NOT NULL AND db.pb >= ?)"
            params.append(conditions['pb_min'])

        # 换手率筛选
        if conditions.get('turnover_rate_min') is not None:
            sql += " AND (db.turnover_rate IS NOT NULL AND db.turnover_rate >= ?)"
            params.append(conditions['turnover_rate_min'])

        # 总市值筛选（亿元）
        if conditions.get('total_mv_max') is not None:
            sql += " AND (db.total_mv IS NOT NULL AND db.total_mv <= ?)"
            params.append(conditions['total_mv_max'] * 10000)  # 转换为万

        # 价格范围
        if conditions.get('price_max') is not None:
            sql += " AND d.close <= ?"
            params.append(conditions['price_max'])

        if conditions.get('price_min') is not None:
            sql += " AND d.close >= ?"
            params.append(conditions['price_min'])

        # 行业筛选
        if conditions.get('industry'):
            sql += " AND b.industry = ?"
            params.append(conditions['industry'])

        # 市场筛选
        if conditions.get('market'):
            sql += " AND b.market = ?"
            params.append(conditions['market'])

        sql += " ORDER BY d.close DESC LIMIT 500"

        try:
            df = pd.read_sql_query(sql, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            conn.close()
            print(f"选股查询错误: {e}")
            return pd.DataFrame()

    def get_industries(self):
        """获取所有行业列表"""
        conn = self.get_connection()
        sql = "SELECT DISTINCT industry FROM stock_basic WHERE industry IS NOT NULL ORDER BY industry"
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df['industry'].tolist()

    def get_markets(self):
        """获取所有市场列表"""
        conn = self.get_connection()
        sql = "SELECT DISTINCT market FROM stock_basic WHERE market IS NOT NULL ORDER BY market"
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df['market'].tolist()


class KLineViewer(QMainWindow):
    """K线查看器主窗口"""

    def __init__(self):
        super().__init__()
        self.db_path = DB_PATH
        self.watchlist_file = os.path.join(os.path.dirname(__file__), 'watchlist.csv')
        self.config_file = os.path.join(os.path.dirname(__file__), 'viewer_config.json')
        self.selector = StockSelector(self.db_path)
        self.current_stock = None
        self.watchlist = []  # [(ts_code, name), ...]
        # 初始化技能管理器
        self.skill_manager = SkillManager()
        self.skill_manager.load_skills()
        self.current_skill = None  # 当前选中的技能
        self.init_ui()
        self.load_watchlist()

    def init_ui(self):
        self.setWindowTitle('K线查看器 - 同花顺选股')
        self.setGeometry(100, 100, 1600, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 水平分割器：左侧自选股 + 右侧内容
        splitter = QSplitter(Qt.Horizontal)

        # ========== 左侧自选股面板 ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 自选股标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel('自选股')
        title_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 添加/删除按钮
        self.add_watch_btn = QPushButton('+添加')
        self.add_watch_btn.setMaximumWidth(60)
        self.add_watch_btn.clicked.connect(self.add_to_watchlist)
        title_layout.addWidget(self.add_watch_btn)

        self.del_watch_btn = QPushButton('删除')
        self.del_watch_btn.setMaximumWidth(60)
        self.del_watch_btn.clicked.connect(self.remove_from_watchlist)
        title_layout.addWidget(self.del_watch_btn)

        left_layout.addLayout(title_layout)

        # 自选股列表
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(3)
        self.watchlist_table.setHorizontalHeaderLabels(['代码', '名称', '最新价'])
        self.watchlist_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.watchlist_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.watchlist_table.setColumnWidth(0, 160)
        self.watchlist_table.setColumnWidth(1, 160)
        self.watchlist_table.horizontalHeader().setStretchLastSection(True)
        self.watchlist_table.itemDoubleClicked.connect(self.on_watchlist_double_click)
        self.watchlist_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.watchlist_table.verticalHeader().setVisible(False)
        self.watchlist_table.horizontalHeader().setFixedHeight(25)
        left_layout.addWidget(self.watchlist_table)

        left_panel.setMinimumWidth(550)
        splitter.addWidget(left_panel)

        # ========== 右侧内容区域 ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 顶部搜索栏
        search_bar = QHBoxLayout()

        # 股票代码/名称输入 - 使用ComboBox实现自动提示
        self.search_combo = QComboBox()
        self.search_combo.setEditable(True)
        self.search_combo.setMinimumWidth(300)
        self.search_combo.setPlaceholderText('输入股票代码、名称或拼音首字母')
        self.search_combo.setInsertPolicy(QComboBox.NoInsert)
        # 搜索输入框
        self.search_input = self.search_combo.lineEdit()
        # 自动补全器
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_input.setCompleter(self.completer)
        # 回车时从补全列表当前选中项加载股票
        self.search_input.returnPressed.connect(self.on_completer_return)
        search_bar.addWidget(QLabel('搜索:'))
        search_bar.addWidget(self.search_combo)

        self.search_btn = QPushButton('搜索')
        self.search_btn.clicked.connect(self.on_search)
        search_bar.addWidget(self.search_btn)

        # 日期范围（默认最近3个月）
        search_bar.addWidget(QLabel('开始日期:'))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat('yyyyMMdd')
        search_bar.addWidget(self.start_date)

        search_bar.addWidget(QLabel('结束日期:'))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat('yyyyMMdd')
        search_bar.addWidget(self.end_date)

        # 加载保存的日期范围
        self.load_date_range()
        self.start_date.dateChanged.connect(self.save_date_range)

        # 搜索历史按钮
        self.prev_btn = QPushButton('< 前一只')
        self.prev_btn.clicked.connect(self.prev_stock)
        search_bar.addWidget(self.prev_btn)

        self.next_btn = QPushButton('后一只 >')
        self.next_btn.clicked.connect(self.next_stock)
        search_bar.addWidget(self.next_btn)

        right_layout.addLayout(search_bar)

        # Tab页
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        # K线Tab
        kline_tab = QWidget()
        kline_layout = QVBoxLayout(kline_tab)

        # K线图
        self.kline_chart = KLineChart(width=10, height=6, dpi=100)
        kline_layout.addWidget(self.kline_chart)

        # 股票信息栏
        info_layout = QHBoxLayout()
        self.stock_info_label = QLabel('股票信息: 无')
        self.stock_info_label.setStyleSheet('padding: 5px; background: #f0f0f0;')
        info_layout.addWidget(self.stock_info_label)
        kline_layout.addLayout(info_layout)

        self.tabs.addTab(kline_tab, 'K线图')

        # 选股Tab
        selector_tab = QWidget()
        selector_layout = QVBoxLayout(selector_tab)

        # ==================== 技能选股区域 ====================
        skill_group = QGroupBox('技能选股')
        skill_layout = QVBoxLayout(skill_group)

        # 技能选择行
        skill_select_layout = QHBoxLayout()
        skill_select_layout.addWidget(QLabel('选择技能:'))
        self.skill_combo = QComboBox()
        self.skill_combo.addItem('-- 请选择技能 --', None)
        # 加载技能列表
        for skill_info in self.skill_manager.get_skills_list():
            self.skill_combo.addItem(
                f"{skill_info['meta']['name']} ({skill_info['meta']['version']})",
                skill_info['name']
            )
        self.skill_combo.currentIndexChanged.connect(self.on_skill_changed)
        skill_select_layout.addWidget(self.skill_combo)

        # 刷新技能按钮
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self.reload_skills)
        skill_select_layout.addWidget(refresh_btn)
        skill_select_layout.addStretch()
        skill_layout.addLayout(skill_select_layout)

        # 技能参数区域
        self.skill_params_widget = QWidget()
        self.skill_params_layout = QFormLayout(self.skill_params_widget)
        self.skill_params = {}  # {name: widget}
        skill_layout.addWidget(self.skill_params_widget)

        # 执行技能按钮
        skill_btn_layout = QHBoxLayout()
        self.run_skill_btn = QPushButton('执行技能选股')
        self.run_skill_btn.clicked.connect(self.do_skill_screen)
        self.run_skill_btn.setStyleSheet('background: #2196F3; color: white; padding: 8px; font-size: 14px;')
        skill_btn_layout.addWidget(self.run_skill_btn)

        self.add_to_watchlist_btn = QPushButton('添加到自选股')
        self.add_to_watchlist_btn.clicked.connect(self.add_skill_result_to_watchlist)
        skill_btn_layout.addWidget(self.add_to_watchlist_btn)
        skill_btn_layout.addStretch()
        skill_layout.addLayout(skill_btn_layout)

        selector_layout.addWidget(skill_group)

        # ==================== 传统条件选股区域 ====================
        cond_group = QGroupBox('条件选股')
        cond_layout = QFormLayout()

        # 市盈率
        pe_layout = QHBoxLayout()
        self.pe_min = QSpinBox()
        self.pe_min.setRange(-1000, 10000)
        self.pe_min.setValue(0)
        self.pe_min.setSuffix(' 倍')
        pe_layout.addWidget(QLabel('PE(市盈率):'))
        pe_layout.addWidget(self.pe_min)
        pe_layout.addWidget(QLabel(' ~ '))
        self.pe_max = QSpinBox()
        self.pe_max.setRange(-1000, 10000)
        self.pe_max.setValue(50)
        self.pe_max.setSuffix(' 倍')
        pe_layout.addWidget(self.pe_max)
        cond_layout.addRow('市盈率范围:', pe_layout)

        # 市净率
        pb_layout = QHBoxLayout()
        self.pb_min = QSpinBox()
        self.pb_min.setRange(-1000, 1000)
        self.pb_min.setValue(0)
        self.pb_min.setSuffix(' 倍')
        pb_layout.addWidget(QLabel('PB(市净率):'))
        pb_layout.addWidget(self.pb_min)
        pb_layout.addWidget(QLabel(' ~ '))
        self.pb_max = QSpinBox()
        self.pb_max.setRange(-1000, 1000)
        self.pb_max.setValue(5)
        self.pb_max.setSuffix(' 倍')
        pb_layout.addWidget(self.pb_max)
        cond_layout.addRow('市净率范围:', pb_layout)

        # 换手率
        self.turnover_min = QSpinBox()
        self.turnover_min.setRange(0, 100)
        self.turnover_min.setValue(0)
        self.turnover_min.setSuffix(' %')
        cond_layout.addRow('最小换手率:', self.turnover_min)

        # 总市值
        self.total_mv_max = QSpinBox()
        self.total_mv_max.setRange(0, 100000)
        self.total_mv_max.setValue(1000)
        self.total_mv_max.setSuffix(' 亿')
        cond_layout.addRow('最大总市值:', self.total_mv_max)

        # 行业
        self.industry_combo = QComboBox()
        self.industry_combo.addItem('不限', None)
        industries = self.selector.get_industries()
        for ind in industries:
            self.industry_combo.addItem(ind if ind else '其他', ind)
        cond_layout.addRow('行业:', self.industry_combo)

        # 市场
        self.market_combo = QComboBox()
        self.market_combo.addItem('不限', None)
        markets = self.selector.get_markets()
        for mkt in markets:
            self.market_combo.addItem(mkt if mkt else '其他', mkt)
        cond_layout.addRow('市场:', self.market_combo)

        # 价格范围
        price_layout = QHBoxLayout()
        self.price_min = QSpinBox()
        self.price_min.setRange(0, 10000)
        self.price_min.setValue(0)
        self.price_min.setSuffix(' 元')
        price_layout.addWidget(self.price_min)
        price_layout.addWidget(QLabel(' ~ '))
        self.price_max = QSpinBox()
        self.price_max.setRange(0, 10000)
        self.price_max.setValue(100)
        self.price_max.setSuffix(' 元')
        price_layout.addWidget(self.price_max)
        cond_layout.addRow('价格范围:', price_layout)

        cond_group.setLayout(cond_layout)
        selector_layout.addWidget(cond_group)

        # 选股按钮
        btn_layout = QHBoxLayout()
        self.screen_btn = QPushButton('开始选股')
        self.screen_btn.clicked.connect(self.do_screen)
        self.screen_btn.setStyleSheet('background: #4CAF50; color: white; padding: 8px; font-size: 14px;')
        btn_layout.addWidget(self.screen_btn)

        self.clear_btn = QPushButton('清空结果')
        self.clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(self.clear_btn)
        selector_layout.addLayout(btn_layout)

        # 选股结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(10)
        self.result_table.setHorizontalHeaderLabels([
            '代码', '名称', '行业', '市场', '现价', 'PE', 'PB', '换手率%', '总市值(亿)', '流通市值(亿)'
        ])
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.doubleClicked.connect(self.on_result_double_click)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        selector_layout.addWidget(self.result_table)

        self.tabs.addTab(selector_tab, '选股')

        # 将右侧内容添加到分割器，并设置central_widget的布局
        splitter.addWidget(right_widget)
        central_widget.setLayout(QHBoxLayout())
        central_widget.layout().addWidget(splitter)

        # 连接搜索框文本变化信号，用于更新自动提示
        self.search_input.textChanged.connect(self.update_search_suggestions)
        # 加载所有股票数据用于自动补全
        self.load_all_stocks_for_completion()

    def load_all_stocks_for_completion(self):
        """加载所有股票用于自动补全"""
        try:
            conn = self.get_db_connection()
            sql = "SELECT ts_code, name FROM stock_basic ORDER BY ts_code"
            df = pd.read_sql_query(sql, conn)
            conn.close()

            # 构建补全列表：格式为 "代码 名称"
            completions = []
            for _, row in df.iterrows():
                pinyin = get_pinyin_initials(row['name'])
                # 同时添加带拼音首字母的版本
                completions.append(f"{row['ts_code']} {row['name']}")
                if pinyin:
                    completions.append(f"{pinyin} {row['ts_code']} {row['name']}")

            # 去重
            completions = list(dict.fromkeys(completions))
            self.completer.model().setStringList(completions)
            self.all_completions = completions  # 保存完整列表
            self.all_stocks_df = df
        except Exception as e:
            print(f"加载股票列表失败: {e}")

    def update_search_suggestions(self, text):
        """根据输入更新搜索建议"""
        # 如果文本为空，恢复完整列表
        if not text:
            if hasattr(self, 'all_completions'):
                self.completer.model().setStringList(self.all_completions)
            return

        if len(text) < 1:
            return

        # 过滤匹配项
        text_upper = text.upper()
        filtered = [s for s in self.all_completions
                   if s.upper().startswith(text_upper) or text_upper in s.upper()]
        self.completer.model().setStringList(filtered[:20])

    def on_completer_return(self):
        """当用户在搜索框按回车时，从补全列表当前选中项加载股票"""
        # 获取当前补全popup中选中的项
        popup = self.completer.popup()
        if popup.isVisible():
            # 从popup当前选中行获取文本
            index = popup.currentIndex()
            if index.isValid():
                text = self.completer.model().data(index)
                if text:
                    parts = text.split()
                    for part in reversed(parts):
                        if '.' in part and len(part) == 9:
                            self.load_stock(part)
                            return
        # 如果popup不可见或没有选中，使用当前输入文本搜索
        self.on_search()

    def load_watchlist(self):
        """加载自选股列表"""
        if os.path.exists(self.watchlist_file):
            try:
                df = pd.read_csv(self.watchlist_file)
                self.watchlist = list(zip(df['ts_code'], df['name']))
                self.update_watchlist_table()
            except Exception as e:
                print(f"加载自选股失败: {e}")

    def save_watchlist(self):
        """保存自选股列表"""
        try:
            df = pd.DataFrame(self.watchlist, columns=['ts_code', 'name'])
            df.to_csv(self.watchlist_file, index=False)
        except Exception as e:
            print(f"保存自选股失败: {e}")

    def load_date_range(self):
        """加载保存的日期范围"""
        import json
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                start_str = config.get('start_date')
                end_str = config.get('end_date')
                if start_str:
                    self.start_date.setDate(QDate.fromString(start_str, 'yyyyMMdd'))
                else:
                    self.start_date.setDate(QDate.currentDate().addMonths(-3))
                if end_str:
                    self.end_date.setDate(QDate.fromString(end_str, 'yyyyMMdd'))
                else:
                    self.end_date.setDate(QDate.currentDate())
            else:
                self.start_date.setDate(QDate.currentDate().addMonths(-3))
                self.end_date.setDate(QDate.currentDate())
        except Exception as e:
            self.start_date.setDate(QDate.currentDate().addMonths(-3))
            self.end_date.setDate(QDate.currentDate())

    def save_date_range(self):
        """保存日期范围"""
        import json
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            config['start_date'] = self.start_date.date().toString('yyyyMMdd')
            config['end_date'] = self.end_date.date().toString('yyyyMMdd')
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"保存日期范围失败: {e}")

    def update_watchlist_table(self):
        """更新自选股列表显示"""
        self.watchlist_table.setRowCount(len(self.watchlist))
        self.watchlist_table.verticalHeader().setDefaultSectionSize(22)

        # 获取每只股票的最新价格
        conn = self.get_db_connection()
        latest_date_sql = "SELECT MAX(trade_date) FROM daily"
        cursor = conn.execute(latest_date_sql)
        latest_date = cursor.fetchone()[0]

        for i, (ts_code, name) in enumerate(self.watchlist):
            self.watchlist_table.setItem(i, 0, QTableWidgetItem(ts_code))
            self.watchlist_table.setItem(i, 1, QTableWidgetItem(name))

            # 获取最新价格
            price_sql = "SELECT close FROM daily WHERE ts_code = ? AND trade_date = ?"
            cursor = conn.execute(price_sql, (ts_code, latest_date))
            result = cursor.fetchone()
            price = f"{result[0]:.2f}" if result else "N/A"
            self.watchlist_table.setItem(i, 2, QTableWidgetItem(price))

        conn.close()

    def add_to_watchlist(self):
        """添加自选股"""
        # 优先使用当前已加载的股票
        if self.current_stock:
            conn = self.get_db_connection()
            sql = "SELECT ts_code, name FROM stock_basic WHERE ts_code = ?"
            df = pd.read_sql_query(sql, conn, params=[self.current_stock])
            conn.close()
            if len(df) > 0:
                ts_code = df.iloc[0]['ts_code']
                name = df.iloc[0]['name']
                self._add_stock_to_watchlist(ts_code, name)
                return

        # 否则使用搜索框内容
        keyword = self.search_combo.currentText().strip()
        if not keyword:
            QMessageBox.information(self, '提示', '请先搜索股票')
            return

        conn = self.get_db_connection()
        sql = """
            SELECT ts_code, name FROM stock_basic
            WHERE ts_code LIKE ? OR name LIKE ? OR symbol LIKE ?
            LIMIT 5
        """
        search_pattern = f'%{keyword}%'
        df = pd.read_sql_query(sql, conn, params=[search_pattern, search_pattern, search_pattern])

        # 如果没有匹配，检查是否是拼音首字母搜索
        if len(df) == 0:
            all_sql = "SELECT ts_code, name FROM stock_basic"
            all_df = pd.read_sql_query(all_sql, conn)
            conn.close()
            mask = all_df['name'].apply(lambda x: has_pinyin_match(x, keyword))
            df = all_df[mask].head(5)
        else:
            conn.close()

        if len(df) == 0:
            QMessageBox.information(self, '提示', '未找到匹配的股票')
            return

        if len(df) == 1:
            ts_code = df.iloc[0]['ts_code']
            name = df.iloc[0]['name']
            self._add_stock_to_watchlist(ts_code, name)
        else:
            dlg = StockSelectionDialog(df, self)
            if dlg.exec_():
                ts_code = dlg.selected_code
                if ts_code:
                    row = df[df['ts_code'] == ts_code].iloc[0]
                    self._add_stock_to_watchlist(ts_code, row['name'])

    def _add_stock_to_watchlist(self, ts_code, name):
        """内部方法：添加股票到自选股"""
        # 检查是否已存在
        for code, _ in self.watchlist:
            if code == ts_code:
                QMessageBox.information(self, '提示', f'{name} 已在自选股中')
                return

        self.watchlist.append((ts_code, name))
        self.save_watchlist()
        self.update_watchlist_table()
        QMessageBox.information(self, '成功', f'已添加 {name} 到自选股')

    def remove_from_watchlist(self):
        """从自选股删除"""
        row = self.watchlist_table.currentRow()
        if row >= 0:
            ts_code, name = self.watchlist[row]
            self.watchlist.pop(row)
            self.save_watchlist()
            self.update_watchlist_table()

    def on_watchlist_double_click(self, index):
        """双击自选股查看K线"""
        row = index.row()
        if row >= 0 and row < len(self.watchlist):
            ts_code, _ = self.watchlist[row]
            self.load_stock(ts_code)

    def get_db_connection(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def on_search(self):
        """搜索股票（支持代码、名称、拼音首字母搜索）"""
        keyword = self.search_combo.currentText().strip()
        if not keyword:
            return

        conn = self.get_db_connection()

        # 尝试匹配代码或名称
        sql = """
            SELECT ts_code, symbol, name, industry, market
            FROM stock_basic
            WHERE ts_code LIKE ? OR name LIKE ? OR symbol LIKE ?
        """
        search_pattern = f'%{keyword}%'
        df = pd.read_sql_query(sql, conn, params=[search_pattern, search_pattern, search_pattern])

        # 如果没有匹配，检查是否是拼音首字母搜索
        if len(df) == 0:
            # 获取所有股票进行拼音首字母匹配
            all_sql = "SELECT ts_code, symbol, name, industry, market FROM stock_basic"
            all_df = pd.read_sql_query(all_sql, conn)
            conn.close()

            # 过滤出拼音首字母匹配的
            mask = all_df['name'].apply(lambda x: has_pinyin_match(x, keyword))
            df = all_df[mask].head(10)
        else:
            conn.close()

        if len(df) == 0:
            QMessageBox.information(self, '提示', '未找到匹配的股票')
            return

        if len(df) == 1:
            row = df.iloc[0]
            self.load_stock(row['ts_code'])
        else:
            # 弹出选择框
            self.show_stock_selection(df)

    def show_stock_selection(self, df):
        """显示股票选择对话框"""
        dlg = StockSelectionDialog(df, self)
        if dlg.exec_():
            ts_code = dlg.selected_code
            if ts_code:
                self.load_stock(ts_code)

    def load_stock(self, ts_code):
        """加载股票数据"""
        conn = self.get_db_connection()

        # 获取股票基本信息
        basic_sql = "SELECT * FROM stock_basic WHERE ts_code = ?"
        basic_df = pd.read_sql_query(basic_sql, conn, params=[ts_code])

        if len(basic_df) == 0:
            conn.close()
            QMessageBox.warning(self, '错误', f'未找到股票 {ts_code}')
            return

        basic = basic_df.iloc[0]
        name = basic['name']
        self.current_stock = ts_code
        self.search_combo.setCurrentText(f"{ts_code} {name}")

        # 获取日期范围
        start_date = self.start_date.date().toString('yyyyMMdd')
        end_date = self.end_date.date().toString('yyyyMMdd')

        # 获取日线数据
        daily_sql = """
            SELECT trade_date, open, high, low, close, vol, amount
            FROM daily
            WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?
            ORDER BY trade_date
        """
        daily_df = pd.read_sql_query(daily_sql, conn, params=[ts_code, start_date, end_date])

        # 获取每日指标
        basic_sql = """
            SELECT trade_date, pe, pb, turnover_rate, total_mv, circ_mv
            FROM daily_basic
            WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?
            ORDER BY trade_date
        """
        basic_data_df = pd.read_sql_query(basic_sql, conn, params=[ts_code, start_date, end_date])

        conn.close()

        # 合并数据
        if len(daily_df) > 0:
            df = daily_df.copy()
            if len(basic_data_df) > 0:
                df = pd.merge(df, basic_data_df, on='trade_date', how='left')

            # 更新K线图
            self.kline_chart.plot_kline(df, ts_code, name)

            # 更新股票信息
            latest = df.iloc[-1]
            info_text = (
                f"代码: {ts_code} | 名称: {name} | "
                f"最新价: {latest['close']:.2f} | "
                f"PE: {latest.get('pe', 'N/A')} | "
                f"PB: {latest.get('pb', 'N/A')} | "
                f"换手率: {latest.get('turnover_rate', 'N/A')}%"
            )
            self.stock_info_label.setText(info_text)
        else:
            self.stock_info_label.setText(f'股票 {name} ({ts_code}) - 暂无数据')

        # 切换到K线Tab
        self.tabs.setCurrentIndex(0)

        # 刷新自选股价格显示
        self.update_watchlist_table()

    def prev_stock(self):
        """切换到上一只股票"""
        if not self.current_stock:
            return
        self._switch_stock(-1)

    def next_stock(self):
        """切换到下一只股票"""
        if not self.current_stock:
            return
        self._switch_stock(1)

    def _switch_stock(self, direction):
        """切换股票"""
        conn = self.get_db_connection()
        sql = "SELECT ts_code FROM stock_basic ORDER BY ts_code"
        df = pd.read_sql_query(sql, conn)
        conn.close()

        codes = df['ts_code'].tolist()
        if self.current_stock in codes:
            idx = codes.index(self.current_stock)
            idx = (idx + direction) % len(codes)
            self.load_stock(codes[idx])

    def do_screen(self):
        """执行选股"""
        conditions = {
            'pe_min': self.pe_min.value() if self.pe_min.value() > 0 else None,
            'pe_max': self.pe_max.value() if self.pe_max.value() > 0 else None,
            'pb_min': self.pb_min.value() if self.pb_min.value() > 0 else None,
            'pb_max': self.pb_max.value() if self.pb_max.value() > 0 else None,
            'turnover_rate_min': self.turnover_min.value() if self.turnover_min.value() > 0 else None,
            'total_mv_max': self.total_mv_max.value() if self.total_mv_max.value() > 0 else None,
            'industry': self.industry_combo.currentData(),
            'market': self.market_combo.currentData(),
            'price_min': self.price_min.value() if self.price_min.value() > 0 else None,
            'price_max': self.price_max.value() if self.price_max.value() > 0 else None,
        }

        # 移除None条件
        conditions = {k: v for k, v in conditions.items() if v is not None}

        df = self.selector.screen_stocks(conditions)

        # 更新表格
        self.result_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.result_table.setItem(i, 0, QTableWidgetItem(str(row.get('ts_code', ''))))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(row.get('name', ''))))
            self.result_table.setItem(i, 2, QTableWidgetItem(str(row.get('industry', ''))))
            self.result_table.setItem(i, 3, QTableWidgetItem(str(row.get('market', ''))))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{row.get('price', 0):.2f}"))
            self.result_table.setItem(i, 5, QTableWidgetItem(f"{row.get('pe', 'N/A')}"))
            self.result_table.setItem(i, 6, QTableWidgetItem(f"{row.get('pb', 'N/A')}"))
            self.result_table.setItem(i, 7, QTableWidgetItem(f"{row.get('turnover_rate', 'N/A')}"))
            self.result_table.setItem(i, 8, QTableWidgetItem(f"{row.get('total_mv', 0)/10000:.2f}"))
            self.result_table.setItem(i, 9, QTableWidgetItem(f"{row.get('circ_mv', 0)/10000:.2f}"))

        QMessageBox.information(self, '选股结果', f'找到 {len(df)} 只符合条件的股票')

    def on_skill_changed(self, index):
        """技能选择改变时更新参数UI"""
        # 清除旧的参数
        while self.skill_params_layout.count():
            item = self.skill_params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.skill_params = {}

        skill_name = self.skill_combo.currentData()
        if not skill_name:
            self.current_skill = None
            return

        # 获取技能实例
        self.current_skill = self.skill_manager.get_skill(skill_name)
        if not self.current_skill:
            return

        # 获取技能条件
        conditions = self.current_skill.get_conditions()
        for cond in conditions:
            if cond.type == 'number':
                spin = QSpinBox()
                spin.setRange(0, 999999)
                spin.setValue(cond.default if cond.default is not None else 0)
                self.skill_params_layout.addRow(f"{cond.label}:", spin)
                self.skill_params[cond.name] = spin
            elif cond.type == 'percent':
                spin = QDoubleSpinBox()
                spin.setRange(0, 100)
                spin.setDecimals(2)
                spin.setValue(cond.default if cond.default is not None else 0)
                spin.setSuffix('%')
                self.skill_params_layout.addRow(f"{cond.label}:", spin)
                self.skill_params[cond.name] = spin
            else:
                line = QLineEdit()
                line.setText(str(cond.default if cond.default is not None else ''))
                self.skill_params_layout.addRow(f"{cond.label}:", line)
                self.skill_params[cond.name] = line

    def reload_skills(self):
        """重新加载技能列表"""
        self.skill_manager.load_skills()
        self.skill_combo.clear()
        self.skill_combo.addItem('-- 请选择技能 --', None)
        for skill_info in self.skill_manager.get_skills_list():
            self.skill_combo.addItem(
                f"{skill_info['meta']['name']} ({skill_info['meta']['version']})",
                skill_info['name']
            )

    def do_skill_screen(self):
        """执行技能选股"""
        if not self.current_skill:
            QMessageBox.information(self, '提示', '请先选择一个技能')
            return

        # 收集参数
        conditions = {}
        for name, widget in self.skill_params.items():
            if isinstance(widget, QSpinBox):
                conditions[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                conditions[name] = widget.value()
            elif isinstance(widget, QLineEdit):
                val = widget.text()
                try:
                    conditions[name] = int(val) if val else 0
                except ValueError:
                    try:
                        conditions[name] = float(val) if val else 0
                    except ValueError:
                        conditions[name] = val

        # 执行选股
        result = self.current_skill.screen(conditions)
        self.skill_result = result  # 保存结果供后续使用

        if result is None or len(result) == 0:
            self.result_table.setRowCount(0)
            QMessageBox.information(self, '选股结果', '没有找到符合条件的股票')
            return

        # 更新表格 - 技能结果可能有不同列
        self.result_table.setColumnCount(max(7, len(result.columns) + 1))
        headers = ['代码', '名称', '最新日期', '收盘价', '涨幅', '累计涨幅', '连续天数']
        for i, col in enumerate(result.columns):
            if i < len(headers):
                self.result_table.setHorizontalHeaderItem(i, QTableWidgetItem(headers[i] if i < 7 else str(col)))
            else:
                self.result_table.setHorizontalHeaderItem(i, QTableWidgetItem(str(col)))

        self.result_table.setRowCount(len(result))
        for i, row in result.iterrows():
            self.result_table.setItem(i, 0, QTableWidgetItem(str(row.get('ts_code', ''))))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(row.get('name', ''))))
            self.result_table.setItem(i, 2, QTableWidgetItem(str(row.get('latest_date', ''))))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{row.get('close', 0):.2f}"))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{row.get('pct_chg', 0):+.2f}%"))
            self.result_table.setItem(i, 5, QTableWidgetItem(f"{row.get('total_pct_chg', 0):+.2f}%"))
            self.result_table.setItem(i, 6, QTableWidgetItem(str(row.get('consecutive_days', ''))))

        QMessageBox.information(self, '选股结果', f'找到 {len(result)} 只符合条件的股票')

    def add_skill_result_to_watchlist(self):
        """将技能选股结果添加到自选股"""
        if not hasattr(self, 'skill_result') or self.skill_result is None or len(self.skill_result) == 0:
            QMessageBox.information(self, '提示', '没有可添加的选股结果')
            return

        added = 0
        for _, row in self.skill_result.iterrows():
            ts_code = row.get('ts_code')
            name = row.get('name')
            if ts_code and name:
                # 检查是否已存在
                exists = False
                for code, _ in self.watchlist:
                    if code == ts_code:
                        exists = True
                        break
                if not exists:
                    self.watchlist.append((ts_code, name))
                    added += 1

        if added > 0:
            self.save_watchlist()
            self.update_watchlist_table()
            QMessageBox.information(self, '成功', f'已添加 {added} 只股票到自选股')
        else:
            QMessageBox.information(self, '提示', '所有股票已在自选股中')

    def clear_results(self):
        """清空选股结果"""
        self.result_table.setRowCount(0)

    def on_result_double_click(self, index):
        """双击选股结果查看K线"""
        row = index.row()
        ts_code = self.result_table.item(row, 0).text()
        if ts_code:
            self.load_stock(ts_code)


class StockSelectionDialog(QDialog):
    """股票选择对话框"""

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.selected_code = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('选择股票')
        self.setGeometry(300, 300, 500, 300)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['代码', '名称', '行业', '市场'])
        self.table.setRowCount(len(self.df))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_select)

        for i, row in self.df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row['ts_code'])))
            self.table.setItem(i, 1, QTableWidgetItem(str(row['name'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get('industry', ''))))
            self.table.setItem(i, 3, QTableWidgetItem(str(row.get('market', ''))))

        layout.addWidget(self.table)

        # 添加按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_select(self, index):
        row = index.row()
        self.selected_code = self.table.item(row, 0).text()
        self.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置字体
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)

    window = KLineViewer()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
