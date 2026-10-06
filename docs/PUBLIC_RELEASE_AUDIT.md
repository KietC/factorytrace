# Public-release review / 公开发布复核

## English

### Scope

This repository is a new, source-only publication. It does not import historical Git commits, case folders, chat exports, production configurations, customer records, supplier contact lists, browser state, mounted-share settings, environment snapshots, or local test receipts. The release working copy is separate from the operational installation.

### De-identification checklist

| Surface | Release rule |
|---|---|
| Code and scripts | No real workspace/user/share paths, internal network addresses, credentials or hard-coded business contacts |
| Documentation | No actual host hardware/OS edition, company/customer profiles, historical attribution conclusions or case-specific IDs |
| JSON/CSV examples and tests | Reserved example domains, fictional entities, synthetic products and non-production fixture values |
| Images | Only synthetic OCR probe PNGs; no real product, label, factory, person or customer image |
| OCR resources | Public upstream language data and open Noto font, pinned origin and hashes, upstream licenses retained |
| Git publication | Fresh history; inspect the staged inventory; exclude environments, caches, build outputs and operational receipts |

Known business/case identifiers were checked in the local review without publishing that private denylist. The generic [public-release verifier](../scripts/verify_public_release.py) checks path/secret patterns, contacts, internal addresses, relative links, fonts and the full source manifest. It is a repeatable guard, not a proof that arbitrary future contributions contain no confidential data. Every contributor must inspect their own additions.

### Verification meaning

The toolkit has deterministic unit tests, Skill preflight tests, installation-helper tests, resource manifests, optional real OCR/metadata/video/Office probes and a hand-triggered multi-platform CI. Runtime receipts remain local because they can disclose host paths. Dependency versions are release declarations; personal hardware settings are not part of reproduction.

Do not confuse a passing release test with a verified manufacturer. Factory confirmation still requires exact product/site/process/batch evidence and independent frozen sources. Hashes preserve bytes, not authenticity of what a document says.

### Known limits

- The URL fetcher is for trusted, inspected public queues. It is not hardened for untrusted server-side URL input or all redirects/private targets.
- Pinned package versions are not wheel hash locks. Actions are pinned to commit SHAs, but packages still require trusted upstream indexes.
- External tools are separate system installations; review installation scripts before opting in. The core does not need these executables.
- A Windows test result does not prove every macOS/Linux/architecture combination. Use the documented target-machine acceptance steps and CI.
- Third-party data/font licenses remain separate from MIT. Read [notices](../THIRD_PARTY_NOTICES.md) before redistribution.

Public publication permits third parties to clone the source. Making a repository private later cannot retract existing copies; therefore all review gates must pass before the first push.

## 中文

### 范围

此仓库是全新历史、仅含源码的公开副本，不导入旧 Git 历史、案件目录、聊天导出、生产配置、客户记录、供应商通讯录、浏览器状态、共享盘配置、环境快照或本机测试回执。发布工作副本与正在使用的安装目录独立。

### 脱敏检查清单

| 部分 | 发布规则 |
|---|---|
| 代码与脚本 | 不含真实工作区/用户/共享路径、内网地址、凭据或硬编码业务联系人 |
| 文档 | 不含宿主真实硬件/系统版本、公司/客户画像、历史归因结论或具体案件号 |
| JSON/CSV 示例与测试 | 使用保留示例域名、虚构主体、合成产品和非生产数据 |
| 图片 | 仅合成 OCR 探针，不含真实产品、标签、厂房、个人或客户照片 |
| OCR 资源 | 公开语言数据及开源 Noto 字体，固定来源与哈希，保留原许可 |
| Git 发布 | 新建历史；检查暂存清单；排除环境、缓存、构建产物和运行回执 |

本地复核检查了已知业务/案件标识，但不会公开该私有禁词表。[公开发布验证器](../scripts/verify_public_release.py) 以通用规则检查路径/凭据、联系方式、内网地址、相对链接、字体与完整源码清单。它是可重复门槛，不是对未来任意贡献“绝无保密数据”的证明；贡献者仍必须逐项检查。

### 如何理解验证

工具包提供确定性单测、Skill 预检、安装器测试、资源哈希、可选真实 OCR/元数据/视频/Office 探针和手动跨平台 CI。本机回执留在仓库之外，因为可能暴露路径。公开依赖版本是发布声明，不包含个人硬件设置。

发布测试通过不代表找到厂家。厂家确认仍须闭合精确产品、场址、工序、批次和独立冻结证据。哈希保证字节一致，不证明文件所说的内容真实。

### 已知限制

- 下载器只接人工复核的可信公开 URL 队列，未覆盖陌生 URL 服务、全部重定向及私网目标风险。
- 包版本锁不等于 wheel 哈希锁。Actions 已固定提交 SHA，包下载仍需可信源。
- 外部引擎属于单独系统安装，选择安装前先检查脚本；核心不需要它们。
- Windows 测试不能代表所有 macOS/Linux/架构组合，要按目标机手册与 CI 验收。
- 第三方数据/字体许可独立于 MIT，重新分发前读 [第三方说明](../THIRD_PARTY_NOTICES.md)。

公开后他人可以克隆源码；后续改为私密也不能收回已有副本，因此必须在第一次推送前完成全部检查。
