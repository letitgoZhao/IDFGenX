# IDFGX-M1-007 执行报告：中英文 clean Prompt 模板

## 1. 结果摘要

新增版本化 `prompt config v0.1` 和中文简洁、中文专家、英文简洁、英文专家四个确定性 clean Prompt family。渲染严格经过 `DisclosurePlan → ScenarioSpecDraft → Prompt`，不会从 ResolvedSpec 偷带未披露默认值；输出记录包含目标 Draft、family、语言、风格、Draft/配置版本和配置哈希。任务未引入噪声、反向标定、Canonical Sample 或数据 release。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `configs/prompts/clean_v0_1.json` | 冻结四个 family、Draft 字段顺序与默认完整披露集合 |
| `idfgenx/data_factory/prompts.py` | 新增不可变配置/记录模型、加载与规范哈希、披露计划和四类渲染 |
| `tests/unit/data_factory/test_prompts.py` | 新增配置、字面输出、确定性、披露边界、错误和追溯测试 |
| `docs/notes/idfgenx/tasks/IDFGX-M1-007-中英文CleanPrompt.md` | 记录设计、范围、验证与完成状态 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 将 M1-007 更新为 done |
| `docs/notes/idfgenx/STATUS.md` | 登记完成证据和下一出口 |

## 3. 关键实现

- `PromptConfig` 强制配置版本、Draft 版本、四个 family 的顺序/语言/风格以及完整字段顺序；未知键和非法组合直接以 `ConfigurationError` 失败；
- 规范 JSON SHA-256 为 `9765eb93206945506b54936ac6a246ddc08e27993096605ead8507ff943a1f5b`，不受源 JSON 顶层键顺序影响；
- `render_clean_prompt` 先调用既有 `derive_draft`，renderer 只读取 Draft 中 `requested` 字段；空披露和未知字段均拒绝；
- 建筑名称只允许 Unicode 字母/数字、内部空格、下划线和连字符，并要求至少一个字母或数字，避免引号、换行和分隔符破坏唯一反向解释；
- 数值以稳定 SI 文本输出，中文/英文枚举术语由固定映射控制；未披露字段明确使用系统默认值；
- `CleanPromptRecord` 是冻结 Pydantic 对象，记录 Prompt/Draft/config 的版本和哈希追溯信息。

与计划相比，独立代码审查后新增了名称安全门禁、空披露门禁和 Draft 版本追溯；这些变更收紧了原定的“唯一目标 Draft”不变量，没有扩张到 M1-008/M1-009。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| `uv run python -m unittest tests.unit.data_factory.test_prompts -v` | PASS | 审查前 10/10；审查修复后 `\.venv\Scripts\python.exe` 专项 13/13，0.018 秒 |
| `uv run python -m unittest discover -s tests -v` | PASS | 提交前 115/115，56.504 秒；包含真实转换、100 Golden、稳定性、V0–V6 和最小仿真 |
| `uv run python -m compileall -q idfgenx tests` | PASS | 退出码 0 |
| `git diff --check` | PASS | 退出码 0 |
| 敏感词与占位实现扫描 | PASS | 未发现密钥、`.env`、`TODO`、`FIXME`、`NotImplemented` 或服务日志 `print` |
| 独立只读代码审查与复核 | PASS | 初审 1 Important/2 Minor 均处理；复核无 Critical/Important，结论 Ready to merge: Yes |

TDD 证据：模块缺失、配置缺失、空文本渲染分别产生预期 RED；审查反馈中的特殊名称、空 DisclosurePlan 和 Draft 版本字段也分别先失败后转绿。最终专项 13/13、全量 115/115。

## 5. 数据和兼容性影响

- 新增内部 `prompt config v0.1` 与 `CleanPromptRecord`，没有修改 ScenarioSpec、Resolver、Compiler、Validator 或 HTTP API；
- 未创建 staging、quarantine 或 release，现有数据无迁移要求；
- 后续构建可把 Prompt 配置哈希和 Draft 版本直接写入 Canonical Sample provenance。

## 6. 未完成项与风险

- M1-008 的单位变体、语序变化、专家改写和受控噪声不在本任务范围；
- M1-009 尚需实现实际 Prompt 数值/单位/实体反向标定；本任务只通过显式字段与模板门禁提供可标定基线；
- 建筑名称安全字符集有意窄于全局 ScenarioSpec 字符能力；未来若需要标点名称，应设计可逆转义协议并升级 prompt config，而不是放宽当前门禁；
- Draft 版本错配分支由两个 `Literal["0.1"]` 模型在正常入口静态阻断，未使用 `model_construct` 绕过 Pydantic 制造非法对象测试内部防御分支。

## 7. 后续任务

- `IDFGX-M1-008`：在 clean 基线上增加单位、语序、专家表达和受控噪声；
- `IDFGX-M1-009`：实现 Prompt 数值/单位/实体反向标定；
- `IDFGX-M1-010`：实现 Canonical Sample 与内容哈希对象存储。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-M1-007-中英文CleanPrompt.md`
- Commit/PR：本报告所在提交；未创建 PR
- Dataset/Model/Eval run：无

未 push、未创建 PR、未修改远端资源。
