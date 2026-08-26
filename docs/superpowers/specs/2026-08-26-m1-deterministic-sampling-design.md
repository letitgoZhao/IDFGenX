# M1 确定性分层与 QMC 采样设计

**目标：** 为 M1 数据工厂提供可审计、可复现的离散分层与 LHS/Sobol 连续采样，输出满足当前场景桶、Schema 和 Compiler 能力边界的 `ResolvedScenarioSpec`。

**架构：** `configs/data/scenario_buckets_v0_1.json` 继续作为参数范围和支持域事实源；新增的 `configs/data/sampling_v0_1.json` 只描述采样策略和配额。`idfgenx.data_factory.sample` 使用 SciPy QMC 产生连续候选、使用局部 NumPy 随机生成器安排离散层，并在返回前通过现有场景桶校验和本模块组合门禁。

**技术栈：** Python 3.11、Pydantic v2、NumPy、SciPy `scipy.stats.qmc`、unittest。

## 1. 任务边界

本任务实现：

- S1–S5/C1–C5 单桶采样；
- S1–S5/C1–C4 训练目录批量采样；
- `LatinHypercube` 与 `Sobol` 两种连续采样引擎；
- `stories`、`zone_layout`、`building_use` 的确定性离散分层；
- 训练 simple/complex 独立建筑数量的 40%/60% 配额；
- 随机种子、尝试次数、拒绝原因和配置哈希等追溯元数据。

本任务不生成 Prompt，不调用 Compiler，不生成 epJSON/IDF，不执行 EnergyPlus，不建立 staging/quarantine/release，不切分数据集。候选失败只在返回记录和结构化异常中统计；把失败材料写入 quarantine 属于 M1-010/M1-013 的构建流程职责。

## 2. 依赖和事实源

- `ScenarioCatalog` 和 `ScenarioBucket` 决定桶 ID、训练资格、允许的布局/用途和字段范围；采样器不得复制或扩大这些范围。
- `ResolvedScenarioSpec v0.1` 决定最终 Schema 上下限和交叉字段约束。
- `perimeter_depth_m` 不参与采样。`perimeter_core` 候选按 Resolver 现有规则派生为 `min(length_m, width_m) / 4`；`single` 候选固定为 `None`。
- SciPy 是直接运行时依赖并固定精确版本；不能依赖当前由其他包间接安装的 NumPy。
- 所有伪随机状态必须来自请求 seed 创建的局部生成器，禁止读取或修改 NumPy 全局随机状态。

## 3. 采样配置

新增 `configs/data/sampling_v0_1.json`，其顶层字段为：

```json
{
  "config_version": "0.1",
  "scenario_catalog_version": "0.1",
  "default_engine": "latin_hypercube",
  "continuous_fields": [
    "length_m",
    "width_m",
    "floor_to_floor_height_m",
    "window_to_wall_ratio",
    "heating_setpoint_c",
    "cooling_setpoint_c"
  ],
  "discrete_fields": ["stories", "zone_layout", "building_use"],
  "training_complexity_shares": {"simple": 0.4, "complex": 0.6},
  "continuous_precision": 6,
  "candidate_multiplier": 8,
  "maximum_candidate_count": 65536
}
```

约束如下：

- 连续字段必须恰好覆盖 `ScenarioBucket.ranges` 中除 `stories` 外的六个字段；
- 离散字段集合固定为上述三个字段；
- simple/complex 占比之和必须为 1；
- 精度为 0–12 位小数；
- 候选倍率至少为 2；最大候选数不得小于候选倍率；
- 配置声明的场景目录版本必须与实际目录一致。

`sampling_config_sha256()` 对 Pydantic 规范 JSON 计算稳定 SHA-256，未来写入 build/release manifest。

## 4. 公共模型和接口

`idfgenx.data_factory.sample` 公开以下不可变模型：

```python
class SamplingEngine(StrEnum):
    LATIN_HYPERCUBE = "latin_hypercube"
    SOBOL = "sobol"


class SamplingDistribution(StrEnum):
    REALISTIC = "realistic"
    HARD_OOD = "hard_ood"


class SamplingRecord(BaseModel):
    sample_index: int
    bucket_id: str
    engine: SamplingEngine
    distribution: SamplingDistribution
    seed: int
    attempt_count: int
    rejection_counts: dict[str, int]
    scenario_catalog_sha256: str
    sampling_config_sha256: str
    spec: ResolvedScenarioSpec
```

`attempt_count` 是从当前请求开始至接受该记录所检查的累计候选数；`rejection_counts` 是同一时点各稳定拒绝原因的累计计数快照。这样每条记录可以独立解释此前消耗的候选，同时批次最后一条记录给出完整构建统计。

公共函数为：

```python
def load_sampling_config(path: Path) -> SamplingConfig: ...

def sampling_config_sha256(config: SamplingConfig) -> str: ...

def sample_bucket(
    catalog: ScenarioCatalog,
    config: SamplingConfig,
    bucket_id: str,
    count: int,
    *,
    seed: int,
    engine: SamplingEngine | None = None,
) -> tuple[SamplingRecord, ...]: ...

def sample_training_catalog(
    catalog: ScenarioCatalog,
    config: SamplingConfig,
    count: int,
    *,
    seed: int,
    engine: SamplingEngine | None = None,
) -> tuple[SamplingRecord, ...]: ...
```

`count` 必须为正整数，`seed` 必须在 `[0, 2**32 - 1]`。未知桶、版本不匹配、非法参数或候选池耗尽均抛出 `ConfigurationError`，并在 context 中保留字段、桶、请求数量、seed、尝试数和拒绝统计。

## 5. 连续采样

QMC 在六维单位超立方体生成点，然后按目标桶的闭区间线性缩放。结果按配置精度舍入，并再次夹取到声明范围，避免二进制浮点舍入产生微小越界。

- LHS 使用 `qmc.LatinHypercube(d=6, scramble=True, seed=seed)`。
- Sobol 使用 `qmc.Sobol(d=6, scramble=True, seed=seed)`，候选池大小取不小于 `count * candidate_multiplier` 的最小二次幂，通过 `random_base2()` 一次生成。
- LHS 同样一次生成确定大小的候选池；不在拒绝后重新初始化引擎，防止重复 strata。
- 候选池不得超过 `maximum_candidate_count`。若候选不足，采样整体失败，不返回不完整批次。

供暖和制冷分别缩放后必须满足 `heating_setpoint_c < cooling_setpoint_c`；不通过时记录 `setpoint_order` 并拒绝，不交换两个值，因为交换会改变 QMC 各维语义。

## 6. 离散分层

每个候选索引对应一个离散组合。模块先构造目标桶允许的笛卡尔积：

```text
stories 范围内的每个整数
× bucket.layouts
× bucket.uses
```

组合列表使用从请求 seed 派生的局部 NumPy `Generator` 做确定性排列，随后循环使用。任意前缀中各合法组合的出现次数差不超过 1；拒绝连续候选时该候选对应的离散组合也被消耗，避免按验证结果选择性重排类别。

输出 `building_name` 使用稳定格式 `IDFGenX-{bucket_id}-{seed:010d}-{sample_index:06d}`，不引入时间戳、UUID 或进程状态。

## 7. 组合门禁和拒绝原因

每个候选依次通过：

1. 长宽比门禁：训练桶为 `[0.4, 2.5]`，C5 为 `[0.2, 5.0]`；
2. 温控顺序门禁；
3. `perimeter_core` 最短边至少 12 m；
4. `ResolvedScenarioSpec` 构造；
5. `validate_bucket_assignment()`；
6. C5 OOD 门禁。

稳定拒绝原因至少包含：

- `aspect_ratio`；
- `setpoint_order`；
- `perimeter_core_minimum`；
- `resolved_schema`；
- `bucket_assignment`；
- `c5_not_outside_training_envelope`。

C5 的训练包络从所有 `training_bucket_ids` 的对应数值范围并集计算，并同时纳入训练桶允许的布局、用途和层数。C5 候选必须至少一个数值或离散字段位于该包络外；仅仅属于 C5 桶但所有值都落在训练包络内不能成为 Hard/OOD 记录。

## 8. 训练目录配额

`sample_training_catalog()` 永远只读取 `training_bucket_ids`，即使调用方传入的目录把 C5 标记错误，目录自身校验也会先失败。

- simple 数量使用 `floor(count * 0.4)`；complex 获得余数，使总数精确等于请求值；
- simple 和 complex 内分别按桶 ID 排序后均匀分配，余数由 seed 决定的稳定轮转起点分配，避免长期偏向首桶；
- 每个桶使用从根 seed、桶 ID 和引擎通过 SHA-256 派生的 32 位子 seed，避免 Python `hash()` 的进程随机化；
- 合并后按根 seed 创建的局部生成器做确定性排列；记录保留原桶 seed，最终 `sample_index` 按合并顺序重编为 0 到 `count - 1`。

当请求数量过小而无法同时覆盖两个复杂度组时，仍严格使用上述整数规则；例如 `count=1` 产生一个 complex 样本。Smoke/Golden 的正式配额统计应使用足够大的样本数，本任务不人为把小批次改成与配置比例不一致的数量。

## 9. 测试策略

单元测试必须证明：

- 配置可载入、版本错配失败、规范哈希稳定；
- 相同 seed/config/engine 的完整模型 dump 相同，不同 seed 至少一个工程字段不同；
- LHS 和 Sobol 均覆盖连续范围且输出满足 Schema、场景桶和组合门禁；
- 离散合法组合在无拒绝的受控桶前缀中次数差不超过 1；
- 训练目录采样精确返回请求数量，并在可整除样本量上达到 40%/60%；
- 训练目录不包含 C5，显式 C5 采样的每条记录均真实超出训练包络；
- 非正 count、非法 seed、未知桶和候选耗尽返回带上下文的 `ConfigurationError`；
- 采样不改变 NumPy 全局随机状态；
- 每个新公共函数、公共模型关键校验和私有业务规则均有直接测试。

测试采用 TDD：先观察针对缺失接口或行为的预期失败，再实现最小行为并运行局部测试。最后运行全量 unittest、语法编译、锁文件检查和 diff 检查。

## 10. 文档、依赖与完成门禁

任务将修改：

- `pyproject.toml`、`uv.lock`：增加固定版本 NumPy/SciPy 直接依赖；
- `configs/data/sampling_v0_1.json`：新增版本化采样策略；
- `idfgenx/data_factory/sample.py`：新增采样模型和实现；
- `tests/unit/data_factory/test_sample.py`：新增单元测试；
- M1-005 任务、执行报告、`MASTER_PLAN.md` 和 `STATUS.md`。

完成前必须运行：

```text
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample -v
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
C:\Users\LEGION\.local\bin\uv.exe lock --check
git diff --check
git status --short
```

不得提交 `.env`、数据集、模型权重、EnergyPlus 安装文件、缓存、构建产物或采样运行输出。
