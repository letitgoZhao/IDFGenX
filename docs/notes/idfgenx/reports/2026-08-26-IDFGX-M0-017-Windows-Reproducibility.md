---
report_id: 2026-08-26-IDFGX-M0-017
task_id: IDFGX-M0-017
status: completed
started: 2026-08-26T14:35:00+08:00
finished: 2026-08-26T14:52:18+08:00
executor: Codex
related_commits: []
related_runs: []
---

# IDFGX-M0-017 执行报告：Windows 代表样本 Compiler 工件可复现性验证

## 1. 结果摘要

在 Windows、Python 3.11.15 和 EnergyPlus v23.1 上，对 `single`、
`perimeter_core` 两类代表 `ResolvedScenarioSpec` 分别在两个独立临时目录中
执行 Compiler 与 V0–V6。两类样本的 canonical epJSON SHA-256、normalized IDF
SHA-256 和阶段摘要均完全一致，且所有阶段通过。

| 场景 | canonical epJSON SHA-256 | normalized IDF SHA-256 |
| --- | --- | --- |
| `single` | `2e020cfeb8ffcf87b69fc9aa891eb22038a8791a06f3a481f2f97de947a431e3` | `c53bf598369140635970cf4c35e4fd09a76137aa7714933e8a0c6186fad98647` |
| `perimeter_core` | `d1acf564c46e84d855ac715199d4bc266d0b5cf8d9258f1d0269b90f660fd631` | `08b0d406ba3560c1b4adde5b300ffb7ff8fa55a10922d8c8497582c366849ad1` |

两类场景的阶段摘要均为 `V0,V4,V1,V2,V3,V5,V6 = passed`。

本任务明确不执行 Linux 或跨平台验证。Windows 内的重复性证据不能推出
Windows/Linux 一致性；如未来恢复该范围，必须以独立任务在真实 Linux 环境
重新收集同一协议的证据。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `tests/integration/test_compiler_reproducibility.py` | 新增代表样本的双次独立编译、哈希和 V0–V6 摘要门禁 |
| `docs/notes/idfgenx/tasks/IDFGX-M0-017-Windows-Reproducibility.md` | 记录修改后的任务范围、比较协议和验收项 |
| `docs/notes/idfgenx/STATUS.md` | 记录 M0-017 的 Windows 范围完成状态 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 将 M0-017 更新为 Windows 可复现性验证 |

## 3. 关键实现

- 每次编译使用独立 `TemporaryDirectory`，避免 `ConvertInputFormat` 的固定
  输出文件名让两次运行共享状态。
- 比较工件记录的 `epjson_sha256` 和 `idf_sha256`；两项由原始 canonical
  epJSON 与 normalized IDF 字节计算，任何内容差异都会失败。
- 比较 V0、V4、V1、V2、V3、V5、V6 的阶段名称与状态；成功阶段不含路径型
  finding。唯一允许的运行时差异是临时工作目录绝对路径，它既不进入哈希，
  也不进入成功阶段摘要。
- 不修改 Compiler、Schema、Validator、EnergyPlus 版本或训练数据边界。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| `.\\.venv\\Scripts\\python.exe -m unittest tests.integration.test_compiler_reproducibility -v` | PASS | 2/2；single 和 perimeter_core 均执行两次完整 V0–V6 |
| `.\\.venv\\Scripts\\python.exe -m unittest tests.integration.test_compiler_stability -v` | PASS | 3/3；既有 round-trip、metamorphic 与 mutation 回归 |
| `.\\.venv\\Scripts\\python.exe -m unittest discover -v` | PASS | 81/81，64.495 秒 |
| `.\\.venv\\Scripts\\python.exe -m compileall -q idfgenx tests` | PASS | 退出码 0 |
| `C:\\Users\\LEGION\\.local\\bin\\uv.exe lock --check` | PASS | 50 个包已解析；`uv` 不在 PATH，使用已定位的绝对路径 |
| `git diff --check` | PASS | 退出码 0；仅提示既有 Markdown 的 LF→CRLF 工作副本转换 |

## 5. 数据和兼容性影响

无 Schema、API、数据 release、模型或部署变更。新增测试仅复用既有 Compiler
与 Validator 接口。

## 6. 未完成项与风险

- Linux 与跨平台一致性未验证，且明确不属于本任务范围；不能把本报告用于
  支撑跨平台兼容性声明。
- `uv` 不在 PowerShell PATH；本次使用 `C:\\Users\\LEGION\\.local\\bin\\uv.exe`
  完成锁文件检查。该路径差异不影响项目锁文件本身。

## 7. 后续任务

- `IDFGX-M1-004`：冻结 S1–S5/C1–C5 场景桶和约束。
- `IDFGX-M1-006`：定义 DisclosurePlan 和 Draft 派生规则。
- 未来若恢复跨平台目标：新建独立任务，在真实 Linux v23.1 环境复用本任务
  的工件和阶段比较口径；不得回填为本任务完成证据。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-M0-017-Windows-Reproducibility.md`
- Commit/PR：未创建；遵循未获授权不自动提交的规则。
