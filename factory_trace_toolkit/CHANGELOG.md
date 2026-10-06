# Changelog

## English

The first public release also canonicalizes trusted OS temporary roots in test fixtures (including the macOS `/var` alias), retains production symlink/junction rejection, and pins current CI actions without leaving checkout credentials behind.

Wheel verification installs pinned pip/setuptools into a disposable build venv before using `--no-build-isolation`; it no longer relies on a backend preinstalled in the caller or CI runner.

Public edition: bilingual entrypoints and comments, explicit non-overwriting Skill installer, reusable source/privacy verifier, MIT licensing with separate third-party notices, commit-pinned manual CI, and open-font OCR reproduction. Historical version headings below describe software evolution, not production cases. Version 2.0.0 introduces separated parties/sites/products/processes/evidence, multi-axis assessment instead of factory odds, ACH and same-source clustering, certificate/site adapters, social links, event chains, and unified reports. Earlier releases add provenance, environment declarations, deterministic image handling and confirmation gates. Preserve version/schema consistency when changing the package; regenerate manifests only after reviewing the actual changes.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

首次公开发布还规范化了测试中的可信系统临时根（包括 macOS 的 `/var` 别名），保留生产代码的软链接/联接拒绝规则，并固定当前 CI 动作提交、不保留检出凭据。

Wheel 验收在使用 `--no-build-isolation` 前，把锁定 pip/setuptools 装入一次性构建 venv，不再依赖调用者或 CI runner 的预装后端。

# Changelog

## 2.0.0 — 2026-08-01

- 完整环境新增固定 revision、SHA-256 校验的英/简中/繁中 Tesseract 数据与真实 OCR 探针，不再把仅有英文语言包写成“OCR完整”。
- 精确依赖锁使用 NumPy 2.4.6，以覆盖 Python 3.11–3.14；2.5.x 不作为 3.11 兼容基线。
- Schema v2：party/site/product/process/claim/evidence/cert/social/event/access/contact 分离，v1只读复制迁移并保留前后哈希。
- 单一“厂家概率”退出公开输出；统一为 S0–S4、分析置信度、ESS、能力适配、认证状态、验证优先级和采购效用。
- 新增ACH H1–H5、同源URL/哈希转载去重、中国内地采购榜硬过滤和报告语义lint。
- 新增WaterMark/UL精确scope与Manufacturer/site硬门槛、社媒绑定链、EPCIS风格事件链。
- 新增sanitary_valve、metal_forming、certified_product三套JSON工艺包及YAML扩展加载。
- 新增MD/JSON/CSV/XLSX/DOCX统一报告、完整CLI、环境能力smoke和正式Agent Skill。
- Python最低版本升至3.11；默认bootstrap安装full栈，核心仍不依赖本地模型、GPU或API Key。

## 1.1.0 — 2026-07-26

- 明确“未记录到模型使用”不等于“证明从未使用”，区分云端助手、外部视觉搜索和本地模型。
- 新增环境/依赖/最低配置、模型运行溯源、Prompt执行协议、来源访问策略和案件数据模型。
- 新增`factorytrace doctor`：环境快照、依赖/编码/磁盘/CPU/RAM检查、并发建议和模型模式声明。
- 新增精确验证约束`constraints-tested.txt`，bootstrap默认使用锁定Pillow版本并检查原生命令退出码。
- 每案新增环境快照、模型日志、执行日志和Cycle状态模板。
- 图片比较auto并发封顶8，显式并发限制到61；网络负参数被拒绝，robots读取加超时，失败`.part`自动清理。
- audit增加candidate/ledger/claim引用完整性、模型声明、日志表头和confirmed字段检查。
- 产品尺寸改为带来源、状态、公差和证据ID的measurement records，避免冲突参数冒充精确事实。
- 验证器增加新增文件、版本一致性、pip check和校验和完整覆盖检查。
- 新增Windows/macOS/Linux × Python 3.11–3.13 CI矩阵定义；本地报告不冒充尚未运行的CI结果。
- 源码便携包默认排除本机环境、验证报告、来源绝对路径和生成的egg-info。

## 1.0.0 — 2026-07-25

- 建立独立跨平台的图片溯源工具包。
- 新增 S/M/L/K/P 主体、地点、SKU和工序隔离。
- 新增并发安全原件摄取、SHA-256、原始来源别名和atomic manifest。
- 新增品牌无关裁片、搜索查询矩阵、礼貌并发URL证据保存和图片初筛。
- 新增基于独立证据簇、反证、hard cap和hard gate的ESS。
- 新增 research/operational/confirmed审计，拒绝手填A/5/5假阳性。
- 新增操作手册、提示词库、照片/视频/文件清单、联网来源、自迭代和三平台说明。
- 增加被反证推翻结论的失效记录规则，保留历史材料但不继续沿用旧结论。
