#!/usr/bin/env python3
# coding=utf-8
"""
测试Prompt管理器
"""

import yaml
from pathlib import Path


def test_prompt_manager():
    """测试Prompt管理器基础功能"""

    # 1. 加载配置文件
    config_path = "prompts_methodology.yaml"

    if not Path(config_path).exists():
        print(f"✗ 配置文件不存在: {config_path}")
        return False

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print(f"✓ 成功加载配置文件")

    # 2. 检查Prompts
    prompts = config.get("prompts", {})
    print(f"✓ 发现 {len(prompts)} 个Prompt模板")

    for stage, prompt_config in prompts.items():
        name = prompt_config.get("name", "")
        print(f"  - {stage}: {name}")

    # 3. 测试渲染
    stage1 = prompts.get("stage1_industry_overview")
    if not stage1:
        print("✗ 未找到stage1模板")
        return False

    template = stage1.get("template", "")
    print(f"\n✓ Stage1模板长度: {len(template)} 字符")

    # 简单渲染测试
    try:
        rendered = template.format(
            industry="电解铝",
            data_section="## 测试数据部分",
            news_section="## 测试新闻部分"
        )
        print(f"✓ 模板渲染成功")
        print(f"\n渲染结果预览（前500字符）：")
        print("=" * 60)
        print(rendered[:500])
        print("=" * 60)
        return True

    except Exception as e:
        print(f"✗ 模板渲染失败: {e}")
        return False


if __name__ == "__main__":
    success = test_prompt_manager()
    exit(0 if success else 1)
