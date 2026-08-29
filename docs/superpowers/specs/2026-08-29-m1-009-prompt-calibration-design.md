# M1-009 Prompt 数值、单位与实体反向标定设计

## 1. 目标与范围

M1-009 为项目自身生成的 clean/robust Prompt 建立独立、确定性、可审计的反向标定门禁。标定器从 Prompt 文本提取已声明字段，再与同一记录携带的 `ScenarioSpecDraft` 目标逐字段比较，确保进入后续数据构建的 Prompt 不遗漏、不串位、不泄漏默认值。

本版本只接受当前四个 clean family、M1-008 的 robust 变体元数据和 Draft schema v0.1；不解析任意用户自由文本，不调用 LLM、Resolver 或 Compiler，不创建 release 或直接移动 quarantine 文件。

## 2. 架构与数据流

新增 `idfgenx/data_factory/calibrate.py`，分成三个纯函数边界：

1. `extract` 根据 family、语言、风格、语序和表达变体选择受限语法，提取字段名、原始数值、单位、枚举实体、建筑名称和文本 span；
2. `compare` 将提取值转换为 Draft 原始单位语义，与 `scenario_spec_draft_target` 比较，只允许目标为 `requested` 的字段出现在 Prompt 中；目标为 `defaulted` 的字段若被声明则失败；
3. `report` 返回冻结的 `CalibrationReport`，包含总体状态、字段结果、缺失/重复/未知实体、解析错误、错误码和稳定摘要哈希。

输入支持单条 `CleanPromptRecord`、`RobustPromptRecord` 或可迭代记录。输出只描述结果；上层构建器负责把失败证据写入 `data/quarantine/<build_id>/calibration`。

## 3. 错误与精度

标定 fail-closed，固定错误码为：`missing_requested_field`、`duplicate_field`、`unknown_entity`、`entity_mismatch`、`unit_missing`、`unit_mismatch`、`numeric_mismatch`、`default_leakage`、`syntax_unrecognized` 和 `configuration_error`。

Prompt 数字用 `Decimal` 解析，并与目标 Draft 的实际显示值比较，不使用宽松相对误差。名称采用现有 `validate_prompt_building_name` 的允许字符集并精确匹配；用途、分区等同义表达只通过版本化别名表映射。配置或 Draft schema 不兼容直接产生 `configuration_error`，不混入普通样本失败统计。

## 4. 兼容与版本

`CalibrationReport` 和提取结果使用 Pydantic v2、`extra="forbid"` 和显式协议版本。新增 Prompt family、别名、Draft 字段或语法必须提升校准协议版本并补充测试；禁止静默扩大 v0.1 解析范围。span 仅用于诊断，不作为通过依据。

## 5. 测试门禁

新增 `tests/unit/data_factory/test_calibrate.py`，至少覆盖：

- 四个 clean family 的完整字段提取与通过；
- robust 的 m/ft、degC/degF、两种语序、两种表达和三种噪声；
- 中英文用途、分区、名称、层数、WWR、尺寸和设定温度；
- 缺失、重复、未知实体、单位缺失/错误、数值漂移、默认值泄漏和非法语法；
- Decimal 精度边界、配置哈希/Schema 版本不兼容和报告确定性；
- 192 个显式 robust 组合全部通过，并用文本变异触发对应错误码。

验收运行专项单测、全量 `python -m unittest discover -s tests -v`、`compileall`、`git diff --check` 和敏感文件扫描。M1-009 完成后生成执行报告并更新状态；本任务不生成数据 release。

## 6. 非目标与风险

- 不实现任意自然语言解析、LLM judge 或自动纠错；
- 不改变 Prompt 渲染器、Resolver、Compiler 和 Draft schema 的既有语义；
- 受限语法会随模板演进维护，新增术语必须通过版本化别名和回归测试；
- 数值无法严格往返时宁可拒绝记录，避免静默标签漂移。
