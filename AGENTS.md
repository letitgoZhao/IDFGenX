# IDFGenX AI 开发规则

本文件是仓库级 AI 编程规则，适用于修改本仓库的 Codex、Claude、Copilot 及其他编码代理。规则优先级低于用户当次明确要求，高于一般实现习惯。

## 1. 开始任务前

1. 阅读 `docs/notes/idfgenx/README.md`、`STATUS.md` 和 `MASTER_PLAN.md`；
2. 阅读与任务对应的 `docs/notes/IDFGenX-M*.md`；
3. 在 `docs/notes/idfgenx/tasks/` 创建或更新任务文件，写清目标、范围、步骤、文件和验收命令；
4. 未确认架构边界时不得直接实现大范围代码；
5. 不得把 `.env`、密钥、模型权重、数据集、EnergyPlus 安装文件或运行时产物提交 Git。

小型只读问答和不修改代码的诊断不要求创建任务文件。任何会修改业务代码、配置、测试、部署或数据规则的工作都必须有任务记录。

## 2. 实施闭环

每个任务执行以下流程：

```text
确认任务与设计
    ↓
创建/更新 docs/notes/idfgenx/tasks/<task-id>.md
    ↓
实现最小可验证变更
    ↓
运行任务定义的验证命令
    ↓
检查 diff、敏感文件和兼容性
    ↓
输出 docs/notes/idfgenx/reports/<date>-<task-id>-<slug>.md
    ↓
更新 docs/notes/idfgenx/STATUS.md 和任务状态
```

没有验证证据和执行报告，不得将任务标记为 `done`。报告必须说明实际完成内容、未完成项、测试结果、风险、后续工作和相关提交。

## 3. Python 工业级注释规则

### 3.1 模块、类和函数

- 新增 Python 模块必须有模块级 docstring，说明用途、边界和重要依赖；
- 公共类、公共函数、公共方法必须有中文 docstring；
- 私有函数只要包含业务规则、单位换算、几何、外部进程、状态变化或非显然算法，也必须有 docstring；
- 简单属性访问器、显而易见的一行包装器不强制长 docstring；
- docstring 优先采用 Google 风格：摘要、`Args`、`Returns`、`Raises`，必要时增加 `Examples`、`Notes`；
- Pydantic 字段和配置项应使用有意义的命名及 `description`，不能只依赖外围注释。

示例：

```python
def convert_epjson_to_idf(
    source: Path,
    work_dir: Path,
    *,
    timeout_seconds: int,
) -> Path:
    """使用 EnergyPlus v23.1 将 canonical epJSON 转换为 IDF。

    每次转换必须使用独立工作目录，以避免 ConvertInputFormat 的固定输出
    文件名在并发任务之间发生冲突。

    Args:
        source: 已通过 schema 校验的 epJSON 文件。
        work_dir: 当前任务独占且可写的工作目录。
        timeout_seconds: 外部转换进程的最大允许运行时间，单位为秒。

    Returns:
        转换后 IDF 文件的绝对路径。

    Raises:
        EnergyPlusVersionError: 当前工具版本不是 23.1。
        ConversionTimeoutError: 转换进程超过时间限制。
        ConversionError: 进程失败或未产生预期 IDF 文件。
    """
```

### 3.2 行内注释

- 注释解释“为什么、约束和不变量”，不要逐字翻译代码；
- 几何代码必须说明坐标系、顶点顺序、法向约定和单位；
- EnergyPlus 对象处理必须说明版本、对象假设、字段语义和引用关系；
- 数值常量必须给出来源、单位或配置入口，禁止无说明 magic number；
- 外部进程、并发、缓存、重试和清理逻辑必须说明失败边界；
- 临时兼容代码必须带任务 ID 和删除条件，例如 `TODO(IDFGX-M4-012)`；
- 注释与实现不一致时，必须在同一变更中更新或删除注释。

### 3.3 适度原则

工业级注释不等于每行加注释。禁止以下低价值写法：

```python
# 遍历列表
for item in items:
    # 添加到结果
    result.append(item)
```

对既有大文件采用“触碰即改善”原则：修改某个函数时补齐该函数及相关数据结构的 docstring/关键注释，不进行一次性无验证的全仓库注释重写。

## 4. Python 工程规则

- Python 统一使用 3.11，依赖以 `pyproject.toml` 和 `uv.lock` 为事实源；
- 新代码必须提供类型标注；公共返回结构优先使用 Pydantic model、dataclass 或 TypedDict，避免无约束 `dict[str, Any]`；
- 路径使用 `pathlib.Path`；时间、单位和坐标系必须显式；
- 禁止裸 `except:` 和静默吞错；异常应归类、保留 cause，并转成项目错误码；
- 使用标准 logging/loguru 记录结构化上下文，不使用 `print` 作为服务日志；
- 业务代码不读取同义环境变量，统一通过 `idfgenx.config`；
- FastAPI route 只做 HTTP 适配，不实现 Compiler、模型或 EnergyPlus 业务；
- 数据、在线服务和评估必须复用同一套 Schema、Compiler 和 Validator；
- LLM 不负责确定性几何计算、对象引用和生产 IDF 修补。

## 5. 测试与验证

- 修复 bug 前先创建最小失败测试或 Golden；
- 新增业务规则必须包含 unit test；
- Compiler 变更必须运行对应 Golden、几何/引用检查和最小仿真；
- API 变更必须检查 contract 和错误响应；
- 前端变更至少运行 `npm run check`，交付前运行 `npm run build`；
- 完成声明必须附实际执行命令和结果，不能用“应该通过”代替；
- 不得为了通过测试删除有效断言、降低门槛或静默隔离失败样本。

## 6. IDFGenX 架构约束

- EnergyPlus 首版固定 v23.1；
- 生产主线固定为 `Prompt → ScenarioSpecDraft → Resolver → Compiler → IDF`；
- Direct-All/Direct-Fragment 是隔离的论文基线；
- 永久不实现真实 `AirLoopHVAC`、`PlantLoop` 和设备拓扑；
- 训练使用 Qwen3-4B、BF16 标准 LoRA，不使用 4-bit/8-bit 量化；
- Compiler 的唯一输入是 `ResolvedScenarioSpec`；
- `data/releases` 一旦 finalize 就只读，禁止原地覆盖；
- 失败样本进入 quarantine，不能直接加入正向 SFT。

## 7. Git 和变更管理

- 保持提交范围单一、信息明确；
- 提交前检查 `git diff`、验证结果和敏感文件；
- 不使用破坏性 reset/checkout 清理用户改动；
- 不提交生成数据、模型权重、runtime、`.env`、依赖目录和构建产物；
- 架构或数据协议变更应在 `docs/notes/idfgenx/decisions/` 记录 ADR；
- 完成任务后在报告中登记相关 commit/PR；
- 除非用户明确要求，不自动 push、创建 PR 或修改远端资源。

## 8. 其他文件注释

- TypeScript/Vue：公共 composable、复杂组件状态、Three.js 坐标/资源释放和 API contract 需要注释；简单模板不逐行注释；
- YAML/TOML：非显然参数说明用途、单位和安全边界；
- Shell/PowerShell：说明前置条件、输入输出和破坏性行为；
- Markdown：避免复制多份相同事实，使用链接指向总体方案和模块文档。
