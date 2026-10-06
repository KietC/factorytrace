# Research workflow

## English

Run environment checks, define the product/site/process question, preserve originals, and create brand-neutral image variants. Split image/text search, corporate/site records, certification and trade documents into independent lanes. Merge image clusters and entity links, request process/batch evidence, then use Researcher, Skeptic and Reconciler rounds. Recompute assessments, lint reports and audit. If evidence is missing, select the next action by information gain and log what remains unknown. Do not take the shortcut same photo → shop → factory. The valid progression is visual lead → entity/site/process binding → exact SKU/batch → independent on-site/certification/commercial closure. Browser access failures are not evidence that a company lacks the item.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 流程图

```mermaid
flowchart TD
    Z["doctor：环境、依赖、模型模式"] --> A["定义角色×部件×地点/工序Claim"]
    A --> B["原件入库：SHA-256、UTC、manifest"]
    B --> C["产品/模具指纹与品牌无关裁片"]
    C --> D1["图片搜索：Lens/Bing/Yandex/TinEye/百度/平台"]
    C --> D2["文本搜索：尺寸/部件/工艺/证书/HS"]
    C --> D3["企业与工厂：工商/环评/设备/招聘"]
    C --> D4["认证与贸易：WMCAB/COO/PO/批次"]
    D1 --> E["图片簇去重与传播时间线"]
    D2 --> E
    D3 --> F["S/M/L/K/P 实体关系图"]
    D4 --> F
    E --> F
    F --> G["随机连续视频/审厂/样品/模具指纹"]
    G --> H["Researcher：支持证据"]
    H --> I["Skeptic：反证与替代解释"]
    I --> J["Reconciler：去重、冲突、ESS、下一轮"]
    J --> K{"confirmed 审计通过？"}
    K -- "否" --> L["记录缺口；按信息增益选择动作"]
    L --> D1
    L --> D3
    L --> D4
    L --> G
    K -- "是" --> M["输出可追责结论与证据包"]
```

最常见的错误捷径：

`同款图 → 店铺 → 厂家`

正确链路：

`同款图 → 候选 → 法人/地址/工序 → 精确SKU/批次 → 独立现场/认证/贸易闭环`
