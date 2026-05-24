"""AI服务 - 支持多provider切换"""
from openai import AsyncOpenAI
from typing import List, Dict, Optional
from config import settings


# ====== 系统提示词 ======
SOUL_CHAT_PROMPT = """你是「星愿」，一位温柔、包容、专业的AI心理陪伴师。
你的角色定位：
- 像一位好朋友一样倾听用户的心事，不评判，不说教
- 用同理心回应用户情绪，先共情再提供建议
- 鼓励用户表达内心感受，帮助他们梳理情绪
- 在适当时候给出正面引导，但不强迫
- 保持温暖、治愈、积极的语气
- 如果用户有严重心理问题，温和建议寻求专业帮助
- 每次回复控制在200字以内，简洁有力
记住：你不是在解决问题，而是在陪伴和支持。"""

FORTUNE_BAZI_PROMPT = """你是「玄机先生」，一位精通中国传统命理学的智慧老者。
你精通：
- 八字命理（年柱、月柱、日柱、时柱，天干地支五行）
- 紫微斗数基础
- 生肖运势
- 风水基本原理
分析方式：
1. 先根据用户提供的生辰八字排盘
2. 分析五行强弱，找出命局特点
3. 结合流年大运给出运势解读
4. 给出具体的开运建议
语气：神秘而智慧，偶尔引用古诗词，但保持通俗易懂
重要提示：这是娱乐性质的占卜，请在末尾注明仅供娱乐请理性看待"""

FORTUNE_STAR_PROMPT = """你是「星辰使者」，精通西方占星术和星座学的占星师。
你精通：
- 十二星座的性格特征与命运走势
- 行星运动对星座的影响（水星逆行等）
- 星盘基础解读
- 星座配对与关系分析
分析风格：
- 结合星座特点给出本周/本月运势
- 分析爱情、事业、财运三个维度
- 给出具体的行动建议
- 语气轻松愉快，充满星光气息
重要提示：这是娱乐性质的占卜，仅供参考"""


def get_ai_client(config: Optional[Dict] = None) -> tuple[AsyncOpenAI, str]:
    """根据配置创建AI客户端，返回(client, model_name)"""
    if config and config.get("api_key"):
        base_url = config.get("base_url") or settings.DEFAULT_AI_BASE_URL
        api_key = config["api_key"]
        model = config.get("model_name") or settings.DEFAULT_AI_MODEL
    else:
        base_url = settings.DEFAULT_AI_BASE_URL
        api_key = settings.DEFAULT_AI_API_KEY
        model = settings.DEFAULT_AI_MODEL

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return client, model


async def ai_chat(
    messages: List[Dict],
    mode: str = "chat",
    user_config: Optional[Dict] = None
) -> str:
    """AI对话，支持树洞聊天和算卦模式"""
    if mode == "fortune_bazi":
        system_prompt = FORTUNE_BAZI_PROMPT
        config_key = "fortune_model"
    elif mode == "fortune_star":
        system_prompt = FORTUNE_STAR_PROMPT
        config_key = "fortune_model"
    else:
        system_prompt = SOUL_CHAT_PROMPT
        config_key = "chat_model"

    # 优先使用功能专用模型
    effective_config = dict(user_config) if user_config else {}
    if user_config and user_config.get(config_key):
        effective_config["model_name"] = user_config[config_key]

    client, model = get_ai_client(effective_config)

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=800,
            temperature=0.85,
        )
        return response.choices[0].message.content or "（AI暂时沉默中...）"
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return "⚠️ AI配置有误，请检查API Key是否正确。"
        elif "model" in error_msg.lower():
            return f"⚠️ 模型「{model}」不可用，请检查模型名称。"
        else:
            return f"⚠️ AI服务暂时不可用，请稍后再试。（{error_msg[:100]}）"


async def build_fortune_messages(fortune_req) -> List[Dict]:
    """构建算命请求消息"""
    if fortune_req.mode == "bazi":
        content = f"""请为我进行八字命理分析：
- 出生日期：{fortune_req.birth_date}
- 出生时间：{fortune_req.birth_time or '不详'}
- 性别：{fortune_req.birth_gender or '不详'}
{f'- 我的问题：{fortune_req.question}' if fortune_req.question else ''}
请详细分析我的命盘特征和近期运势。"""
    elif fortune_req.mode == "star":
        content = f"""请为我进行星座运势分析：
- 星座：{fortune_req.star_sign}
- 出生日期：{fortune_req.birth_date or '不详'}
{f'- 我想了解：{fortune_req.question}' if fortune_req.question else ''}
请分析近期运势，包括爱情、事业、财运三个方面。"""
    else:
        content = fortune_req.question or "请给我占卜今日运势"

    return [{"role": "user", "content": content}]
