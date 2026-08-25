---
task_id: IDFGX-M0-013-014
date: 2026-08-25
status: done
commits:
  - 41d07bc
  - fd21f54
  - 5121fe5
  - a071d76
---

# M0-013/014 Validator 与 20 Golden 执行报告

## 实际完成内容

- 新增独立 `idfgenx.validation`：V0 输入契约、V1 对象 allowlist、V2 引用闭合、V3 几何、V4 工件哈希、V5 EnergyPlus v23.1 设计日、V6 场景摘要。
- V5 在调用方独占目录执行 `energyplus.exe --design-day`，强制 `.err` 中 Severe=0、Fatal=0。
- Compiler 注入最小 `Site:Location` 和夏/冬设计日；跨层内部面使用对称 `Internal Construction`，修复 EnergyPlus 的 interzone 构造反向层错误。
- 冻结 20 个独立 Golden：10 single、10 perimeter_core；每项保留 `spec.json` 与包含 canonical epJSON SHA-256、Zone/Surface/Window 数量的 `expected.json`，不提交 IDF。

## 验证证据

| 命令 | 结果 |
| --- | --- |
| `python -m unittest discover -v` | 76/76 通过；包含 20/20 V0–V6 + 真实设计日 Golden |
| `python -m compileall -q idfgenx tests` | 通过 |
| `uv lock --check` | 通过 |
| `git diff --check` | 通过 |

## 未完成项与风险

- 本任务范围内无未完成项。
- V5 仅为设计日可执行性门禁，不代表全年天气文件能耗校准；全年仿真属于后续任务。
- Golden 的 hash 是 Compiler v0.1 输出契约的一部分，后续有意修改模板或 canonical 序列化时必须人工复核后更新。

## 后续工作

- M0-015 扩展至 100 个 Golden，随后执行 M0-016 的 round-trip、metamorphic 与 mutation 测试。

## 相关提交

- `41d07bc`、`fd21f54`、`5121fe5`、`a071d76`，以及本报告所在分支的当前 HEAD（Golden 收尾提交）。
