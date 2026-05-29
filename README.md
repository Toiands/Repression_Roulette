# 压抑模拟器

基于 Streamlit 的纯文字生存游戏。

## 运行

```bash
cd repression_simulator
pip install -r requirements.txt
streamlit run app.py
```

浏览器将自动打开本地页面（默认 `http://localhost:8501`）。

同一 WiFi 内临时分享（跨路由器无效）：

```bash
streamlit run app.py --server.address 0.0.0.0
```

用终端里显示的 `Network URL` 发给同局域网的人。

## 部署到 GitHub + 公网（推荐给群友）

GitHub 只存代码；要让**不同局域网**的人玩，需要再部署到 [Streamlit Community Cloud](https://share.streamlit.io)（免费）。

### 1. 推送到 GitHub

本目录即仓库根目录。在 GitHub 网页新建**空仓库**（例如 `repression-simulator`，不要勾选 README），然后：

```bash
cd repression_simulator   # 本仓库根目录
git remote add origin https://github.com/<你的用户名>/repression-simulator.git
git push -u origin main
```

若已用 GitHub CLI 登录，也可一键创建并推送：

```bash
gh repo create repression-simulator --public --source=. --remote=origin --push
```

### 2. 部署到 Streamlit Cloud

1. 打开 https://share.streamlit.io ，用 GitHub 登录  
2. **New app** → 选仓库 `repression-simulator`、分支 `main`  
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
- 初始压抑 50，每轮 +10；胜利：存活 25 回合；NPC 100 人且不重复（池空洗牌）；追问 2～4 次随机跑路（不显示次数）；感染带叙事。
- 疾病：梅毒、尖锐湿疣、HIV（感染 HIV 立刻 Game Over）；试纸不限次数；治疗压抑 +50。
