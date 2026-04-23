# 🚀 TrendRadar 方法论驱动分析 - 快速启动指南

**版本**: MVP Demo v0.1
**状态**: ✅ 可用

---

## 📦 文件清单

```
TrendRadar/
├── prompts_methodology.yaml          # ✅ Prompt模板配置
├── trendradar/ai/
│   ├── prompt_manager.py             # ✅ Prompt管理模块
│   └── data_formatter.py             # ✅ 数据格式化工具
├── demo_methodology.py               # ✅ Demo运行脚本
├── test_prompt_manager.py            # ✅ 测试脚本
├── DEMO_VERIFICATION.md              # ✅ 验证报告
├── METHODOLOGY_SUMMARY.md            # ✅ 方案总结
├── implementation_roadmap.md         # ✅ 实施路线图
├── example_aluminum_analysis.md      # ✅ 电解铝示例
└── output/                           # ✅ 生成的Prompt文件
    ├── aluminum_stage1_prompt.txt
    └── aluminum_cost_prompt.txt
```

---

## ⚡ 快速开始（3步）

### Step 1: 运行Demo

```bash
# 进入项目目录
cd /Users/wangxinlong/Code/TrendRadar

# 运行Stage1分析（宏观认知）
python3 demo_methodology.py --industry aluminum --stage stage1

# 运行成本拆解分析
python3 demo_methodology.py --industry aluminum --stage cost
```

### Step 2: 查看生成的Prompt

```bash
# 查看Stage1 Prompt
cat output/aluminum_stage1_prompt.txt

# 查看成本拆解Prompt
cat output/aluminum_cost_prompt.txt

# 复制到剪贴板（Mac）
cat output/aluminum_stage1_prompt.txt | pbcopy
```

### Step 3: 测试AI效果

1. 打开 [Claude.ai](https://claude.ai) 或 ChatGPT
2. 粘贴生成的Prompt
3. 查看AI生成的分析报告
4. 评估报告质量（字数、结构、数据支撑）

---

## 🎯 Demo演示

### 演示1: 生成行业宏观认知分析

```bash
python3 demo_methodology.py --industry aluminum --stage stage1
```

**输出**：
```
============================================================
🎯 方法论驱动分析 - stage1
============================================================

📋 加载Prompt配置...
✓ 加载成功: 行业宏观认知 - 第一阶段

📊 获取数据...
✓ 数据类别: 5个
✓ 新闻条数: 5条

📝 格式化数据...
✓ 格式化完成

🎨 渲染Prompt模板...
✓ Prompt渲染成功（1703字符）

✓ 完整Prompt已保存到: output/aluminum_stage1_prompt.txt

============================================================
✅ Demo运行成功！
============================================================
```

**生成的Prompt包含**：
- 📊 完整的数据部分（价格、产量、消费、库存、宏观）
- 📰 5条相关新闻
- 🎯 6大分析章节要求
- 📝 明确的输出格式（1500-2000字 + 数据速查表）

---

### 演示2: 生成成本拆解分析

```bash
python3 demo_methodology.py --industry aluminum --stage cost
```

**输出**：
```
✓ 加载成功: 成本结构深度拆解
✓ Prompt已保存到: output/aluminum_cost_prompt.txt
```

**生成的Prompt包含**：
- 🎯 核心问题（多少电？多少铝？多少成本？）
- 📊 物料平衡表要求
- 📈 敏感性分析
- 🗺️ 区域成本对比
- 💰 盈亏平衡分析

---

## 📖 使用示例

### 示例1: 快速了解电解铝行业（5天）

**需求**：我对电解铝行业一无所知，希望5天内能进行10-20分钟专业对话。

**步骤**：
```bash
# 1. 生成Stage1 Prompt
python3 demo_methodology.py --industry aluminum --stage stage1

# 2. 复制Prompt到Claude
cat output/aluminum_stage1_prompt.txt | pbcopy

# 3. Claude生成报告（预计1500-2000字）

# 4. 阅读报告（30分钟）
# 重点：
# - 盈利模式（靠加工费赚钱）
# - 产业链（铝土矿→氧化铝→电解铝→铝材）
# - 成本结构（电力37%、氧化铝37%）
# - 3个核心认知（电解铝=电力密集型、供给受限、需求分化）
```

**效果**：
- ✅ 5天内掌握行业全貌
- ✅ 能进行10-20分钟专业对话
- ✅ 掌握关键数据（产量、价格、库存）

---

### 示例2: 回答细节问题（1小时）

**需求**：电解铝行业到底需要多少电？多少铝？多少成本？

**步骤**：
```bash
# 1. 生成成本拆解Prompt
python3 demo_methodology.py --industry aluminum --stage cost

# 2. Claude生成成本分析报告

# 3. 获得精确答案
```

**答案**（从报告中提取）：
- ⚡ **电力**：13,500度/吨（占成本37.4%）
- 🏭 **氧化铝**：1.93吨/吨（占成本36.6%）
- 📊 **总成本**：11,700-13,000元/吨（取决于电价）
- 💰 **盈亏平衡点**：13,500元/吨

**关键发现**：
- 新疆vs山东：成本差20%（2,300元/吨）
- 电价每降0.1元 → 成本省1,350元/吨
- 90%新增产能都在西北（低电价地区）

---

## 🎨 自定义使用

### 添加新行业

1. 在 `demo_methodology.py` 的 `get_mock_data()` 中添加数据：

```python
def get_mock_data(industry: str):
    if industry == "steel":  # 新增钢铁行业
        return {
            "price": ["螺纹钢期货：3,850元/吨"],
            "production": ["粗钢产量：8,500万吨/月"],
            # ...
        }
```

2. 运行分析：

```bash
python3 demo_methodology.py --industry steel --stage stage1
```

---

### 修改Prompt模板

编辑 `prompts_methodology.yaml`：

```yaml
prompts:
  stage1_industry_overview:
    template: |
      你是一位资深的{industry}行业分析师。

      # 修改这里，调整分析要求
      ## 1. 行业盈利模式（调整占比）
      - 这个行业靠什么赚钱？
      # ...
```

---

## 🔍 故障排查

### 问题1: ModuleNotFoundError: No module named 'yaml'

**解决**：
```bash
pip3 install pyyaml --break-system-packages
```

### 问题2: 找不到配置文件

**检查**：
```bash
ls prompts_methodology.yaml  # 确保文件存在
pwd  # 确认在TrendRadar目录
```

### 问题3: Prompt渲染失败

**检查**：
```bash
# 测试Prompt管理器
python3 test_prompt_manager.py
```

---

## 📊 下一步

### 立即可做

1. **测试实际AI效果**
   ```bash
   # 生成Prompt
   python3 demo_methodology.py --industry aluminum --stage stage1

   # 复制到Claude测试
   cat output/aluminum_stage1_prompt.txt | pbcopy
   ```

2. **尝试不同阶段**
   ```bash
   # Stage1: 宏观认知
   python3 demo_methodology.py --stage stage1

   # Stage3: 微观跟踪（尚未完全实现）
   python3 demo_methodology.py --stage stage3

   # 成本拆解
   python3 demo_methodology.py --stage cost
   ```

3. **添加新行业**
   - 编辑 `demo_methodology.py`
   - 添加行业的模拟数据
   - 运行测试

---

### 后续开发（2周）

参考 `implementation_roadmap.md`：

- [ ] 集成真实数据源（AKShare）
- [ ] 添加产业链分析模块
- [ ] 集成AI API自动调用
- [ ] 完善Stage2/3 Prompt
- [ ] 扩展到钢铁、铜行业

---

## 📚 相关文档

- `DEMO_VERIFICATION.md` - Demo验证报告
- `METHODOLOGY_SUMMARY.md` - 方案总结（回答核心问题）
- `implementation_roadmap.md` - 完整实施路线图（12周）
- `example_aluminum_analysis.md` - 电解铝完整示例
- `prompts_methodology.yaml` - Prompt模板配置

---

## 💡 快速技巧

### 技巧1: 快速查看Prompt

```bash
# 前50行
head -50 output/aluminum_stage1_prompt.txt

# 搜索关键词
grep "数据要求" output/aluminum_stage1_prompt.txt
```

### 技巧2: 批量生成

```bash
# 一次生成多个Prompt
for stage in stage1 stage2 stage3 cost; do
    python3 demo_methodology.py --stage $stage
done
```

### 技巧3: 对比不同行业

```bash
# 生成铝和钢的Prompt对比
python3 demo_methodology.py --industry aluminum --stage stage1
python3 demo_methodology.py --industry steel --stage stage1

# 对比
diff output/aluminum_stage1_prompt.txt output/steel_stage1_prompt.txt
```

---

## 🎉 开始使用

```bash
# 运行你的第一个Demo
python3 demo_methodology.py --industry aluminum --stage stage1

# 查看结果
cat output/aluminum_stage1_prompt.txt

# 复制到Claude测试
cat output/aluminum_stage1_prompt.txt | pbcopy

# 🚀 开始体验方法论驱动的行业分析！
```

---

**准备好了吗？运行第一个Demo！** 🎯
