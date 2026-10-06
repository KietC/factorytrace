# Evidence Reasoning and ACH

## English

### Purpose and hypotheses

Turn “who performs which process for which exact product at which site” into falsifiable hypotheses, avoiding conclusions driven by matching photos, brands, or marketing stories. Keep `S → M → L → K → P` distinct: seller/contracting entity, manufacturer, site, exact SKU, and process.

- `H1`: candidate actually performs the target manufacturing process.
- `H2`: candidate only assembles, tests, or packs.
- `H3`: candidate is a trader, brand owner, licence holder, or payee.
- `H4`: an unidentified upstream factory makes the target component.
- `H5`: images/certificates/pages reflect resale or historical relationships.

### ACH matrix

Use `C` consistent, `I` inconsistent, `N` neutral, and `?` unknown. Prioritize discriminating contradictions: a shared product photo explained by many hypotheses contributes little discrimination.

| Field | Meaning |
|---|---|
| evidence_id | Stable evidence identifier |
| fact | Atomic observation without inference |
| source_owner | Publisher or record custodian |
| independence | direct / independent / derivative / unknown |
| bindings | Entity, site, SKU, and process bindings |
| H1..Hn | C / I / N / ? |
| limitations | Date/scope/login/missing-page/hearsay limitations |
| frozen_path | Preserved evidence location |
| sha256 | Hash of original bytes |

### Strength, independence, and contradiction

Strong evidence includes official registries, certification/government records, identity-bound continuous production video, site audits, and exact-batch transaction/test records. Medium evidence includes first-party process pages, equipment lists, hiring/patents, historical social posts, trade records, and repeatable fingerprints. Weak evidence includes storefronts, summaries, isolated workshop photos, appearance, and contact statements. AI output, invented probabilities, unsaved impressions, and unverifiable oral claims are not evidence.

Even a strong record supports only its specific scope: product certification may not prove in-house component or tooling production. Trace the earliest visible source; copies of one PDF/CDN image/press release belong to one source family, not independent confirmations.

Actively test missing target equipment, mismatched entity/site/model, earlier content from another entity, assembly-only official records, transactions/labels/CoO/tests pointing elsewhere, and unverifiable process/batch/site answers. A refusal is an information limitation, not by itself proof of fraud or outsourcing.

### End-of-cycle states

- `CONFIRMED`: direct/strong entity-site-SKU-process closure and resolved critical contradictions.
- `UNRESOLVED`: valuable available paths exhausted, at least one hard gate missing.
- `CONTRADICTED`: a key claim overturned by stronger evidence.
- `BLOCKED`: genuinely requires new material from the user/third party.

A high score, first rank, or “most likely” is not confirmation. Record the remaining evidence request before ending an unresolved cycle.

## 中文

# 证据推理与 ACH

## 目标

把“谁在何处为哪个精确产品完成哪道工序”拆成可证伪假设，防止同款图片、品牌关系和营销故事驱动结论。

## 建立假设

为每个候选同时写出：

- `H1`：候选是目标工序的真实生产主体。
- `H2`：候选只装配、测试或包装。
- `H3`：候选是贸易商、品牌方、持证人或收款主体。
- `H4`：目标件由未识别的上游工厂制造。
- `H5`：图片、证书或产品页面来自转售或历史关系。

使用 `S → M → L → K → P` 责任链：销售/签约主体、制造责任主体、实际地点、精确 SKU、目标工序。

## ACH 矩阵

为证据记录 `C` 一致、`I` 不一致、`N` 中性、`?` 未知。优先比较不一致证据，因为多个候选都能解释的“同款图”区分度很低。

推荐列：

| 字段 | 内容 |
|---|---|
| evidence_id | 稳定证据 ID |
| fact | 不带推论的原子事实 |
| source_owner | 发布者或记录管理者 |
| independence | direct / independent / derivative / unknown |
| bindings | 主体、地点、SKU、工序绑定 |
| H1..Hn | C / I / N / ? |
| limitations | 时间、范围、登录态、缺页、转述等限制 |
| frozen_path | 冻结文件路径 |
| sha256 | 原始字节 SHA-256 |

## 证据等级

- 强：官方注册表、认证机构记录、政府文件、带身份连续生产视频、现场审计、精确批次交易和测试文件。
- 中：候选官网工艺页、设备清单、招聘、专利、长期社媒、贸易记录和可重复图片指纹。
- 弱：平台商品页、搜索摘要、单张车间照、同款外观、联系人陈述。
- 非证据：AI 输出、人工概率、未保存的浏览印象、无法复查的口头说法。

强证据也只支持其明确范围。例如活跃 WaterMark 证书可支持某型号已获证，未必支持盘体、阀体或模具在持证人厂内制造。

## 独立性与重复计数

追踪图片、文字和文件的最早可见来源。多个网站复制同一厂家 PDF、同一 CDN 图片或同一新闻稿时，只计一个来源族。经销商列表不自动构成多源确认。

## 反证队列

主动寻找：

- 厂房没有目标设备或连续工序。
- 证书主体、地点或型号不匹配。
- 更早图片来自另一主体。
- 招聘和环评只显示装配/销售。
- 提单、包装、CoO 或测试文件指向另一工厂。
- 候选对设备、模具、材料批次或现场地址拒绝给出可验证答案。

## 停止条件

只在以下之一满足时结束当前周期：

- `CONFIRMED`：直接证据闭合主体、地点、精确 SKU 和目标工序，且关键反证已关闭。
- `UNRESOLVED`：高价值路径已穷尽，但仍缺少至少一个硬门槛。
- `CONTRADICTED`：候选的关键主张被更强证据推翻。
- `BLOCKED`：必须由用户或第三方提供的新材料才能继续。

不要把高分、排名第一或“最可能”自动升级为确认。

拒绝提供资料本身只构成信息限制，不自动证明欺诈或外协。未闭合周期结束时记录下一项所需材料。
