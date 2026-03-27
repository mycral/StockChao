import akshare as ak

# ========== 1. 获取所有地区板块（同花顺接口，全版本兼容） ==========
area_list = ak.stock_board_area_ths()
print("===== 全部地区板块 =====")
print(area_list[["code", "name"]])

# ========== 2. 获取福建板块（全版本可用） ==========
fj_stocks = ak.stock_board_area_cons_ths(symbol="福建")
print("\n===== 福建板块股票 =====")
print(fj_stocks[["代码", "名称", "涨跌幅"]])

# ========== 3. 获取海峡两岸概念（全版本可用） ==========
hxla_stocks = ak.stock_board_concept_cons_ths(symbol="海峡两岸")
print("\n===== 海峡两岸概念 =====")
print(hxla_stocks[["代码", "名称", "涨跌幅"]])