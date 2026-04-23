# 数据源配置说明

## 📊 已配置的数据源

### 钢材行业（5个）

| ID | 名称 | 品种 | 更新频率 | 状态 |
|----|------|------|---------|------|
| `rebar_future_price` | 螺纹钢期货价格 | 螺纹钢 | 实时 | ✅ 启用 |
| `hot_rolled_coil_future` | 热轧卷板期货 | 热轧卷板 | 实时 | ✅ 启用 |
| `iron_ore_future` | 铁矿石期货 | 铁矿石 | 实时 | ✅ 启用 |
| `coke_future` | 焦炭期货 | 焦炭 | 实时 | ✅ 启用 |
| `coking_coal_future` | 焦煤期货 | 焦煤 | 实时 | ✅ 启用 |

### 有色金属（3个）

| ID | 名称 | 品种 | 更新频率 | 状态 |
|----|------|------|---------|------|
| `copper_future` | 铜期货价格 | 铜 | 实时 | ✅ 启用 |
| `aluminum_future` | 铝期货价格 | 铝 | 实时 | ✅ 启用 |
| `zinc_future` | 锌期货价格 | 锌 | 实时 | ✗ 禁用 |

### 库存数据（2个）

| ID | 名称 | 数据类型 | 更新频率 | 状态 |
|----|------|---------|---------|------|
| `shfe_warehouse` | 上期所仓单库存 | 交易所库存 | 日度 | ✅ 启用 |
| `dce_warehouse` | 大商所仓单库存 | 交易所库存 | 日度 | ✅ 启用 |

### 产量数据（1个）

| ID | 名称 | 数据类型 | 更新频率 | 状态 |
|----|------|---------|---------|------|
| `crude_steel_production` | 粗钢产量 | 产量 | 月度 | ✅ 启用 |

### 宏观数据（3个）

| ID | 名称 | 数据类型 | 更新频率 | 状态 |
|----|------|---------|---------|------|
| `pmi_index` | PMI指数 | 宏观 | 月度 | ✅ 启用 |
| `industrial_production` | 工业增加值 | 宏观 | 月度 | ✅ 启用 |
| `fixed_asset_investment` | 固定资产投资 | 宏观 | 月度 | ✅ 启用 |

**总计**：14个数据源（13个启用，1个禁用）

---

## 🚀 快速开始

### 1. 测试数据获取

```bash
# 测试所有数据源
python test_data_manager.py

# 或测试AKShare
python test_akshare_demo.py
```

### 2. 启用/禁用数据源

编辑 `config/data_sources.yaml`：

```yaml
# 启用锌期货
zinc_future:
  name: "锌期货价格"
  type: "akshare"
  enabled: true  # ← 改为 true
  function: "futures_main_sina"
  params:
    symbol: "ZN0"
```

### 3. 添加新的数据源

在 `config/data_sources.yaml` 中添加：

```yaml
data_sources:
  # 添加镍期货
  nickel_future:
    name: "镍期货价格"
    type: "akshare"
    enabled: true
    function: "futures_main_sina"
    params:
      symbol: "NI0"
    data_category: "price"
    data_type: "future"
    product: "nickel"
```

---

## 📖 配置字段说明

### 必填字段

- `name`: 数据源名称（用于显示）
- `type`: 数据源类型（`akshare` / `web_scrape` / `api`）
- `enabled`: 是否启用（`true` / `false`）
- `function`: AKShare函数名
- `data_category`: 数据类别（`price` / `inventory` / `production` / `macro`）
- `product`: 产品名称（`steel` / `copper` / `aluminum` 等）

### 可选字段

- `params`: 函数参数（字典）
- `data_type`: 数据类型（`spot` / `future` / `exchange` 等）
- `field_mapping`: 字段映射（用于指定日期和数值字段）

---

## 🔍 AKShare支持的品种代码

### 期货代码

```python
# 黑色系
RB0  - 螺纹钢
HC0  - 热轧卷板
I0   - 铁矿石
J0   - 焦炭
JM0  - 焦煤

# 有色金属
CU0  - 铜
AL0  - 铝
ZN0  - 锌
PB0  - 铅
NI0  - 镍
SN0  - 锡

# 贵金属
AU0  - 黄金
AG0  - 白银

# 能源
FU0  - 燃料油
BU0  - 沥青
SC0  - 原油
```

### AKShare函数

```python
# 期货价格
ak.futures_main_sina(symbol="RB0")

# 仓单库存
ak.get_shfe_warehouse()
ak.get_dce_warehouse()
ak.get_czce_warehouse()

# 宏观数据
ak.macro_china_pmi()
ak.macro_china_steel_production()
ak.macro_china_industrial_production()
ak.macro_china_fixed_asset_investment()
```

---

## 📈 数据类别说明

### price（价格）

- 期货价格（实时）
- 现货价格（日度）
- 价格指数

### inventory（库存）

- 交易所库存（日度）
- 社会库存（周度）
- 保税区库存（周度）

### production（产量）

- 钢铁产量（月度）
- 有色金属产量（月度）

### macro（宏观）

- PMI指数（月度）
- GDP（季度）
- 固定资产投资（月度）
- 工业增加值（月度）

---

## ⚙️ 全局配置

```yaml
global:
  # 请求配置
  request:
    timeout: 30
    retry: 3
    retry_interval: 5

  # 缓存配置
  cache:
    enabled: true
    ttl: 3600

  # 并发配置
  concurrency:
    max_workers: 5
```

---

## 🐛 故障排查

### 问题1：AKShare函数找不到

**解决**：
1. 检查AKShare版本：`pip show akshare`
2. 更新到最新版：`pip install --upgrade akshare`
3. 查看AKShare文档确认函数名：https://akshare.akfamily.xyz/

### 问题2：数据获取失败

**可能原因**：
- 网络问题：检查网络连接
- 接口更新：AKShare接口可能变更
- 数据源维护：数据源网站可能临时维护

**解决**：
```bash
# 测试单个数据源
python -c "import akshare as ak; print(ak.futures_main_sina(symbol='RB0'))"
```

### 问题3：字段映射错误

如果默认字段映射不正确，手动指定：

```yaml
field_mapping:
  date: "日期"      # 日期字段名
  value: "收盘价"   # 数值字段名
  close: "收盘价"   # 或使用close
```

---

## 📚 相关文档

- `数据源获取方案.md` - 完整技术方案
- `数据源快速启动指南.md` - 快速上手
- `全球矿产资源清单.md` - 可监控的所有矿产
- `test_akshare_demo.py` - AKShare演示脚本
- `test_data_manager.py` - 数据源管理器测试

---

**更新日期**: 2025-02-11
