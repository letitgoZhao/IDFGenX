# M0-016 Compiler Stability Design

## 目标

在不扩展 Compiler 支持域的前提下，证明当前受支持的 single 与
perimeter_core 场景在双向格式转换、等价变换和故意破坏下具有可审计行为。

## 测试设计

1. **语义 round-trip**：对一个 single 和一个 perimeter_core Spec，先用
   `compile_scenario` 生成 canonical epJSON/IDF，再用 EnergyPlus
   `ConvertInputFormat -f epjson` 将 IDF 转回 epJSON。两个 epJSON 经
   `canonical_epjson_bytes` 规范化后必须语义相同；原始字节不作为契约，
   因为 EnergyPlus 可自动注入格式字段。原始生成工件仍必须通过真实 V0–V6。
2. **metamorphic**：在允许域内改变一个输入，仅断言该变换应保持或单调变化
   的量：建筑名不改变几何摘要；WWR 提升不减少窗面积且不改变 Zone/Surface
   数；single 的层数从 1 提升到 3 时 Zone/Surface/Window 数线性扩展。
3. **mutation**：篡改已编译 epJSON 文件后，V4 artifact hash 门禁必须失败；
   把窗顶点移出宿主墙平面后，V3 geometry 门禁必须以
   `V3_WINDOW_OUTSIDE_HOST` 失败。任何失败均不得伪装成通过。

## 范围与边界

- 真实 V0–V6 只覆盖 round-trip 的两个代表性场景；低成本 metamorphic/
  mutation 检查复用同一 Compiler、Validator 和 epJSON 解析器。
- 不新建任何 IDF fixture，不提交转换输出。
- 本设计由 ADR-0001 约束：测试工件是审计证据，不能成为 LoRA 训练记录字段。
