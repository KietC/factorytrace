# Code guide / 代码导读

## English

Read [the Skill entrypoint](../skills/trace-source-factory/SKILL.md) for workflow decisions and [the CLI](../factory_trace_toolkit/src/factorytrace/cli.py) for exact commands. Bilingual comments explain intent and fragile boundaries without replacing tests.

| Module | Responsibility | Boundary |
|---|---|---|
| [assessment](../factory_trace_toolkit/src/factorytrace/assessment.py) | Product/site/process/batch trace stages and ACH | A recorded field is not proof of source authenticity |
| [audit](../factory_trace_toolkit/src/factorytrace/audit.py) | Hashes, references, independent direct evidence, confirmation gates | Readiness does not confirm a factory |
| [certification](../factory_trace_toolkit/src/factorytrace/certification.py) | UL/WaterMark scope and authorized site binding | Licence holder is not necessarily manufacturer |
| [social](../factory_trace_toolkit/src/factorytrace/social.py) | Account/entity/site/equipment/process/SKU links | Reposts are not independent votes |
| [events](../factory_trace_toolkit/src/factorytrace/events.py) | Batch and supply-chain event consistency | A shipper is not automatically the producer |
| [common](../factory_trace_toolkit/src/factorytrace/common.py) | Hashing, lock, atomic writes and URL redaction | Integrity is not truth of depicted content |
| [fetch](../factory_trace_toolkit/src/factorytrace/fetch.py) | Bounded queues, host throttles, retry and evidence capture | Trusted public URL queue only; not an internet-facing URL service |
| [reporting](../factory_trace_toolkit/src/factorytrace/reporting.py) | One payload for MD/JSON/CSV/XLSX/DOCX | Evidence score is not calibrated probability |

The public edition documents the core logic rather than publishing only wrappers. Case data and operational receipts remain external. Font provenance and release validation were adapted for public reproducibility; supplier-attribution algorithms were not redesigned for this release.

## 中文

先读 [Skill 入口](../skills/trace-source-factory/SKILL.md) 理解调查决策，再读 [CLI](../factory_trace_toolkit/src/factorytrace/cli.py) 核对实际参数。中英注释解释意图和容易出错的边界，不能替代测试。

| 模块 | 职责 | 边界 |
|---|---|---|
| assessment | 产品、地点、工序、批次阶段及 ACH | 字段填好不等于来源真实 |
| audit | 哈希、引用、独立直接证据、确认硬门槛 | 流程可运行不等于确认厂家 |
| certification | UL/WaterMark 范围与授权地点绑定 | 持证人不一定是制造商 |
| social | 账号、主体、场址、设备、工序、SKU 绑定 | 多次转载不是多张独立选票 |
| events | 批次与物流事件一致性 | 发货人不一定是生产者 |
| common | 哈希、锁、原子写入、URL 脱敏 | 文件完整不等于内容真实 |
| fetch | 有界队列、单域节流、重试、证据保存 | 只接可信公开 URL，不作为互联网 URL 接口 |
| reporting | 同一数据生成五种报告 | 证据分数不是校准过的概率 |

公开版保留完整核心，不只公开包装层。案件数据与运行回执留在仓库之外。本次调整字体来源与发布校验以便公开复现，没有重新设计供应商归因算法。
