# -*- coding: utf-8 -*-
"""
Pytdx 分时数据源
通过 Pytdx 获取实时分时数据
"""
import subprocess
import time
import threading
import pandas as pd
from pytdx.hq import TdxHq_API
from .base import MinuteSource
from .cache import MinuteCache


def get_tdxw_server() -> str:
    """获取 TdxW.exe 连接的远程服务器地址

    Returns:
        str: 服务器地址，如 "123.60.164.122:7709"，无连接返回 ""
    """
    try:
        ps_get_pid = "(Get-Process -Name TdxW -ErrorAction SilentlyContinue).Id"
        pid_result = subprocess.run(
            ['powershell', '-Command', ps_get_pid],
            capture_output=True, text=True, encoding='utf-8'
        )
        if not pid_result.stdout.strip():
            return ""

        pid = pid_result.stdout.strip()
        ps_script = f"Get-NetTCPConnection -OwningProcess {pid} -ErrorAction SilentlyContinue"
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True, text=True, encoding='utf-8'
        )

        output = result.stdout
        if not output or 'Established' not in output:
            return ""

        for line in output.split('\n'):
            if 'Established' in line and 'RemoteAddress' not in line:
                parts = line.split()
                if len(parts) >= 4:
                    return f"{parts[2]}:{parts[3]}"
        return ""
    except Exception:
        return ""


# 默认服务器（用户本地通达信）
DEFAULT_SERVER = '123.60.164.122'
DEFAULT_PORT = 7709


class PytdxMinuteSource(MinuteSource):
    """Pytdx 分时数据源"""

    def __init__(
        self,
        host=DEFAULT_SERVER,
        port=DEFAULT_PORT,
        auto_refresh=True,
        refresh_interval=300
    ):
        """
        初始化 Pytdx 数据源

        Args:
            host: 默认服务器地址
            port: 默认服务器端口
            auto_refresh: 是否自动检测 TdxW 服务器变化
            refresh_interval: 刷新间隔(秒)，默认5分钟
        """
        self._host = host
        self._port = port
        self._api = None
        self._auto_refresh = auto_refresh
        self._refresh_interval = refresh_interval
        self._last_server = f"{host}:{port}"
        self._refresh_thread = None
        self._running = False
        self._cache = MinuteCache()

        # 优先使用缓存的服务器
        cached = self._cache.get_server()
        if cached[0] and cached[1]:
            self._host = cached[0]
            self._port = cached[1]
            self._last_server = f"{cached[0]}:{cached[1]}"

        # 启动自动刷新
        if auto_refresh:
            self._start_refresh_thread()

    def _start_refresh_thread(self):
        """启动后台线程定时检测服务器变化"""
        self._running = True
        self._refresh_thread = threading.Thread(
            target=self._refresh_loop,
            daemon=True
        )
        self._refresh_thread.start()

    def _refresh_loop(self):
        """定时刷新循环"""
        while self._running:
            time.sleep(self._refresh_interval)
            if not self._running:
                break
            self._check_new_server()

    def _check_new_server(self):
        """检查是否有新的服务器地址，添加到列表"""
        try:
            new_server = get_tdxw_server()
            if new_server:
                host, port_str = new_server.split(':')
                port = int(port_str)
                # 添加到服务器列表
                self._cache.add_server(host, port)
                print(f"[PytdxMinuteSource] 添加服务器到列表: {new_server}")
        except Exception as e:
            print(f"[PytdxMinuteSource] 检测新服务器失败: {e}")

    def _try_connect(self, host: str, port: int) -> bool:
        """尝试连接服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            test_api = TdxHq_API()
            if test_api.connect(host, port):
                # 测试获取一只股票
                data = test_api.get_security_bars(3, 1, '600519', 0, 1)
                test_api.disconnect()
                return data is not None
        except Exception:
            pass
        return False

    def _connect(self):
        """建立连接，失败时尝试备用服务器"""
        # 检查现有连接是否有效
        if self._api is not None:
            try:
                # 测试连接是否有效
                test_data = self._api.get_security_bars(3, 1, '600519', 0, 1)
                if test_data:
                    return True
            except Exception as e:
                print(f"[PytdxMinuteSource] 连接测试失败: {e}")
                # 连接已失效，断开重连
                self._disconnect()

        # 尝试当前服务器
        if self._try_connect(self._host, self._port):
            self._api = TdxHq_API()
            self._api.connect(self._host, self._port)
            return True

        # 从缓存获取服务器列表，尝试其他服务器
        server_list = self._cache.get_server_list()
        for host, port in server_list:
            # 跳过当前服务器
            if host == self._host and port == self._port:
                continue
            print(f"[PytdxMinuteSource] 尝试备用服务器: {host}:{port}")
            if self._try_connect(host, port):
                self._host = host
                self._port = port
                self._last_server = f"{host}:{port}"
                self._api = TdxHq_API()
                self._api.connect(self._host, self._port)
                # 更新缓存中的主服务器
                self._cache.set_server(host, port)
                return True

        # 所有服务器都失败
        print(f"[PytdxMinuteSource] 所有服务器连接失败")
        # 移除当前服务器（标记为不可用）
        self._cache.remove_server(self._host, self._port)
        return False

    def _disconnect(self):
        """断开连接"""
        if self._api:
            try:
                self._api.disconnect()
            except:
                pass
            self._api = None

    @property
    def name(self) -> str:
        return "pytdx"

    def fetch(self, ts_code: str) -> pd.DataFrame:
        """获取分时数据

        Args:
            ts_code: 股票代码，如 '600519.SH'

        Returns:
            DataFrame 或 None
        """
        try:
            # 解析市场代码
            code = ts_code.split('.')[0]
            suffix = ts_code.split('.')[1].upper()
            market = 1 if suffix == "SH" else 0

            # 建立连接
            if not self._connect() or self._api is None:
                return None

            import datetime

            # 判断当前时间：9:30之前用历史数据，9:30之后用实时数据
            now = datetime.datetime.now()
            current_time = now.time()
            market_open = datetime.time(9, 30)  # 开盘时间
            is_before_open = current_time < market_open

            # 如果在9:30之前，先尝试获取昨天的历史数据
            # 如果在9:30之后，尝试获取今天的实时数据
            today = int(now.strftime('%Y%m%d'))
            yesterday = int((now - datetime.timedelta(days=1)).strftime('%Y%m%d'))
            data_date = today

            data = None

            if is_before_open:
                # 9:30之前：使用历史分钟数据（昨天）
                try:
                    data = self._api.get_history_minute_time_data(market, code, yesterday)
                    if data and len(data) >= 10:
                        data_date = yesterday
                except:
                    pass
            else:
                # 9:30之后：尝试获取今天的实时数据
                try:
                    data = self._api.get_minute_time_data(market, code)
                except:
                    pass

                # 如果实时数据不足，尝试历史数据
                if not data or len(data) < 10:
                    try:
                        data = self._api.get_history_minute_time_data(market, code, today)
                    except:
                        pass

                    # 再尝试昨天
                    if not data or len(data) < 10:
                        try:
                            data = self._api.get_history_minute_time_data(market, code, yesterday)
                            if data and len(data) >= 10:
                                data_date = yesterday
                        except:
                            pass

            # 如果还是没有，回退到 get_security_bars
            if not data or len(data) < 10:
                data = self._api.get_security_bars(3, market, code, 0, 240)

            if data is None or len(data) == 0:
                return None

            # 转换为 DataFrame
            df = pd.DataFrame.from_records(data)

            # 检查数据类型：get_history_minute_time_data 返回 price/vol，get_security_bars 返回 OHLCV
            if 'price' in df.columns:
                # 分钟数据：price, vol -> 转换为 OHLCV 格式
                df = df.rename(columns={'price': 'close', 'vol': 'volume'})
                df['volume'] = df['volume'].abs()  # 成交量取绝对值

                # 过滤异常价格（调整为合理范围）
                df = df[(df['close'] > 0) & (df['close'] < 10000)]
                df = df[df['volume'] > 0]

                # 排序（时间正序）
                df = df.sort_index()

                # 添加 day 列（使用索引作为时间代理）
                if len(df) > 0:
                    # 确定使用的日期（昨天还是今天）
                    if data_date == today:
                        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
                    else:
                        date_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

                    # 生成时间序列 09:30 - 15:00
                    times = []
                    base_minute = 9 * 60 + 30  # 570
                    for i in range(len(df)):
                        hour = (base_minute + i * 1) // 60
                        minute = (base_minute + i * 1) % 60
                        if hour < 15 or (hour == 15 and minute == 0):
                            times.append(f"{date_str} {hour:02d}:{minute:02d}:00")
                    df['day'] = times[:len(df)]
                    df['open'] = df['close']
                    df['high'] = df['close']
                    df['low'] = df['close']
                    df['amount'] = df['close'] * df['volume'] * 100  # 估算

                    # 选择需要的列
                    cols = ['day', 'open', 'high', 'low', 'close', 'volume', 'amount']
                    df = df[cols]
            else:
                # get_security_bars 返回的数据（已有 OHLCV 格式）
                df = df.rename(columns={'vol': 'volume'})
                cols = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
                df = df[cols].copy()
                df = df.rename(columns={'datetime': 'day'})

            # 过滤最后交易日
            if len(df) > 0:
                df['day'] = pd.to_datetime(df['day'])
                last_date = df['day'].max().date()
                df = df[df['day'].dt.date == last_date].copy()

            return df

        except Exception as e:
            print(f"[PytdxMinuteSource] 获取 {ts_code} 失败: {e}")
            # 连接失败时断开
            self._disconnect()
            return None

    def close(self):
        """关闭连接和后台线程"""
        self._running = False
        self._disconnect()