---
task_id: IDFGX-M1-006
title: DisclosurePlan 与 Draft 派生规则
module: M1
status: done
owner: Codex
created: 2026-08-26
updated: 2026-08-26
depends_on: [IDFGX-M0-001, IDFGX-M0-002]
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-26-IDFGX-M1-006-DisclosurePlan.md
---

# IDFGX-M1-006：DisclosurePlan

定义 Prompt 可披露字段，并从 ResolvedSpec 派生保留 `requested/defaulted` 来源的 Draft；禁止把默认或派生事实伪装成用户请求。

验收：DisclosurePlan 单测通过；无 Schema、Compiler 或数据 release 变更。
