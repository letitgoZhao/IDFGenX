# Staged Qwen Training Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 IDFGenX 的训练架构统一调整为 RTX 4060 8GB 本地 Qwen3-0.6B/1.7B 闭环与云端 Qwen3-8B+ 正式训练路线。

**Architecture:** 本任务只修改版本化文档，不改业务代码、依赖或数据。ADR-0002 作为模型分层和晋级门的单一决策源，总体方案、M2/M3/M5、主计划与仓库规则分别投影训练、评估、部署和执行顺序，最后通过全仓术语扫描消除旧的固定 4B/4090 假设。

**Tech Stack:** Markdown、Git、PowerShell `Select-String`

**Spec:** `docs/superpowers/specs/2026-08-28-staged-qwen-training-design.md`

## Global Constraints

- 生产路线仍为 `Prompt → ScenarioSpecDraft → Resolver → Compiler → IDF`。
- Direct-All 和 Direct-Fragment 仍是隔离的论文基线。
- 本地主线为 Qwen3-0.6B Smoke 与 Qwen3-1.7B 候选，云端正式主线为 Qwen3-8B。
- Qwen3-4B 只保留为可选中间对照或资源回退，不是必经生产门。
- Qwen3-14B 及以上仅在 8B 显示容量瓶颈且收益覆盖成本时开展。
- 默认使用 BF16 标准 LoRA，不使用 4-bit/8-bit 量化训练。
- RTX 4060 8GB 的序列长度、吞吐和 1.7B 可行性必须由实际显存 smoke 证明。
- 不允许静默截断；训练只读取冻结 release，测试集不参与调参。
- 每个 Adapter 必须用 Model Manifest 固定基础模型、tokenizer、数据、代码、训练配置和硬件环境。
- 不提交模型权重、数据集、训练产物、密钥或 `.env`。

---

### Task 1: 冻结跨模块架构决策与仓库规则

**Files:**
- Create: `docs/notes/idfgenx/decisions/ADR-0002-staged-qwen-training.md`
- Modify: `AGENTS.md`
- Modify: `docs/notes/IDFGenX的模块文档索引.md`
- Modify: `docs/notes/idfgenx/MASTER_PLAN.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-08-28-staged-qwen-training-design.md` 中已批准的 L0/L1/C1/C2/C3 分层。
- Produces: ADR-0002 的模型职责、晋级门、回退条件，以及 M2 任务表采用的统一术语。

- [x] **Step 1: 新增 ADR-0002**

  写明选择 0.6B→1.7B→8B+ 的原因、4B 的可选角色、BF16 标准 LoRA 边界、
  本地显存 smoke、同基座正式比较和 14B+ 触发条件。备选方案必须覆盖保留
  4B 主线与跳过 1.7B 两种方案。

- [x] **Step 2: 更新仓库级训练约束**

  把 `AGENTS.md` 中“训练使用 Qwen3-4B”替换为精确分层：本地 0.6B/1.7B、
  云端 8B 正式候选、14B+ 可选上界；保留 Python 3.11、BF16 标准 LoRA 和
  不默认量化的约束。

- [x] **Step 3: 更新模块索引和主计划**

  模块索引的主模型摘要与执行顺序改为 0.6B→1.7B→8B+。在
  `MASTER_PLAN.md` 增加 `IDFGX-X-006` 并把 M2-003 至 M2-010 重排为：
  0.6B 本地 Smoke、1.7B 本地候选、8B 云端 Spec Pilot、8B Direct Pilot、
  8B Scale、checkpoint 评估和 Adapter 发布；依赖保持可执行。

- [x] **Step 4: 验证治理文档术语**

  Run:

  ```powershell
  Select-String -Path 'AGENTS.md','docs/notes/IDFGenX的模块文档索引.md','docs/notes/idfgenx/MASTER_PLAN.md','docs/notes/idfgenx/decisions/ADR-0002-staged-qwen-training.md' -Pattern 'Qwen3-0.6B|Qwen3-1.7B|Qwen3-8B|RTX 4060|BF16'
  ```

  Expected: 四个模型/硬件核心术语均可定位；不存在仍把 4B 写成固定生产主线的有效条款。

### Task 2: 同步总体方案与 M2/M3/M5 模块设计

**Files:**
- Modify: `docs/notes/IDFGenX总体的方案规划.md`
- Modify: `docs/notes/IDFGenX-M2-模型训练.md`
- Modify: `docs/notes/IDFGenX-M3-实验评估与论文.md`
- Modify: `docs/notes/IDFGenX-M5-部署与运维.md`

**Interfaces:**
- Consumes: ADR-0002 的 L0/L1/C1/C2/C3 术语和 Task 1 的 M2 任务编号。
- Produces: 训练配置规划、正式公平比较规则、本地/云端部署出口和项目完成门。

- [x] **Step 1: 重写 M2 模型、配置与硬件分层**

  在 M2 中设置 0.6B 本地 Smoke、1.7B 本地候选、8B 云端 Pilot/Scale，
  配置名与职责一一对应。明确 8GB OOM 的处理顺序、禁止静默截断、8B 重新
  校准超参、4B 可选回退、14B+ 非默认完成条件。

- [x] **Step 2: 更新 M3 公平比较协议**

  把固定 Qwen3-4B 公平基座改为冻结的 Qwen3-8B revision。E2/E3/E4 Pilot
  必须同基座；预算不足时统一缩小样本或统一降档，不允许用 1.7B Direct 与
  8B Spec 宣称公平比较。把模型规模列为独立消融。

- [x] **Step 3: 更新 M5 本地与云端部署边界**

  把 Windows 本地环境明确为 RTX 4060 8GB 的 0.6B/1.7B Transformers 开发档；
  正式云端服务以通过门禁的 8B Adapter 为默认候选。保留依据统一指标选择
  1.7B 低资源部署档和 14B+ 可选上界的条件。

- [x] **Step 4: 同步总体方案中的重复事实**

  更新总体方案的摘要、模型表、显存策略、训练顺序、实验基座、目录注释、
  技术栈、阶段计划、交付物、风险和最终决策摘要。历史背景可保留日期与事实，
  当前有效规则不得继续声称 4B 是固定生产主线或 4090 是唯一开发硬件。

- [x] **Step 5: 运行模块一致性扫描**

  Run:

  ```powershell
  Select-String -Path 'docs/notes/IDFGenX总体的方案规划.md','docs/notes/IDFGenX-M2-模型训练.md','docs/notes/IDFGenX-M3-实验评估与论文.md','docs/notes/IDFGenX-M5-部署与运维.md' -Pattern 'Qwen3-4B.*生产主|相同 Qwen3-4B|单卡 4090.*必须|1.7B 只|8B 是可选上界'
  ```

  Expected: 无当前有效旧约束；若匹配历史/备选方案，逐条人工确认上下文明确标记为已替代或未选择。

### Task 3: 状态收口、验证、报告、提交与推送

**Files:**
- Modify: `docs/notes/idfgenx/STATUS.md`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-X-006-分阶段Qwen训练策略.md`
- Create: `docs/notes/idfgenx/reports/2026-08-28-IDFGX-X-006-Staged-Qwen-Training.md`
- Modify: `docs/superpowers/plans/2026-08-28-staged-qwen-training.md`

**Interfaces:**
- Consumes: Task 1 与 Task 2 的最终文档差异和验证输出。
- Produces: 完成状态、实际验证证据、关联提交和远端 `origin/main` 更新。

- [x] **Step 1: 更新状态与任务清单**

  在 `STATUS.md` 登记 X-006 完成内容、无活动任务、下一项仍为 M1-008/M1-009；
  将任务清单和状态改为 `done`，但只有完成全部验证后执行。

- [x] **Step 2: 运行全仓术语和安全扫描**

  Run:

  ```powershell
  Get-ChildItem -Recurse -File -Include '*.md' | Where-Object { $_.FullName -notmatch '\\.git\\|\\.worktrees\\' } | Select-String -Pattern 'Qwen3-4B.*生产主|相同 Qwen3-4B|1.7B 只做|8B 是可选上界|只有.*4090'
  git diff --check
  git status --short
  git diff --name-only HEAD~1
  ```

  Expected: 旧约束只有明确的历史、备选方案或被替代表述；`git diff --check` 退出码 0；无权重、数据、`.env` 或运行时产物。

- [x] **Step 3: 编写执行报告**

  报告必须列出实际修改文件、未运行训练的范围边界、术语扫描结果、
  `git diff --check` 结果、风险和后续 M1/M2 任务。不得声称 RTX 4060 的
  1.7B 可行性已验证。

- [x] **Step 4: 检查最终差异并提交**

  Run:

  ```powershell
  git diff --stat HEAD~1
  git diff --check
  git status --short
  ```

  Expected: 仅包含本任务文档；检查通过后提交：

  ```text
  docs(training): adopt local-to-cloud qwen roadmap
  ```

- [ ] **Step 5: 推送并验证远端**

  Run:

  ```text
  git push origin main
  git status --short
  git log -3 --oneline --decorate
  ```

  Expected: 推送成功，工作树干净，`origin/main` 指向最终文档提交。
