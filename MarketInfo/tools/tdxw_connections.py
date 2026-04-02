# -*- coding: utf-8 -*-
"""
查看 TdxW.exe 进程的网络连接
"""
import subprocess


def get_tdxw_server() -> str:
    """获取 TdxW.exe 连接的远程服务器地址

    Returns:
        str: 服务器地址，如 "123.60.164.122:7709"，无连接返回 ""
    """
    try:
        # 获取进程 ID
        ps_get_pid = "(Get-Process -Name TdxW -ErrorAction SilentlyContinue).Id"
        pid_result = subprocess.run(
            ['powershell', '-Command', ps_get_pid],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if not pid_result.stdout.strip():
            return ""

        pid = pid_result.stdout.strip()

        # 获取 TCP 连接
        ps_script = f"Get-NetTCPConnection -OwningProcess {pid} -ErrorAction SilentlyContinue"
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        output = result.stdout
        if not output or 'Established' not in output:
            return ""

        # 提取远程服务器地址
        for line in output.split('\n'):
            if 'Established' in line and 'RemoteAddress' not in line:
                parts = line.split()
                if len(parts) >= 4:
                    return f"{parts[2]}:{parts[3]}"

        return ""

    except Exception:
        return ""


def get_tdxw_connections():
    """获取 TdxW.exe 的 TCP 连接（详细版）"""
    output = get_tdxw_server()
    if not output:
        return []

    return [{"host": output.split(":")[0], "port": int(output.split(":")[1])}]


def main():
    print("=== TdxW.exe TCP 连接 ===\n")

    # 方法1: 获取单个服务器
    server = get_tdxw_server()
    if server:
        print(f"远程服务器: {server}\n")
    else:
        print("未发现 TdxW.exe 的活动连接\n")

    # 方法2: 获取连接列表
    connections = get_tdxw_connections()
    print(f"发现 {len(connections)} 个连接:")
    for conn in connections:
        print(f"  {conn['host']}:{conn['port']}")


if __name__ == '__main__':
    main()