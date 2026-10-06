# Self-iteration and adversarial review

## English

Run bounded Researcher/Skeptic/Reconciler cycles with explicit questions, evidence requirements and stop conditions. Select the next action by expected information gain, not by repeatedly searching an unchanged keyword. Keep a contradiction queue, alternative explanations, source clusters, last verification times and regression cases. Reopen conclusions on certificate/site/product/tooling/batch changes or new adverse evidence. Improve prompts/scripts only after observed failure, add a meaningful regression test, and retain source provenance. Do not save customer data in generic memory or promote a one-case preference into a universal attribution rule. Stop at documented unresolved status when further progress requires unavailable evidence or authority.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 自迭代、自审查和停止条件

## 一、三角色闭环

每个 `Cycle N` 固定包含三个逻辑阶段：

1. **Phase A / Researcher**：新增候选和证据，不给最终厂名。
2. **Phase B / Skeptic**：以第一名错误为假设，找反证和替代解释。
3. **Phase C / Reconciler**：去重、处理冲突、重算多轴评估与ACH、决定下一轮。

三者输出写入不同文件或不同 JSON 字段，避免研究者自己给自己的结论背书。

使用`work/research_round.json`作为当前Cycle状态；其模板来自
`templates/research_round.example.json`。并行泳道不得直接修改canonical候选或证据台账，只有Phase C是单写入者。

## 二、每轮状态

```text
round_id
started_at_utc / completed_at_utc
new_evidence_count
new_independence_groups
new_candidates
contradictions_opened / resolved
queries_attempted / failed
axes_before / axes_after
next_actions
```

新版本字段名使用`cycle_id`；旧案件中的`round_id`只作为迁移别名。

失败查询也保存。下一轮先读失败日志，避免重复访问同一空页、登录墙或失效关键词。

## 三、信息增益排序

下一动作按以下因素排序：

```text
priority =
  distinction_power
  × source_independence
  × target_process_binding
  × exact_sku_binding
  × expected_success
  ÷ (time_cost + money_cost + supplier_friction)
```

通常优先级：

1. 认证机构确认制造地点/是否外购盘体；
2. 目标批次 COO 的 producer；
3. 随机挑战连续深拉视频；
4. 第三方现场审厂；
5. 模具台账、工单和批次闭环；
6. 环评/设备/招聘；
7. 更多相似商品页。

当已有几十个同款商品页时，继续找第几十一个网页的边际价值接近零，应转向现场、认证和批次链。

## 四、冲突处理

不得多数表决。按以下顺序：

1. 保留支持和反证原件；
2. 检查时间、revision、地址和工序是否不同；
3. 判断是否为销售主体与制造主体分离；
4. 判断是否为装配厂与盘体厂分离；
5. 比较直接性、独立性、时间接近度和绑定精度；
6. 设计能区分两个解释的新证据；
7. 无法消除时降级并写“冲突未解决”。

## 五、自动阻断

以下情况禁止生成 confirmed：

- exact site 未绑定；
- exact SKU/revision/batch 未绑定；
- target process 只有装配/包装证据；
- 只有候选方自述；
- 没有两个冻结的独立直接证据簇；
- critical red flag 未解决；
- 本地证据缺失或 SHA-256 不符；
- 旧 CSV 手填 A，但候选 JSON 重算不通过；
- 当前状态与旧报告冲突却没有 superseded 说明。

## 六、反幻觉审查

发布前逐条回答：

- 这是观察事实还是推断？
- 来源是否真的说了这句话？
- 是否把同名公司、简称或地址合并错了？
- 是否把 Licence Holder、brand、shipper 或 seller 当成 manufacturer？
- 是否把 same design family 写成 exact SKU？
- 是否把“当前未发现”写成“不存在”？
- 联系方式是否有来源和最后核验时间？
- 百分比是否被误写成统计概率？
- 第一名如果错误，现有证据还有什么替代解释？

## 七、复查周期

| 项目 | 周期 |
|---|---|
| 链接、商品页、联系方式 | 每次报告前；活跃案件每30天 |
| 工商和关联主体 | 每90天 |
| WaterMark/产品认证 | 每月、下单前、出货前 |
| 第三方验厂报告 | 12个月；重大订单前 |
| 设备和制造地点 | 每12个月 |
| 合同、银行、开票主体 | 每笔订单 |
| 模具指纹 | 新模具、新revision、材料/工艺/地点变化 |
| 工单/QC/包装/物流闭环 | 每个批次 |

立即全面复查：

- 公司名、地址、域名、银行户名变化；
- 证书号、持证人、型号变化；
- 设计、材料、关键部件、工艺或地点变化；
- 包装、激光码、孔位或不可调尺寸变化；
- 供应商承认外包或明确没有关键设备；
- 视频、地图、报告和厂牌互相冲突。

## 八、停止条件

### 暂停候选扩展

- 连续两轮没有新增独立证据簇；
- 新结果只是既有营销图转载；
- 下一步只能由供应商、认证机构或第三方验厂提供。

### 达到采购预筛

- S/M/L/K/P 已分开；
- 没有 critical 红旗；
- 至少一项独立工厂能力证据；
- 风险、缺口和主动验证要求已写入合同/询证。

### 达到 confirmed

- `trace_stage=S4_BATCH_LINKED` 且 `factorytrace audit --stage confirmed` PASS；
- 至少两个独立直接证据簇冻结在本地；
- 精确地点、精确 SKU、目标工序和批次闭环；
- 反方审查无法给出同等解释力的未排除模型。
