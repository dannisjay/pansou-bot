import requests
import json
import logging
import asyncio
import os
import platform
from urllib.parse import urlparse, urlunparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# 强制输出所有打印信息
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("=== BOT 启动 ===")

# === 从环境变量读取白名单 ===
def get_allowed_users():
    """从环境变量获取允许的用户ID列表"""
    allowed_users_str = os.getenv('ALLOWED_USERS', '')
    print(f"🔐 读取白名单环境变量: '{allowed_users_str}'")
    
    if not allowed_users_str or allowed_users_str.strip() == '':
        print("🔐 白名单为空，允许所有用户访问")
        return []
    
    try:
        allowed_users = []
        for user_id_str in allowed_users_str.split(','):
            user_id_str = user_id_str.strip()
            if user_id_str:
                allowed_users.append(int(user_id_str))
        
        print(f"🔐 解析后的白名单用户: {allowed_users}")
        return allowed_users
    except Exception as e:
        print(f"❌ 解析白名单时出错: {e}")
        return []

ALLOWED_USER_IDS = get_allowed_users()

def check_user_permission(user_id):
    """检查用户权限"""
    if not ALLOWED_USER_IDS:  # 如果列表为空，允许所有人
        return True
    return user_id in ALLOWED_USER_IDS

print(f"🔐 权限控制: {f'仅允许用户 {ALLOWED_USER_IDS}' if ALLOWED_USER_IDS else '允许所有用户'}")

# 从环境变量加载配置
BOT_TOKEN = os.getenv('BOT_TOKEN')
SEARCH_API_URL = os.getenv('SEARCH_API_URL')
PANSOU_USERNAME = os.getenv('PANSOU_USERNAME')
PANSOU_PASSWORD = os.getenv('PANSOU_PASSWORD')

# 检查必要配置
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN 环境变量未设置")
if not SEARCH_API_URL:
    raise Exception("SEARCH_API_URL 环境变量未设置")
if not PANSOU_USERNAME:
    raise Exception("PANSOU_USERNAME 环境变量未设置")
if not PANSOU_PASSWORD:
    raise Exception("PANSOU_PASSWORD 环境变量未设置")

print(f"🔧 配置检查:")
print(f"  SEARCH_API_URL: {SEARCH_API_URL}")
print(f"  PANSOU_USERNAME: {PANSOU_USERNAME}")
print(f"  PANSOU_PASSWORD: ***{PANSOU_PASSWORD[-2:] if PANSOU_PASSWORD else 'None'}")

# 使用字典来存储 Token，避免全局变量问题
token_storage = {'token': None}

def get_verify_url():
    """获取验证接口URL"""
    parsed_url = urlparse(SEARCH_API_URL)
    verify_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '/api/auth/verify', '', '', ''))
    return verify_url

def get_login_url():
    """获取登录接口URL"""
    parsed_url = urlparse(SEARCH_API_URL)
    login_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '/api/auth/login', '', '', ''))
    return login_url

def verify_token(token):
    """验证Token是否有效"""
    print("🔄 验证Token有效性...")
    try:
        verify_url = get_verify_url()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(verify_url, headers=headers, timeout=10)
        print(f"🔄 Token验证响应: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('valid') == True:
                print("✅ Token验证成功")
                return True
            else:
                print("❌ Token验证失败")
                return False
        else:
            print(f"❌ Token验证请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Token验证异常: {str(e)}")
        return False

def refresh_token():
    """刷新Token"""
    print("🔄 refresh_token() 被调用")
    try:
        login_url = get_login_url()
        
        login_data = {
            "username": PANSOU_USERNAME,
            "password": PANSOU_PASSWORD
        }
        
        print(f"🔄 尝试登录: {login_url}")
        response = requests.post(login_url, json=login_data, timeout=10)
        print(f"🔄 登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            new_token = result.get('token')
            if new_token:
                # 验证新获取的Token是否有效
                if verify_token(new_token):
                    token_storage['token'] = new_token
                    print(f"✅ Token获取并验证成功: {new_token[:20]}...")
                    return new_token
                else:
                    print("❌ 新获取的Token验证失败")
            else:
                print("❌ 响应中没有token字段")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"💥 异常: {str(e)}")
    
    return None

def get_valid_token():
    """获取有效的Token"""
    current_token = token_storage['token']
    
    # 如果没有Token，直接获取新的
    if not current_token:
        print("🔑 无Token，获取新Token...")
        return refresh_token()
    
    # 验证现有Token是否有效
    if verify_token(current_token):
        print("🔑 使用现有有效Token")
        return current_token
    else:
        print("🔑 Token已失效，刷新Token...")
        return refresh_token()

def sync_search_api(keyword: str):
    """同步的API搜索函数"""
    print(f"🔍 sync_search_api() 被调用，关键词: {keyword}")
    
    # 获取有效的Token
    print("🔄 获取有效Token...")
    valid_token = get_valid_token()
    if not valid_token:
        print("❌ 无法获取有效Token")
        return None
    
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json",
    }
    
    data = {"kw": keyword}
    
    print(f"🔍 发送搜索请求到: {SEARCH_API_URL}")
    try:
        response = requests.post(SEARCH_API_URL, headers=headers, json=data, timeout=30)
        print(f"🔍 搜索响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 搜索API调用成功")
            else:
                print(f"❌ 搜索API返回错误: {result.get('message')}")
        else:
            print(f"❌ 搜索请求失败: {response.status_code}")
        
        return response
        
    except Exception as e:
        print(f"💥 请求异常: {str(e)}")
        return None

# 资源类型显示名称映射
RESOURCE_TYPE_NAMES = {
    'pikpak': 'Pikpak',
    'xunlei': '迅雷云盘', 
    'baidu': '百度云盘',
    'magnet': '磁力链接',
    'other': '其它',
    'others': '其它',
    'tianyi': '天翼云盘',
    '115': '115网盘',
    'quark': '夸克网盘',
    'aliyun': '阿里云盘'
}

# 快速搜索菜单配置
QUICK_SEARCH_MENU = {
    "115网盘": "115",
    "阿里云盘": "aliyun", 
    "百度云盘": "baidu",
    "迅雷云盘": "xunlei",
    "夸克网盘": "quark",
    "Pikpak": "pikpak",
    "天翼云盘": "tianyi",
    "磁力链接": "magnet"
}

def get_resource_display_name(resource_type):
    """获取资源类型的显示名称"""
    return RESOURCE_TYPE_NAMES.get(resource_type.lower(), resource_type.upper())

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

# 用户会话数据
user_sessions = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    # 权限检查
    user_id = update.effective_user.id
    if not check_user_permission(user_id):
        print(f"❌ 用户 {user_id} 无权限访问")
        await update.message.reply_text("❌ 您无权使用此机器人")
        return
    
    menu_buttons = [
        ["🔍 开始搜索", "📋 使用帮助"],
        ["⚡ 快速搜索", "📊 机器人状态"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔍 盘搜机器人\n\n直接发送关键词即可搜索资源\n\n例如：\n• 钢铁侠\n• 天下第一\n\n支持所有常见的搜索关键词！",
        reply_markup=reply_markup
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理搜索命令 /search"""
    # 权限检查
    user_id = update.effective_user.id
    if not check_user_permission(user_id):
        print(f"❌ 用户 {user_id} 无权限访问")
        await update.message.reply_text("❌ 您无权使用此机器人")
        return
    
    if not context.args:
        await update.message.reply_text("请提供搜索关键词，例如：/search 钢铁侠")
        return
    
    keyword = ' '.join(context.args)
    await perform_search(update, keyword, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通消息作为搜索请求"""
    # 权限检查
    user_id = update.effective_user.id
    if not check_user_permission(user_id):
        print(f"❌ 用户 {user_id} 无权限访问")
        await update.message.reply_text("❌ 您无权使用此机器人")
        return
    
    keyword = update.message.text.strip()
    print(f"📨 收到用户 {user_id} 消息: {keyword}")
    
    # 处理菜单按钮点击
    if keyword == "🔍 开始搜索":
        await start_command(update, context)
        return
    elif keyword == "📋 使用帮助":
        await help_command(update, context)
        return
    elif keyword == "⚡ 快速搜索":
        await show_quick_search_menu(update, context)
        return
    elif keyword == "📊 机器人状态":
        await stats_command(update, context)
        return
    
    # 忽略命令
    if keyword.startswith('/'):
        return
        
    await perform_search(update, keyword, context)

async def show_quick_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示快速搜索菜单"""
    keyboard = []
    row = []
    
    for display_name, resource_type in QUICK_SEARCH_MENU.items():
        button = InlineKeyboardButton(display_name, callback_data=f"quick_{resource_type}")
        row.append(button)
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 返回主菜单", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚡ 快速搜索\n\n请选择要搜索的网盘类型：\n\n选择后直接发送关键词即可搜索该类型的资源",
        reply_markup=reply_markup
    )

async def handle_quick_search(update: Update, resource_type: str, context: ContextTypes.DEFAULT_TYPE):
    """处理快速搜索选择"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    context.user_data['quick_search_type'] = resource_type
    display_name = get_resource_display_name(resource_type)
    
    await query.edit_message_text(
        f"✅ 已选择: {display_name}\n\n现在请直接发送搜索关键词，我将只搜索{display_name}的资源"
    )

async def perform_search(update: Update, keyword: str, context: ContextTypes.DEFAULT_TYPE):
    """执行搜索并返回结果"""
    try:
        user_id = update.effective_user.id
        print(f"🎯 用户 {user_id} 执行搜索，关键词: {keyword}")
        
        message = await update.message.reply_text(f"🔍 正在搜索: {keyword}...")
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, sync_search_api, keyword)
        
        if response is None:
            print("❌ 搜索失败：无法获取Token")
            await message.edit_text("❌ 搜索失败：无法获取Token")
            return
            
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 搜索成功，准备显示结果")
                search_data = result.get('data', {})
                await show_resource_types(update, keyword, search_data, message, context)
            else:
                error_msg = result.get('message', '未知错误')
                print(f"❌ API返回错误: {error_msg}")
                await message.edit_text(f"❌ API返回错误: {error_msg}")
        else:
            print(f"❌ 搜索失败，状态码: {response.status_code}")
            await message.edit_text(f"❌ 搜索失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"💥 搜索时发生错误: {str(e)}")
        await update.message.reply_text(f"❌ 搜索时发生错误: {str(e)}")

async def perform_normal_search(update: Update, keyword: str, context: ContextTypes.DEFAULT_TYPE):
    """执行普通搜索（所有类型）"""
    message = await update.message.reply_text(f"🔍 正在搜索: {keyword}...")
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, sync_search_api, keyword)
    
    if response is None:
        await message.edit_text("❌ 搜索失败：无法获取Token")
        return
        
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            search_data = result.get('data', {})
            await show_resource_types(update, keyword, search_data, message, context)
        else:
            await message.edit_text(f"❌ API返回错误: {result.get('message', '未知错误')}")
    else:
        await message.edit_text(f"❌ 搜索失败，状态码: {response.status_code}")

async def perform_quick_search(update: Update, keyword: str, resource_type: str, context: ContextTypes.DEFAULT_TYPE):
    """执行快速搜索（特定类型）"""
    message = await update.message.reply_text(f"🔍 正在搜索{get_resource_display_name(resource_type)}资源: {keyword}...")
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, sync_search_api, keyword)
    
    if response is None:
        await message.edit_text("❌ 搜索失败：无法获取Token")
        return
        
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            search_data = result.get('data', {})
            merged_by_type = search_data.get('merged_by_type', {})
            
            if resource_type in merged_by_type and merged_by_type[resource_type]:
                resources = merged_by_type[resource_type]
                await show_quick_search_results(update, keyword, resource_type, resources, message, context)
            else:
                display_name = get_resource_display_name(resource_type)
                await message.edit_text(f"🔍 未找到{display_name}关于『{keyword}』的资源")
        else:
            await message.edit_text(f"❌ API返回错误: {result.get('message', '未知错误')}")
    else:
        await message.edit_text(f"❌ 搜索失败，状态码: {response.status_code}")

async def show_quick_search_results(update: Update, keyword: str, resource_type: str, resources: list, message, context: ContextTypes.DEFAULT_TYPE):
    """显示快速搜索结果"""
    try:
        display_name = get_resource_display_name(resource_type)
        
        user_id = update.effective_user.id
        user_sessions[user_id] = {
            'keyword': keyword,
            'merged_by_type': {resource_type: resources},
            'total': len(resources)
        }
        
        await show_resource_page(message, resource_type, resources, 0, user_id, context)
        
    except Exception as e:
        await message.edit_text(f"❌ 显示搜索结果时出错: {str(e)}")

async def show_resource_types(update: Update, keyword: str, data: dict, message, context: ContextTypes.DEFAULT_TYPE):
    """显示资源类型选择按钮"""
    try:
        total = data.get('total', 0)
        merged_by_type = data.get('merged_by_type', {})
        
        if total == 0:
            await message.edit_text(f"🔍 未找到关于『{keyword}』的资源")
            return
        
        user_id = update.effective_user.id
        user_sessions[user_id] = {
            'keyword': keyword,
            'merged_by_type': merged_by_type,
            'total': total
        }
        
        keyboard = []
        row = []
        
        for resource_type in merged_by_type.keys():
            resources_count = len(merged_by_type[resource_type])
            if resources_count > 0:
                display_name = get_resource_display_name(resource_type)
                button_text = f"{display_name}({resources_count})"
                callback_data = f"type_{resource_type}_{user_id}"
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("📊 显示所有类型统计", callback_data=f"stats_{user_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        response_text = f"🔍 搜索『{keyword}』结果\n\n📊 总计: {total} 个资源\n\n📁 请选择资源类型查看详情:"
        
        await message.edit_text(response_text, reply_markup=reply_markup)
        
    except Exception as e:
        await message.edit_text(f"❌ 显示资源类型时出错: {str(e)}")

async def show_resource_details(update: Update, resource_type: str, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """显示指定资源类型的详细结果"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_data = user_sessions.get(user_id)
        if not user_data:
            await query.edit_message_text("❌ 会话已过期，请重新搜索")
            return
        
        keyword = user_data['keyword']
        merged_by_type = user_data['merged_by_type']
        resources = merged_by_type.get(resource_type, [])
        
        if not resources:
            await query.edit_message_text(f"❌ 未找到 {resource_type} 类型的资源")
            return
        
        await show_resource_page(query, resource_type, resources, 0, user_id, context)
        
    except Exception as e:
        await query.edit_message_text(f"❌ 显示资源详情时出错: {str(e)}")

async def show_resource_page(query, resource_type: str, resources: list, page: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """显示资源分页"""
    try:
        items_per_page = 5
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_resources = resources[start_idx:end_idx]
        
        user_data = user_sessions.get(user_id)
        keyword = user_data['keyword'] if user_data else "未知"
        
        display_name = get_resource_display_name(resource_type)
        response_text = f"🔍 {display_name}资源 - 『{keyword}』\n\n"
        response_text += f"📄 第 {page + 1}/{(len(resources) - 1) // items_per_page + 1} 页 | 共 {len(resources)} 个资源\n\n"
        
        keyboard = []
        
        for i, resource in enumerate(page_resources, start=start_idx + 1):
            note = resource.get('note', resource.get('title', '无标题'))
            url = resource.get('url', '')
            password = resource.get('password', '')
            source = resource.get('source', '未知来源')
            datetime_str = resource.get('datetime', '')[:10]
            
            if len(note) > 60:
                note = note[:60] + "..."
            
            note = note.replace('*', '×').replace('_', ' ').replace('`', "'").replace('[', '(').replace(']', ')')
            
            response_text += f"{i}. {note}\n"
            
            if url:
                if url.startswith('magnet:'):
                    response_text += f"   🧲 {url}\n"
                elif url.startswith('thunder://'):
                    response_text += f"   ⚡ {url}\n"
                else:
                    response_text += f"   🔗 {url}\n"
            
            if password:
                safe_password = password.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
                response_text += f"   🔐 密码: {safe_password}\n"
            
            info_parts = []
            if datetime_str:
                info_parts.append(f"⏰ {datetime_str}")
            if source:
                safe_source = source.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
                if source.startswith('tg:'):
                    info_parts.append(f"📡 {safe_source[3:]}")
                elif source.startswith('plugin:'):
                    info_parts.append(f"🔌 {safe_source[7:]}")
                else:
                    info_parts.append(f"📡 {safe_source}")
            
            if info_parts:
                response_text += f"   {' | '.join(info_parts)}\n"
            
            response_text += "\n"
            
            if url and (url.startswith('magnet:') or url.startswith('thunder://')):
                button_text = f"Link-{i}"
                session_key = f"copy_{user_id}_{page}_{i}"
                user_sessions[user_id][session_key] = url
                callback_data = session_key
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ 上一页", callback_data=f"page_{resource_type}_{page-1}_{user_id}"))
        
        if end_idx < len(resources):
            nav_buttons.append(InlineKeyboardButton("下一页 ➡️", callback_data=f"page_{resource_type}_{page+1}_{user_id}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 返回类型选择", callback_data=f"back_types_{user_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(query, 'edit_message_text'):
            await query.edit_message_text(response_text, reply_markup=reply_markup, parse_mode=None)
        else:
            await query.edit_text(response_text, reply_markup=reply_markup, parse_mode=None)
        
    except Exception as e:
        error_msg = f"❌ 显示资源页面时出错: {str(e)}"
        if hasattr(query, 'edit_message_text'):
            await query.edit_message_text(error_msg, parse_mode=None)
        else:
            await query.edit_text(error_msg, parse_mode=None)

async def handle_copy_request(update: Update, session_key: str):
    """处理复制请求"""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = session_key.split('_')
        user_id = int(parts[1])
        page = int(parts[2])
        resource_num = int(parts[3])
        
        user_data = user_sessions.get(user_id)
        if not user_data:
            await query.answer("❌ 会话已过期", show_alert=True)
            return
        
        url = user_data.get(session_key)
        if not url:
            await query.answer("❌ 链接不存在", show_alert=True)
            return
        
        await query.message.reply_text(url)
        
    except Exception as e:
        await query.answer("❌ 复制失败", show_alert=True)

async def show_stats(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """显示所有类型统计"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_data = user_sessions.get(user_id)
        if not user_data:
            await query.edit_message_text("❌ 会话已过期，请重新搜索")
            return
        
        keyword = user_data['keyword']
        merged_by_type = user_data['merged_by_type']
        total = user_data['total']
        
        response_text = f"🔍 搜索『{keyword}』统计\n\n"
        response_text += f"📊 总计: {total} 个资源\n\n"
        response_text += "📁 资源类型分布:\n"
        
        for resource_type, resources in merged_by_type.items():
            if resources:
                display_name = get_resource_display_name(resource_type)
                response_text += f"• {display_name}: {len(resources)} 个资源\n"
        
        keyboard = [[InlineKeyboardButton("🔙 返回类型选择", callback_data=f"back_types_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(response_text, reply_markup=reply_markup)
        
    except Exception as e:
        await query.edit_message_text(f"❌ 显示统计时出错: {str(e)}")

async def back_to_types(update: Update, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """返回到类型选择"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_data = user_sessions.get(user_id)
        if not user_data:
            await query.edit_message_text("❌ 会话已过期，请重新搜索")
            return
        
        await show_resource_types(update, user_data['keyword'], {'total': user_data['total'], 'merged_by_type': user_data['merged_by_type']}, query.message, context)
        
    except Exception as e:
        await query.edit_message_text(f"❌ 返回类型选择时出错: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理按钮回调"""
    query = update.callback_query
    data = query.data
    
    try:
        if data.startswith('type_'):
            parts = data.split('_')
            resource_type = parts[1]
            user_id = int(parts[2])
            await show_resource_details(update, resource_type, user_id, context)
            
        elif data.startswith('page_'):
            parts = data.split('_')
            resource_type = parts[1]
            page = int(parts[2])
            user_id = int(parts[3])
            
            user_data = user_sessions.get(user_id)
            if user_data:
                resources = user_data['merged_by_type'].get(resource_type, [])
                await show_resource_page(query, resource_type, resources, page, user_id, context)
            
        elif data.startswith('stats_'):
            user_id = int(data.split('_')[1])
            await show_stats(update, user_id, context)
            
        elif data.startswith('back_types_'):
            user_id = int(data.split('_')[2])
            await back_to_types(update, user_id, context)
            
        elif data.startswith('quick_'):
            resource_type = data.split('_')[1]
            await handle_quick_search(update, resource_type, context)
            
        elif data.startswith('copy_'):
            await handle_copy_request(update, data)
            
        elif data == 'back_main':
            await query.edit_message_text("已返回主菜单")
            
    except Exception as e:
        await query.edit_message_text(f"❌ 处理按钮时出错: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """帮助命令"""
    # 权限检查
    user_id = update.effective_user.id
    if not check_user_permission(user_id):
        print(f"❌ 用户 {user_id} 无权限访问")
        await update.message.reply_text("❌ 您无权使用此机器人")
        return
    
    menu_buttons = [
        ["🔍 开始搜索", "📋 使用帮助"],
        ["⚡ 快速搜索", "📊 机器人状态"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 使用帮助\n\n"
        "🔍 搜索方法:\n"
        "1. 直接发送关键词\n"
        "2. 使用 /search 关键词 命令\n"
        "3. 点击『⚡ 快速搜索』选择特定网盘\n\n"
        "📝 示例:\n"
        "钢铁侠\n"
        "天下第一\n\n"
        "📋 功能特点:\n"
        "• 按资源类型分类显示\n"
        "• 支持分页浏览\n"
        "• 显示完整资源链接\n"
        "• 快速搜索特定网盘\n"
        "• 一键复制磁力和迅雷链接\n\n"
        "⚡ 搜索后会显示资源类型按钮，点击查看详情",
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """统计命令"""
    # 权限检查
    user_id = update.effective_user.id
    if not check_user_permission(user_id):
        print(f"❌ 用户 {user_id} 无权限访问")
        await update.message.reply_text("❌ 您无权使用此机器人")
        return
    
    menu_buttons = [
        ["🔍 开始搜索", "📋 使用帮助"],
        ["⚡ 快速搜索", "📊 机器人状态"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    
    arch = platform.machine()
    arch_display = "ARM64" if arch in ['aarch64', 'arm64', 'armv8'] else "AMD64" if arch in ['x86_64', 'amd64'] else arch
    
    await update.message.reply_text(
        f"📊 机器人状态\n\n"
        f"✅ 运行正常\n"
        f"🔗 API: 已连接\n"
        f"🏗️ 架构: {arch_display}\n"
        f"🐳 容器: 已部署\n"
        f"🕒 重启策略: unless-stopped\n\n"
        f"⚡ 支持快速搜索以下网盘:\n"
        f"• 115网盘\n• 阿里云盘\n• 百度云盘\n• 迅雷云盘\n"
        f"• 夸克网盘\n• Pikpak\n• 天翼云盘\n• 磁力链接",
        reply_markup=reply_markup
    )

def main():
    """启动机器人"""
    try:
        print("🚀 启动机器人...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("search", search_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print("✅ 机器人启动完成")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
