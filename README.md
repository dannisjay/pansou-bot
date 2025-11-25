# Pansou Telegram Bot 🤖

基于 Pansou API 搭建的 Telegram 机器人，支持多网盘资源搜索和磁力链接查找。

![Docker](https://img.shields.io/badge/Docker-支持-2496ED?logo=docker)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![架构](https://img.shields.io/badge/架构-ARM64%2FAMD64-0091BD)
![版本](https://img.shields.io/badge/版本-1.0-brightgreen)
![许可证](https://img.shields.io/badge/LICENSE-MIT-green)

## ✨ 特性

- 🔍 **网盘搜索** - 115网盘、阿里云盘、百度云盘、迅雷云盘、夸克网盘、Pikpak、天翼云盘
- 🧲 **磁力链接** - 直接获取磁力链接和迅雷链接
- 🤖 **智能交互** - 完整的Telegram Bot交互界面，支持按钮和快速搜索
- 🐳 **容器部署** - Docker Compose部署，支持AMD64, ARM64架构
- ⚡ **快速响应** - 异步处理，搜索结果快速返回
- 📱 **用户友好** - 直观的按钮交互和分页浏览
- 🗂️ **115集成** - 配置115账号，支持快速转存和离线下载

## 🚀 快速开始

## 环境要求

- Docker & Docker Compose
- Telegram Bot Token
- Pansou API 账号

## 前置准备
1. **申请 Telegram 机器人 Token**（通过 @BotFather 获取）
2. **获取用户 ID**（通过 @VersaToolsBot 获取）
3. **确保 pansou 账号**（用户名/密码）可正常访问搜索 API
4. **本地安装** Docker 和 Docker Compose

## 部署步骤
### 1. 创建项目目录

```bash
cd /opt/pansou-bot && mkdir -p logs data && touch .env docker-compose.yml
```
```bash
sudo chmod 777 /opt/pansou-bot/logs /opt/pansou-bot/data
```

### 2. 配置环境变量（.env 文件）
在已创建的.env 文件，填入以下内容（替换为你的实际信息）：
```bash
# Telegram Bot配置
BOT_TOKEN=你的Telegram机器人Token
ALLOWED_USERS=TG_ID

# 盘搜API配置
SEARCH_API_URL=http://ip:端口/api/search
PANSOU_USERNAME=账号
PANSOU_PASSWORD=密码

# Nullbr配置(留空则不启用)
NULLBR_APP_ID=
NULLBR_API_KEY=
NULLBR_BASE_URL=https://api.nullbr.eu.org

# 代理配置（可选，如果网络访问受限时使用）
# HTTP_PROXY=http://proxy_ip:port
# HTTPS_PROXY=https://proxy_ip:port

```
### 3. 编写 docker-compose.yml

```yaml
services:
  pansou-bot:
    image: dannis1514/pansou-bot:latest
    container_name: pansou-bot
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - TZ=Asia/Shanghai
    networks:
      - pansou-network

networks:
  pansou-network:
    driver: bridge
```

### 4. 启动服务
```bash
docker compose up -d
```



## 💝 特别感谢

<p align="center">
  <br>
  <strong>感谢以下开源项目</strong>
  <br><br>
  
  <a href="https://github.com/fish2018/pansou">
    <img src="https://img.shields.io/badge/🔗_pansou-原项目-8A2BE2" alt="原项目">
  </a>
  <a href="https://github.com/fish2018">
    <img src="https://img.shields.io/badge/👤_fish2018-作者-00BFFF" alt="作者">
  </a>
</p>

> 本项目基于 [fish2018/pansou](https://github.com/fish2018/pansou) ，在此向原作者表示诚挚的感谢！
