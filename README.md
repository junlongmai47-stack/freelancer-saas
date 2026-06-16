# FreelanceFlow - 自由职业者管理平台

一个完整的自由职业者 SaaS 应用，使用 Python Flask 构建。

## 功能特性

- 📊 **项目管理** - 创建、编辑、跟踪项目
- ⏱️ **时间追踪** - 记录工作时间
- 📄 **发票生成** - 自动生成 PDF 发票
- 👥 **客户管理** - 维护客户信息
- 📈 **数据分析** - 收入和工时统计
- 💳 **订阅系统** - Stripe 集成（Pro 版本）

## 快速开始

### 本地安装

1. **克隆仓库**
```bash
git clone https://github.com/junlongmai47-stack/freelancer-saas.git
cd freelancer-saas
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **创建 .env 文件**
```bash
cp .env.example .env
# 编辑 .env，填入你的 SECRET_KEY 和 Stripe 密钥
```

5. **运行应用**
```bash
python app.py
```

应用将在 `http://localhost:5000` 运行。

## 部署到 Heroku

1. **安装 Heroku CLI**
```bash
brew tap heroku/brew && brew install heroku
```

2. **登录 Heroku**
```bash
heroku login
```

3. **创建应用**
```bash
heroku create your-app-name
```

4. **设置环境变���**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set STRIPE_SECRET_KEY=your-stripe-key
```

5. **部署**
```bash
git push heroku main
```

## 部署到 Railway

1. 访问 [railway.app](https://railway.app)
2. 连接 GitHub 仓库
3. 选择此仓库
4. 设置环境变量
5. 部署

## 部署到 PythonAnywhere

1. 访问 [pythonanywhere.com](https://pythonanywhere.com)
2. 上传你的代码
3. 配置 WSGI 文件
4. 设置环境变量
5. 启动 Web 应用

## 定价模式

- **免费版**：基础功能，每月 2 张发票
- **Pro 版本**：$19.99/月，无限制功能

## 技术栈

- **后端**：Python Flask
- **数据库**：SQLite / PostgreSQL
- **前端**：HTML/CSS/JavaScript
- **支付**：Stripe
- **部署**：Heroku / Railway / PythonAnywhere

## 文件结构

```
freelancer-saas/
├── app.py                 # 主应用
├── requirements.txt       # Python 依赖
├── Procfile              # Heroku 部署配置
├── .env.example          # 环境变量示例
├── README.md             # 本文件
├── templates/            # HTML 模板
│   ├── base.html         # 基础模板
│   ├── login.html        # 登录页
│   ├── dashboard.html    # 仪表盘
│   ├── projects.html     # 项目列表
│   ├── invoices.html     # 发票列表
│   └── ...
└── static/               # 静态文件
```

## 使用说明

1. **注册账户** - 访问 `/register`
2. **创建项目** - 在仪表盘创建新项目
3. **记录时间** - 为项目添加工时
4. **生成发票** - 创建并下载发票
5. **升级 Pro** - 获取更多功能

## 开发

### 添加新功能

1. 修改 `app.py` 添加新路由
2. 在 `templates/` 添加相应的 HTML 模板
3. 本地测试
4. 提交 Pull Request

## 许可证

MIT License

## 支持

有问题？提交 Issue 或 PR！

## 变现路线图

- [ ] 月订阅系统
- [ ] 团队协作功能
- [ ] API 接口
- [ ] 移动应用
- [ ] 企业版本
