# weekly/

这里存放每期周报源文件。

命名规则：

```text
YYYY-MM-DD-ai-weekly.md
```

例如：

```text
2025-07-06-ai-weekly.md
```

周报结构：

```markdown
# AI 每周热点同步（YYYY-MM-DD ~ YYYY-MM-DD）

## 1. AI 热点动态
## 2. 好用的 Skill / 插件 / 功能
## 3. GitHub 热门 AI 项目
## 4. AI + 生物医药科研
## 5. 可应用到我自己工作的建议
## 6. 下周关注
## 7. 附录：全部链接
```

生成网站：

```powershell
python scripts/build_site.py
```

打开：

```text
site/index.html
```