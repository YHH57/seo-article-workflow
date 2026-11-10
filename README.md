# SEO Article Workflow

用于英文 SEO 文章的通用内容工作流，支持外部投稿、自有博客、已有稿件续作和逐阶段测试。当前版本 **0.1.1**，将通用流程、可选输出格式和测试观察分开；不依赖特定行业、品牌或付费 SEO 供应商，不强制所有文章采用同一模板。

## 入口与用法

Skill 位于 [skills/seo-article-workflow/SKILL.md](skills/seo-article-workflow/SKILL.md)。可在支持本地 Skill 的环境中安装该文件夹，或直接指定路径使用。此仓库的创建不代表已自动安装到本机全局 Skill 目录。

示例请求：

- “使用 $seo-article-workflow，先理解这个目标页和读者情境，本轮不要查关键词或写文章。”
- “沿用已确认 brief 和研究，完成一篇英文外部文章，平台未确定；只交付 Markdown。”
- “本篇使用标准模式，先生成大纲供我审阅，暂不写正文。”
- “审阅当前稿件，列问题和优先级，不修改。”

按请求逐步交付或连续完成已授权工作，不另设通用审批门槛。图片、HTML、付费查询和发布不会因生成文章而自动执行。

## 包含什么

- 业务与目标页理解，读者情境、问题池、候选方向及可读比较。
- 意图查询与内容研究分开；研究复用、完整查询条件、指标状态和证据范围。
- 作者配置、大纲、自然英文写作、通用 Conclusion 提示词。
- 关键词、品牌链接与技术来源分开管理，外部文章与自有博客区分。
- 事实复核、可选表达编辑、内容诊断、定向修改与版本收尾。
- 按需 HTML、发布交接及批量复用指导。

原项目选择的 FAQ、引用格式、自有博客链接数量和视觉样式现作为可选的**标准模式**，配置仍位于 [project-editorial-profile.json](skills/seo-article-workflow/assets/project-editorial-profile.json)。用户选择后固定沿用这些约定及其条件；未选时按内容或用户模板安排，不自动套用。大纲阶段展示本篇采用的格式，具体见 [output-format.md](skills/seo-article-workflow/references/output-format.md)。标准模式固定呈现骨架，不固定题材、小标题、段数或作者语气，也不是通用 SEO 规定。

## 本地验证

```bash
python3 -m unittest discover -s tests -v
python3 skills/seo-article-workflow/scripts/validate_run.py --run /path/to/task/run.json
```

检查器只核对记录与文件一致性，不做网络查询，不证明文风、技术事实、Google 排名或平台接受。

来源与版本见 [provenance.md](docs/provenance.md)；实际测试范围和未验证项见 [validation.md](docs/validation.md)。客户正文、原始研究响应、截图和私有资料不随仓库发布。
