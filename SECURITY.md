# Security and Sensitive-Data Handling

[English](#english) · [中文](#中文)

## English

FactoryTrace is a local, trusted-operator research toolkit. It is **not** an untrusted multi-tenant service, an isolated document sandbox, or a complete network-SSRF defense. Current package series: 2.x. Security fixes should target the current maintained source; older exported copies may not receive fixes automatically.

### Threat boundaries

- Review file and URL inputs before processing. Images, Office files, PDFs, archives, and media may be malicious; keep parsers/system tools updated and use a disposable restricted environment for untrusted material.
- `fetch` restricts input schemes to HTTP(S), uses bounded capture, and respects robots by default, but it must not be exposed as a public URL-fetch endpoint. Do not assume destination addresses/redirects are comprehensively protected against private/local/metadata network targets.
- Do not disable robots checks or bypass login/CAPTCHA to expand a research run. Normal authorized browser access and explicit URL capture are different workflows.
- Platform accounts, browser cookies, API credentials, SSH keys, and cloud model access are outside the toolkit; never embed them in source, fixtures, logs, or inquiry templates.
- Evidence contains claims as well as facts. Reposted media, a certificate holder name, a machine photograph, and a model response do not independently prove exact-source attribution.
- Installers can change system packages/user PATH where documented. Inspect them before execution, especially on shared machines. Prefer the manual separated deployment path when changes need tighter control.

### Keep private data outside Git

Store cases, original photos/documents, contact books, procurement records, certificates containing private fields, session exports, OCR results, environment/verification receipts, and model logs outside this repository. Review output paths before every automated run. A tool may record absolute paths and system information locally; these are not automatically suitable for public sharing.

Use synthetic fixtures or reserved `example` domains for reproduction. Redacting obvious names is not enough if dimensions, unique SKU combinations, certificate numbers, dates, addresses, and media still identify the business. Review linkage and metadata as well as visible text.

### Reporting a vulnerability

If GitHub's private reporting is enabled, open the repository's **Security → Advisories → Report a vulnerability** path and submit a private report: [Security advisories](https://github.com/KietC/factorytrace/security/advisories). Availability depends on repository settings; this document does not claim the feature is enabled. See [GitHub private-reporting guidance](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).

Include affected commit/version, component, impact, a minimal synthetic reproduction, expected/actual result, and proposed mitigation if known. Do not post secrets, real cases, private URLs, or live harmful payloads in public issues. If a private route is unavailable, open only a non-sensitive issue requesting a private reporting channel; do not disclose the exploit or data there. There is no published response-time/SLA promise.

### If sensitive content was published

1. Stop further publication and identify exact exposed files/commits/artifacts privately.
2. Revoke/rotate exposed credentials first; deleting a file does not revoke a key.
3. Restrict access where possible and follow the hosting platform's removal/history-cleanup procedure with repository-owner coordination.
4. Do not assume removing the latest file removes Git history, forks, caches, downloads, or release assets.
5. Notify affected owners through an appropriate private channel and preserve a minimal incident record outside the public repository.
6. Re-scan the staged/released copy, inspect generated artifacts, and fix the publishing workflow before resuming.

### Release review

Review source, documentation, synthetic fixtures, assets, manifests, dependency metadata, Git history, staged paths, and attached releases. Check [public release audit](docs/PUBLIC_RELEASE_AUDIT.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Automated pattern scanning is a safeguard, not proof of zero sensitive data; human contextual review remains necessary.

---

## 中文

FactoryTrace 是可信操作员使用的本地研究工具，**不是**不可信多租户服务、隔离文档沙箱或完整 SSRF 防护。当前包系列 2.x；安全修复针对维护中的源码，旧导出副本不会自动更新。

### 威胁边界

- 处理前审查文件/URL；图片、Office、PDF、压缩包和媒体可能恶意。保持解析器/系统工具更新，陌生材料用可弃的受限环境。
- fetch 只接受 HTTP(S)、有界抓取、默认遵守 robots，但不能公开成任意 URL 抓取接口，不假定目的地址/跳转全面防住内网/本地/metadata。
- 不为扩大调查关闭 robots 或绕登录/验证码；正常授权浏览器和明确 URL 取证不同。
- 平台账号、Cookie、API 凭据、SSH、模型权限不属 toolkit，不嵌源码/测试/log/询问模板。
- 证据含主张与事实；转载、持证人、机器图、模型回答都不能独立证明精确源头。
- 安装器可能改系统包/用户 PATH，执行前看脚本，共用机优先手动分开安装。

### 私有数据不进 Git

案件、原图/文件、联系人、采购记录、有私字段证书、会话导出、OCR、环境/验证回执、模型日志放仓库外；每次自动跑前核对输出路径。工具本地会记路径/系统信息，不自动适合公开。

复现用合成数据/保留示例域名。仅改名字不够，尺寸组合、SKU、证号、日期、地址、图片可能反识别，文字和元数据关联都要审。

### 漏洞报告

若 GitHub 私密报告已启用，用仓库 **Security → Advisories → Report a vulnerability**：[安全公告入口](https://github.com/KietC/factorytrace/security/advisories)。是否可用取决仓库设置，本文不声称已启用，见 [GitHub 官方](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)。

附受影响 commit/版本、组件、影响、最小合成复现、预期/实际、已知修复。公开 issue 不贴密钥、案件、私 URL 或有害 live payload；无私密通道只开无敏感请求渠道的 issue，不披露利用/数据。不承诺响应 SLA。

### 已公开敏感内容

1. 停继续公开，私下确定文件/commit/附件。
2. 先吊销/轮换泄露凭据，删文件不吊销 key。
3. 尽可能限制访问，和 owner 配合按托管平台流程清文件/历史。
4. 删最新文件不代表 Git 历史/fork/cache/download/release 都消失。
5. 私密适当渠道通知受影响方，最小事件记录放公开仓库外。
6. 重查 staged/released 副本和生成附件，修发布流程再继续。

### 发布审查

看源码、文档、合成测试、资源、清单、依赖、历史、stage 和发行附件，参考 [公开发布审计](docs/PUBLIC_RELEASE_AUDIT.md) 与 [第三方声明](THIRD_PARTY_NOTICES.md)。模式扫描只是辅助，不保证零敏感，必须人工上下文复核。
