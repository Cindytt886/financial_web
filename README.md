# 基于WRDS的金融建模工具

## 项目简介

这是一个基于WRDS (Wharton Research Data Services) 数据库的金融建模Web应用，使用Streamlit框架开发。提供DCF估值、收入预测、公司对比和技术分析等功能。

## 数据来源

| 数据类型 | 数据库 | 说明 |
|---------|--------|------|
| 财务数据 | Compustat | 财务报表（收入、利润、现金流等） |
| 价格数据 | CRSP | 历史股票价格和成交量 |

**注意**: 仅使用WRDS作为数据源，已移除其他数据源（akshare、FMP等）。

## 功能模块

### 1. DCF估值 (Discounted Cash Flow)
- 基于自由现金流（FCF）计算企业内在价值
- 可调整参数：WACC、永续增长率、预测年数、盈利增长率
- 输出：DCF估值、上涨空间、企业价值、股权价值
- 敏感性分析：WACC vs 永续增长率

### 2. 收入预测
- 从Compustat获取历史收入数据
- 计算历史增长率（平均/中位数）
- 基于增长率预测未来收入
- 敏感性分析：不同增长率假设

### 3. 公司对比
- 选择多家公司进行财务指标对比
- 对比指标：当前价格、平均FCF、市值估算
- 可视化：价格对比图、FCF对比图

### 4. 技术分析
- K线数据（CRSP历史价格）
- 技术指标：MA均线、MACD、RSI、布林带
- 支持自定义分析周期

## 技术栈

- **Web框架**: Streamlit
- **数据处理**: Pandas
- **可视化**: Plotly
- **数据库**: WRDS + psycopg2
- **Python版本**: 3.12+

## 项目结构

```
financial_web/
├── app.py                 # 主应用入口
├── pages/
│   ├── 1_DCF估值.py      # DCF估值页面
│   ├── 2_收入预测.py     # 收入预测页面
│   ├── 3_公司对比.py     # 公司对比页面
│   └── 4_技术分析.py     # 技术分析页面
├── utils/
│   ├── data_fetcher.py   # WRDS数据获取模块
│   └── __init__.py
├── test_wrds.py          # WRDS连接测试
└── README.md             # 本文件
```

## 本地开发

### 环境要求

```bash
# Python 3.12+
python --version
```

### 安装依赖

```bash
# 克隆或进入项目目录
cd financial_web

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖 (使用清华镜像加速)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit pandas plotly wrds psycopg2-binary matplotlib
```

### 运行应用

```bash
streamlit run app.py --server.port 8501
```

访问 http://localhost:8501

## 服务器部署 (Ubuntu/Dell服务器)

### 1. 环境配置

```bash
# 安装Python和venv
sudo apt update
sudo apt install -y python3.12-venv python3-pip

# 创建项目目录
mkdir -p ~/financial_web
cd ~/financial_web
```

### 2. 上传代码

```bash
# 从本地上传文件到服务器
scp -i ~/.ssh/majiang_key -r /path/to/financial_web/* jackey@192.168.3.4:~/financial_web/
```

### 3. 安装依赖

```bash
# SSH登录服务器
ssh -i ~/.ssh/majiang_key jackey@192.168.3.4

# 创建虚拟环境
cd ~/financial_web
python3 -m venv venv
source venv/bin/activate

# 安装依赖 (使用清华镜像)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit pandas plotly wrds psycopg2-binary matplotlib
```

### 4. 启动应用

```bash
# 前台运行（测试用）
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# 后台运行（生产用）
cd ~/financial_web
source venv/bin/activate
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &

# 查看日志
tail -f streamlit.log

# 停止应用
pkill -f streamlit
```

### 5. 端口转发配置

如需外网访问，需在路由器配置端口转发：
- 外部端口：8501
- 内部端口：8501
- 内网IP：192.168.3.4

## WRDS连接配置

在 `utils/data_fetcher.py` 中配置：

```python
WRDS_CONFIG = {
    "username": "guzixin",
    "password": "your_password"
}
```

**注意**: 需要有效的WRDS账户才能连接数据库。

## 预设股票列表

应用中预设了以下热门美股：
- AAPL (苹果)
- MSFT (微软)
- JNJ (强生)
- XOM (埃克森美孚)
- JPM (摩根大通)
- WMT (沃尔玛)
- PG (宝洁)
- KO (可口可乐)
- GE (通用电气)
- IBM

## 常见问题

### 1. WRDS连接失败
- 检查网络是否可访问 wharton.edu
- 确认用户名和密码正确
- 检查VPN/代理设置

### 2. 数据为空
- 某些股票可能没有FCF数据
- 尝试选择其他股票

### 3. Streamlit端口被占用
- 更换端口：`--server.port 8502`
- 或杀死占用进程：`pkill -f streamlit`

### 4. pip安装超时
- 使用国内镜像源
- 增加超时时间：`pip --default-timeout=100 install ...`

## 界面预览

### 首页
- 显示功能概览
- 历史FCF数据快速预览
- 快速导航链接

### DCF估值
- 输入参数侧边栏
- 核心指标展示（DCF估值、上涨空间、企业价值）
- 现金流预测表格
- 可视化图表
- 敏感性分析矩阵

### 收入预测
- 历史收入数据展示
- 增长率统计
- 未来收入预测
- 趋势可视化

### 公司对比
- 多股票选择
- 对比表格
- 价格/FCF对比图表

### 技术分析
-没有数据暂时不做

## 风险提示

- 本工具仅供学习参考，不构成投资建议
- 预测结果可能与实际差异较大
- 投资需谨慎

## 开发者

如有问题或建议，请联系开发团队。

---
最后更新: 2026-03-27
