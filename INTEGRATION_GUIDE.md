# TrendRadar 双引擎集成指南

**版本**: v2.1.0
**创建时间**: 2026-03-04
**状态**: ✅ 可用

---

## 📊 架构总览

TrendRadar v2.1.0 采用双引擎架构，根据分析场景智能选择：

```
┌──────────────────────────────────────────────────────┐
│               TrendRadar v2.1.0                       │
│                  双引擎架构                           │
└──────────────────────────────────────────────────────┘

              ┌────────────────┐
              │ 智能路由器      │
              │ (Router)       │
              └────────┬───────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
    ┌────▼────┐                ┌────▼────┐
    │ 引擎A    │                │ 引擎B    │
    │ 实时监控 │                │ 深度分析 │
    │ (原版)   │                │ (方法论)  │
    └────┬────┘                └────┬────┘
         │                           │
         └─────────────┬─────────────┘
                       │
              ┌────────▼───────┐
              │  统一输出       │
              └────────────────┘
```

---

## 🎯 使用场景

### 场景1：突发热点监控

**需求**：快速了解当日热点、舆情走向、异常信号

**推荐模式**：实时模式（引擎A）

**输出**：
- 5段式分析（~600字）
- 分析时间：<5分钟
- 特点：信号检测、跨平台对比、舆情分析

**示例代码**：
```python
from trendradar.ai.intelligent_router import IntelligentRouter, AnalysisScenario

router = IntelligentRouter(
    original_analyzer=original_analyzer,
    methodology_analyzer=None  # 不需要方法论分析器
)

result = router.route(
    scenario=AnalysisScenario.BREAKING_NEWS,
    stats=hot_news_stats,
    rss_stats=rss_stats
)

print(result["result"].core_trends)
print(result["result"].signals)
```

---

### 场景2：行业深度研究

**需求**：系统性了解某行业（产业链、成本、供需）

**推荐模式**：方法论模式（引擎B）

**输出**：
- 6章节报告（1500-2000字）
- 分析时间：30-60分钟
- 特点：产业链分析、成本拆解、数据驱动

**示例代码**：
```python
router = IntelligentRouter(
    original_analyzer=None,  # 不需要原版分析器
    methodology_analyzer=methodology_analyzer
)

result = router.route(
    scenario=AnalysisScenario.INDUSTRY_RESEARCH,
    industry="aluminum",
    stage="stage1",
    data={...},  # 行业数据
    news=[...]   # 新闻列表
)

print(result["result"]["full_report"])
```

---

### 场景3：定期行业报告

**需求**：周报/月报，既要热点又要深度

**推荐模式**：混合模式（引擎A + 引擎B）

**输出**：
- 实时热点摘要 + 深度行业分析（2000-3000字）
- 分析时间：30-60分钟
- 特点：全面覆盖

**示例代码**：
```python
router = IntelligentRouter(
    original_analyzer=original_analyzer,
    methodology_analyzer=methodology_analyzer
)

result = router.route(
    scenario=AnalysisScenario.PERIODIC_REPORT,
    # 原版分析参数
    stats=hot_news_stats,
    rss_stats=rss_stats,
    # 方法论分析参数
    industry="aluminum",
    stage="stage1",
    data={...}
)

# 获取合并报告
print(result["merged_report"])
```

---

## 📁 文件清单

### 核心文件

```
trendradar/ai/
├── analyzer.py                    # 原版分析器（保留）
├── client.py                      # AI客户端（LiteLLM）
├── prompt_manager.py              # Prompt管理器（新增）
├── data_formatter.py              # 数据格式化（新增）
├── intelligent_router.py          # 智能路由器（新增）
└── methodology_analyzer.py        # 方法论分析器（待实现）

config/
├── ai_analysis_prompt.txt         # 原版Prompt
├── ai_analysis_prompt_enhanced.txt# 增强版Prompt（新增）
└── prompts_methodology.yaml       # 方法论Prompt模板（新增）
```

---

## 🚀 快速开始

### 步骤1：保持原版功能不变

原版TrendRadar的所有功能仍然可用，不受影响：

```python
from trendradar.ai.analyzer import AIAnalyzer

# 原版分析（与之前完全一样）
analyzer = AIAnalyzer(ai_config, analysis_config, get_time_func)
result = analyzer.analyze(stats, rss_stats, "default", "综合", platforms, keywords)

# 输出5段式分析
print(result.core_trends)
print(result.signals)
```

---

### 步骤2：使用增强版Prompt（可选）

如果想让原版分析器也有更多数据支撑，切换到增强版Prompt：

**修改配置文件** `config/config.yaml`：

```yaml
ai_analysis:
  # 原来
  prompt_file: config/ai_analysis_prompt.txt

  # 修改为
  prompt_file: config/ai_analysis_prompt_enhanced.txt
```

**效果对比**：

| 版本 | 输出示例 |
|------|---------|
| 原版 | "铝价大幅上涨，供需偏紧" |
| 增强版 | "铝价上涨1.5%至15,200元/吨，供需缺口1.9%（需求+5.1% > 供给+3.2%），库存85万吨（35分位）" |

---

### 步骤3：启用方法论分析（新功能）

#### 3.1 安装依赖

```bash
pip3 install pyyaml --break-system-packages
```

#### 3.2 准备行业数据

创建数据获取函数（临时方案，使用模拟数据）：

```python
def get_industry_data(industry: str) -> Dict:
    """获取行业结构化数据"""
    if industry == "aluminum":
        return {
            "price": [
                "沪铝期货均价：15,200元/吨（最近1个月）",
                "氧化铝现货价：2,400元/吨",
                "预焙阳极价格：1,900元/吨"
            ],
            "production": [
                "电解铝月产量：340万吨（2025年2月）",
                "同比增长：+3.2%",
                "开工率：86.5%"
            ],
            "inventory": [
                "交易所库存：85万吨",
                "环比：-7.6%",
                "历史分位：35分位（偏低）"
            ],
            # ... 更多数据
        }
    return {}
```

#### 3.3 运行方法论分析

```bash
# 命令行方式
python3 demo_methodology.py --industry aluminum --stage stage1

# 查看生成的Prompt
cat output/aluminum_stage1_prompt.txt

# 复制到Claude.ai测试
cat output/aluminum_stage1_prompt.txt | pbcopy
```

#### 3.4 集成到代码

```python
from trendradar.ai.prompt_manager import PromptManager
from trendradar.ai.data_formatter import DataFormatter

# 加载Prompt模板
manager = PromptManager("prompts_methodology.yaml")

# 格式化数据
formatter = DataFormatter()
data_section = formatter.format_data_section(
    industry="aluminum",
    data=get_industry_data("aluminum")
)
news_section = formatter.format_news_section(news_list)

# 渲染Prompt
prompt = manager.render_prompt(
    stage="stage1",
    industry="aluminum",
    data_section=data_section,
    news_section=news_section
)

# 调用AI（使用现有的AIClient）
from trendradar.ai.client import AIClient
client = AIClient(ai_config)
response = client.chat([{"role": "user", "content": prompt}])

print(response)  # 1500-2000字深度分析报告
```

---

### 步骤4：使用智能路由器（推荐）

智能路由器自动选择合适的分析引擎：

```python
from trendradar.ai.intelligent_router import IntelligentRouter, AnalysisScenario

# 初始化路由器
router = IntelligentRouter(
    original_analyzer=original_analyzer,
    methodology_analyzer=methodology_analyzer  # 暂未实现，先传None
)

# 场景1：突发热点（自动选择实时模式）
result1 = router.route(
    scenario=AnalysisScenario.BREAKING_NEWS,
    stats=stats,
    rss_stats=rss_stats
)

# 场景2：行业研究（自动选择方法论模式）
result2 = router.route(
    scenario=AnalysisScenario.INDUSTRY_RESEARCH,
    industry="aluminum",
    stage="stage1",
    data=get_industry_data("aluminum")
)

# 场景3：手动指定模式
from trendradar.ai.intelligent_router import AnalysisMode

result3 = router.route(
    mode=AnalysisMode.MIXED,  # 混合模式
    stats=stats,
    rss_stats=rss_stats,
    industry="aluminum",
    data=get_industry_data("aluminum")
)
```

---

## 🔧 配置说明

### 原版分析器配置（不变）

`config/config.yaml` 中的 `ai_analysis` 部分保持不变：

```yaml
ai_analysis:
  enabled: true
  language: "zh-CN"
  max_news_for_analysis: 50
  include_rss: true
  prompt_file: config/ai_analysis_prompt.txt  # 或 ai_analysis_prompt_enhanced.txt
```

### 方法论分析器配置（新增）

在 `config/config.yaml` 中新增：

```yaml
methodology_analysis:
  enabled: true
  prompt_file: prompts_methodology.yaml
  output_dir: output/
  stages:
    - stage1  # 宏观认知
    - stage2  # 公司研究
    - stage3  # 微观跟踪
    - cost    # 成本拆解
  industries:
    - aluminum
    - steel
    - copper
```

---

## 📊 输出对比

### 同一事件的输出对比

**事件**：沪铝期货涨1.5%

#### 原版输出（~600字）

```
# 核心热点态势
沪铝期货今日涨1.5%突破15,500元关口，成为金属板块领涨品种。
多平台热榜显示铝价上涨引发关注，微博讨论量+120%...

# 信号检测
异常信号：云南限电消息在抖音平台热度暴涨（排名3→1），但微博
仅排名15，存在信息差。
弱信号：氧化铝价格下跌，但铝价上涨...
```

**特点**：
- ✅ 快速（<5分钟）
- ✅ 跨平台对比
- ❌ 缺数据支撑

---

#### 增强版输出（~600字）

```
# 核心热点态势
沪铝期货上涨1.5%至15,200元/吨，月产量340万吨（+3.2%），
消费350万吨（+5.1%），供需缺口10万吨/月（1.9%）。
库存85万吨（35分位，环比-7.6%），相当于24.3天消费...

# 信号检测
异常信号：云南限电影响产量约15万吨/月（占全国4.4%），
导致抖音热度暴涨（排名3→1），但微博仅排名15。
弱信号：氧化铝价格下跌3%至2,400元/吨，吨铝利润扩张至1,554元...
```

**特点**：
- ✅ 快速（<5分钟）
- ✅ 跨平台对比
- ✅ **数据支撑充分**

---

#### 方法论版本输出（~1800字）

```
# 电解铝行业宏观认知分析

## 执行摘要：3个核心认知
1. 电解铝=电力密集型：电力占成本37%，新疆电价优势20%
2. 供给受限+需求分化：产能天花板4,500万吨，建筑-2%，新能源车+25%
3. 当前供需偏紧：库存35分位（24天消费），需求+5.1% > 供给+3.2%

## 1. 行业盈利模式
电解铝靠"加工费"赚钱，当前利润1,554元/吨...

## 2. 产业链结构
铝土矿（几内亚45%）→ 氧化铝（1.93吨） → 电解铝（13,500度电）...

## 3. 主要玩家
中国宏桥产能680万吨/年（15.1%市占率），中国铝业560万吨...

## 4. 上下游关系
上游（铝土矿）有定价权，价格传导：矿价+10% → 氧化铝+7% → 铝价+2.5%...

## 5. 法律监管
产能天花板4,500万吨，能耗双控...

## 6. 关键数据速查表
| 指标 | 最新值 | 同比 | 历史均值 |
|------|--------|------|----------|
| 产量 | 340万吨 | +3.2% | 330万吨 |
| 消费 | 350万吨 | +5.1% | 335万吨 |
| 库存 | 85万吨 | -7.6% | 120万吨 |

## 沪铝价格上涨深度分析
直接原因：供需缺口1.9%
库存验证：35分位（24.3天消费）
成本支撑：利润1,554元/吨 > 盈亏平衡1,200元
展望：短期有上行空间，关注库存去化速度...
```

**特点**：
- ✅ 系统性认知（6章节）
- ✅ 数据驱动（20+个数据点）
- ✅ 回答细节问题（13,500度电/吨）
- ✅ 可操作性强（精确点位+风险）
- ❌ 分析时间较长（30-60分钟）

---

## 🎯 实施建议

### 阶段1：立即可做（本周）

1. **使用增强版Prompt**
   ```yaml
   # 修改 config/config.yaml
   ai_analysis:
     prompt_file: config/ai_analysis_prompt_enhanced.txt
   ```

2. **测试效果**
   - 运行原版分析器
   - 对比原版 vs 增强版输出
   - 评估数据支撑是否改善

---

### 阶段2：短期实施（2周）

1. **集成真实数据源**
   ```python
   # 替换模拟数据
   def get_industry_data(industry: str) -> Dict:
       # 使用AKShare获取真实数据
       import akshare as ak

       if industry == "aluminum":
           # 价格数据
           price_df = ak.futures_main_sina(symbol="AL0")

           # 产量数据（从统计局API）
           production = get_production_data("aluminum")

           # 库存数据（从交易所API）
           inventory = get_inventory_data("SHFE", "AL")

           return format_data(price_df, production, inventory)
   ```

2. **实现MethodologyAnalyzer**
   ```python
   # trendradar/ai/methodology_analyzer.py
   class MethodologyAnalyzer:
       def __init__(self, ai_config, prompt_manager):
           self.client = AIClient(ai_config)
           self.prompt_manager = prompt_manager

       def analyze(self, industry, stage, data, news):
           # 格式化数据
           # 渲染Prompt
           # 调用AI
           # 返回结构化结果
           pass
   ```

3. **集成到主流程**
   ```python
   # 在 trendradar/main.py 中
   if config.get("methodology_analysis", {}).get("enabled"):
       methodology_analyzer = MethodologyAnalyzer(...)
       router = IntelligentRouter(original_analyzer, methodology_analyzer)
   ```

---

### 阶段3：完整实施（12周）

参考 `implementation_roadmap.md`：
- Phase 1: Prompt体系 ✅（已完成）
- Phase 2: 数据源扩展（4周）
- Phase 3: AI引擎升级（3周）
- Phase 4: 智能路由优化（2周）
- Phase 5: 测试与优化（3周）

---

## 💡 最佳实践

### 1. 场景选择

| 场景 | 推荐模式 | 原因 |
|------|---------|------|
| 突发热点 | 实时模式 | 速度优先 |
| 行业研究 | 方法论模式 | 深度优先 |
| 定期报告 | 混合模式 | 全面覆盖 |
| 投资决策 | 方法论模式 | 数据驱动 |

### 2. 数据准备

**最小数据集**（方法论分析必需）：
- 价格数据：期货价格、现货价格
- 产量数据：月产量、同比增速
- 库存数据：绝对库存、历史分位
- 消费数据：表观消费、同比增速

**推荐数据集**（更好的分析）：
- 成本数据：上游原料价格、成本占比
- 开工率：产能利用率
- 下游数据：各应用领域占比
- 宏观数据：PMI、固投

### 3. Prompt优化

**原版Prompt优化方向**：
- 增加数据引用要求
- 禁止模糊表达
- 强制量化

**方法论Prompt优化方向**：
- 增加实时性（Stage3微观跟踪）
- 增加跨平台舆情分析
- 优化输出格式

---

## 🐛 故障排查

### 问题1：找不到配置文件

```
FileNotFoundError: prompts_methodology.yaml
```

**解决**：
```bash
# 确认文件存在
ls prompts_methodology.yaml

# 确认在正确目录
pwd
# 应该输出: /Users/wangxinlong/Code/TrendRadar
```

---

### 问题2：模块导入失败

```
ModuleNotFoundError: No module named 'trendradar.ai.intelligent_router'
```

**解决**：
```python
# 确保__init__.py存在
# trendradar/ai/__init__.py

# 或使用绝对导入
import sys
sys.path.append("/Users/wangxinlong/Code/TrendRadar")
from trendradar.ai.intelligent_router import IntelligentRouter
```

---

### 问题3：增强版Prompt无效果

**检查**：
1. 确认配置文件已修改
2. 重启TrendRadar服务
3. 查看日志，确认加载了正确的Prompt文件

---

## 📚 相关文档

- `COMPARISON_ANALYSIS.md` - 原版 vs 方法论对比分析
- `METHODOLOGY_SUMMARY.md` - 方法论完整方案
- `DEMO_VERIFICATION.md` - Demo验证报告
- `implementation_roadmap.md` - 12周实施路线图
- `QUICKSTART.md` - 快速启动指南

---

## 🎉 总结

### 核心优势

1. **向后兼容**：原版功能完全保留，不影响现有用户
2. **灵活扩展**：双引擎架构，可独立使用或组合使用
3. **智能路由**：自动选择最合适的分析模式
4. **数据驱动**：增强版Prompt强制数据支撑
5. **渐进式升级**：可逐步实施，无需一次性完成

### 升级路径

```
当前版本
    ↓
使用增强版Prompt（1天）
    ↓
集成真实数据（2周）
    ↓
实现方法论分析器（2周）
    ↓
启用智能路由器（1周）
    ↓
完整v2.1.0
```

### 下一步

1. **立即**：切换到增强版Prompt，测试效果
2. **本周**：准备行业数据源，规划数据接入
3. **2周后**：实现MethodologyAnalyzer，完成MVP

---

**文档版本**: v1.0
**更新时间**: 2026-03-04
**维护者**: TrendRadar Team
