# Method sources and historical research notes

## English

This is a dated method-reference inventory, not a current validation of every linked service or certificate rule. Open current primary sources before each investigation and record access limits. Reverse-image services answer different questions: transformed copies, similar objects, text in pictures and platform products. Earliest crawl is not authorship. Corporate records, certification sites, process evidence, customs/origin documents and social history support different claims. Do not combine them without exact entity/site/product binding. Local CV matches are triage signals, not same-tooling proof. Respect browser login, platform limits and robots policies; do not circumvent access blocks. Current README-format research is in the root docs directory; it does not imply that highly starred projects endorse this toolkit.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 联网研究更新（2026-07-25）

本文件保存方法来源和本轮得到的新改进。网页会变化，实际案件出报告前应重新访问并保存页面原件。

## 一、反向图片搜索的正确分工

| 来源 | 可用能力 | 不能证明 |
|---|---|---|
| [Google Lens官方帮助](https://support.google.com/websearch/answer/1325808?hl=en) | 上传图片或局部区域，寻找相关图片、对象和使用该图的网页 | 结果排序不是图片原创或制造证明 |
| [Google Lens工作方式](https://lens.google/howlensworks/) | 识别对象、文字、产品及视觉相似内容 | 视觉相似不等于同一SKU/模具 |
| [Bing Visual Search官方帮助](https://support.microsoft.com/en-US/bing/using-bing-visual-search) | 用图片搜索网页、相关图片和产品 | AI结果可能错误；需打开原网页核验 |
| [Yandex图片搜索说明](https://yandex.com/support/browser/en/search-and-browse/search-image) | 用图片或局部对象搜索相似页面，补充地域索引 | 受索引覆盖限制 |
| [TinEye工作方式](https://help.tineye.com/article/233-how-does-tineye-work) | 擅长识别同一图片的裁剪、缩放、改色和加水印版本 | 不擅长把不同角度实物自动认成同一产品 |
| [TinEye First Found解释](https://help.tineye.com/article/248-what-does-tineye-first-found-on-mean) | 给出TinEye首次抓到该图的时间线线索 | 不是图片首次发布或原创日期 |
| [百度图像搜索API](https://ai.baidu.com/ai-doc/index/IMAGESEARCH) | 对指定图库建库和相似搜索 | 不是完整公共互联网反向搜索API |
| [Alibaba图片搜索入口](https://www.alibaba.com/search/page?SearchScene=preImageTextSearch) | 平台内发现相同/相似商品和供应商 | 店铺可能是工厂、贸易商或分销商 |
| [阿里云Image Search场景](https://www.alibabacloud.com/help/en/image-search/product-overview/scenarios) | 解释以图搜商品/图库的典型用途 | 只解决视觉检索，不验证制造关系 |

改进：

1. 把“同一图片衍生版本”和“同一实物不同角度”分开记录。
2. 以底面孔位、R角/翻边、盖板、阀头等不可调特征裁片搜索。
3. 商标无关时生成有 lineage 的中性遮挡副本；商标命中只进入传播链。
4. 二十家店复制一张图只算一个图片簇。

## 二、时间线、域名和证据保全

- [Internet Archive保存网页说明](https://archivesupport.zendesk.com/hc/en-us/articles/360001513491-Save-Pages-in-the-Wayback-Machine)：发现关键公开页后立即请求归档，同时保存本地副本。
- [Common Crawl Index Server](https://index.commoncrawl.org/) 和 [URL Index说明](https://commoncrawl.org/url-index)：可查历史抓取记录和WARC位置。
- [Common Crawl FAQ](https://commoncrawl.org/faq)：公共基础设施应礼貌、低速使用；不要因本机带宽大就对同一服务高并发。
- [ICANN RDAP](https://www.icann.org/rdap/)：RDAP是WHOIS的标准化替代，可查当前域名注册数据；隐私代理和数据遮挡仍会限制归因。
- [ExifTool官方文档](https://www.exiftool.org/ExifTool.html)：ExifTool能读取也能写入元数据，因此EXIF时间/GPS只作辅助。
- [C2PA 2.2规范](https://spec.c2pa.org/specifications/specifications/2.2/specs/C2PA_Specification.html)：Content Credentials能记录带签名的来源链，但来源链本身不证明画面叙述真实。

判断规则：

- SHA-256相同只证明文件字节相同；
- 感知hash接近只证明可能为同一图片变体；
- 网页最早归档只证明“最晚在该日已出现”；
- sitemap `lastmod`、HTTP `Last-Modified`、CDN文件名均为弱时间信号；
- 每个页面必须保存URL、UTC、HTML/PDF/图片、截图和哈希。

## 三、企业、工厂与知识产权

- [国家企业信用信息公示系统](https://www.gsxt.gov.cn/)：核对法定名称、统一社会信用代码、状态、地址、股东和变更。“经营范围含制造”仍只是弱证据。
- [国家市场监督管理总局](https://www.samr.gov.cn/)：官方入口和监管资料。
- [国家知识产权局公共服务平台](https://ggfw.cnipa.gov.cn/homeindex)：可按申请人、产品名、图像等检索专利/外观设计；专利权人可能委外生产。
- [海关政务服务](https://online.customs.gov.cn/)：包含企业信息公示和海关统计入口。
- [生态环境部环境影响评价入口](https://www.mee.gov.cn/ywgz/hjyxpj/) 与 [全国排污许可证公开平台](https://permit.mee.gov.cn/)：地方环评/排污资料可能出现准确厂址、设备数量、工艺、原料和产能。
- [Alibaba Verified Supplier说明/免责声明](https://activity.alibaba.com/page/verifiedsuppliers.html)：应下载完整assessment report并核对被审法人、厂址、business type、设备、工艺、产品和日期；平台/第三方评估不替代目标SKU现场证据。

环评、招聘、设备采购和政府文件能证明“某地址可能具备工艺能力”，但仍必须用目标 SKU 工单、挑战视频、批次文件或独立审厂把产品绑到该地点。

## 四、WaterMark穿透

关键官方事实：

1. [Approved Users / Licensees说明](https://watermark.abcb.gov.au/certification/approved-users-or-watermark-licensees)明确：WaterMark许可协议可与 manufacturer、assembler、distributor、retailer 或 importer 签订。因此 Licence Holder 不能自动当制造厂。
2. [WaterMark Scheme Manual](https://watermark.abcb.gov.au/sites/default/files/resources/2022/Manual-for-WaterMark-certification-scheme.pdf)规定型式测试、质量管理、制造地点评估、年度符合性监督和变化控制；认证机构掌握比公开证书更深的制造地点资料。
3. [ABCB WaterMark说明](https://www.abcb.gov.au/faq/watermark)说明产品须经认可实验室测试、符合规范并按批准质量体系制造；证书应从相应WMCAB获取。
4. [WaterMark产品数据库](https://ncc.abcb.gov.au/watermark-search)可按证书号、model ID、brand、产品类型和Licence Holder查询，但公开字段不必然给出外协盘体厂。
5. [ABCB WaterMark教程](https://www.abcb.gov.au/resources/videos/ncc-tutor-lesson-understanding-watermark)说明年度监督和设计/制造变化时的再评估。
6. [Global-Mark产品符合性](https://www.global-mark.com.au/product-conformance/)说明持续工厂监督用于监控制造和设计变化；[官方联系方式](https://www.global-mark.com.au/contact/)为进一步询证入口。

新做法不是只问“谁生产”，而是逐工序问：

- 持证人是否也是法定制造商；
- 哪个法人、哪个物理地址被审；
- 哪个地址执行盘体开模/深拉；
- 盘体是否为外购critical/integral component；
- 哪个地点最终装配和batch release；
- 换证是否涉及主体、地点、设计、材料或工艺变化。

## 五、贸易文件的更强入口

[澳大利亚政府 ChAFTA 使用指南及原产地证模板](https://www.dfat.gov.au/sites/default/files/guide-to-using-chafta-to-export-and-import-goods.pdf)把 exporter 与 producer 的名称/地址分开填写（producer在已知时填写）。

因此针对中国→澳大利亚链条，优先向买方索取目标批次的：

- Certificate of Origin；
- 商业发票；
- packing list；
- supplier declaration；
- PO和批次/箱贴。

它们比公开舱单更有机会暴露 exporter 与 producer 是否不同。公开提单或贸易数据库只证明某段运输关系，shipper可能是贸易商或货代。

## 六、实物与模具指纹的限制

- [NIST Surface Texture and Forensic Topography](https://www.nist.gov/programs-projects/surface-texture-and-forensic-topography)支持使用表面拓扑、客观相似度和不确定性研究toolmark，但同一工具会产生变化，不同工具也可能相似。
- [NIST IR 8387](https://nvlpubs.nist.gov/nistpubs/ir/2022/NIST.IR.8387.pdf)提供数字证据保全和哈希相关基础。
- [SWGDE图像认证最佳实践](https://www.swgde.org/documents/published-complete-listing/18-i-001-best-practices-for-image-authentication/)说明元数据、压缩和处理历史的限制。

因此：

- 网页JPG只能做候选筛选；
- 宏观尺寸吻合最多支持“同设计族”；
- 同模判断要统一角度、焦距、尺度、光照和基准面；
- 优先比较不可调孔位、R角、翻边截面和表面拓扑；
- 有条件时使用3D表面测量；
- 输出必须包含不确定性，不能把人工叠图冒充司法级鉴定。

## 七、本轮最有效的流程升级

旧路线：

`同款图 → 候选网站 → 人工百分比`

升级路线：

`原件保全 → 多裁片/多引擎 → 图片簇去重与时间线 → S/M/L/K/P实体图 → 政府文件确认工艺能力 → 认证机构确认制造地点 → COO/采购绑定批次 → 随机连续生产视频 → 实物模具指纹 → 反方审查 → confirmed审计`

关键变化：

- 从“公司级厂家”升级为“工序级厂家”；
- 从来源数量升级为独立证据簇；
- 从人工概率升级为有硬封顶的ESS；
- 从只找支持证据升级为主动找反证；
- 从静态报告升级为可复查、可覆盖旧结论的案件状态。

## 八、2026-07-26补充核对

### 8.1 外部图片搜索不是本地模型

- [Bing Visual Search官方帮助](https://support.microsoft.com/en-US/bing/using-bing-visual-search)说明图片会提交给Bing完成视觉搜索。这属于外部服务处理，不等于本机运行模型。
- [TinEye How it works](https://www.tineye.com/how)说明其上传图片不会保存或加入索引；这仍不取消上传前的权利和保密审查。
- [Google Lens搜索帮助](https://support.google.com/websearch/answer/1325808)允许在图片搜索后增加文字限定，适合“局部结构裁片+尺寸/工艺词”组合。
- [Google About this image](https://support.google.com/websearch/answer/14177408)可提供图片早期使用和元数据线索，但Google也提醒元数据可被添加或删除。

因此环境日志把`model-mode`与`external_visual_search_services`分开。无论服务后端是否使用AI，结果仍只用于发现候选。

### 8.2 可选确定性CV

[OpenCV局部特征与Homography教程](https://docs.opencv.org/4.9.0/d1/de0/tutorial_py_feature_homography.html)
展示了在裁剪、尺度和透视变化下做特征匹配的标准方法。它可作为Pillow初筛之后的可选增强，但匹配分数仍不证明同模或同厂；必须保存参数、inlier、变换和失败样本。

### 8.3 C2PA与来源链

- [c2patool CLI使用说明](https://github.com/contentauth/c2pa-rs/blob/main/cli/docs/usage.md)提供跨平台Content Credentials检查工具；
- [C2PA Explainer](https://c2pa.org/specifications/specifications/2.2/explainer/Explainer.html)说明签名来源链解决的是内容来源和编辑声明，不保证画面中的商业陈述为真。

### 8.4 平台自动化限制

- [1688法律声明](https://terms.alicdn.com/legal-agreement/terms/suit_bu1_b2b/suit_bu1_b2b201802011532_36855.html)
- [Alibaba.com平台服务条款](https://terms.alicdn.com/legal-agreement/terms/platform_service/20230224145817207/20230224145817207.html)
- [RFC 9309 Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html)

流程据此收紧为：1688/Alibaba登录态、图片搜索和验证码页面只走正常人工浏览器；脚本仅处理用户合法保存的本地材料、明确允许访问的公开URL、正式API或书面许可范围。

### 8.5 制造地点年度监督

[WaterMark Lead Free制造地点年度工厂检查文件](https://ncc.abcb.gov.au/sites/default/files/resources/2023/2022-4.0-NoD-Annual-factory-inspections.pdf)
进一步支持按每个制造地点询问审核和监督记录。仍需区分整机最终装配地点、盘体深拉地点、阀头/止回阀供应商和模具制造地点。

### 8.6 三轴Claim升级

新流程不再只问“哪家公司概率最高”，而是分别建Claim：

```text
角色：seller/exporter/licence holder/assembler/component maker/tooling maker
× 部件：整机/盘体/盖板/阀头/止回阀/模具
× 地点与工序：site + tooling/deep_draw/punching/welding/assembly/test
```

这能直接阻断“贸易商有同款图，所以是开模厂”和“持证人等于每个部件制造厂”的错误捷径。
