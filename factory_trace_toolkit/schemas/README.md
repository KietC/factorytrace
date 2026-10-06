# Schema reference

## English

Schemas define structured case/product/candidate/evidence and v2 assessments. Validate canonical records before generating derived reports. IDs must be unique and references must resolve; missing exact site/SKU/process/batch bindings must remain unknown rather than inferred from neighboring fields. JSON Schema checks structure, not whether claims are true. Use factorytrace validate and audit for the additional semantic gates. Synthetic examples demonstrate shape only and must be replaced before a real case.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# Schemas

这些 JSON Schema 用于编辑器提示、外部验证和跨工具交换：

- `case.schema.json`
- `product_profile.schema.json`
- `evidence.schema.json`
- `candidate.schema.json`
- `claim.schema.json`
- `case.v2.schema.json`
- `candidate.v2.schema.json`
- `evidence.v2.schema.json`
- `assessment.v2.schema.json`

`factorytrace validate --case-root CASE` 会校验案件、候选、内嵌Evidence并重新生成/校验Assessment。Schema通过只证明结构一致，不等于证据真实、认证有效或confirmed审计通过。
