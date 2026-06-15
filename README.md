<div align="center">

# cbec-qualification-review

**跨境商品上架前的 AI 体检：选品、竞品、定价、包装、物流、平台准入和补件清单一次性梳理。**

[English](./README.en.md)

Claude Code / Codex / OpenClaw / Hermes 等支持 Skills 的 agent 均可使用。给它一个商品、目标市场、平台、包装标签、证书报告或品牌材料，它会帮你判断：这个品能不能卖、值不值得卖、上架前还缺什么、哪里最容易被平台或监管卡住。

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![No dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](./scripts/qualification_audit_schema.py)

</div>

---

## 每个跨境卖家都会遇到的问题

- **选品前**：这个商品适合卖到美国、欧盟、东南亚还是中国跨境？有没有明显禁售、认证、标签或物流坑？
- **上架前**：Amazon、TikTok Shop、Shopee、Temu、Lazada、AliExpress、Tmall Global 需要哪些材料？
- **被卡审时**：平台说缺资质、标签不合规、品牌授权不完整，到底该补什么？
- **做定价时**：竞品是谁，主流渠道和价格带是什么，自己的包装和定位应该怎么拉开差异？
- **做发货时**：空运、海运、中欧班列、海外仓、本地配送的成本、时效、风险怎么取舍？
- **给团队协作时**：怎么把商品信息、证书、品牌材料、补件项和风险结论整理成一份能执行的报告？

## 能输出什么

- **出海可行性判断**：目标市场、平台、类目、禁限售、认证、标签、物流和品牌风险的初步结论。
- **竞品与渠道洞察**：竞品价格带、销售渠道、包装表达、消费人群和差异化机会。
- **包装与标签建议**：正背标信息、卖点表达、合规标签、认证标识和本地化文案方向。
- **平台准入清单**：按平台、国家/地区和类目生成上架前材料清单与审核风险。
- **物流与预算对比**：按时效、成本、资金占用、品类限制和海外仓需求拆解方案。
- **资质与证书核验**：营业执照、品牌授权、商标、检测报告、COA、SDS/MSDS、CE、FCC、ISO、HACCP 等材料一致性检查。
- **补件与整改话术**：把缺失、过期、不一致或无法核验的问题转成能发给供应商、商家或服务商的补件请求。

## 中文效果示意

以下示意图展示中文业务场景下的输出形态：从消费者与竞品信号，到渠道价格、包装标签、配方建议、定价策略和物流预算，都可以被整理成便于运营、审核和补件沟通的结构化页面。

### 消费者与竞品信号

![消费者与竞品信号](./assets/demo-consumer-competitor-signals.png)

### 竞品价格与渠道洞察

![竞品价格与渠道洞察](./assets/demo-competitor-pricing-channels.png)

### 包装、配方与定价建议

![包装、配方与定价建议](./assets/demo-packaging-formula-pricing.png)

### 美国零售货架概念

![美国零售货架概念](./assets/demo-retail-shelf-concept.png)

### 物流对比与预算

![物流对比与预算](./assets/demo-logistics-budget-eu.png)

## 常见使用场景

| 场景 | 为什么高频 | 典型输出 |
| --- | --- | --- |
| 新品出海前评估 | 每个新品上架前都要判断市场、平台和合规风险 | 可卖性判断、风险点、材料清单、下一步动作 |
| 平台/类目卡审补件 | 卖家经常被要求补资质、补授权、改标签 | 缺口解释、补件清单、申请人/供应商话术 |
| 竞品与定价复盘 | 定价和定位会反复调整 | 竞品表、渠道价格带、差异化建议 |
| 包装标签改版 | 食品、化妆品、电子、家化类目常要本地化 | 正背标建议、声明/警示/认证标识检查 |
| 物流方案选择 | 成本、时效、品类限制和资金占用持续影响利润 | 空运/海运/铁路/海外仓对比 |
| 内部审核 SOP | 团队需要把经验沉淀为可复用流程 | 规则矩阵、JSON 输出、审计日志和复核记录 |

## 整体项目逻辑图

![跨境商品出海上架评估整体逻辑图](./assets/project-logic-diagram-zh.png)

## 结论状态

当用户需要明确判断时，skill 的最终结论固定为六类，便于系统集成和复核：

| 状态 | 含义 |
| --- | --- |
| `approve` | 当前材料和核验结果支持推进。 |
| `conditional_approve` | 可以推进，但需要完成边界清楚的低/中风险补正。 |
| `request_more_info` | 关键信息或材料缺失，暂不能判断。 |
| `reject` | 已确认禁售、严重不合规、无权销售、材料失效且不可补正等问题。 |
| `escalate_human` | 疑似造假、制裁/出口管制、身份敏感、法律歧义或官方来源冲突。 |
| `not_applicable` | 请求范围不适用于给定平台、市场、类目或审核目的。 |

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

## 使用示例

```text
用 cbec-qualification-review 看看这款橄榄油适不适合卖美国 Amazon，竞品、定价、包装、物流和准入风险一起评估。
```

```text
用 cbec-qualification-review 帮我做 TikTok Shop 马来西亚护肤品上架前检查，列出需要补的材料和标签风险。
```

```text
用 cbec-qualification-review 对比空运、海运、海外仓三种方案，看这个产品去欧盟怎么发更合适。
```

```text
用 cbec-qualification-review 根据这些竞品截图和产品信息，给我一份价格带、渠道、包装卖点和上架准备建议。
```

```text
用 cbec-qualification-review 把营业执照、商标证书、COA、SDS 和检测报告整理成结构化审核 JSON，并生成补件通知。
```

## 安全与边界

本项目用于跨境电商商品出海评估、上架准备、资质审核、材料初审、补件生成和内部流程设计，不提供法律意见，也不替代平台、监管机构、认证机构或专业合规顾问的最终判断。

含身份证件、银行账户、个人联系方式、合同、营业执照编号等敏感信息时，应按 [`references/privacy-security.md`](./references/privacy-security.md) 做最小化展示、脱敏和审计记录。
