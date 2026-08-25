# M0-013/014 Validator 与 20 个 Golden 设计

## 目标与范围

为既有确定性 Compiler 增加独立质量门禁，并冻结 20 个可人工审阅的 MVP Golden。输入固定为
`ResolvedScenarioSpec` 与 `CompilationArtifact`；不改变 Draft、Resolver 或 Compiler 的职责，不实现真实
`AirLoopHVAC`、`PlantLoop`、数据采样或在线 API。

Golden 必须全部通过 V0–V6，其中 V5 强制使用 EnergyPlus v23.1 设计日最小仿真，且 `.err` 中
Severe=0、Fatal=0。

## 设计

新增 `idfgenx.validation`：

```text
CompilationArtifact + ResolvedScenarioSpec + EnergyPlusToolchain
                    |
                    v
           validate_artifact(...)
                    |
                    v
             ValidationReport
```

`ValidationReport`、`StageReport`、`Finding` 均为冻结 dataclass，阶段状态只允许 `passed`、`failed`、
`not_run`。每个 finding 带稳定代码、中文消息和结构化证据；失败不静默修补工件。

Validator 不调用 Compiler 的几何构建函数。它只读取 canonical epJSON/IDF，用独立向量计算检查顶点、面、
开窗和相邻面，因此能发现 Compiler 共享逻辑遗漏的错误。

| 阶段 | 检查 | 失败归类 |
| --- | --- | --- |
| V0 | `ResolvedScenarioSpec`、工件路径和 SHA-256 一致性 | schema |
| V1 | epJSON 版本、受支持对象 allowlist、对象字段结构 | object |
| V2 | Zone、Surface、Construction、Schedule、HVAC/温控引用闭合 | reference |
| V3 | 非退化四边形、法向、窗口在宿主面内、Surface 双向配对 | geometry |
| V4 | epJSON/IDF 均存在且哈希匹配；转换工件契约完整 | conversion |
| V5 | `energyplus.exe -D` 设计日运行、Severe=0、Fatal=0、输出完整 | simulation |
| V6 | Zone 数、面积、体积、WWR、层数与 Spec 一致 | sanity |

V5 在调用方提供的独占目录运行，保留 `.err` 摘要在报告中；无工具链或显式关闭仿真时为 `not_run`，但
Golden 测试不允许 `not_run`。

## Golden 组织

不建立集中 manifest。每个场景为独立文件夹：

```text
tests/golden/compiler/<case-id>/
  spec.json
  expected.json
```

`expected.json` 只保存人工审阅的 Spec、Zone/Surface/Window 数量、面积/体积摘要和 canonical epJSON
SHA-256；IDF 不入库。Golden 测试按目录发现这 20 个夹具，编译、验证并逐项比对期望值。

| 类别 | 数量 | 覆盖 |
| --- | ---: | --- |
| single | 10 | 1/2/3 层、office/residential/classroom、WWR 0.2/0.4/0.6、不同长宽比 |
| perimeter_core | 10 | 1/2 层、三种用途、方形/长方形、WWR 0.2/0.4/0.6 |

## 错误、测试与验收

先为每个阶段写最小失败测试，再实现该阶段。除单元测试外，增加：一项真实 V5 集成测试、20 个 Golden
端到端测试，以及篡改顶点、引用、哈希和 `.err` 的失败回归测试。

验收要求：20/20 Golden 在本机 EnergyPlus v23.1 通过 V0–V6；全量测试、`compileall`、`uv lock --check`
与 `git diff --check` 通过。任何未运行 V5 的 Golden 都不算通过。

## 非目标与风险

本任务不做 100 Golden、跨平台一致性、天气文件全年仿真或生产异步 worker。设计日通过仅说明最小可执行性，
不等同于全年能耗正确性。EnergyPlus 安装路径通过既有 `EPLUS_PATH` 配置取得。
