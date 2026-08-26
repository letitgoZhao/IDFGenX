# M1 场景桶与约束配置 v0.1 设计

**目标：** 冻结可由当前 M0 Compiler 生成的 S1–S5 / C1–C5 场景契约，供后续采样、Prompt、标定、数据切分与评估复用。

**架构：** `configs/data/scenario_buckets_v0_1.json` 是人工审阅的声明式事实源；`idfgenx.data_factory.scenarios` 以 Pydantic 将其载入为不可变配置，并验证桶、参数范围、组合约束与训练资格。M1-005 只消费该已验证配置，不重写任何范围或支持域判断。

**技术栈：** Python 3.11、Pydantic v2、JSON、unittest。

## 1. 适用边界

本配置只描述 `ResolvedScenarioSpec v0.1` 已支持的矩形建筑：

- `zone_layout` 只能为 `single` 或 `perimeter_core`；
- `building_use` 只能为 `office`、`residential` 或 `classroom`；
- 长、宽、层高、层数、WWR 和温控必须同时满足 Schema 与配置范围；
- `perimeter_core` 的深度由 Resolver 从最短边派生，配置不允许采样或覆盖该字段；
- 不生成真实 `AirLoopHVAC`、`PlantLoop`、设备拓扑、非矩形体块或复杂屋顶。

非矩形、复杂屋顶、真实 HVAC 和任何未来 Schema 字段以 `unsupported_features`
显式记录；它们不得成为正向 SFT、Golden、Smoke 或 Pilot 样本。

## 2. 配置形状

顶层 JSON 包含：

```json
{
  "config_version": "0.1",
  "supported_schema_version": "0.1",
  "supported_compiler_version": "0.1",
  "training_bucket_ids": ["S1", "S2", "S3", "S4", "S5", "C1", "C2", "C3", "C4"],
  "evaluation_only_bucket_ids": ["C5"],
  "unsupported_features": ["non_rectangular_footprint", "complex_roof", "real_hvac_topology"],
  "buckets": []
}
```

每个 bucket 包含 `id`、`complexity`、`purpose`、`training_eligible`、
`allowed_zone_layouts`、`allowed_building_uses`、`parameter_ranges` 和
`constraints`。范围以 `{ "minimum": number, "maximum": number }` 表达；
`parameter_ranges` 的字段只允许 `length_m`、`width_m`、
`floor_to_floor_height_m`、`stories`、`window_to_wall_ratio`、
`heating_setpoint_c`、`cooling_setpoint_c`。

## 3. 全局数值规则

| 参数 | 现实/训练范围 | C5 Hard/OOD 范围 | Schema 上限 |
| --- | --- | --- | --- |
| 长/宽（m） | 8–60 | 3–120 | (2, 200] |
| 层高（m） | 2.7–4.5 | 2.2–6.0 | (2, 8] |
| 层数 | 1–6 | 1–10 | 1–10 |
| WWR | 0.20–0.60 | 0.10–0.75 | 0.10–0.80 |
| 供暖设定（°C） | 18–22 | 14–25 | 10–26 |
| 制冷设定（°C） | 24–28 | 19–32 | 18–35 |

全局组合不变量：`length_m / width_m` 必须在 `[0.4, 2.5]`（C5 为
`[0.2, 5.0]`）；`heating_setpoint_c < cooling_setpoint_c`；每个 bucket 的
范围必须收敛于其训练或 OOD 全局范围；并且 `perimeter_core` 仅在最短边
至少为 12 m 时允许，以保证 Resolver 派生的四分之一深度保留有效周边 Zone。

## 4. 场景桶

| 桶 | 复杂度 | 定义 | 训练资格 |
| --- | --- | --- | --- |
| S1 | simple | 单层 `single` 基线几何；一次只覆盖尺度和用途的常规组合 | 是 |
| S2 | simple | 多层或 `perimeter_core` 分区；覆盖楼层和热区数量 | 是 |
| S3 | simple | 矩形纵横比、WWR 与分区的围护组合 | 是 |
| S4 | simple | 现有三种 `building_use` 所绑定的固定 M0 模板差异 | 是 |
| S5 | simple | 合法供暖/制冷设定点组合 | 是 |
| C1 | complex | 支持域内的紧凑/狭长矩形与边缘纵横比 | 是 |
| C2 | complex | 2–6 层 `perimeter_core` 的多 Zone/楼板邻接组合 | 是 |
| C3 | complex | 纵横比、WWR、层数和分区的耦合组合 | 是 |
| C4 | complex | 用途、几何、分区和温控至少四个维度同时变化的组合 | 是 |
| C5 | hard_ood | 仍合法但位于 C1–C4 训练范围外的边缘矩形参数 | 否，仅评估 |

S1–S5 与 C1–C4 的独立建筑目标比例是 40% simple、60% complex；C5 不计入
训练样本配额或 SFT record 数。语言及 Prompt 改写在分桶后派生，不能改变
`scenario_bucket` 或创建新的独立建筑事实。

## 5. 组合和拒绝规则

- `single` 不得与 `perimeter_depth_m` 一起出现；
- `perimeter_core` 不得使用小于 12 m 的最短边；
- S1 不允许 `perimeter_core`、超过 2 层或多因素耦合；
- S2 必须包含 `perimeter_core` 或至少 2 层；
- S3 必须改变 WWR 或纵横比，不能退化为 S1 基线；
- S4 必须显式选择一个受支持 `building_use`，但不得假设尚不存在的材料或日程字段；
- S5 必须包含一对合法温控设定；
- C1–C4 各自必须满足表中定义的最少组合维度；
- C5 必须包含至少一个超出训练全局范围、但仍在 Schema 范围内的参数；
- 所有 `unsupported_features` 请求必须被拒绝，不能降级为看似成功的样本。

## 6. 模块接口与验证

新增 `idfgenx.data_factory.scenarios`：

```python
def load_scenario_catalog(path: Path) -> ScenarioCatalog: ...
def validate_bucket_assignment(spec: ResolvedScenarioSpec, bucket: ScenarioBucket) -> None: ...
def scenario_catalog_sha256(catalog: ScenarioCatalog) -> str: ...
```

`ScenarioCatalog` 和 `ScenarioBucket` 为冻结的 Pydantic model；失败使用项目
`ResolutionError` 或新增稳定的 `DataConfigurationError`，并保留 bucket、字段、
实际值与期望范围。配置的规范 JSON 字节哈希将写入未来 build/release manifest。

测试必须证明：十个桶均可载入；每条范围受 Schema 限制；代表 Spec 可通过其
预期桶；非法分区、温控、C5 训练资格、unsupported feature 和范围越界均失败；
等价 JSON 载入后产生稳定哈希。

## 7. 非目标与后续

本任务不采样、不生成 Prompt、不编译数据集、不创建 release，也不实现
DisclosurePlan。M1-005 使用此配置做分层/LHS/Sobol 采样；M1-006 将 Prompt
披露规则与此处的字段能力边界对齐。
