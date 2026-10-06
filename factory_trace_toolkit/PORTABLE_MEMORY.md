# Portable rules, not portable case conclusions

## English

Reuse decision rules and failure patterns, never a previous candidate/company conclusion. Keep seller, manufacturer, site, product and process separate. Same-image results discover candidates only; irrelevant brands contribute no manufacturing attribution. Not found does not mean not produced. A certificate holder, exporter or assembler need not own tooling or perform the target process. Preserve originals and trace derivatives. Every contact needs a source and last verification time. Same-source reposts count once. ESS and analytic confidence are not statistically calibrated manufacturer odds. Strong contradictions cap conclusions; keep current status separate from history. No operational host, customer or historical company data belongs in this portable memory.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 可迁移记忆：图片追溯源头厂家

机器可读和分层版本：

- [通用核心规则](memory/CORE_RULES.md)
- [机器可读规则](memory/core_rules.json)
- [失效规则](memory/DEPRECATIONS.md)

本文件只保留通用摘要。具体候选、公司和旧案当前状态不能当成跨案件真值。

## 永久规则

1. **供应商不是一个对象。** 永远拆成销售/合同/收款主体、制造责任法人、制造地点、精确 SKU、具体工序。
2. **开模厂、深拉厂、零部件厂、装配厂可能不同。** “真正厂家”必须先说清追的是哪一道工序。
3. **相同图片只发现候选。** 同款图、最早网页、店铺标题、平台标签、专利和商标都不能单独证明生产。
4. **商标可与供应商无关。** 一旦操作方声明商标无关，商标只能用于追图片传播/贴牌链，厂家归因计零分。
5. **“没找到”不是“没有”。** 官网目录空、站内搜索无结果，只能写“当前未发现公开单品页”；还要查 sitemap、历史索引、平台店铺和归档。
6. **证书持有人不等于制造商。** WaterMark Approved User 可为制造商、装配商、分销商、零售商或进口商。
7. **发货人不等于生产者。** 提单/舱单证明运输关系；优先索取能区分 exporter 与 producer 的原产地证、采购和批次文件。
8. **有设备不等于生产目标 SKU。** 设备必须绑定准确地点、目标工序、目标型号/批次和拍摄时间。
9. **联系方式必须有来源。** 电话、邮箱、微信、WhatsApp、LinkedIn、官网均记录来源 URL、证据文件和最后核验时间；不要把猜测补进报告。
10. **保存原件再处理。** 原始文件不重编码；裁剪、遮挡、OCR、增强和截图全部作为派生物，保留 lineage。
11. **哈希证明文件未变，不证明画面真实。** EXIF、GPS、文件名和 C2PA 也是辅助证据，不代替现场与商业闭环。
12. **同源资料不得重复投票。** 公司官网、Alibaba店铺、Facebook和销售员发来的材料通常属于同一“供应商自述簇”。
13. **概率不得伪精确。** 默认输出 ESS 和置信等级。没有真假历史样本校准时，52%、47%不是统计概率。
14. **反证优先。** 一条强反证不能被十条重复营销图覆盖。记录盗图、地址冲突、设备缺失、SKU几何不符和证书过期。
15. **状态必须可覆盖旧结论。** 每个案件维护 `STATUS.md`、`last_verified_utc` 和被推翻假设；历史报告保留但不得继续作为当前结论。

真实案件材料、候选身份和旧案结论不进入本源码包的可迁移记忆，避免污染新产品调查。
