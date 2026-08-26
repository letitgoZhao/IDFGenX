# IDFGX-M1-005 执行报告

## 实际完成内容

- 新增 `sampling_v0_1.json`，冻结连续/离散字段、默认引擎、40%/60% 训练配额、精度、候选倍率和资源上限；配置可规范哈希；
- 固定直接依赖 `numpy==2.4.6` 与 `scipy==1.17.0`，Python 仍固定为 3.11；
- 新增 LHS/Sobol 单桶采样，连续值按桶范围缩放，层数/布局/用途按合法笛卡尔积分层；
- 新增纵横比、温控顺序、perimeter_core 最短边、Resolved Schema 和桶归属门禁；候选耗尽整批失败并返回结构化拒绝统计；
- 新增稳定建筑名、配置哈希、场景哈希、引擎、seed、尝试次数和拒绝快照等追溯字段；
- 采样配额和拒绝快照在验证后转换为只读 Mapping，拒绝通过嵌套字典绕过 Pydantic `frozen=True` 篡改配置哈希或审计证据；
- 新增训练目录采样，精确执行 40% simple / 60% complex 配额，组内桶数量差不超过 1，并通过 SHA-256 派生子 seed；
- 默认训练接口仅读取 S1–S5/C1–C4；显式 C5 候选必须至少一个字段位于动态训练桶包络外。

## 未完成项

无 M1-005 范围内未完成项。本任务按设计未生成 Prompt、Draft、epJSON、IDF、staging、quarantine 或 release，也未实现去重、切分和训练视图。

## 测试与验证证据

| 命令 | 结果 |
| --- | --- |
| `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample -v` | 16/16 通过，0.046 秒 |
| `.\.venv\Scripts\python.exe -m unittest discover -v` | 102/102 通过，61.224 秒；包含真实 EnergyPlus 转换、100 Golden、稳定性与 V0–V6 |
| `.\.venv\Scripts\python.exe -m compileall -q idfgenx tests` | 退出码 0 |
| `C:\Users\LEGION\.local\bin\uv.exe lock --check` | 退出码 0；51 个包解析一致 |
| `git diff --check` | 退出码 0 |

TDD 证据：配置测试最初 2/2 因模块缺失失败；单桶测试最初 5/5 因接口缺失失败；训练/C5 测试最初 4/4 因训练接口缺失失败。代码审查后的深冻结与完整错误上下文测试最初 3/12 失败，修复后相关 12/12 转绿，最终专项 16/16。

## 风险与限制

- 约束拒绝会削弱接受样本子集的理想低差异性质；固定候选池、尝试次数和拒绝统计使该影响可量化，后续 Smoke 应按桶监控拒绝率；
- 离散组合在无拒绝候选前缀中严格均衡；存在拒绝时不回填原组合，以避免验证结果驱动类别重排，最终接受分布需要数据质量报告继续审计；
- 当前最大候选数为 65,536，单请求超过资源门禁会整体失败；大规模构建应按批次调用，而不是提高进程内单批上限；
- SciPy 1.17.0 是支持 CPython 3.11 Windows x86-64 的固定版本；升级需要独立依赖任务和复现验证。

## 后续工作

下一主任务为 `IDFGX-M1-007`：实现中英文 clean Prompt 模板。`IDFGX-M1-010` 的 Canonical Sample 与内容哈希对象存储依赖也已满足，可在独立任务中开展。

## 相关提交

- `9d71ab4 feat(data): add versioned sampling policy`
- `3cdcfce feat(data): sample scenario buckets with qmc`
- `5304189 feat(data): allocate training and hard ood samples`
- `5f66911 docs(m1): close deterministic sampling task`
- 深冻结审查修复与最终证据由本报告后续所在提交承载。

未 push、未创建 PR、未修改远端资源。
