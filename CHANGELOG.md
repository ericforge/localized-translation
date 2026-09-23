# Changelog

## 3.6.0 - 2026-09-23

- 将合规处理改为按法域、品类、载体和渠道核验，禁止模型自行宣布合规或删除 claim。
- 修正韩国电气规格、瑞士数字格式、复数类别和占位符顺序规则。
- 将 RTL、文化替换、Amazon 字段、SEO 参数和 `hreflang` 规则改为条件化表述。
- 补充 Markdown/代码/HTML 保护矩阵以及 `PASS` / `FAIL` / `NOT_RUN` / `NOT_VERIFIED` 状态。
- 新增 `scripts/validate_localization.py` 和最小测试 fixture，覆盖受保护 token、HTML 标签、JSON 结构和 UTF-8/BOM。
- 拆分宿主安装说明，移除固定个人和宿主记忆路径。
