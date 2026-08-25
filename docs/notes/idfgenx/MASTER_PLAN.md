# IDFGenX AI 实施总计划

> 计划版本：1.0  
> 基线日期：2026-08-21  
> 覆盖范围：M0–M5 全项目  
> 工作区：`docs/notes/idfgenx/`  
> 当前优先级：先完成 M0/M1 Golden 与 Smoke，再开始正式训练

## 1. 总体出口

```text
M0 共享核心
 ├─→ M1 数据获取与标定 ─→ M2 模型训练 ─→ M3 实验评估与论文
 └─→ M4 应用服务 ←──────────── 已发布 Adapter
                         ↓
                    M5 部署与运维
```

项目总出口：中英文 Prompt 能通过 Qwen3-4B Spec-LoRA 生成严格 ScenarioSpecDraft，经确定性 Compiler 得到 EnergyPlus v23.1 可执行 IDF，并完成验证、仿真、3D 展示；论文公平比较 Spec、Direct-All 和 Direct-Fragment 路线。

## 2. Phase 0：仓库与工程基线

| ID | 任务 | 依赖 | 交付物 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-SETUP-001 | 提交现有仿真/3D 代码，建立 AI 工作流和项目规则 | 无 | Git 基线、`docs/notes/idfgenx/`、`AGENTS.md` | done |
| IDFGX-SETUP-002 | 配置 Windows uv/Python 3.11 与 EnergyPlus v23.1 本地环境 | SETUP-001 | `.venv`、`.env.example`、工具链 smoke 报告 | done |
| IDFGX-X-001 | 建立根目录 `idfgenx` 包与配置/错误骨架 | SETUP-001 | 包结构、config、errors、测试入口 | done |
| IDFGX-X-002 | 配置 Ruff、类型检查、pytest 和前端检查 | X-001 | 质量配置与基础 CI 命令 | proposed |
| IDFGX-X-003 | 建立测试目录和 Golden fixture 约定 | X-001 | unit/integration/golden/e2e 骨架 | proposed |
| IDFGX-X-004 | 将现有 server 业务逐步迁入 `idfgenx/simulation` | X-003 | 薄 route、兼容 re-export、回归测试 | proposed |

## 3. M0：共享核心与 Compiler

模块设计见 `docs/notes/IDFGenX-M0-共享核心与Compiler.md`。

| ID | 任务 | 依赖 | 主要出口 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-M0-001 | 冻结 ScenarioSpecDraft v0.1 字段和状态语义 | X-001 | Pydantic model、JSON schema、样例 | ready |
| IDFGX-M0-002 | 定义 ResolvedScenarioSpec v0.1 与能力边界 | M0-001 | 完整 Compiler 输入协议 | ready |
| IDFGX-M0-003 | 实现 Resolver：单位、默认值、派生值和错误 | M0-002 | Resolver、unit tests | proposed |
| IDFGX-M0-004 | 封装 EnergyPlus v23.1 路径、版本和外部进程 | X-001 | Toolchain adapter、健康检查 | proposed |
| IDFGX-M0-005 | 实现稳定命名器和对象依赖图 | M0-002 | naming/reference graph | proposed |
| IDFGX-M0-006 | 实现矩形单层建筑几何 Compiler | M0-003/005 | canonical epJSON | proposed |
| IDFGX-M0-007 | 实现矩形多层和基础多区分区 | M0-006 | floor/zone geometry | proposed |
| IDFGX-M0-008 | 实现窗、宿主墙和 WWR 几何 | M0-006 | fenestration compiler | proposed |
| IDFGX-M0-009 | 实现内墙、楼板、屋面邻接配对 | M0-007 | adjacency compiler | proposed |
| IDFGX-M0-010 | 审核并注入材料、构造和日程模板 | M0-004/005 | v23.1 templates | proposed |
| IDFGX-M0-011 | 实现内部负荷、温控和 IdealLoads | M0-010 | supported object graph | proposed |
| IDFGX-M0-012 | 实现 epJSON 序列化与 IDF 转换 | M0-004/006 | normalized IDF | proposed |
| IDFGX-M0-013 | 实现 V0–V6 Validator 和质量报告 | M0-012 | ValidationReport | proposed |
| IDFGX-M0-014 | 建立 20 个 MVP Golden 并全部通过 | M0-013 | 20 Golden | proposed |
| IDFGX-M0-015 | 扩展到 100 Golden 和复杂场景 | M0-014 | Compiler v1 候选 | proposed |
| IDFGX-M0-016 | 建立 Round-trip、metamorphic 和 mutation 测试 | M0-013 | 稳定性证据 | proposed |
| IDFGX-M0-017 | Windows/Linux 代表样本一致性验证 | M0-015 | 跨平台报告 | proposed |

M0 发布门：100 Golden 的 schema、引用、几何、转换和最小仿真通过率均为 100%，合法支持域无未处理异常，同输入规范化结果可重复。

## 4. M1：数据获取与标定

模块设计见 `docs/notes/IDFGenX-M1-数据获取与标定.md`。

| ID | 任务 | 依赖 | 主要出口 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-M1-001 | 扫描 EnergyPlus v23.1 安装并建立一次性官方语料快照 | SETUP-002 | 68 个精选 IDF、778 条 inventory、manifest 和许可证 | done |
| IDFGX-M1-002 | 分类官方 IDF 对象、几何、HVAC 和可复用角色 | M1-001 | 778 条可检索 inventory | done |
| IDFGX-M1-003 | 人工审核核心种子、几何参考、模板和 allowlist | M1-002 | 12/20/25/11 精选名单 | done |
| IDFGX-M1-004 | 冻结 S1–S5/C1–C5 场景桶和约束 | M0-002 | data config v0.1 | ready |
| IDFGX-M1-005 | 实现离散分层与 LHS/Sobol 连续采样 | M1-004/M0-003 | deterministic sampler | proposed |
| IDFGX-M1-006 | 定义 DisclosurePlan 和 Draft 派生规则 | M0-001/002 | disclosure schema | ready |
| IDFGX-M1-007 | 实现中英文 clean Prompt 模板 | M1-006 | prompt config v0.1 | proposed |
| IDFGX-M1-008 | 实现单位、语序、专家表达和受控噪声 | M1-007 | robust prompt families | proposed |
| IDFGX-M1-009 | 实现 Prompt 数值/单位/实体反向标定 | M1-007 | calibration report | proposed |
| IDFGX-M1-010 | 实现 Canonical Sample 与内容哈希对象存储 | M0-013 | canonical records | proposed |
| IDFGX-M1-011 | 实现 building family 去重和分组切分 | M1-010 | leak-free splits | proposed |
| IDFGX-M1-012 | 导出 Spec/Direct-All/Direct-Fragment 视图 | M1-010/011 | JSONL/Parquet views | proposed |
| IDFGX-M1-013 | 实现 staging/quarantine/finalize release | M1-010/012 | immutable release | proposed |
| IDFGX-M1-014 | 构建并人工审核 100 Golden 数据 | M0-015/M1-013 | Golden dataset | proposed |
| IDFGX-M1-015 | 构建 1K Smoke 和完整数据质量报告 | M1-014 | Smoke release | proposed |
| IDFGX-M1-016 | 构建 10K Pilot | M1-015 | Pilot release | proposed |
| IDFGX-M1-017 | 根据 Pilot 扩展 50K/100K | M2/M3 Pilot 门 | Scale release | proposed |
| IDFGX-M1-018 | 迁移精选官方 IDF 目录并补充中文说明 | M1-001 | `selected_official_idfs`、README、迁移验证 | ready |

M1 发布门：进入 release 的标签 V0–V6 通过率 100%，Prompt 可反向标定，无 building family 泄漏，所有样本可追溯到 catalog、配置、Compiler 和质量报告。

## 5. M2：模型训练

模块设计见 `docs/notes/IDFGenX-M2-模型训练.md`。

| ID | 任务 | 依赖 | 主要出口 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-M2-001 | 实现 release/view 读取和 manifest 校验 | M1-015 | training dataset loader | proposed |
| IDFGX-M2-002 | 实现 chat template、loss mask 和 no-truncation gate | M2-001 | collator/token report | proposed |
| IDFGX-M2-003 | 完成 Qwen3-1.7B Spec 训练 smoke | M2-002 | smoke Adapter/report | proposed |
| IDFGX-M2-004 | 完成 Qwen3-4B Spec 单卡 4090 Pilot | M1-016/M2-003 | Spec Adapter | proposed |
| IDFGX-M2-005 | 完成双卡 4090 DDP 复现 | M2-004 | distributed report | proposed |
| IDFGX-M2-006 | 训练 Direct-All 独立 Adapter | M1-016/M2-003 | baseline Adapter | proposed |
| IDFGX-M2-007 | 训练 Direct-Fragment 独立 Adapter | M1-016/M2-003 | baseline Adapter | proposed |
| IDFGX-M2-008 | 实现 checkpoint 自动小评估 | M0-013/M2-003 | callback/eval gate | proposed |
| IDFGX-M2-009 | 导出 Adapter 和 Model Manifest | M2-004/008 | versioned model | proposed |
| IDFGX-M2-010 | 完成 50K/100K 与 LoRA rank 消融 | M3 Pilot 决策 | scale models | proposed |

M2 发布门：无静默截断，训练来源和资源可追溯，Adapter 可由统一 ModelBackend 加载，Spec 输出能驱动 M0 完成端到端 IDF。

## 6. M3：实验评估与论文

模块设计见 `docs/notes/IDFGenX-M3-实验评估与论文.md`。

| ID | 任务 | 依赖 | 主要出口 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-M3-001 | 冻结 E0–E4 实验协议和资源匹配规则 | M1-016 | eval protocol | proposed |
| IDFGX-M3-002 | 建立 Golden/In-domain/Simple/Complex 分桶 | M1-015 | benchmark definitions | proposed |
| IDFGX-M3-003 | 建立 Hard-200/OOD/双语 benchmark | M1-015 | hard benchmark | proposed |
| IDFGX-M3-004 | 建立 Debug-240 确定性错误注入 | M0-016 | diagnostic benchmark | proposed |
| IDFGX-M3-005 | 实现 Spec、IDF、仿真和系统指标 | M0-013 | metrics library | proposed |
| IDFGX-M3-006 | 实现 paired bootstrap、区间和显著性统计 | M3-005 | statistics library | proposed |
| IDFGX-M3-007 | 运行 E0 Oracle 和 E1 Zero/Few-shot | M3-001/005 | baseline report | proposed |
| IDFGX-M3-008 | 运行 E2/E3/E4 Pilot 公平对比 | M2-004/006/007 | route decision | proposed |
| IDFGX-M3-009 | 运行数据量、语言、复杂度和 LoRA 消融 | M2-010 | ablation report | proposed |
| IDFGX-M3-010 | 完成错误分类和代表案例复核 | M3-008/009 | taxonomy/cases | proposed |
| IDFGX-M3-011 | 导出论文表格、图片和可复现 manifest | M3-010 | paper artifacts | proposed |

M3 发布门：所有路线在同一冻结样本和最终 IDF 门禁上比较，raw/纠正/修复口径清楚，统计与资源成本可审计，结论不依赖挑选案例。

## 7. M4：应用服务

模块设计见 `docs/notes/IDFGenX-M4-应用服务.md`。

| ID | 任务 | 依赖 | 主要出口 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-M4-001 | 定义 Generation/Job/Artifact API contract | M0-001/002 | API DTO/schema | proposed |
| IDFGX-M4-002 | 实现 Mock/Transformers ModelBackend | X-001 | backend protocol | proposed |
| IDFGX-M4-003 | 实现 Generation Orchestrator 和一次 Spec 纠正 | M0-013/M4-002 | orchestration service | proposed |
| IDFGX-M4-004 | 实现本地 JobStore、状态机和 artifact manifest | M4-001 | async domain model | proposed |
| IDFGX-M4-005 | 将仿真改为异步 Job 并持久化 `.err` | X-004/M4-004 | SimulationService | proposed |
| IDFGX-M4-006 | 封装 GeometryService 并保持现有 DTO 兼容 | X-004 | 3D service | proposed |
| IDFGX-M4-007 | 实现 `/api/v1` generation/jobs/artifacts | M4-003/004 | FastAPI routes | proposed |
| IDFGX-M4-008 | 实现 Redis + RQ worker backend | M4-004 | server queue | proposed |
| IDFGX-M4-009 | 重构现有上传页为 Validate 功能 | M4-001 | validate page | proposed |
| IDFGX-M4-010 | 实现 Prompt 生成工作台和任务进度 | M4-007 | generation UI | proposed |
| IDFGX-M4-011 | 实现结果、3D、曲线、日志和下载 | M4-005/006/010 | result UI | proposed |
| IDFGX-M4-012 | 建立 20 个固定 Prompt E2E | M4-011 | E2E report | proposed |

M4 发布门：固定 Prompt 可重复完成 Prompt→Spec→IDF→验证→可选仿真→3D，长任务不阻塞 HTTP，错误定位明确，产物可追溯和下载。

## 8. M5：部署与运维

模块设计见 `docs/notes/IDFGenX-M5-部署与运维.md`。

| ID | 任务 | 依赖 | 主要出口 | 状态 |
| --- | --- | --- | --- | --- |
| IDFGX-M5-001 | 冻结本地 uv 和服务器 Miniconda 安装流程 | X-002 | deploy README/lock | proposed |
| IDFGX-M5-002 | 服务器部署 EnergyPlus v23.1 并做健康检查 | M0-004 | server toolchain | proposed |
| IDFGX-M5-003 | 部署 vLLM BF16 Spec Adapter 服务 | M2-009 | model service | proposed |
| IDFGX-M5-004 | 建立 Compose/Nginx/Redis/RQ 拓扑 | M4-008 | deployment stack | proposed |
| IDFGX-M5-005 | 建立日志、指标、磁盘和 worker 监控 | M5-004 | observability | proposed |
| IDFGX-M5-006 | 实现 job TTL、artifact 清理和备份 | M4-004/M5-004 | retention jobs | proposed |
| IDFGX-M5-007 | 单卡 4090 全链路 smoke | M5-003/004 | single-GPU report | proposed |
| IDFGX-M5-008 | 双卡训练/服务资源隔离 smoke | M2-005/M5-004 | dual-GPU report | proposed |
| IDFGX-M5-009 | 发布、升级、故障恢复和回滚演练 | M5-005/006 | operations report | proposed |

M5 发布门：全新单/双 4090 服务器可以按文档重建，模型与 EnergyPlus worker 资源隔离，服务可恢复和回滚，结果版本链完整。

## 9. 计划维护规则

1. 只有通过上一阶段门，才能把依赖任务改为 `ready`；
2. 实际执行使用单独任务文件，不直接在本表写实施细节；
3. 任务拆分或合并必须保留旧 ID 和迁移说明；
4. 方案范围变化先更新 `docs/notes` 和 ADR；
5. 完成任务后更新状态并链接执行报告；
6. 任何模型训练、数据 release 和正式评估都必须记录精确 manifest；
7. 不以赶进度为由跳过 Golden、门禁或报告。
