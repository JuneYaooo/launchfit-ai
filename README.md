<div align="center">

# cbec-qualification-review

**跨境商品上架前的 AI 体检：帮你判断一个品能不能卖、值不值得卖、上架前还缺什么。**

[English](./README.en.md)

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Hackathon](https://img.shields.io/badge/International%20Food%20Expo%20Hackathon-2nd%20Place-gold.svg)](#)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![No dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](./scripts/qualification_audit_schema.py)

国际食品展黑客松第二名项目，现已开源。

</div>

---

给它一个商品、目标市场、平台、包装标签、证书报告或品牌材料，它会把卖家最容易踩坑的地方提前摊开：平台准入、竞品价格、包装标签、物流预算、资质缺口和补件动作。

## 卖家最常卡在这三件事

- **平台卡审**：Amazon / TikTok Shop / Shopee / Temu 要补什么材料？品牌授权、标签、证书到底哪里不够？
- **上架前不确定**：这个品有没有禁限售、认证、标签、物流、进口责任人或本地合规风险？
- **定价没依据**：竞品是谁，价格带在哪，包装卖点和渠道定位怎么做出差异？

## 先看结果

### 消费者与竞品信号

![消费者与竞品信号](./assets/demo-consumer-competitor-signals.png)

### 竞品价格与渠道洞察

![竞品价格与渠道洞察](./assets/demo-competitor-pricing-channels.png)

### 包装、配方与定价建议

![包装、配方与定价建议](./assets/demo-packaging-formula-pricing.png)

### 物流对比与预算

![物流对比与预算](./assets/demo-logistics-budget-eu.png)

### 美国零售货架概念

![美国零售货架概念](./assets/demo-retail-shelf-concept.png)

## 你可以直接这样问

```text
这款橄榄油适合卖美国 Amazon 吗？帮我看竞品、定价、包装、物流和准入风险。
```

```text
这个护肤品要上 TikTok Shop 马来西亚，需要哪些材料？标签有什么风险？
```

```text
这个电子产品去欧盟，空运、海运、海外仓哪个更合适？
```

```text
平台让我补品牌授权和检测报告，帮我判断到底缺什么，顺便写一段补件话术。
```

```text
根据这些竞品截图和产品信息，给我一份价格带、渠道、包装卖点和上架准备建议。
```

## 它会给你什么

| 输出 | 解决的问题 |
| --- | --- |
| 出海可行性判断 | 这个品能不能卖，哪里可能被平台或监管卡住 |
| 竞品与价格带 | 怎么定价，怎么找差异化 |
| 包装标签建议 | 正背标、卖点、认证、警示和本地化文案怎么改 |
| 平台准入清单 | Amazon / TikTok Shop / Shopee / Temu 等平台需要补什么 |
| 物流预算对比 | 空运、海运、铁路、海外仓、本地配送怎么选 |
| 资质与证书核验 | 营业执照、品牌授权、商标、COA、SDS、检测报告是否匹配 |
| 补件话术 | 发给供应商、商家或服务商的清晰请求 |

## 适合哪些高频场景

| 场景 | 为什么高频 | 典型输出 |
| --- | --- | --- |
| 新品出海前评估 | 每个新品上架前都要判断市场、平台和合规风险 | 可卖性判断、风险点、材料清单、下一步动作 |
| 平台/类目卡审补件 | 卖家经常被要求补资质、补授权、改标签 | 缺口解释、补件清单、申请人/供应商话术 |
| 竞品与定价复盘 | 定价和定位会反复调整 | 竞品表、渠道价格带、差异化建议 |
| 包装标签改版 | 食品、化妆品、电子、家化类目常要本地化 | 正背标建议、声明/警示/认证标识检查 |
| 物流方案选择 | 成本、时效、品类限制和资金占用持续影响利润 | 空运/海运/铁路/海外仓对比 |
| 内部审核 SOP | 团队需要把经验沉淀为可复用流程 | 规则矩阵、JSON 输出、审计日志和复核记录 |

## 它怎么判断

![跨境商品出海上架评估整体逻辑图](./assets/project-logic-diagram-zh.png)

<details>
<summary>结构化结论状态</summary>

| 状态 | 含义 |
| --- | --- |
| `approve` | 当前材料和核验结果支持推进。 |
| `conditional_approve` | 可以推进，但需要完成边界清楚的低/中风险补正。 |
| `request_more_info` | 关键信息或材料缺失，暂不能判断。 |
| `reject` | 已确认禁售、严重不合规、无权销售、材料失效且不可补正等问题。 |
| `escalate_human` | 疑似造假、制裁/出口管制、身份敏感、法律歧义或官方来源冲突。 |
| `not_applicable` | 请求范围不适用于给定平台、市场、类目或审核目的。 |

</details>

## 安全与边界

本项目用于跨境电商商品出海评估、上架准备、资质审核、材料初审、补件生成和内部流程设计，不提供法律意见，也不替代平台、监管机构、认证机构或专业合规顾问的最终判断。

含身份证件、银行账户、个人联系方式、合同、营业执照编号等敏感信息时，应按 [`references/privacy-security.md`](./references/privacy-security.md) 做最小化展示、脱敏和审计记录。

## 安装

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R /path/to/cbec-qualification-review ~/.codex/skills/cbec-qualification-review
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R /path/to/cbec-qualification-review ~/.claude/skills/cbec-qualification-review
```

安装后重启对应 agent，让 skill 元数据重新加载。

## 本地可运行能力

这个仓库不只是提示词文档，也提供可执行的审核辅助脚本：

```bash
python3 scripts/qualification_audit_schema.py checklist --platform amazon --market US --category food
```

生成平台/市场/类目检查清单。

```bash
python3 scripts/qualification_audit_schema.py review-skeleton \
  --platform amazon \
  --market US \
  --category food \
  --applicant-name "Example Trading Co., Ltd." \
  --applicant-role distributor \
  --business-model marketplace_seller \
  --brand-name "Example Brand" \
  > /tmp/cbec_review_skeleton.json
```

生成符合 JSON contract 的结构化评审草稿，包含 scope、requirements、sources、findings、missing materials、补件话术和 audit log。默认结论是 `request_more_info`，因为没有用户提交材料和证据匹配时不能给最终通过。

```bash
python3 scripts/qualification_audit_schema.py validate /tmp/cbec_review_skeleton.json
python3 scripts/qualification_audit_schema.py case-check cases/golden-unverified-applicant-docs.json /tmp/cbec_review_skeleton.json
python3 scripts/qualification_audit_schema.py golden-replay
python3 scripts/qualification_audit_schema.py source-freshness
python3 scripts/qualification_audit_schema.py quality-gate
```

当前已为全量已索引规则补入来源，`source-freshness` 应返回：

```text
checked_source_links: 116
unverified_requirements: []
stale: []
missing: []
```

其中三条高频路径已重点补入 T1 官方来源：

- `Amazon + US + food`：Amazon Seller Central、FDA、CBP
- `TikTok Shop + ASEAN/Malaysia + cosmetics`：TikTok Shop Seller Center、ASEAN、Singapore HSA、Malaysia NPRA
- `Temu + electronics`：Temu 官方入口/条款/安全召回、FCC、European Commission、CPSC

Shopee、Lazada、AliExpress、Tmall Global、EU、UK、Japan、China import、supplements、household chemicals 也已补入官方或权威来源入口。注意：规则包成熟度仍是 `seed`，来源齐备不等于可以自动给最终通过；进入 `validated/production` 前仍需要更多 golden cases、真实案例回放和人工抽检。

当前也提供 7 个 produced review fixtures，覆盖 approve、request_more_info、reject、escalate_human、expired certificate、territory mismatch、unverified evidence 等关键路径。运行 `golden-replay` 可批量校验。

发布前可直接运行 `quality-gate`，一次性检查规则包索引、来源新鲜度和 golden replay。

更多命令见 [`examples/README.md`](./examples/README.md)。
