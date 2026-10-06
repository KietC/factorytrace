# Evidence standard

## English

Separate observed facts, inference, leads, contradictions and unresolved questions. Bind evidence to the exact entity, site, SKU/revision, target process and batch where applicable. Preserve source URL, title, publication/capture time, original bytes, SHA-256, scope and limitations. Seller marketing, social reposts and platform badges are discovery leads; official records may establish only the specific object/claim in their scope. Same owner, same URL, copied image or shared upstream material belongs to one source cluster. Freeze strong/direct evidence and retain adverse facts instead of averaging them away. Hashes protect integrity, not authenticity. A model answer or search snippet is never a substitute for its underlying source. Confirmation requires fresh audited gates, independent frozen direct sources and no unresolved critical contradiction.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 证据标准与 ESS

## 一、证据不能跨命题借用

一条证据只支持一个明确命题：

- 商品页：该主体展示/销售过该产品；
- 企业登记：该法人存在、登记字段为何；
- 环评：该地址申报过哪些设备和工艺；
- 连续视频：该地点在该时间执行了画面中的工序；
- 批次文件：某 SKU/批次与工单、检验、包装的关系；
- 认证机构确认：某型号对应的被审制造地点；
- 原产地证：特定货物的 exporter/producer 声明。

不允许从“展示过”跳到“生产过”，从“有设备”跳到“生产目标 SKU”，或从“持证”跳到“开模”。

命题至少写明`角色 × 部件 × 法人 × 地点 × SKU/批次 × 工序`。整机装配证据不得借给盘体深拉Claim，盘体证据也不得借给阀头或模具制造Claim。

模型回答、OCR猜测、CLIP/相似度分数和搜索引擎摘要不是证据；它们只能指向需要冻结和核验的底层来源。

## 二、证据等级

### A：独立且直接

- 认证机构确认精确型号、准确制造地点和目标工序。
- 第三方现场审厂同时绑定法人、地址、设备、工序和目标 SKU。
- 随机挑战连续视频完整拍到厂牌、设备铭牌、目标模具、实际生产、测量和批次。
- 生产指令、模具台账、检验、包装和物流形成闭环，并被独立来源交叉验证。

### B：直接但由候选控制

- BOM、受控工程图、模具编号、生产工单、领料和检验记录。
- 模具采购发票、资产台账、维修/改模记录。
- 未经独立第三方核实的实时生产视频。

### C：独立但间接

- 环评、排污、技改、消防、设备采购和招聘。
- 原产地证、提单、装箱单和贸易关系。
- 厂区地图、政府检查、历史网页和展会资料。

### D：营销证据

- 官网、平台商品、目录、SEO页、Facebook、LinkedIn、抖音。

### E：线索

- 同款图、相同商标、相似联系人、店铺会员年限、搜索摘要。

## 三、结构化字段

证据 CSV/JSON 至少保存：

```text
case_id, claim_id, evidence_id, candidate_id
role, component, legal_entity, physical_site, process, claim_text
source_class, source_url, local_path, issuer
published_at, captured_at_utc
fact_or_inference, stance, strength
independence_group
entity_bind, site_bind, sku_bind
batch_or_revision, quoted_text, OCR confidence
sha256, archive_path
conflict_group, review_status, reviewer, notes
```

`stance`：

- `support`
- `contradict`
- `neutral`
- `absence`

“未搜索到”使用 `absence`，默认不扣分。

## 四、独立性

同一根来源必须放入同一个 `independence_group`：

- 公司官网、同公司店铺、销售员文件、公司社媒通常同簇；
- 搜索摘要与其原网页同簇；
- 新闻稿及转载同簇；
- 同一验厂报告的截图、PDF和平台摘要同簇；
- 不同认证机构、政府记录、买方批次文件和第三方现场审厂可为独立簇。

新评分器在同一维度、同一 stance、同一独立簇中只保留最强信号，阻止重复营销材料堆分。

## 五、ESS 与多轴结论

| 维度 | 上限 |
|---|---:|
| 主体链：合同、收款、制造责任 | 15 |
| 准确地点与目标工序能力 | 25 |
| 精确 SKU/批次与目标工序闭环 | 30 |
| 采购、批次和物流责任链 | 15 |
| 认证与实际制造地点 | 10 |
| 真正独立交叉验证 | 5 |

评分同时考虑：

- `strength`: direct / strong / supporting / lead；
- `source_class`: certifier / government / buyer_document / independent_audit / supplier_live / logistics / trade_data / media / platform / self_published / search_snippet；
- `entity_bind/site_bind/sku_bind`: exact / partial / family / similar / none；
- `independence_group` 去重；
- 同维度反证扣分。

ESS 是证据充分性指数，不是统计概率，最高默认 95。能力适配、认证状态、验证优先级和采购效用是独立轴；任何一个都不得改写成“真实厂家概率”。最终来源闭合使用 `S0_UNLINKED → S4_BATCH_LINKED`，而不是分数阈值。

## 六、硬门槛

要达到 `S4_BATCH_LINKED` 并通过 confirmed 审计，必须全部满足：

1. 合同、收款和制造责任主体已明确；
2. 准确制造地点已绑定；
3. 独立强证据证明该地点执行目标工序；
4. 精确 SKU/批次绑定到该地点和目标工序；
5. 商务/质量责任链有文件和解释；
6. 无未解决 critical red flag；
7. `confirmed` 审计另外要求至少两个冻结在本地的独立直接证据簇。
8. Claim与Evidence引用完整，材料confirmed门槛、环境声明、模型/执行日志均通过。

## 七、强制封顶

- 只有营销、平台、社媒或搜索摘要：最高 20。
- 没有独立证据证明准确地点的目标工序：最高 55。
- 没有精确 SKU/批次绑定：最高 59。
- 制造地点冲突未解决：最高 50。
- critical red flag 未解决：最高 35。
- 不可调精确 SKU 特征明确不符：最高 20。

## 八、红旗

- 多家公司共用同一工厂视频、设备图或员工照片。
- 平台主体、营业执照、合同、收款、厂牌和证书主体互相冲突。
- 只有展厅、仓库和打包；不展示关键工序。
- 产品跨度巨大，设备和工艺无法解释。
- 拒绝提供完整验厂报告、连续挑战视频、设备铭牌或目标批次。
- 证书过期、型号不在 scope、设计或地点变化未解释。
- 产能与厂房、设备、人数和交期明显矛盾。
- 不可调孔位、R角、翻边或截面与目标样品不符。

## 九、允许和禁止的措辞

允许：

- “已确认其为销售/收款主体。”
- “官网当前未发现可访问的具体单品页。”
- “公司自称拥有深拉设备，尚无独立现场证据。”
- “证据支持该地点很可能执行最终装配，但尚不能证明盘体在此深拉。”

禁止：

- “官网没有，所以它不生产。”
- “WaterMark持证人就是制造商。”
- “提单发货人就是开模厂。”
- “相同图片证明同模具。”
- “有油压机，所以目标产品由它生产。”
