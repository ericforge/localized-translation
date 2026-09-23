# localized-translation

**多语言本地化翻译流水线** —— 面向跨境电商、独立站和 App 出海场景的多语言本地化翻译 Skill。

> English: A language-agnostic localization pipeline skill — translate → proofread → **localize** → polish → optional compliance review. Built for cross-border e-commerce listings, ads, DTC sites, app copy and regulatory text. Not a literal translation tool: the goal is output that reads like it was written natively in the target market.

---

## 它解决什么问题

直接用 ChatGPT「一步翻译」，产出的是**字面忠实但读起来像外语**的文本。这个 Skill 把它拆成一条有明确交付物的流水线，并且补上了通用翻译提示词普遍缺失的一环 —— **本土化编辑**。

| 段 | 角色 | 关注点 |
| --- | --- | --- |
| 1 | 翻译专家 | 忠实 + 自然，出初稿 |
| 2 | 资深校对编辑（目标语言母语级） | 语法用词、术语统一、数字单位不漂移 |
| 3 | **本土化编辑** | 度量衡 / 货币 / 日期格式 / 文化替换 / 拼写变体 / 平台字符上限 / 合规敏感词 |
| 4 | 润色专家 | 按文体切换：文学求意境、科技求精确、营销求转化 |
| 5 | 合规审核（可选） | 仅受监管品类启用 |

## 核心特性

- **语言不可知**：角色能力按「目标语言母语级」定义，不绑定中英。任意语言对、任意方向（含外→中、中文站内多语言）；法域规则必须按项目配置启用。
- **locale 精确到「语言-地区」**：`es-ES ≠ es-MX`、`pt-BR ≠ pt-PT`、`zh-CN ≠ zh-TW`、`en-US ≠ en-GB`，覆盖多个常用 locale。
- **禁止 pivot 中转**：不允许「源 → 英文 → 目标」的二次失真路径，例外需用户同意 + 标注风险 + 回译验证。
- **交付物是原生的，不是对照的**：终稿 + 关键处理说明表 + 术语表 + 待确认清单。
- **URL 与 IP 默认逐字符冻结**：标识符不是普通文案；经批准的 slug 本地化或换指向属于独立的链接变更，交付前仍须做源文/译文地址清单比对（URL / IP / MAC）。

## 参考文件

| 文件 | 内容 |
| --- | --- |
| `references/locale-profiles.md` | 多个常用 locale 速查：文字方向 / 复数规则 / 默认敬语 / 长度膨胀 / 易错点 |
| `references/localization-checklist.md` | 本土化段逐条检查：度量衡换算、数字与货币格式、尺码、敬语档位、合规敏感词、地区名称与地图合规 |
| `references/industry-labels.md` | 受管制品类强制标签（食品过敏原、化妆品 INCI、CLP、纺织纤维、WEEE、原产地）与销售国官方语言强制（法国 Loi Toubon、魁北克 Bill 96 等） |
| `references/engineering.md` | 交付物是语言包 / JSON / 代码时：ICU 复数语法、占位符保护、禁止字符串拼接、大小写转换坑、伪本地化测试、LQA/MQM 评分 |
| `references/case-orthography.md` | 大小写与正字法：英语大小写改词义（china/China、polish/Polish）、各语系国籍词与月份惯例对照、搜索不区分大小写、URL/SKU 大小写敏感 |
| `references/typography-and-scripts.md` | 表面形式层：引号体系、破折号/省略号/顿号、连字符三级、不可断空格、汉字字形（Han unification）、东阿拉伯数字、简繁词汇差异、「惯例正确≠数学正确」 |
| `references/urls-and-links.md` | URL、IP 与网络地址：默认逐字符冻结（含路径里可读的英文词、`localhost`），识别边界、四种翻车方式、IP/端口/CIDR/MAC 的专属坑、href 不译而锚文本要译、何时该「换指向」、slug 本地化的取舍与 301、`hreflang` 规则、RTL 隔离与不可断行、**交付前的地址清单比对** |

## 安装

### 通用 Agent 安装

本 Skill 适用于支持 Agent Skills 规范或兼容 `SKILL.md` 的 Agent 宿主。将仓库放入宿主配置的 skills 目录即可；具体目录以宿主文档为准。

#### 通用方式

将下面的 `/path/to/your-agent/skills` 替换为目标 Agent 的 skills 目录：

```bash
git clone https://github.com/ericforge/localized-translation.git \
  /path/to/your-agent/skills/localized-translation
```

#### 常见宿主示例

WorkBuddy：

```bash
git clone https://github.com/ericforge/localized-translation.git \
  ~/.workbuddy/skills/localized-translation
```

Claude Code：按其当前 Skills 文档，将仓库放入 `~/.claude/skills/localized-translation`。其他宿主请放入其配置的 skills 目录；不要把宿主专属的记忆路径写入本 Skill。

Skill 加载后，说「翻译 / 汉化 / 本地化 / 翻成德语日语 / localize」即可触发。

## 使用示例

```
把下面这段 Listing 标题本地化到 de-DE 和 ja-JP，文体是亚马逊商品页：

Wireless Earbuds, Bluetooth 5.3 Headphones with 48H Playtime, IPX7 Waterproof
```

输出会包含目标语终稿、关键处理说明表（原文 / 直译不采用 / 终稿 / 理由）、术语表和待确认清单。

## 设计立场

1. **翻译 ≠ 本地化。** 字面忠实只是及格线。
2. **信息不足时先跑再问**：按最可能的假设产出，把假设写进「待确认」，而不是反问一堆问题卡住流程。
3. **硬约束**：不新增原文没有的事实与功效宣称；不删减警告与免责条款；品牌名与 SKU 不译；**URL、IP 与网络地址默认逐字符冻结**（语言无关的标识符，路径里可读的英文单词、`localhost`、`192.0.2.1:8080` 通常都照原样保留。经批准的 slug 本地化或换指向必须作为独立链接变更记录，并完成地址校验）。
4. **不冒充已核实的依据**：所有换算系数、字符上限、复数类别数与法规条文均标注「以 CLDR / ICU / 平台后台 / 官方文本为准」。

## 免责声明

本 Skill 中的法规、认证、平台字段上限等内容**会随时间变化**，且可能因品类、站点、销售国而异。它可以作为**起草与自查的辅助**，但**不构成合规依据**。任何面向市场的宣称、标签与条款，请以目标市场官方法规文本与平台后台实时提示为准。涉及受监管品类（食品、化妆品、医疗器械、儿童用品、化学品、电池等）时，建议交由目标市场的专业合规顾问复核。

## License

[MIT](LICENSE) © 2026 ericforge
