# -*- coding: utf-8 -*-
"""
AI分析Agent
使用New API进行数据分析，包括情绪分析、真实性验证、关键信息提取
"""

import json
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# 导入UserManager
try:
    from .user_manager import UserManager
except ImportError:
    from user_manager import UserManager


class AnalyzerAgent:
    """
    AI分析Agent
    - 调用New API进行AI分析
    - 支持多种分析类型（情绪分析、真实性验证、摘要生成）
    - 自动计量Token消耗并扣费
    - 上下文维护和连续对话
    """

    def __init__(
        self,
        user_manager: UserManager,
        api_base: str = "http://45.197.145.24:3000/v1",
        api_key: str = "sk-QlwwecImBL1Yx0p2ji8Awsr0ROuD6HPeimWQIRBtgqYSPnXj",
        default_model: str = "deepseek/deepseek-chat",
        mock_mode: bool = False
    ):
        """
        初始化分析Agent

        Args:
            user_manager: 用户管理器实例
            api_base: New API基础URL
            api_key: API密钥
            default_model: 默认使用的模型
            mock_mode: 是否使用Mock模式（用于测试）
        """
        self.user_mgr = user_manager
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.default_model = default_model
        self.mock_mode = mock_mode

        # 会话上下文存储 {user_id: [messages]}
        self.contexts = {}

    # ============================================
    # 主分析接口
    # ============================================

    def analyze(
        self,
        user_id: str,
        data: List[Dict],
        analysis_type: str = "comprehensive",
        subscription_id: Optional[int] = None,
        model: Optional[str] = None,
        maintain_context: bool = False
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        分析数据（统一入口）

        Args:
            user_id: 用户ID
            data: 标准化的数据列表（来自CrawlerAgent）
            analysis_type: 分析类型
                - comprehensive: 综合分析（情绪+关键信息+总结）
                - sentiment: 情绪分析
                - summary: 摘要生成
                - verify: 真实性验证
            subscription_id: 关联的订阅ID（可选）
            model: 使用的模型（可选，默认deepseek-chat）
            maintain_context: 是否维护对话上下文

        Returns:
            (是否成功, 消息, 分析结果)
        """
        # 1. 检查用户
        if not self.user_mgr.user_exists(user_id):
            return False, "用户不存在", None

        # 2. 检查会员状态
        user_info = self.user_mgr.get_user_info(user_id)
        if user_info['membership']['is_expired']:
            return False, f"会员已过期，到期时间：{user_info['membership']['end_date']}", None

        # 3. 检查Token余额
        token_balance = self.user_mgr.get_token_balance(user_id)
        if token_balance <= 0:
            return False, "Token余额不足，请充值", None

        # 4. 检查数据
        if not data:
            return False, "没有可分析的数据", None

        # 5. 选择模型
        model = model or self.default_model

        # 6. 构建提示词
        prompt = self._build_prompt(data, analysis_type)

        # 7. 调用AI API
        try:
            success, msg, response = self._call_ai_api(
                user_id=user_id,
                prompt=prompt,
                model=model,
                maintain_context=maintain_context
            )

            if not success:
                return False, msg, None

            # 8. 扣除Token
            total_tokens = response.get('usage', {}).get('total_tokens', 0)
            prompt_tokens = response.get('usage', {}).get('prompt_tokens', 0)
            completion_tokens = response.get('usage', {}).get('completion_tokens', 0)

            deduct_success, deduct_msg, deduct_result = self.user_mgr.deduct_token(
                user_id=user_id,
                amount=total_tokens,
                operation=f"analyze_{analysis_type}",
                model=model,
                subscription_id=subscription_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )

            if not deduct_success:
                return False, f"Token扣除失败: {deduct_msg}", None

            # 9. 解析结果
            analysis_result = {
                'analysis_type': analysis_type,
                'target': data[0].get('target') if data else None,
                'platform': data[0].get('platform') if data else None,
                'data_count': len(data),
                'content': response.get('content', ''),
                'model': model,
                'tokens_used': total_tokens,
                'remaining_balance': deduct_result['remaining_balance'],
                'timestamp': datetime.now().isoformat()
            }

            # 10. 尝试提取结构化信息（如果是JSON格式）
            try:
                parsed_content = json.loads(response.get('content', '{}'))
                if isinstance(parsed_content, dict):
                    analysis_result.update(parsed_content)
            except json.JSONDecodeError:
                # 如果不是JSON，保留原文本
                pass

            return True, f"分析完成，消耗{total_tokens}个Token", analysis_result

        except Exception as e:
            return False, f"分析失败: {str(e)}", None

    # ============================================
    # AI API调用
    # ============================================

    def _call_ai_api(
        self,
        user_id: str,
        prompt: str,
        model: str,
        maintain_context: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        调用New API

        Args:
            user_id: 用户ID
            prompt: 提示词
            model: 模型名称
            maintain_context: 是否维护上下文
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            (是否成功, 消息, API响应)
        """
        # Mock模式：返回模拟数据
        if self.mock_mode:
            return self._mock_ai_response(prompt, model)

        try:
            # 构建消息列表
            messages = []

            # 如果需要维护上下文，加载历史消息
            if maintain_context and user_id in self.contexts:
                messages = self.contexts[user_id].copy()

            # 添加当前消息
            messages.append({
                "role": "user",
                "content": prompt
            })

            # 构建请求
            url = f"{self.api_base}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # 发送请求
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            result = response.json()

            # 提取响应内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']

                # 保存上下文
                if maintain_context:
                    if user_id not in self.contexts:
                        self.contexts[user_id] = []

                    self.contexts[user_id].append({
                        "role": "user",
                        "content": prompt
                    })
                    self.contexts[user_id].append({
                        "role": "assistant",
                        "content": content
                    })

                    # 限制上下文长度（最多保留最近10轮对话）
                    if len(self.contexts[user_id]) > 20:
                        self.contexts[user_id] = self.contexts[user_id][-20:]

                return True, "API调用成功", {
                    'content': content,
                    'usage': result.get('usage', {}),
                    'model': result.get('model', model)
                }
            else:
                return False, "API响应格式错误", None

        except requests.exceptions.RequestException as e:
            return False, f"API请求失败: {str(e)}", None
        except Exception as e:
            return False, f"未知错误: {str(e)}", None

    # ============================================
    # 提示词构建
    # ============================================

    def _build_prompt(self, data: List[Dict], analysis_type: str) -> str:
        """
        根据分析类型构建提示词

        Args:
            data: 数据列表
            analysis_type: 分析类型

        Returns:
            提示词文本
        """
        # 数据摘要
        target = data[0].get('target', '未知')
        platform = data[0].get('platform', '未知')
        data_count = len(data)

        # 提取内容
        posts_text = self._format_posts(data)

        # 根据类型选择提示词模板
        if analysis_type == "comprehensive":
            return self._prompt_comprehensive(target, platform, data_count, posts_text)
        elif analysis_type == "sentiment":
            return self._prompt_sentiment(target, platform, data_count, posts_text)
        elif analysis_type == "summary":
            return self._prompt_summary(target, platform, data_count, posts_text)
        elif analysis_type == "verify":
            return self._prompt_verify(target, platform, data_count, posts_text)
        else:
            return self._prompt_comprehensive(target, platform, data_count, posts_text)

    def _format_posts(self, data: List[Dict], max_posts: int = 30) -> str:
        """格式化帖子内容为文本"""
        formatted = []

        for i, item in enumerate(data[:max_posts], 1):
            author = item.get('author_name', '匿名')
            content = item.get('content', '')
            time = item.get('publish_time', '')
            likes = item.get('metrics', {}).get('likes', 0)
            comments = item.get('metrics', {}).get('comments', 0)

            formatted.append(
                f"{i}. [{author}] ({time})\n"
                f"   {content}\n"
                f"   👍 {likes}  💬 {comments}"
            )

        return "\n\n".join(formatted)

    # ============================================
    # 提示词模板
    # ============================================

    def _prompt_comprehensive(self, target: str, platform: str, count: int, posts: str) -> str:
        """综合分析提示词"""
        return f"""你是一位专业的金融数据分析师。请分析以下来自{platform}平台关于"{target}"的{count}条讨论数据。

数据内容：
{posts}

请从以下角度进行综合分析，并以JSON格式返回结果：

1. **市场情绪** (sentiment): 整体情绪倾向（positive/neutral/negative）及置信度(0-1)
2. **关键主题** (key_topics): 讨论中的3-5个主要话题
3. **热点事件** (hot_events): 提到的重要事件或消息（如有）
4. **真实性评估** (credibility): 信息的可信度评估（high/medium/low）及理由
5. **投资建议** (suggestion): 基于讨论内容的简要建议（仅供参考）
6. **摘要** (summary): 200字以内的核心摘要

请返回标准JSON格式，确保可被解析。"""

    def _prompt_sentiment(self, target: str, platform: str, count: int, posts: str) -> str:
        """情绪分析提示词"""
        return f"""请分析以下{count}条关于"{target}"的讨论，判断整体市场情绪。

数据：
{posts}

请以JSON格式返回：
{{
    "sentiment": "positive/neutral/negative",
    "confidence": 0.85,
    "positive_ratio": 0.6,
    "negative_ratio": 0.2,
    "neutral_ratio": 0.2,
    "reasoning": "情绪判断的主要依据"
}}"""

    def _prompt_summary(self, target: str, platform: str, count: int, posts: str) -> str:
        """摘要生成提示词"""
        return f"""请为以下{count}条关于"{target}"的讨论生成简洁摘要（200字以内）。

数据：
{posts}

要求：
1. 提取核心信息和关键观点
2. 突出重要事件和趋势
3. 保持客观中立
4. 200字以内

请直接返回摘要文本，不需要JSON格式。"""

    def _prompt_verify(self, target: str, platform: str, count: int, posts: str) -> str:
        """真实性验证提示词"""
        return f"""请评估以下{count}条关于"{target}"的讨论的真实性和可信度。

数据：
{posts}

请以JSON格式返回：
{{
    "credibility": "high/medium/low",
    "confidence": 0.75,
    "reliable_posts": [帖子序号],
    "suspicious_posts": [帖子序号],
    "warning_signs": ["发现的可疑特征"],
    "reasoning": "评估依据"
}}"""

    # ============================================
    # Mock模式（用于测试）
    # ============================================

    def _mock_ai_response(self, prompt: str, model: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        生成模拟的AI响应（用于测试）

        Args:
            prompt: 提示词
            model: 模型名称

        Returns:
            (成功, 消息, 响应数据)
        """
        # 根据提示词内容生成不同的响应
        if "综合分析" in prompt or "comprehensive" in prompt:
            content = json.dumps({
                "sentiment": "positive",
                "confidence": 0.75,
                "key_topics": ["交付量增长", "财报预期", "技术面看多", "自动驾驶技术"],
                "hot_events": ["Q1财报即将发布", "交付量超预期"],
                "credibility": "medium",
                "credibility_reason": "多数观点基于公开信息，但缺乏深度数据支持",
                "suggestion": "短期看多，但需关注财报披露的毛利率变化和估值水平",
                "summary": "市场对特斯拉整体情绪偏积极，主要关注点在于即将发布的Q1财报和交付量表现。技术面显示看多信号，但也有投资者担心估值偏高可能带来短期回调风险。长线投资者更看重自动驾驶等技术优势。"
            }, ensure_ascii=False, indent=2)
            prompt_tokens = 500
            completion_tokens = 200
        elif "情绪" in prompt or "sentiment" in prompt:
            content = json.dumps({
                "sentiment": "positive",
                "confidence": 0.80,
                "positive_ratio": 0.60,
                "negative_ratio": 0.20,
                "neutral_ratio": 0.20,
                "reasoning": "大部分讨论集中在交付量增长和技术面看多信号，正面评价占主导，少数投资者担心估值问题"
            }, ensure_ascii=False, indent=2)
            prompt_tokens = 400
            completion_tokens = 100
        elif "摘要" in prompt or "summary" in prompt:
            content = "特斯拉近期讨论热度较高，市场关注Q1财报和交付量数据。多数投资者情绪偏乐观，认为交付量超预期且技术面看多。部分投资者提示估值风险和短期回调可能。长线投资者强调自动驾驶技术的长期价值。"
            prompt_tokens = 400
            completion_tokens = 80
        elif "真实性" in prompt or "verify" in prompt:
            content = json.dumps({
                "credibility": "medium",
                "confidence": 0.70,
                "reliable_posts": [1, 2, 5],
                "suspicious_posts": [4],
                "warning_signs": ["技术分析指标可能存在滞后性"],
                "reasoning": "多数观点基于公开信息，但缺乏一手数据验证，技术分析存在主观性"
            }, ensure_ascii=False, indent=2)
            prompt_tokens = 450
            completion_tokens = 120
        else:
            content = "模拟AI分析结果"
            prompt_tokens = 300
            completion_tokens = 50

        total_tokens = prompt_tokens + completion_tokens

        return True, "Mock API调用成功", {
            'content': content,
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens
            },
            'model': model
        }

    # ============================================
    # 上下文管理
    # ============================================

    def clear_context(self, user_id: str):
        """清除用户的对话上下文"""
        if user_id in self.contexts:
            del self.contexts[user_id]

    def get_context(self, user_id: str) -> List[Dict]:
        """获取用户的对话上下文"""
        return self.contexts.get(user_id, [])

    # ============================================
    # 批量分析
    # ============================================

    def analyze_batch(
        self,
        user_id: str,
        crawl_results: Dict[int, Tuple[bool, str, List[Dict]]],
        analysis_type: str = "comprehensive"
    ) -> Dict[int, Tuple[bool, str, Optional[Dict]]]:
        """
        批量分析多个订阅的数据

        Args:
            user_id: 用户ID
            crawl_results: 爬取结果字典 {subscription_id: (成功?, 消息, 数据)}
            analysis_type: 分析类型

        Returns:
            {subscription_id: (成功?, 消息, 分析结果)}
        """
        analysis_results = {}

        for sub_id, (success, msg, data) in crawl_results.items():
            if not success or not data:
                analysis_results[sub_id] = (False, f"跳过分析: {msg}", None)
                continue

            # 分析数据
            result = self.analyze(
                user_id=user_id,
                data=data,
                analysis_type=analysis_type,
                subscription_id=sub_id
            )

            analysis_results[sub_id] = result

        return analysis_results


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    # 示例：如何使用 AnalyzerAgent

    from user_manager import UserManager
    from crawler_agent import CrawlerAgent

    # 1. 初始化
    user_mgr = UserManager("/tmp/test_analyzer.db")
    crawler = CrawlerAgent(user_mgr)
    analyzer = AnalyzerAgent(user_mgr)

    # 2. 注册测试用户
    user_id = "telegram_test_456"
    user_mgr.register_user(user_id)

    # 3. 爬取数据
    success, msg, data = crawler.crawl(
        user_id=user_id,
        platform='eastmoney',
        target='TSLA',
        max_items=20
    )

    print(f"爬取: {success} - {msg}")

    if success and data:
        # 4. 分析数据
        success, msg, result = analyzer.analyze(
            user_id=user_id,
            data=data,
            analysis_type='comprehensive'
        )

        print(f"\n分析: {success} - {msg}")

        if success and result:
            print(f"\n目标: {result['target']}")
            print(f"数据量: {result['data_count']}")
            print(f"Token消耗: {result['tokens_used']}")
            print(f"剩余余额: {result['remaining_balance']}")
            print(f"\n分析结果:")
            print(result['content'][:500])
