<div align="center">

# 出海体检官

**先找对标，再查风险：给你的跨境商品做一次卖前 AI 体检。**

[English](./README.en.md)

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Hackathon](https://img.shields.io/badge/International%20Food%20Expo%20Hackathon-2nd%20Place-gold.svg)](#)

国际食品展黑客松第二名项目，现已开源。

</div>

---

跨境上架最贵的错误，往往不是选品错了，而是**货已经备好，平台才告诉你资质不够、授权不覆盖、标签要改、类目不能卖**。

出海体检官把“我这个品能不能出海”变成一份可执行的 AI 体检报告。给它一个商品、目标市场、平台、包装标签、证书报告、品牌材料，或几张当地竞品截图，它会先帮你找清楚：目标市场的类似商品怎么卖、怎么包装、怎么定价、靠什么建立信任；再判断哪里能推进，哪里要补件，哪里可能亏钱，哪里必须停下来复核。

## 现在能本地跑什么

这个 repo 现在包含一个不依赖外部服务的离线 MVP：把商品信息、已抽取的证书字段、包装文案、竞品行和物流行整理成一个 case bundle，就能生成结构化 JSON 体检报告和 Markdown 备忘录。

```bash
python3 scripts/qualification_audit_schema.py launch-report \
  examples/offline-launch-case.json \
  > /tmp/launchfit-offline-report.json

python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json

python3 scripts/qualification_audit_schema.py launch-report-markdown \
  /tmp/launchfit-offline-report.json \
  > /tmp/launchfit-offline-report.md
```

离线 MVP 会覆盖 README 里最核心的报告面：目标市场对标、价格/单位价格、包装和宣称风险、物流路线风险、平台准入缺口、过期/错配材料、补件话术和审计记录。

边界也很明确：当前仓库不内置 OCR、实时竞品抓取、证书/商标/企业注册库查询、物流报价 API 或审核 UI。用户提供的截图、证书和报价会被标为 T4 / `user_provided`；需要官方或实时来源确认的事项会保留为 `needs_external_verification`。

## 它解决的核心问题

- **上架前不确定**：这个品在 Amazon / TikTok Shop / Shopee / Temu / Lazada / AliExpress / Tmall Global 能不能卖？
- **平台卡审说不清**：到底缺品牌授权、检测报告、标签、证书，还是主体/地区/类目不匹配？
- **找不到对标**：目标市场同类商品怎么定价、怎么包装、主打什么卖点、在哪些渠道卖？
- **包装和宣称有风险**：正背标、成分、过敏原、警示、认证标识、责任方、语言和功效宣称哪里要改？
- **定价和物流没依据**：竞品是谁、价格带在哪、空运/海运/海外仓会不会吃掉利润？
- **团队审核口径不一致**：每个人都凭经验判断，补件话术、证据记录和复核链路难统一。

## 体检报告长什么样

| 报告模块 | 用户拿到的结论 |
| --- | --- |
| 出海体检结论 | go / caution / stop / unknown，一眼看出这个品是否值得继续推 |
| 目标市场对标 | 当地类似商品的价格、规格、包装、卖点、渠道、认证和评论信号 |
| 上架风险清单 | 平台、市场、类目、品牌、标签、证书、物流分别卡在哪里 |
| 资质缺口表 | 哪份材料缺、哪份过期、哪份主体/地区/类目/型号不匹配 |
| 包装标签建议 | 正背标、成分、过敏原、警示语、认证标识、本地化语言和功效宣称怎么改 |
| 价格与定位 | 价格带、单位价格、渠道层级、包装卖点和差异化机会 |
| 物流预算判断 | 空运、海运、海外仓、本地配送的成本、时效和风险 |
| 补件话术 | 可直接发给供应商、客户或服务商的材料请求 |
| 复核记录 | 结论、证据、来源、缺口和下一步动作，方便团队交接 |

## 先看结果

### 消费者与竞品信号

![消费者与竞品信号](./assets/demo-consumer-competitor-signals.png)

### 目标市场对标与渠道洞察

![竞品价格与渠道洞察](./assets/demo-competitor-pricing-channels.png)

### 包装、配方与定价建议

![包装、配方与定价建议](./assets/demo-packaging-formula-pricing.png)

### 物流对比与预算

![物流对比与预算](./assets/demo-logistics-budget-eu.png)

### 美国零售货架概念

![美国零售货架概念](./assets/demo-retail-shelf-concept.png)

## 适合谁

- **跨境卖家 / 品牌方**：在打样、备货、投流前，先知道这个品是否值得继续。
- **选品和运营团队**：不只看销量和价格，把准入、包装、物流、合规成本一起纳入判断。
- **合规 / 资质审核团队**：把审核口径变成固定状态、证据表、缺口表和可复核记录。
- **服务商 / 代运营**：快速判断客户材料哪些能用、哪些必须重开，减少反复沟通。

## 覆盖范围

- 平台：Amazon、TikTok Shop、Shopee、Temu、Lazada、AliExpress、Tmall Global
- 市场 / 区域：US、EU / EEA、UK、Japan、China import、ASEAN / Southeast Asia
- 类目：food、cosmetics、supplements、electronics、household chemicals

规则来源连接到 Amazon Seller Central、TikTok Shop Seller Center、FDA、CBP、European Commission、FCC、CPSC、ASEAN、Singapore HSA、Malaysia NPRA、GOV.UK、MHLW、METI、GACC、SAMR、NMPA、WIPO、EUIPO、USPTO 等官方或权威入口。

## 为什么它不是普通“建议”

- 先确认平台、国家、类目、业务模式、申请人角色、品牌/IP 和材料范围，再给判断。
- 申请人材料只算提交证据，不默认等于真实有效；关键事实需要官方来源、注册库、签发机构或平台政策确认。
- 每个风险都落到 severity、evidence、source、impact、required action，方便人工复核。
- 缺范围、缺材料、材料过期、授权不覆盖、疑似造假或官方来源冲突时，不会硬给通过，会输出补件、拒绝或人工升级。

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

## 🙏 致谢

### 核心贡献者

- [刘申奥](https://v.douyin.com/2i9vkcO2jl4/) ![Douyin](https://img.shields.io/badge/Douyin-抖音-000000?logo=tiktok&logoColor=white)
- [光城](https://github.com/light-city) ![GitHub](https://img.shields.io/badge/GitHub-light--city-181717?logo=github&logoColor=white)
- [tobin](https://github.com/TobinZuo) ![GitHub](https://img.shields.io/badge/GitHub-TobinZuo-181717?logo=github&logoColor=white)
- [梁馨匀](https://github.com/halobaby0917-maker) ![GitHub](https://img.shields.io/badge/GitHub-halobaby0917--maker-181717?logo=github&logoColor=white)
- [June](https://github.com/JuneYaooo) ![GitHub](https://img.shields.io/badge/GitHub-JuneYaooo-181717?logo=github&logoColor=white)
