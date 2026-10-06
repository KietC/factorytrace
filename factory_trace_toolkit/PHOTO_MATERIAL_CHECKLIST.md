# Photo and material checklist

## English

For initial discovery collect unobstructed front/back/side/top/bottom views, interfaces, removable parts, packaging labels and a ruler/caliper shown in the same plane. Preserve original resolution and metadata; distinguish measurements from guesses based on perspective. Record material grade, thickness, tolerances, revisions and conflicting specifications. For process attribution request identifiable premises, equipment/model/nameplate, tool ID/ownership, raw material/heat or lot, continuous input-process-output video and dated challenge context. For certification request exact model/scope, status and authorized manufacturing-site evidence. For supply-chain closure request orders, batch labels, CoC/CoO, packing/logistics mapping and original test records, with permission and redaction as needed. Missing materials remain explicit gaps; a glossy marketing image never fills them.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 照片、视频和文件采集清单

## 采集等级与能回答的问题

| 等级 | 最少材料 | 允许输出 |
|---|---|---|
| P0 候选发现 | 至少1张未重编码全分辨率原图；原始来源/URL或提供人；已知型号、尺寸或部件边界至少一项 | 只能生成候选和补拍清单 |
| P1 结构比对 | 六面、四个45°、尺标/卡尺、底面孔位、R角、翻边、板厚/重量、拆件和包装批次 | 可判断同设计族、排除明显不符 |
| P2 工序验证 | 准确厂址、随机挑战连续视频、设备/模具铭牌、原料、工单、QC和批次 | 可评估某地点是否执行目标工序 |
| P3 确认闭环 | P2 + 独立审厂/认证/采购/COO/批次文件 + 样品模具指纹或现场监检 | 才有资格进入confirmed审计 |

P0不够时不要停止建案：先冻结现有材料并明确缺口；但不得给出厂家概率或“没有生产”的否定结论。

每案编辑`work/materials_plan.json`后运行：

```bash
factorytrace materials --case-root CASE --stage discovery
factorytrace materials --case-root CASE --stage comparison
factorytrace materials --case-root CASE --stage process
factorytrace materials --case-root CASE --stage confirmed
```

PASS只表示声明的材料齐备且文件存在，不证明文件真实或厂家身份。

### P0接收门槛

- 原图能正常解码，长边建议不少于2000像素；
- 不能只有聊天窗口截图、Word中的缩略图或二次拍屏；
- 必须记录从谁/哪个URL/哪个平台取得以及UTC时间；
- 商标是否与供应商相关必须由操作方明确声明；
- 如果只有压缩图，标记`compressed_copy`并继续索取原件。

### 必须重拍或降级

- 尺标不与产品平面共面；
- 关键孔位、底面、翻边或标签被裁掉；
- 美颜、背景替换、生成式补绘或强降噪改变结构；
- 只有包装/展厅/机器空转；
- 连续生产视频存在跳切，或无法从厂牌走到目标设备和成形件；
- 所谓“当天视频”没有随机挑战码、日期或工单闭环。

## 一、目标样品照片

最低要求使用原始文件，不要只交微信压缩图或截图。

### 整体

- 正上方垂直全景，钢尺与产品同平面。
- 正下方完整底面。
- 前、后、左、右四侧。
- 四个 45° 角。
- 产品与包装、配件的全套合照。

### 模具几何

- 外长、外宽、总高。
- 内槽长、宽、深。
- 四个内外圆角半径。
- 翻边宽度、卷边截面。
- 侧壁斜度、底部过渡半径。
- 两个底孔的直径、中心距、各自到边缘距离。
- 冲孔盖板正反面、孔数、孔径、孔距和排列方向。
- 阀头直径、臂数、臂宽和角度。
- 卡尺、深度尺、厚度规和称重结果同时入镜。

### 工艺微痕

- 底部拉伸流线、褶皱和局部压痕。
- 修边刀痕。
- 冲孔毛刺方向。
- 焊缝、热影响区和夹具定位痕。
- 抛光方向、死角和表面缺陷。
- 激光码、冲压暗记、模具号和批次号。

### 零部件

- 盘体、盖板、阀头、弹簧、止回阀、喷嘴、进水杆、弯头拆分正反面。
- 螺纹规格、密封件、紧固件。
- 配件之间的装配关系。

### 包装

- 外箱六面。
- 箱贴、条码、型号、数量、毛净重、原产地和批次。
- 彩盒、说明书、合格证、保修卡和证书标识。

## 二、拍摄规范

- 使用原相机文件；关闭美颜、滤镜、水印和自动背景替换。
- 尽量使用固定焦距、三脚架、均匀漫反射光和中性背景。
- 参考样品与候选样品使用相同角度、距离、焦距、尺标和光照。
- 尺标必须与测量平面共面，避免透视误差。
- 每组照片拍一张写有案件 ID、日期和随机码的纸。
- 不删除 EXIF；即使 EXIF 缺失也不要重新另存。
- 上传前保留原文件名；通过云盘或邮件传原件。

## 三、工厂连续挑战视频

挑战码在拍摄开始前临时发送：

```text
CASE-YYYYMMDD-随机6位
```

一次连续、不可剪辑地完成：

1. 厂区外部、公司牌和完整门牌；
2. 手写挑战码；
3. 从厂门进入车间；
4. 板材仓库和原料炉批标签；
5. 目标模具上模、下模、铭牌、编号和装机状态；
6. 油压机/冲床铭牌、吨位、序列号；
7. 板材进入设备；
8. 实际深拉/冲压动作；
9. 半成品脱模；
10. 修边和冲孔；
11. 焊接、抛光、装配、测试；
12. 当场测量关键尺寸；
13. 与目标样品并排；
14. 当日工单、批次卡、检验和包装标签。

不能只拍空载机器。保护商业秘密时可以遮住图纸细节，但必须看到不会泄密的模具编号局部、设备铭牌和产品成形闭环。

## 四、主体和收款文件

- 营业执照、统一社会信用代码。
- 国家企业信用信息公示系统当前记录和变更。
- 工厂产权/租赁或委托加工关系。
- 合同、形式发票、增值税发票抬头。
- 对公银行户名和开户证明。
- 官网域名、企业邮箱、名片。
- 销售公司与工厂不一致时的关联关系和责任条款。

## 五、产品、模具和生产文件

- 受控工程图及 revision。
- BOM。
- 模具总装图、编号、资产台账和所有权声明。
- 模具采购合同、发票、试模和验收报告。
- 模具保养、维修和改模记录。
- 生产工单、排期、领料单。
- 首件、巡检、末件、成品放行记录。
- 原料 MTC/炉批；材质争议时使用 XRF，不用磁铁代替。
- 包装规范和标签模板。

## 六、认证和审厂

- 完整证书及所有 schedule/附件，不只首页。
- 型号、scope、标准、有效期。
- 测试报告编号、实验室、样品描述。
- 第三方工厂审核原件和报告日期。
- 被审核法人、准确厂址、设备表、工艺和产品范围。
- 最近年度监督、不符合项和关闭记录。
- 设计、材料、关键部件、制造地点变更记录。

## 七、采购和物流

- PO、商业发票、packing list。
- 原产地证（区分 exporter/producer）。
- 报关单。
- Master B/L、House B/L。
- 箱唛、托盘和集装箱封条。
- 批次号与工单、检验、外箱和物流文件对应关系。

## 八、联系方式证据

电话、邮箱、微信、WhatsApp、LinkedIn、官网逐项记录：

- 信息本身；
- 对应人员和职位；
- 来源 URL；
- 页面/截图本地路径；
- 最后核验 UTC；
- 是否来自官网、平台、名片、邮件签名或第三方转载。

微信“号码未公开”就保持未公开，不猜测、不用手机号自动填充。
