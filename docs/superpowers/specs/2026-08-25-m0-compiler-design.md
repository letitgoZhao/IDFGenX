# M0 Draft、Resolver 与 Compiler 设计

## 目标

实现 IDFGenX 的确定性主线：`ScenarioSpecDraft → ResolvedScenarioSpec → Resolver → canonical epJSON → EnergyPlus v23.1 IDF → ValidationReport`。本设计覆盖 `IDFGX-M0-001` 至 `IDFGX-M0-013`，不包含 Golden 扩充、数据 release、模型训练和 HTTP API。

## 能力边界

- 输入是结构化 Draft；LLM 只可产生 Draft，不能计算顶点、引用或修补 IDF。
- 支持 SI/英制长度、摄氏/华氏温度、矩形建筑、1–10 层、`single` 与 `perimeter_core` 分区、0.1–0.8 窗墙比、办公/住宅/教室内部负荷、理想负荷空调。
- 输出固定 EnergyPlus v23.1 的 `GlobalGeometryRules`、Zone、详细面、窗、构造、日程、负荷、温控和 `ZoneHVAC:IdealLoadsAirSystem` 对象。
- 永久拒绝真实 `AirLoopHVAC`、`PlantLoop`、设备拓扑、曲面、多建筑园区、未消歧字段和未支持单位。

## 数据流与接口

`schemas/scenario.py` 定义带字段状态和原始单位的 Draft；`schemas/resolved.py` 定义仅含 SI、完整默认值和已确认能力边界的 Compiler 输入。`compiler/resolve.py` 是唯一把 Draft 转为 Resolved 的地方，并将不合法值转为 `ResolutionError`。

`compiler/compile.py` 只接受 `ResolvedScenarioSpec`，调用命名、几何、开窗、模板和 epJSON 序列化模块生成 canonical epJSON。`toolchain.py` 使用每次独立工作目录调用 v23.1 ConvertInputFormat；`validation/` 按 V0–V6 输出结构化报告。每层均用项目错误码表达失败，绝不静默回退。

## 几何与对象约定

坐标为右手系米单位：x 为建筑长度，y 为宽度，z 向上；每个 Zone 使用绝对坐标。详细表面顶点以从外侧观察的逆时针顺序生成，楼板法向向下、屋顶法向向上、墙体法向朝外。相邻 Zone 的公共面使用同一组顶点反向顺序，并彼此声明 `Surface` 边界。

外窗在四面外墙的局部坐标系中居中放置，窗高由目标 WWR 和墙面积推导，且保留 0.2 m 边界；当 WWR 会导致不可放置窗时 Resolver 拒绝输入。构造、日程与负荷对象由受控内置模板生成，不把官方快照文件直接拼入最终 IDF。

## 验证与错误

V0 验证模型；V1 检查只生成 allowlist 对象；V2 检查对象引用闭合；V3 检查顶点、法向、面积、窗包含和邻接；V4 检查转换命令和 IDF 产物；V5 对可用天气文件运行最小设计日仿真；V6 将 Zone 数、面积和体积与 ResolvedSpec 比较。没有天气文件时 V5 明确标为 `not_run`，而不是伪造通过。

每个公共模型和函数使用中文 docstring、类型标注与稳定错误码。转换使用独占临时目录、超时和 stdout/stderr 保留；任何失败保留 cause 与上下文。

## 测试策略

所有功能先写 unittest 失败用例。单元测试覆盖状态语义、单位换算、默认值、边界拒绝、命名、顶点/邻接、窗包含、引用闭合和 deterministic epJSON。集成测试使用本机 v23.1 进行 epJSON→IDF 转换；若本机 EnergyPlus 可用，再运行一个最小设计日仿真。Golden 与 100 样本扩展仍属于 M0-014/015，未纳入本轮。
