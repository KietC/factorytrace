# Source access policy

## English

Use only authorized/allowed sources with normal browser interactions for login-bound platforms. Public URL queues must be explicitly inspected; do not expose the downloader to untrusted server-side input. Respect rate limits, robots and access controls. Higher local resources do not justify higher site concurrency. Failed login, CAPTCHA or unavailable DOM means blocked access, not absence of products. Separate public marketing images from supplier-confidential, design-secret, certification-controlled and personal material before external uploads. Download through normal controls where possible and preserve source receipts; do not scrape hidden credentials or migrate browser cookies.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 来源访问、自动化与隐私策略

## 原则

宽带和高核CPU只用于合法的跨来源并行，不用于绕过登录、验证码、速率限制、访问控制或平台条款。

| 来源类型 | 默认方式 | 自动化边界 |
|---|---|---|
| 1688/Alibaba登录态与以图搜货 | 人工浏览器 | 不做未经许可的机器人/系统性抓取；保存单案必要证据 |
| Google Lens/Bing/Yandex/TinEye | 人工浏览器 | 按服务政策上传；敏感图先做授权和脱敏 |
| 明确公开且允许保存的URL | `factorytrace fetch` | 全局并发、单域限流、robots、Retry-After、缓存 |
| 政府/认证公开数据库 | 浏览器或正式API | 遵守查询频率、下载和再发布限制 |
| 付费海关/企业数据库 | 正常账号 | 不共享Cookie/token，不绕过导出额度 |
| 供应商私发文件 | 本地入库 | 未获许可不得上传公共模型/图片搜索 |

## 平台条款入口

- [1688法律声明](https://terms.alicdn.com/legal-agreement/terms/suit_bu1_b2b/suit_bu1_b2b201802011532_36855.html)
- [Alibaba.com平台服务条款](https://terms.alicdn.com/legal-agreement/terms/platform_service/20230224145817207/20230224145817207.html)
- [RFC 9309 Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html)

robots不是访问授权；平台条款、合同、账号权限和适用法律仍优先。

## 公网并发

默认：

```text
global workers = 8–12
per host = 1–2
delay = 1–3 seconds
429/503 = obey Retry-After and back off
```

不要因本机 CPU 核数多就把单站并发提高到几十。反向图片搜索和登录态平台使用正常浏览器；本地脚本主要并行处理已合法保存的文件。

## 上传前决策

```text
是否已经公开？
  是 -> 核对服务条款和来源许可
  否 -> 是否有供应商/权利人上传授权？
         否 -> 只做本地处理
         是 -> 先脱敏，再按最少必要原则上传
```

不得把Cookie、OAuth token、银行账户、个人手机号、未公开图纸或完整审厂保密报告写入URL队列、提示词或便携包。

## 抓取回执

每个URL至少记录：

- 原URL和规范化URL；
- 抓取UTC；
- 状态码、Content-Type、响应大小；
- Retry-After或失败原因；
- 本地文件、SHA-256；
- robots和访问方式；
- 是否需要登录、验证码或人工操作；
- 最后允许重试时间。
