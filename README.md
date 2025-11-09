# Pansou Telegram Bot 🤖

基于 Pansou API 搭建的 Telegram 机器人，支持多网盘资源搜索和磁力链接查找。

![Docker](https://img.shields.io/badge/Docker-支持-2496ED?logo=docker)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![架构](https://img.shields.io/badge/架构-ARM64%2FAMD64-0091BD)
![版本](https://img.shields.io/badge/版本-1.0-brightgreen)
![许可证](https://img.shields.io/badge/LICENSE-MIT-green)

## ✨ 特性

- 🔍 **多网盘搜索** - 115网盘、阿里云盘、百度云盘、迅雷云盘、夸克网盘、Pikpak、天翼云盘
- 🧲 **磁力链接** - 直接获取磁力链接和迅雷链接
- 🤖 **智能交互** - 完整的Telegram Bot交互界面，支持按钮和快速搜索
- 🐳 **容器化部署** - Docker Compose部署，支持AMD64, ARM64架构
- ⚡ **快速响应** - 异步处理，搜索结果快速返回
- 📱 **用户友好** - 直观的按钮交互和分页浏览

## 🚀 快速开始

## 环境要求

- Docker & Docker Compose
- Telegram Bot Token
- Pansou API 账号

## 前置准备
1. 申请 Telegram 机器人 Token（通过 @BotFather 获取）
2. 确保 pansou 账号（用户名/密码）可正常访问搜索 API
3. 本地安装 Docker 和 Docker Compose

## 部署步骤
### 1. 创建项目目录及文件

```bash
mkdir -p /opt/pansou-bot/logs && touch /opt/pansou-bot/.env && touch /opt/pansou-bot/docker-compose.yml
```

### 2. 配置环境变量（.env 文件）
打开 .env 文件，填入以下内容（替换为你的实际信息）：
```bash
BOT_TOKEN=你的Telegram机器人Token  
SEARCH_API_URL=https://your_pansou_address/api/search  
PANSOU_USERNAME=账户名  
PANSOU_PASSWORD=密码
```
### 3. 编写 docker-compose.yml
```yaml
services:
  pansou-bot:
    image: dannis1514/pansou-bot:1.0-amd64 #arm请更换为arm64v8
    container_name: pansou-telegram-bot
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs #目录持久化
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
