# TrendRadar 方法论驱动升级 - 实施路线图

## 📋 目标

将TrendRadar从"新闻监控工具"升级为"行业深度分析系统"，满足知识沉淀方法论的要求。

---

## 🎯 核心能力对比

### 当前能力（v1.0）
- ✅ RSS新闻监控
- ✅ 基础数据采集（价格、库存、产量）
- ✅ AI摘要分析
- ✅ 多渠道通知

### 目标能力（v2.0 - 方法论驱动）
- ✅ 新闻监控（保留）
- 🆕 **上下游关联分析**（产业链追溯）
- 🆕 **成本结构拆解**（多少电？多少料？）
- 🆕 **阶段性认知构建**（宏观→中观→微观）
- 🆕 **数据驱动Prompt**（每个结论有数据支撑）
- 🆕 **产地溯源能力**（了解矿山、冶炼厂分布）

---

## 📅 实施计划（分4个阶段,12周）

### 🔹 Phase 1: Prompt体系构建（Week 1-2）

**目标**：建立完整的方法论驱动Prompt库

#### 任务清单

- [x] 创建 `prompts_methodology.yaml`（已完成✅）
  - [x] Stage1: 宏观认知Prompt
  - [x] Stage2: 公司研究Prompt
  - [x] Stage3: 微观跟踪Prompt
  - [x] Special: 成本拆解Prompt

- [ ] 扩展行业覆盖
  ```bash
  # 基于电解铝模板,复制到其他行业
  cp prompts_methodology.yaml prompts_steel.yaml    # 钢铁
  cp prompts_methodology.yaml prompts_copper.yaml   # 铜
  # 修改行业特定参数（成本项、产业链结构等）
  ```

- [ ] 创建Prompt管理模块
  ```python
  # trendradar/ai/prompt_manager.py
  class PromptManager:
      def __init__(self, config_dir="prompts/"):
          self.prompts = self._load_all_prompts()

      def get_prompt(self, industry, stage):
          """获取指定行业的指定阶段Prompt"""
          pass

      def render_prompt(self, template, data, news):
          """渲染Prompt模板（填充数据和新闻）"""
          pass
  ```

**交付物**：
- `prompts_methodology.yaml`（通用模板）✅
- `prompts_aluminum.yaml`（电解铝专用）
- `prompts_steel.yaml`（钢铁专用）
- `prompts_copper.yaml`（铜专用）
- `trendradar/ai/prompt_manager.py`

---

### 🔹 Phase 2: 数据源扩展（Week 3-5）

**目标**：补充缺失的数据维度，特别是**上下游关联数据**和**成本数据**

#### 2.1 扩展AKShare数据源（Week 3）

当前已有：价格、库存、产量、宏观

需要新增：

```yaml
# config/data_sources.yaml

data_sources:
  # ───────────────────────────────────────────────────────
  # 上游：原料数据
  # ───────────────────────────────────────────────────────

  # 铝土矿进口
  bauxite_import:
    name: "铝土矿进口量"
    type: "akshare"
    enabled: true
    function: "import_export_commodity"  # 需确认函数名
    params:
      commodity: "铝土矿"
      trade_type: "进口"
    data_category: "import"
    product: "bauxite"
    upstream_of: "aluminum"  # 🆕 标注产业链关系

  # 几内亚铝土矿出口（如果AKShare有）
  guinea_bauxite_export:
    name: "几内亚铝土矿出口"
    type: "akshare"
    enabled: true
    function: "country_export_data"
    params:
      country: "几内亚"
      commodity: "铝土矿"
    data_category: "production"
    product: "bauxite"
    region: "Guinea"

  # ───────────────────────────────────────────────────────
  # 下游：终端消费数据
  # ───────────────────────────────────────────────────────

  # 汽车产量（已有，补充新能源车细分）
  new_energy_vehicle_production:
    name: "新能源汽车产量"
    type: "akshare"
    enabled: true
    function: "auto_production_detail"
    params:
      category: "新能源"
    data_category: "downstream"
    product: "new_energy_vehicle"
    consume_product: "aluminum"  # 🆕 标注消费的产品

  # 空调产量（家电用铝）
  air_conditioner_production:
    name: "空调产量"
    type: "akshare"
    enabled: true
    function: "home_appliance_production"
    params:
      product: "空调"
    data_category: "downstream"
    product: "air_conditioner"
    consume_product: "aluminum"

  # 电缆产量（电力用铝）
  cable_production:
    name: "电缆产量"
    type: "akshare"
    enabled: true
    function: "cable_production"
    params: {}
    data_category: "downstream"
    product: "cable"
    consume_product: "aluminum"

  # ───────────────────────────────────────────────────────
  # 成本数据（关键！）
  # ───────────────────────────────────────────────────────

  # 电价（分地区）
  electricity_price_regional:
    name: "各省工业电价"
    type: "akshare"
    enabled: true
    function: "energy_price_elec"  # 需确认
    params: {}
    data_category: "cost"
    data_type: "electricity_price"

  # 天然气价格（钢铁行业用）
  natural_gas_price:
    name: "天然气价格"
    type: "akshare"
    enabled: true
    function: "energy_price_gas"
    params: {}
    data_category: "cost"
    data_type: "energy"
```

**任务清单**：

- [ ] 调研AKShare可用函数（`dir(akshare)` 查看）
- [ ] 测试并配置20个新数据源：
  - [ ] 5个上游数据源（铝土矿、氧化铝、铁矿石、焦煤、焦炭）
  - [ ] 8个下游数据源（汽车、家电、建筑、电力等）
  - [ ] 5个成本数据源（电价、天然气、运费等）
  - [ ] 2个国际数据源（LME、COMEX等）

- [ ] 更新 `DataSourceBase` 添加产业链关系标注
  ```python
  @dataclass
  class DataPoint:
      # ... 原有字段 ...
      upstream_of: str = ""   # 🆕 这是哪个产品的上游
      downstream_of: str = "" # 🆕 这是哪个产品的下游
  ```

#### 2.2 开发产业链关联分析模块（Week 4）

```python
# trendradar/analyzer/supply_chain.py

class SupplyChainAnalyzer:
    """产业链关联分析器"""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.chain_config = self._load_chain_config()

    def get_upstream_data(self, product: str) -> Dict:
        """
        获取指定产品的上游数据

        示例：
        product="aluminum" →
        {
            "bauxite_import": [...],  # 铝土矿进口
            "alumina_price": [...],   # 氧化铝价格
            "electricity_price": [...] # 电价
        }
        """
        pass

    def get_downstream_data(self, product: str) -> Dict:
        """
        获取指定产品的下游数据

        示例：
        product="aluminum" →
        {
            "auto_production": [...],      # 汽车产量
            "air_conditioner": [...],      # 空调产量
            "construction_starts": [...]   # 建筑开工
        }
        """
        pass

    def calculate_price_transmission(
        self,
        upstream_product: str,
        downstream_product: str,
        price_change_pct: float
    ) -> float:
        """
        计算价格传导

        示例：
        calculate_price_transmission("bauxite", "aluminum", 10)
        → 返回：1.2（铝土矿涨10% → 电解铝涨1.2%）
        """
        pass

    def generate_chain_report(self, product: str) -> str:
        """生成产业链分析报告"""
        pass
```

配置文件：`config/supply_chain.yaml`

```yaml
# 产业链配置
supply_chains:
  aluminum:
    name: "电解铝产业链"

    upstream:
      - product: "bauxite"
        name: "铝土矿"
        ratio: 2.0  # 生产1吨氧化铝需要2吨铝土矿
        cost_share: 12%  # 占电解铝成本12%

      - product: "alumina"
        name: "氧化铝"
        ratio: 1.93  # 生产1吨电解铝需要1.93吨氧化铝
        cost_share: 36.6%

      - product: "electricity"
        name: "电力"
        ratio: 13500  # 单位：度
        cost_share: 37.4%

      - product: "anode"
        name: "预焙阳极"
        ratio: 0.55
        cost_share: 8.3%

    downstream:
      - product: "construction"
        name: "建筑"
        consumption_share: 32%

      - product: "transportation"
        name: "交通（汽车）"
        consumption_share: 28%
        growth_driver: "新能源车渗透率"

      - product: "electrical"
        name: "电力"
        consumption_share: 15%

      - product: "packaging"
        name: "包装"
        consumption_share: 10%

    # 价格传导系数
    price_transmission:
      - from: "bauxite"
        to: "alumina"
        coefficient: 0.33  # 铝土矿涨10% → 氧化铝涨3.3%

      - from: "alumina"
        to: "aluminum"
        coefficient: 0.37  # 氧化铝涨10% → 电解铝涨3.7%

      - from: "electricity"
        to: "aluminum"
        coefficient: 0.37  # 电价涨10% → 电解铝成本涨3.7%
```

**任务清单**：

- [ ] 创建 `supply_chain.yaml` 配置（铝、铜、钢3个行业）
- [ ] 实现 `SupplyChainAnalyzer` 类
- [ ] 单元测试：验证价格传导计算正确性

#### 2.3 开发产地溯源模块（Week 5 - 可选）

```python
# trendradar/analyzer/origin_tracker.py

class OriginTracker:
    """产地溯源分析器"""

    def __init__(self):
        self.origins_db = self._load_origins_database()

    def get_major_origins(self, product: str) -> List[Dict]:
        """
        获取主要产地

        返回：
        [
            {"country": "几内亚", "share": 45%, "reserves": "7.4亿吨"},
            {"country": "澳大利亚", "share": 30%, "reserves": "6.2亿吨"},
            ...
        ]
        """
        pass

    def get_mine_locations(self, product: str, country: str) -> List[Dict]:
        """获取矿山位置（如有）"""
        pass

    def get_smelter_locations(self, product: str) -> List[Dict]:
        """获取冶炼厂位置"""
        pass
```

数据源：
- 静态数据：`data/origins/bauxite.json`（铝土矿产地）
- API数据：USGS（美国地质调查局）、BGS（英国地质调查局）

**任务清单**：

- [ ] 收集主要金属的产地数据（手动整理）
- [ ] 创建产地数据库（JSON格式）
- [ ] 实现 `OriginTracker` 类
- [ ] 集成到Prompt（在Stage1中自动引用产地数据）

**交付物**：
- 扩展的 `data_sources.yaml`（+20个数据源）
- `trendradar/analyzer/supply_chain.py`
- `config/supply_chain.yaml`
- `trendradar/analyzer/origin_tracker.py`（可选）
- `data/origins/*.json`（产地数据库）

---

### 🔹 Phase 3: AI分析引擎升级（Week 6-8）

**目标**：集成Prompt体系，实现阶段性分析

#### 3.1 扩展AI分析器（Week 6）

```python
# trendradar/ai/methodology_analyzer.py

from .prompt_manager import PromptManager
from ..analyzer.supply_chain import SupplyChainAnalyzer
from ..data.source_manager import DataSourceManager

class MethodologyAnalyzer:
    """基于方法论的AI分析器"""

    def __init__(self, config):
        self.ai_client = AIClient(config)
        self.prompt_manager = PromptManager()
        self.data_manager = DataSourceManager(config["data_sources_path"])
        self.supply_chain = SupplyChainAnalyzer(self.data_manager)

    def analyze_stage1(
        self,
        industry: str,
        news_items: List,
        date_range: tuple = None
    ) -> str:
        """
        阶段1分析：宏观认知

        返回：Markdown格式的分析报告
        """
        # 1. 获取Prompt模板
        prompt_template = self.prompt_manager.get_prompt(
            industry=industry,
            stage="stage1_industry_overview"
        )

        # 2. 获取所需数据
        required_categories = prompt_template.get("required_data", [])
        data = self._fetch_required_data(industry, required_categories, date_range)

        # 3. 构建数据输入部分
        data_section = self._format_data_section(data)

        # 4. 构建新闻输入部分
        news_section = self._format_news_section(news_items)

        # 5. 渲染完整Prompt
        prompt = self.prompt_manager.render_prompt(
            template=prompt_template["template"],
            data_section=data_section,
            news_section=news_section,
            industry=industry
        )

        # 6. AI分析
        analysis = self.ai_client.analyze(prompt)

        return analysis

    def analyze_stage2(
        self,
        industry: str,
        company: str,
        news_items: List
    ) -> str:
        """阶段2分析：公司研究"""
        # 类似Stage1，但获取公司级别数据
        pass

    def analyze_stage3(
        self,
        industry: str,
        recent_days: int = 7
    ) -> str:
        """阶段3分析：微观动态跟踪"""
        # 重点识别异常变化
        pass

    def analyze_cost_breakdown(
        self,
        industry: str,
        product: str
    ) -> str:
        """专项分析：成本拆解"""
        # 详细的成本结构分析
        pass

    def _fetch_required_data(
        self,
        industry: str,
        categories: List[str],
        date_range: tuple
    ) -> Dict:
        """根据Prompt要求获取数据"""
        data = {}

        for category in categories:
            # 获取该类别的所有数据源
            source_ids = self.data_manager.get_sources_by_category(category)

            # 筛选该行业相关的数据源
            industry_sources = [
                sid for sid in source_ids
                if self._is_relevant_to_industry(sid, industry)
            ]

            # 获取数据
            for sid in industry_sources:
                data_points = self.data_manager.fetch_one(sid)
                data[sid] = data_points

        return data

    def _format_data_section(self, data: Dict) -> str:
        """格式化数据为Markdown"""
        sections = []

        # 按类别组织
        by_category = {}
        for sid, points in data.items():
            source = self.data_manager.sources[sid]
            category = source.data_category

            if category not in by_category:
                by_category[category] = []

            by_category[category].append({
                "source": source,
                "data": points
            })

        # 生成Markdown
        for category, sources in by_category.items():
            sections.append(f"### {category.upper()}数据\n")

            for item in sources:
                source = item["source"]
                data_points = item["data"]

                if not data_points:
                    sections.append(f"- **{source.name}**: 数据待补充\n")
                    continue

                # 统计
                latest = data_points[-1] if data_points else None
                avg = sum(dp.value for dp in data_points) / len(data_points)

                sections.append(f"""
- **{source.name}**: {latest.value:.2f} {latest.unit}
  - 时间：{latest.date.strftime("%Y-%m-%d")}
  - 历史均值：{avg:.2f}
  - 数据点数：{len(data_points)}
""")

        return "\n".join(sections)

    def _format_news_section(self, news_items: List) -> str:
        """格式化新闻为Markdown"""
        lines = []
        for i, news in enumerate(news_items, 1):
            lines.append(f"{i}. 【{news.platform_name}】{news.title}")
        return "\n".join(lines)

    def _is_relevant_to_industry(self, source_id: str, industry: str) -> bool:
        """判断数据源是否与行业相关"""
        source = self.data_manager.sources.get(source_id)
        if not source:
            return False

        # 直接匹配
        if source.product.lower() == industry.lower():
            return True

        # 通过产业链关系匹配
        chain_config = self.supply_chain.chain_config.get(industry, {})
        upstream_products = [u["product"] for u in chain_config.get("upstream", [])]
        downstream_products = [d["product"] for d in chain_config.get("downstream", [])]

        if source.product in upstream_products or source.product in downstream_products:
            return True

        return False
```

**任务清单**：

- [ ] 实现 `MethodologyAnalyzer` 类
- [ ] 实现数据获取和格式化逻辑
- [ ] 实现产业链关联数据自动引入
- [ ] 单元测试

#### 3.2 集成到主流程（Week 7）

修改 `trendradar/core/analyzer.py`:

```python
from trendradar.ai.methodology_analyzer import MethodologyAnalyzer

class Analyzer:
    def __init__(self, config):
        # ... 原有代码 ...
        self.methodology_analyzer = MethodologyAnalyzer(config)

    def analyze_with_methodology(
        self,
        industry: str,
        stage: str,  # "stage1" / "stage2" / "stage3" / "cost_breakdown"
        news_items: List,
        **kwargs
    ):
        """使用方法论进行分析"""

        if stage == "stage1":
            return self.methodology_analyzer.analyze_stage1(
                industry, news_items
            )
        elif stage == "stage2":
            company = kwargs.get("company")
            return self.methodology_analyzer.analyze_stage2(
                industry, company, news_items
            )
        elif stage == "stage3":
            recent_days = kwargs.get("recent_days", 7)
            return self.methodology_analyzer.analyze_stage3(
                industry, recent_days
            )
        elif stage == "cost_breakdown":
            product = kwargs.get("product", industry)
            return self.methodology_analyzer.analyze_cost_breakdown(
                industry, product
            )
        else:
            raise ValueError(f"Unknown stage: {stage}")
```

#### 3.3 CLI命令支持（Week 8）

```python
# trendradar/__main__.py

@click.command()
@click.option("--industry", help="行业名称")
@click.option("--stage", type=click.Choice(["stage1", "stage2", "stage3", "cost"]))
@click.option("--company", help="公司名称（仅stage2需要）")
def methodology_analysis(industry, stage, company):
    """方法论驱动的行业分析"""

    # 加载配置
    config = load_config()

    # 创建分析器
    analyzer = Analyzer(config)

    # 获取最近新闻
    news_items = get_recent_news(industry, days=7)

    # 执行分析
    if stage == "stage1":
        report = analyzer.analyze_with_methodology(
            industry, "stage1", news_items
        )
    elif stage == "stage2":
        if not company:
            click.echo("Error: --company required for stage2")
            return
        report = analyzer.analyze_with_methodology(
            industry, "stage2", news_items, company=company
        )
    elif stage == "stage3":
        report = analyzer.analyze_with_methodology(
            industry, "stage3", news_items
        )
    elif stage == "cost":
        report = analyzer.analyze_with_methodology(
            industry, "cost_breakdown", news_items
        )

    # 输出报告
    click.echo(report)

    # 保存报告
    save_report(report, f"{industry}_{stage}_{datetime.now().strftime('%Y%m%d')}.md")
```

**使用示例**：

```bash
# 阶段1：快速了解电解铝行业
python -m trendradar methodology-analysis --industry aluminum --stage stage1

# 阶段2：深入研究中国宏桥
python -m trendradar methodology-analysis --industry aluminum --stage stage2 --company "中国宏桥"

# 阶段3：微观跟踪（每周执行）
python -m trendradar methodology-analysis --industry aluminum --stage stage3

# 专项：成本拆解
python -m trendradar methodology-analysis --industry aluminum --stage cost
```

**交付物**：
- `trendradar/ai/methodology_analyzer.py`
- 集成到 `trendradar/core/analyzer.py`
- CLI命令支持
- 单元测试和集成测试

---

### 🔹 Phase 4: 完善与优化（Week 9-12）

#### 4.1 数据验证和质量保证（Week 9）

问题：Prompt要求"每个结论有数据支撑"，但数据可能缺失

解决方案：

```python
# trendradar/utils/data_validator.py

class DataValidator:
    """数据完整性验证器"""

    def validate_stage1_data(self, industry: str) -> Dict:
        """
        验证Stage1所需数据是否完整

        返回：
        {
            "complete": True/False,
            "missing": ["成本结构数据", "下游消费数据"],
            "coverage": 0.75  # 数据覆盖率
        }
        """
        required = [
            "production",  # 产量
            "price",       # 价格
            "inventory",   # 库存
            "consumption", # 消费
            "macro"        # 宏观
        ]

        available = self._check_available_categories(industry)

        missing = [r for r in required if r not in available]

        return {
            "complete": len(missing) == 0,
            "missing": missing,
            "coverage": len(available) / len(required)
        }

    def suggest_data_sources(self, missing_category: str) -> List[str]:
        """建议补充的数据源"""
        suggestions = {
            "cost_structure": [
                "查阅公司年报（如：中国宏桥、中国铝业）",
                "阅读券商研报（如：中信证券、国泰君安）",
                "Wind数据库（付费）",
                "手动整理行业数据"
            ],
            "consumption": [
                "配置下游行业数据源（汽车、家电、建筑）",
                "中国有色金属工业协会",
                "行业年鉴"
            ],
            # ...
        }
        return suggestions.get(missing_category, [])
```

在AI分析前调用验证：

```python
# 在analyze_stage1()开始时
validator = DataValidator()
validation = validator.validate_stage1_data(industry)

if not validation["complete"]:
    warnings.append(f"""
⚠️  数据不完整（覆盖率：{validation['coverage']*100:.0f}%）

缺失数据：
{chr(10).join(f"- {m}" for m in validation['missing'])}

建议：
{chr(10).join(validator.suggest_data_sources(validation['missing'][0]))}
    """)
```

#### 4.2 报告模板和格式化（Week 10）

创建专业的报告模板：

```python
# trendradar/report/methodology_report.py

class MethodologyReport:
    """方法论驱动的报告生成器"""

    def __init__(self):
        self.template_dir = "templates/reports/"

    def generate_stage1_report(
        self,
        industry: str,
        analysis: str,
        data_summary: Dict,
        metadata: Dict
    ) -> str:
        """
        生成Stage1报告

        模板：
        - 封面页（行业名称、分析日期、分析师）
        - 执行摘要（3个核心认知）
        - 详细分析（6大章节）
        - 数据附录（速查表）
        - 数据来源说明
        """
        template = self._load_template("stage1_template.md")

        return template.format(
            industry=industry,
            date=metadata.get("date"),
            analyst="Claude Sonnet 4.5 + TrendRadar",
            analysis=analysis,
            data_coverage=data_summary.get("coverage"),
            # ...
        )

    def export_to_pdf(self, markdown_report: str, output_path: str):
        """导出为PDF（使用pandoc或weasyprint）"""
        pass
```

模板示例：`templates/reports/stage1_template.md`

```markdown
# {industry}行业宏观认知分析报告

**分析日期**: {date}
**分析师**: {analyst}
**数据覆盖率**: {data_coverage}%

---

## 执行摘要

{executive_summary}

---

## 详细分析

{analysis}

---

## 附录：数据来源

{data_sources_table}

---

**报告生成**: TrendRadar v2.0 - Methodology-Driven
```

#### 4.3 定时任务和自动化（Week 11）

配置定时任务：

```yaml
# config/scheduler.yaml

jobs:
  # ... 原有的RSS监控任务 ...

  # 🆕 阶段3微观跟踪（每周一）
  stage3_tracking:
    name: "微观动态跟踪"
    enabled: true
    schedule: "0 9 * * 1"  # 每周一9:00
    task: "methodology_analysis"
    params:
      industry: "aluminum"
      stage: "stage3"
      notification_channels: ["feishu", "telegram"]

  # 🆕 月度产业链分析（每月1号）
  monthly_supply_chain:
    name: "产业链月报"
    enabled: true
    schedule: "0 10 1 * *"  # 每月1号10:00
    task: "supply_chain_report"
    params:
      industry: "aluminum"
      notification_channels: ["feishu"]
```

#### 4.4 文档和示例（Week 12）

- [ ] 编写用户手册（`docs/methodology_guide.md`）
- [ ] 创建视频教程（录屏演示）
- [ ] 补充API文档
- [ ] 创建更多行业示例：
  - [ ] 钢铁行业（`examples/steel_analysis.md`）
  - [ ] 铜行业（`examples/copper_analysis.md`）
  - [ ] 锂行业（`examples/lithium_analysis.md`）

**交付物**：
- `trendradar/utils/data_validator.py`
- `trendradar/report/methodology_report.py`
- `templates/reports/*.md`
- 定时任务配置
- 完整文档

---

## 📊 进度跟踪表

| 阶段 | 任务 | 优先级 | 预计工时 | 状态 |
|------|------|--------|---------|------|
| Phase 1 | 创建Prompt模板 | P0 | 10h | ✅ 完成 |
| Phase 1 | Prompt管理模块 | P0 | 8h | ⏳ 待开始 |
| Phase 2 | 扩展数据源配置 | P0 | 16h | ⏳ 待开始 |
| Phase 2 | 产业链分析模块 | P0 | 20h | ⏳ 待开始 |
| Phase 2 | 产地溯源模块 | P1 | 12h | ⏳ 待开始 |
| Phase 3 | AI分析器升级 | P0 | 24h | ⏳ 待开始 |
| Phase 3 | CLI命令集成 | P0 | 8h | ⏳ 待开始 |
| Phase 4 | 数据验证 | P1 | 10h | ⏳ 待开始 |
| Phase 4 | 报告模板 | P1 | 8h | ⏳ 待开始 |
| Phase 4 | 定时任务 | P1 | 6h | ⏳ 待开始 |
| Phase 4 | 文档编写 | P2 | 12h | ⏳ 待开始 |

**总计**: 134小时（约3-4周全职，或12周兼职）

---

## 🚀 快速启动（MVP版本）

如果时间紧张，可以先实现MVP（最小可行产品）：

### Week 1-2: 核心功能
- ✅ Prompt模板（已完成）
- 基础Prompt管理（简化版）
- 手动运行（不需要定时任务）

### Week 3-4: 数据集成
- 补充10个关键数据源（只做铝行业）
- 简单的产业链关联（手动配置）

### Week 5-6: AI分析
- 实现 `analyze_stage1()` 和 `analyze_cost_breakdown()`
- 跳过Stage2和Stage3（后续补充）

### Week 7: 测试和优化
- 运行完整的铝行业分析
- 优化Prompt
- 撰写基础文档

**MVP交付物**：
- 能用1个命令生成完整的铝行业Stage1分析报告
- 能回答"多少电？多少铝？多少成本？"
- 报告包含数据支撑和产业链分析

---

## 📌 下一步行动

请选择启动方式：

### 选项A：完整实施（12周）
```bash
# 按照4个Phase逐步实施
cd /Users/wangxinlong/Code/TrendRadar
git checkout -b feature/methodology-driven

# 开始Phase 1
mkdir -p trendradar/ai/prompts
mkdir -p prompts/
# ...
```

### 选项B：MVP快速验证（6周）
```bash
# 只实现核心功能，快速验证效果
cd /Users/wangxinlong/Code/TrendRadar
git checkout -b feature/methodology-mvp

# 聚焦铝行业，实现Stage1和成本拆解
# ...
```

### 选项C：渐进式改进（持续）
```bash
# 每周完成1个小模块，持续迭代
# 第1周：Prompt管理
# 第2周：补充5个数据源
# 第3周：实现Stage1分析
# ...
```

---

**建议**：先做MVP（选项B），验证效果后再完整实施。

---

## 💡 关键成功因素

1. **数据质量**：数据完整性决定分析质量
   - 优先补充高价值数据（成本、上下游）
   - 手动整理也可以（不一定需要API）

2. **Prompt优化**：持续优化Prompt模板
   - 根据AI输出质量调整
   - 收集用户反馈

3. **产业链知识**：需要行业专家输入
   - 成本结构
   - 价格传导机制
   - 产地信息

4. **渐进式交付**：不要追求一次性完美
   - 先做1个行业（铝）
   - 验证后复制到其他行业（钢、铜）

---

**准备好开始了吗？请告诉我选择哪个方案！** 🚀
