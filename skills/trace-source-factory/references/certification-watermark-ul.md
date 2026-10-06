# WaterMark and UL Certification Tracing

## English

### Official entry points

- [WaterMark Product Search](https://watermark.abcb.gov.au/watermark-search).
- [WaterMark Scheme Manual](https://watermark.abcb.gov.au/sites/default/files/resources/2022/Manual-for-WaterMark-certification-scheme.pdf).
- [UL certification information](https://code-authorities.ul.com/about/certifications/).
- [UL Product iQ](https://productiq.ulprospector.com/).

Save official results, certificate PDFs, status, query time, and reproducible URLs. Supplier scans/product pages are leads to check with the issuer. Official websites and manuals may change: follow the issuing body's current official links and record the edition checked.

### WaterMark checks

Record certificate/licence number, current status/expiry, licence holder, exact model ID/name/brand, product type/specification, certification body, history of transfers/reapplications/site changes, and whether manufacturer/site equals the holder. Search by identifiers and product fields rather than brand alone.

Ask the certification body:

1. Is the licence holder also the actual manufacturer?
2. What legal name and address identify the audited manufacturing site?
3. Which forming, machining, assembly, and testing processes occur there for the exact model?
4. Which critical components are purchased externally?
5. Did a certificate change involve manufacturer, site, or design lock?
6. If details are confidential, can it confirm whether the target process occurs at the audited site?

### UL checks

Record UL file number, Category Control Number (CCN), Listed/Classified/Recognized mark type, exact model/nomenclature, standards/ratings/Conditions of Acceptability, manufacturer and authorized inspection site, status, and issue/revision date. Distinguish testing to a UL standard, ANSI/CSA compliance, use of a UL component, and certification of the exact end product. Close a UL certification claim only with an official UL/Product iQ record covering it.

### Scope and receipts

Check WaterMark and UL independently. A different model under one brand, changed rating/size/material, or holder-only record does not close exact product/site/process attribution. Product certification alone does not identify the tooling or upstream component maker. Expired, suspended, revoked, or unknown status goes on `HOLD`.

Even if an official record identifies product/entity/site, process attribution still needs process, site, or audit evidence. Save `queried_at_utc`, query terms/session state, result count, official URL, raw path/hash, status, model/site scope, screenshot, access failures, and next review date. Research authority does not by itself authorize contacting an issuer or supplier.

## 中文

# WaterMark 与 UL 认证穿透

## 官方入口

- WaterMark Product Search：<https://watermark.abcb.gov.au/watermark-search>
- WaterMark Scheme Manual：<https://watermark.abcb.gov.au/sites/default/files/resources/2022/Manual-for-WaterMark-certification-scheme.pdf>
- UL Product iQ 说明：<https://code-authorities.ul.com/about/certifications/>
- UL Product iQ：<https://productiq.ulprospector.com/>

优先保存官方数据库结果、证书 PDF、状态、查询时间和可复查 URL。产品页和供应商证书扫描件只作线索，必须回到签发机构核验。

官网与手册可能更新，沿签发机构当前官方链接查阅，并记录核验版本。研究授权不自动包含对认证机构或供应商发送消息。

## WaterMark 检查项

逐项记录：

- Licence/Certificate Number
- 当前状态及到期日
- Licence Holder
- Model ID、Model Name、Brand
- Product Type 和 Specification
- 认证机构
- 证书历史、转移、重新申请或地点变更
- Manufacturer / Manufacturing Site 是否与持证人一致

WaterMark 搜索页支持按证书号、Model ID、Model Name、Brand、Product Type、Specification 和 Licence Holder 查询。不要只按品牌搜索。

向认证机构询问：

1. 持证人是否同时为实际制造商。
2. 审厂的制造地点名称和完整地址。
3. 精确型号是否在该地点成形、机加工、装配和测试。
4. 哪些部件属于外购 critical components。
5. 证书变更是否涉及 manufacturer、site 或 design lock。
6. 若保密，能否只确认目标工序是否在审厂地点完成。

## UL 检查项

逐项记录：

- UL File Number
- Category Control Number (CCN)
- Listed / Classified / Recognized 等 Mark 类型
- 精确型号或 nomenclature
- 适用标准、额定值和 Conditions of Acceptability
- Manufacturer 名称和工厂/inspection location
- 状态、issue/revision 日期

把“按 UL 标准测试”“符合 ANSI/CSA”“UL component used”与“精确产品拥有 UL Certification”严格分开。只有 Product iQ 或 UL 出具的正式记录才能闭合 UL 认证主张。

## 闭合规则

分别验证 WaterMark 和 UL，不允许证书借用：

- 同品牌不同型号：不闭合。
- 同系列但额定压力、温度、口径或材料不同：不闭合。
- 只有持证人、没有制造地点：只支持持证关系。
- 只有产品认证、没有目标工序：不支持模具或上游零件来源。
- 证书过期、暂停、撤销或状态未知：转 `HOLD`。

若官方证书确实列出产品、法律主体和实际制造地点，可提升工厂归属；若需要证明热锻、深拉、模具或关键部件来源，仍需工艺、现场或审厂证据。

## 回执字段

保存 `queried_at_utc`、查询条件、登录态、结果数量、证书 URL、下载路径、SHA-256、状态、型号范围、地点范围、截图路径、页面不可达原因和下一次复核日期。
