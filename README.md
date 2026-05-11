# html-library

我的个人 HTML 阅读知识库 — 把 LLM 生成的可视化文章、报告、dashboard、artifact 收在一起,自动分组,一键分享。

## 用法

```bash
# 添加一个 html 文件 (会问你确认标题和标签)
add ~/Downloads/some-article.html

# 跳过 LLM, 手动给标签
add ~/Downloads/some.html --tags AI,指南

# 本地只更新, 不 push
add ~/Downloads/some.html --no-push
```

## 结构

```
~/html-library/
├── artifacts/                ← html 文件本体, 每个都是单文件可分享
├── metadata.json             ← 自动维护的标题/标签/日期
├── index.html                ← 苹果风格 gallery, 自动生成
├── README.md
└── scripts/
    ├── add.py                ← 入库
    └── build_gallery.py      ← 重建首页
```

## 部署

- Push 到 GitHub → Vercel 自动部署
- 公开访问: `https://html-library-sooty.vercel.app`
- 单篇分享: `https://html-library-sooty.vercel.app/artifacts/<slug>.html`

## 别名 (推荐)

把 `add` 加进 `~/.zshrc` 方便随时调用:

```bash
alias add='python3 ~/html-library/scripts/add.py'
```
