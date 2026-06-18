# 自动发现的安全与恶意风险判断

自动发现候选 Skill 时，需要同时做安全风险初筛。这个判断只用于提醒维护者，不代表仓库一定安全或一定恶意。

候选结果中后续应增加 `risk_level` 和 `risk_reasons` 字段：

- `risk_level` 可取 `low`、`medium`、`high`、`unknown`
- `risk_reasons` 记录触发风险判断的原因，方便人工复核
- 高风险信号包括：README 诱导执行不明脚本、混淆代码、可疑下载链接、要求输入密钥或 token、异常权限说明
- 中风险信号包括：仓库信息过少、无 README、无 License、维护记录很少、功能描述与代码结构明显不一致
- 低风险信号包括：仓库结构清晰、说明完整、维护记录正常、代码和描述基本一致
- 风险较高的候选不应自动写入 `data.js`
- 最终是否加入正式页面仍由维护者人工确认

后续实现时，自动发现流程应保持：

```text
GitHub Search
  ->
候选仓库
  ->
Skill 相关性打分
  ->
安全风险初筛
  ->
candidates/skills_candidates.json
  ->
维护者人工确认
  ->
正式写入 data.js
```
