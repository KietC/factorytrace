# Operations manual

## English

Start with the target process and exact component, not a seller name. Capture dimensions with units, uncertainty and source; preserve original files before transforms. Build product/crop plans, initialize a separate case, declare analysis mode and ingest artifacts. Generate queries and manually inspect image/platform/official sources. Create atomic claims and candidate evidence with all bindings, independent clusters and contrary facts. Compare geometry/material/process, inspect certificate scope, trace social account/site/equipment links and request batch or subcontracting records. Run ledger, validate, assess, hypotheses, report, lint and the appropriate audit. Research and operational outputs remain provisional. Do not send inquiries without task authorization. Reopen conclusions when sites, certificates, BOMs, tooling, batches or sources change. For executable setup and recovery use the root deployment and pitfalls guide.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 源头制造厂追溯操作手册

## -1. 环境预检与模式声明

安装后先冻结运行环境：

```bash
factorytrace doctor \
  --output ./environment.current.json \
  --profile auto \
  --model-mode none \
  --strict
```

模式只能选`none/cloud/local/hybrid`；不是默认猜测。若使用模型，每次调用写入案件
`logs/model_usage_log.csv`。模型输出只能生成候选或审查意见，不能直接进入生产证据。

最低规划配置为4核、8GB RAM、5GB可用空间；推荐8核、16GB、SSD 20GB+。本地模型和GPU不是依赖。详细安装、锁定依赖和三平台差异见
[ENVIRONMENT_AND_DEPENDENCIES.md](ENVIRONMENT_AND_DEPENDENCIES.md)。

## 0. 先定义追溯目标

不要用一句“找真正厂家”开始。先写清：

- 产品：精确 SKU、版本、尺寸、材料、证书号、包装或批次。
- 目标工序：模具设计、模具制造、深拉、冲孔/修边、焊接、抛光、阀头制造、装配、测试、包装中的哪一项。
- 目标输出：候选发现、采购预筛、已核实制造地点，还是已确认目标工序生产厂。
- 截止时间与允许使用的来源：公开网页、已登录平台、供应商提供材料、付费数据库、第三方验厂。

角色编码：

| 代码 | 对象 |
|---|---|
| S | 销售、签约、开票、收款主体 |
| M | 对图纸、BOM、生产和批次放行负责的制造法人 |
| L | 实际制造地点和车间 |
| K | 精确 SKU、revision 和批次 |
| P | 具体制造工序 |

任何结论必须至少写成 `M + L + K + P`，例如：“证据支持 A 公司在 B 地址为 K 型号执行最终装配”，而不是“它就是厂家”。

同时建立“角色—部件—地点/工序”三轴Claim。例如销售整机、装配整机、深拉盘体、制造阀头、持证和模具制造可以是六个不同主体。数据约束见
[CASE_DATA_MODEL.md](CASE_DATA_MODEL.md)。

## 1. 建案与证据冻结

```bash
factorytrace init CASE-NAME --root ./cases --time-zone "Asia/Shanghai"
factorytrace ingest ./source-materials --recursive --case-root ./cases/CASE-NAME --workers 8
```

规则：

1. 原件放 `artifacts/original/`，不重编码、不覆盖。
2. 每个文件记录原始来源、接收时间、传输方式、SHA-256、尺寸和关系说明。
3. 聊天软件压缩图仍可入库，但必须标为“压缩副本”；继续索取相机原图、邮件原附件或云盘原件。
4. 网页截图必须同时保存 URL、页面标题、HTML/PDF、抓取 UTC 时间；只有截图没有 URL 的证据降级。
5. 每个裁剪、遮挡、OCR或标注文件必须能回指原件哈希。

## 2. 建立产品与模具指纹

编辑：

- `work/product_profile.json`
- `work/crop_plan.json`

主指纹分四层：

1. 可调营销属性：颜色、Logo、包装、阀头表面处理。
2. 设计族属性：总尺寸、整体轮廓、盖板形式、阀头臂数。
3. 模具几何：内外 R 角、翻边、卷边截面、侧壁斜度、底部过渡、孔中心坐标。
4. 工艺微痕：拉伸流线、修边刀痕、冲孔毛刺方向、焊缝起止点、夹具定位痕、抛光死角、激光码位置。

```bash
factorytrace variants PRESERVED_IMAGE \
  --case-root CASE \
  --crop-plan CASE/work/crop_plan.json
```

如果商标被声明与供应商无关：

- 原图保持不变；
- 在 crop plan 的 `masks` 中声明商标区域；
- 搜索时同时使用原图、无商标主体和独特部件；
- 商标不得进入厂家评分。

## 3. 并行发现候选

并行任务各写独立泳道目录，最终只允许一个Reconciler合并canonical候选、证据和Claim。提示词必须声明真实可用工具；没有登录浏览器时不得声称已执行1688/Lens。见
[PROMPT_EXECUTION_PROTOCOL.md](PROMPT_EXECUTION_PROTOCOL.md)。

### 3.1 图片搜索泳道

对整图和每个独特裁片分别运行：

- Google Lens：广泛网页、局部框选、文字补充。
- Bing Visual Search：产品页、相似图、Google遗漏页面。
- Yandex：精确副本以及东欧/俄语覆盖。
- TinEye：裁剪、压缩、改色、加水印后的同一营销图。
- 百度识图：中文网页补充。
- 1688、Alibaba、淘宝：平台内候选和别名。

每一轮记录 `engine + input_variant + time + result URL + result type`。结果类型必须区分：

- exact-image：同一图片衍生版本；
- same-object：同一实物的不同角度；
- same-design-family：同一结构族；
- visually-similar：仅视觉相似；
- false-positive。

### 3.2 文本搜索泳道

```bash
factorytrace queries \
  --case-root CASE \
  --pack metal_forming
```

按以下组合扩展：

- 精确型号、证书号、PDF文件名；
- 尺寸 + 品类；
- 两个不可调结构特征；
- 部件 + 工艺 + 厂家；
- 企业别名 + 地址 + 环评/排污/招聘/设备；
- 收货人 + 发货人 + HS 候选 + 月份；
- 图片 CDN 文件名和商品 ID；
- 证书旧号/新号 + model ID。

### 3.3 独立来源泳道

并行核查：

- 工商主体、股东、变更和实际状态；
- 环评、排污、技改、消防、用电、政府检查；
- 专利/外观设计；
- WaterMark或其他认证数据库、CAB/WMCAB；
- 海关、原产地证、采购/批次文件；
- 招聘、设备采购/拍卖和厂房；
- LinkedIn、Facebook、抖音、视频号中的厂牌、设备铭牌和连续工序。

网页和社交资料只能按其能证明的命题计分。Facebook车间视频若无法绑定地址、日期和目标 SKU，仍是供应商控制的营销证据。

## 4. 去重并建立时间线

对每个命中保存：

- 页面 URL、商品 ID、卖家展示名、法定主体；
- 原始图片及 SHA-256、dHash；
- 页面截图/HTML/PDF；
- 当前可见日期、归档首次捕获日期；
- 来源簇 `independence_group`。

时间线解释：

- 最早网页只证明“最晚在该日已公开出现”；
- sitemap `lastmod`、HTTP `Last-Modified`、CDN名均可被重写，只算弱时间信号；
- TinEye “First Found”是爬虫首次看到，不是原始发布日期；
- 同一根新闻稿或供应商资料的二十个转载页面只算一个证据簇。

## 5. 法人与厂址穿透

为每个候选分别填：

1. 店铺/报价主体；
2. 合同和开票主体；
3. 对公收款人；
4. 声称的制造法人；
5. 注册地址；
6. 实际制造地址；
7. 厂牌、楼栋、园区和坐标；
8. 每道工序的执行公司和地点；
9. 精确 SKU 的图纸、BOM、工单和批次；
10. 关联公司、委托加工协议或租赁关系。

“经营范围包含制造”“厂家认证”“有工厂”都是线索。必须继续找能把法人、地址、设备、工序和 SKU 绑在一起的证据。

## 6. 工厂能力核验

盘体开模/深拉厂至少应有合理连续工序：

`板材 → 开料 → 模具/油压深拉 → 修边 → 冲孔 → 焊接/附件 → 抛光 → 清洗 → 装配 → 测试 → 包装`

检查：

- 大吨位油压机、冲床、模具、修边、焊接、抛光设备；
- 设备铭牌、数量、吨位、厂址和报告日期；
- 原料、在制品、工装夹具、量具、首件和批次卡；
- 产能与设备、人数、厂房、交期是否相称；
- 是否只拍展厅、仓库、打包和空载机器；
- 环评/排污工艺与公开视频是否一致。

“没有看到设备”只写成未验证；供应商明确承认没有设备，或现场证据确认不存在，才构成相应工序反证。

## 7. 认证与贸易链穿透

### WaterMark

按顺序核对：

1. licence/certificate number；
2. Approved User；
3. model ID、catalogue number、trade name；
4. integral/critical components；
5. 状态、有效期、Scope of Use；
6. WMCAB；
7. 被审制造地点；
8. 设计、材料、工艺或地点变更。

不要把 Licence Holder 写成实际制造厂。向认证机构问：

```text
Is the Licence Holder also the legal manufacturer?
What legal entity and physical site were assessed for model [MODEL]?
Which site performs tray-body tooling and deep drawing?
Is the tray an externally sourced critical/integral component?
Which site performs final assembly and batch-release testing?
Did certificate [A] → [B] involve a manufacturer, site, design, material or process change?
If the address is confidential, can you confirm only whether the tray is deep-drawn at the audited site?
```

### 采购和物流

优先级：

1. 目标批次生产单、BOM、检验和包装标签；
2. PO、商业发票、packing list、供应商声明；
3. 原产地证中 exporter 与 producer；
4. 报关单、Master/House B/L；
5. 公开舱单或贸易数据库。

提单上的 shipper 可能是贸易商或货代；只能证明运输关系。

## 8. 主动验证

发出当天随机挑战码，要求一次连续、不可剪辑视频：

`厂牌/门牌 → 挑战码 → 进入车间 → 设备铭牌 → 目标模具编号 → 原料 → 实际深拉/冲孔 → 刚下线盘体 → 测量 → 工单/批次 → 包装标签`

挑战码在开始拍摄前临时发送。不能接受：

- 旧视频；
- 多段剪辑；
- 机器空转；
- 只展示同类产品；
- 只有装配/包装却声称证明深拉；
- 无法解释厂牌、营业主体和收款主体差异。

高价值采购应增加第三方现场验厂、受控样品和首单驻厂监检。

## 9. 评分与反证

每家候选建立 `candidates/CAND-xxx.json`。每条证据只支持一个命题，并填写：

- `dimension`
- `stance`
- `strength`
- `source_class`
- `independence_group`
- `entity_bind/site_bind/sku_bind`
- `process`
- URL、本地证据路径和 SHA-256。

```bash
factorytrace validate --case-root CASE
factorytrace assess --case-root CASE
factorytrace hypotheses --case-root CASE
factorytrace ledger --case-root CASE
```

标准输出是多轴评估，不是单一概率：`trace_stage`、`analytic_confidence`、ESS、能力适配、UL/WaterMark状态、验证优先级和采购效用分别计算。重复来源先去重；反证在同维度直接扣分；地域只过滤大陆采购榜，不能提高源头归因。

## 10. 每个Cycle的三阶段自审查

### Phase A：Researcher

只新增候选和证据，不写“已确认”。

### Phase B：Skeptic

假设第一名不是开模厂，主动寻找：

- 贸易公司；
- 关联装配厂；
- 外包深拉厂；
- 借厂/旧视频；
- 图片复用；
- 旧证书、不同 revision；
- 地址和主体错绑；
- 不可调尺寸不一致。

### Phase C：Reconciler

逐条处理冲突，寻找最有区分力的下一项证据，再重算 ESS。无法解释的冲突保留并降级。

## 11. 审计与交付

```bash
factorytrace audit --case-root CASE --stage research
factorytrace audit --case-root CASE --stage operational
factorytrace audit --case-root CASE --stage confirmed
factorytrace report --case-root CASE --format md,json,csv,xlsx,docx
factorytrace lint-report --case-root CASE
```

最终报告每个关键结论必须包含：

- observed fact；
- inference；
- claim/evidence IDs；
- 可点击 URL；
- 本地证据路径；
- 限制和反证；
- last verified UTC；
- 下一项可证伪测试。

推荐结论：

> 已确认其为销售/收款主体。独立资料支持该地点具有不锈钢深拉能力，但尚无直接证据证明目标盘体在此深拉。

禁止结论：

> 有同款图，所以它就是开模厂。

`operational PASS`只表示预处理流水线可运行，不是采购、厂家或证据就绪门槛。只有重新计算得到 `S4_BATCH_LINKED` 且 `confirmed PASS`，才允许使用“已确认目标工序生产厂”，且仍需报告有效期和适用批次。

## 12. 时间预算

| 阶段 | 建议预算 |
|---|---:|
| 原件入库与指纹 | 1–2 小时 |
| 多引擎/平台发现 | 2–8 小时 |
| 法人、厂址、工艺核验 | 1–3 天 |
| 主动询证与样品 | 3–10 天 |
| 高价值第三方验厂 | 下单前 |
