# coding=utf-8
"""
Prompt模板管理器 - 方法论驱动分析
"""

import yaml
import os
from typing import Dict, Optional
from pathlib import Path


class PromptManager:
    """Prompt模板管理器"""

    def __init__(self, config_file: str = None):
        """
        初始化Prompt管理器

        Args:
            config_file: Prompt配置文件路径（默认：项目根目录的prompts_methodology.yaml）
        """
        if config_file is None:
            # 默认使用项目根目录的prompts_methodology.yaml
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            config_file = str(project_root / "prompts_methodology.yaml")
        elif not os.path.isabs(config_file):
            # 如果是相对路径，从项目根目录查找
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            config_file = str(project_root / config_file)

        self.config_file = config_file
        self.prompts_config = None
        self._load_prompts()

    def _load_prompts(self):
        """加载Prompt配置文件"""
        config_path = self.config_file

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Prompt配置文件不存在: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.prompts_config = yaml.safe_load(f)
            print(f"✓ 成功加载Prompt配置: {config_path}")
        except Exception as e:
            raise RuntimeError(f"加载Prompt配置失败: {e}")

    def get_prompt(self, stage: str) -> Dict:
        """
        获取指定阶段的Prompt配置

        Args:
            stage: 阶段名称（stage1_industry_overview/stage2_company_analysis/
                           stage3_micro_tracking/special_cost_breakdown）

        Returns:
            Prompt配置字典
        """
        if not self.prompts_config:
            raise RuntimeError("Prompt配置未加载")

        prompts = self.prompts_config.get("prompts", {})
        prompt = prompts.get(stage)

        if not prompt:
            available = list(prompts.keys())
            raise ValueError(
                f"未找到Prompt: {stage}，可用的有: {available}"
            )

        return prompt

    def render_prompt(
        self,
        stage: str,
        industry: str,
        data_section: str,
        news_section: str,
        **kwargs
    ) -> str:
        """
        渲染Prompt模板

        Args:
            stage: 阶段名称
            industry: 行业名称（如：电解铝）
            data_section: 数据部分（Markdown格式）
            news_section: 新闻部分（Markdown格式）
            **kwargs: 其他参数（如company用于stage2）

        Returns:
            渲染后的完整Prompt
        """
        prompt_config = self.get_prompt(stage)
        template = prompt_config.get("template", "")

        # 简单的字符串替换（后续可升级为Jinja2）
        rendered = template.format(
            industry=industry,
            data_section=data_section,
            news_section=news_section,
            **kwargs
        )

        return rendered

    def get_required_data_categories(self, stage: str) -> list:
        """
        获取指定阶段需要的数据类别

        Args:
            stage: 阶段名称

        Returns:
            数据类别列表（如：['production', 'price', 'inventory']）
        """
        prompt_config = self.get_prompt(stage)
        required_data = prompt_config.get("required_data", [])

        categories = []
        for item in required_data:
            if isinstance(item, dict):
                categories.append(item.get("category", ""))
            else:
                categories.append(str(item))

        return [c for c in categories if c]

    def list_available_stages(self) -> list:
        """列出所有可用的分析阶段"""
        if not self.prompts_config:
            return []

        prompts = self.prompts_config.get("prompts", {})
        return [
            {
                "stage": stage,
                "name": config.get("name", ""),
                "goal": config.get("goal", "")
            }
            for stage, config in prompts.items()
        ]


# 便捷函数
def load_prompt_manager(prompts_dir: str = None) -> PromptManager:
    """加载Prompt管理器"""
    return PromptManager(prompts_dir)


if __name__ == "__main__":
    # 测试
    manager = PromptManager()

    print("\n可用的分析阶段：")
    for stage_info in manager.list_available_stages():
        print(f"- {stage_info['stage']}: {stage_info['name']}")

    print("\nStage1需要的数据类别：")
    categories = manager.get_required_data_categories("stage1_industry_overview")
    print(categories)

    print("\n渲染Prompt示例：")
    prompt = manager.render_prompt(
        stage="stage1_industry_overview",
        industry="电解铝",
        data_section="## 测试数据\n- 产量: 340万吨/月",
        news_section="1. 测试新闻"
    )
    print(prompt[:500] + "...")
