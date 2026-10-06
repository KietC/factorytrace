# Browser Access and Evidence Receipts

## English

### Record each action

For searches, opens, clicks, downloads, and failures, record:

- `run_id`, `action_id`, and `query_id`.
- Browser surface/session state, platform, input variant, and exact query.
- Start/end UTC times, requested/final URL, and page title.
- Status: `OPENED`, `RESULT_ONLY`, `DOWNLOADED`, `BLOCKED_POLICY`, `LOGIN_REQUIRED`, `CAPTCHA`, `RATE_LIMITED`, `ERROR`, or `UNVERIFIED`.
- Tool/HTTP status, retry count, and actual failure reason.
- Frozen screenshot/HTML/PDF/HAR/download path, SHA-256, and evidence ID.
- What the page supports and what it cannot establish.

### Truthfulness and downloads

Search results without an opened detail page are `RESULT_ONLY`. An open tab whose contents cannot be verified is `UNVERIFIED`. A tool policy block is `BLOCKED_POLICY`, not a guessed login/CAPTCHA/rate-limit failure. A reseller page establishes a sales display, not factory or certification status. Screenshots lacking URL/time/page identity need a context limitation.

Use ordinary authorized downloads. Preserve raw bytes; save acquisition metadata and hashes separately. Do not publish cookies, tokens, account identifiers, or private session data in reports. HAR/HTML files can contain secrets: inspect and redact a publishable derivative while keeping the original in protected evidence storage. An image upload to a third-party search service is external disclosure; obtain permission for confidential material.

### Retries and evidentiary scope

Bound per-host concurrency and backoff; respect `Retry-After`. Stop automated retries on CAPTCHA, access-control denial, or explicit refusal and switch to normal user interaction/export. A receipt proves what was attempted or observed, not that a publisher's statement is true. Assess publisher identity, original source, date, and source independence separately.

## 中文

# 浏览器访问与证据回执

## 记录每次动作

为搜索、打开、点击、下载和阻断记录：

- `run_id`、`action_id`、`query_id`
- 浏览器表面和登录态
- 引擎/平台、输入变体和准确查询词
- 开始/结束 UTC 时间
- 目标 URL、最终 URL 和页面标题
- 状态：`OPENED`、`RESULT_ONLY`、`DOWNLOADED`、`BLOCKED_POLICY`、`LOGIN_REQUIRED`、`CAPTCHA`、`RATE_LIMITED`、`ERROR`、`UNVERIFIED`
- HTTP/工具状态、重试次数和失败原因
- 截图、HTML、PDF、HAR 或下载文件路径
- SHA-256 和证据 ID
- 页面能支持什么、不能支持什么

## 真实性规则

- 搜索结果可见但未打开详情页：写 `RESULT_ONLY`。
- 标签页已打开但无法读取 DOM：写 `UNVERIFIED`。
- Browser Use 安全策略阻断：写 `BLOCKED_POLICY`，不要改写成登录失败、验证码或限频。
- 页面打开成功但只有转售内容：只支持转售展示，不支持厂家或认证。
- 截图不含地址栏、时间或页面身份时，标记上下文不足。

## 下载

友好下载，遵守页面操作和平台限制。保存原始字节，不重新编码 PDF、图片或 HTML；另存获取元数据和 SHA-256。登录态页面避免把 cookie、token 或个人账户信息写入报告。

HAR/HTML 可能携带密钥或会话信息；原件保存在受保护证据区，公开前另做脱敏副本。图片提交第三方搜索属于对外披露，保密材料须先获得授权。

## 重试

限制每域并发和退避，尊重 `Retry-After`。遇到验证码、访问控制或明确拒绝时停止自动重试，转正常人工浏览或请求用户提供导出文件。

## 证据强度

浏览器回执证明“执行了什么、看到了什么、哪里受阻”，不自动证明页面内容真实。把页面发布者、原始来源、时间和独立性纳入证据评估。
