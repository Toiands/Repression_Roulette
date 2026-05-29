# 压抑模拟器

基于 Streamlit 的纯文字生存游戏。

## 本地测试（改代码后先跑这个，满意再 push）

```bash
cd repression_simulator

# 需要 Python 3.10+（推荐 3.11；你若是 3.9 会报类型注解错误）
python3 --version

# 首次：建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 启动（以后每次改完代码都执行）
streamlit run app.py
```

浏览器打开 `http://localhost:8501`。改 `app.py` / `ui/theme.py` 等后保存，页面会提示 **Rerun**，点一下即可刷新。

**本地满意后再发版：**

```bash
git add .
git commit -m "你的说明"
git push   # Streamlit Cloud 会自动重新部署
```

`.venv` 已在 `.gitignore` 中，不会提交到 GitHub。

## 运行（简写）

```bash
cd repression_simulator
source .venv/bin/activate
streamlit run app.py
```

同一 WiFi 内临时分享（跨路由器无效）：

```bash
streamlit run app.py --server.address 0.0.0.0
```

用终端里显示的 `Network URL` 发给同局域网的人。

## 部署到 GitHub + 公网（推荐给群友）

GitHub 只存代码；要让**不同局域网**的人玩，需要再部署到 [Streamlit Community Cloud](https://share.streamlit.io)（免费）。

### 1. 推送到 GitHub

本目录即仓库根目录。远程仓库示例：[Toiands/Repression_Roulette](https://github.com/Toiands/Repression_Roulette)

```bash
cd repression_simulator   # 本仓库根目录
git remote add origin git@github.com:Toiands/Repression_Roulette.git
git push -u origin main
```

### 2. 部署到 Streamlit Cloud

1. 打开 https://share.streamlit.io ，用 GitHub 登录  
2. **New app** → 选仓库 `Repression_Roulette`、分支 `main`  
3. **Main file path** 填：`app.py`  
4. **Deploy**，等待构建完成  
5. 把生成的 `https://xxx.streamlit.app` 链接发给群友  

之后每次 `git push`，云端会自动更新（或到控制台手动 Redeploy）。

### 3. 注意

- 免费 Streamlit Cloud 需要 **公开仓库**（Public）  
- 久未访问会休眠，首次打开可能需等待十几秒  
- 每人浏览器独立一局，互不影响  

## 玩法概要

- 在 **压抑值**（100 爆表失败）与 **健康值**（0 归零失败）之间平衡。
- 初始压抑 50，每轮自动压抑（后期略升）；胜利：存活 **10** 回合；中后期更易遇高危嘉宾；连续「全程安全」会叠孤独惩罚；有套仍有疏漏概率；**14 项成就**（侧栏查看，同浏览器 localStorage 保留）；NPC 100 人不重复（池空洗牌）。
- 疾病：梅毒、尖锐湿疣、HIV（感染 HIV 立刻 Game Over）；试纸不限次数；治疗压抑 +50。
