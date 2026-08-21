# IDFGenX AI 工程工作区

`docs/notes/idfgenx/` 是 IDFGenX 的可版本化 AI 编程控制面，借鉴 Superpowers 的“先设计、再计划、按任务执行、验证后完成”方法。虽然父目录 `docs/notes/` 保持在 `.gitignore` 中，但本目录使用显式 `git add -f` 纳入版本管理；任务事实因此能够随项目共享，同时不暴露其他本地笔记。

## 1. 目录

```text
docs/notes/idfgenx/
├─ README.md                      # 工作流和命名规则
├─ MASTER_PLAN.md                 # 覆盖整个项目的任务分解
├─ STATUS.md                      # 当前阶段、活动任务和阻塞项
├─ tasks/
│  ├─ README.md                   # 任务状态与维护规则
│  └─ TASK-TEMPLATE.md            # 单任务计划模板
├─ reports/
│  ├─ README.md                   # 执行报告规则
│  ├─ REPORT-TEMPLATE.md          # 报告模板
│  └─ YYYY-MM-DD-<task-id>-*.md   # 每次任务完成报告
└─ decisions/
   ├─ README.md                   # ADR 使用说明
   └─ ADR-TEMPLATE.md             # 架构决策模板
```

任务文件直接放在 `docs/notes/idfgenx/tasks/`，状态由 YAML frontmatter 管理，避免在 backlog/active/completed 之间移动文件造成链接变化。

## 2. 使用流程

### 开始前

1. 阅读 `AGENTS.md`；
2. 在 `MASTER_PLAN.md` 找到任务 ID；
3. 检查 `STATUS.md` 是否有并发冲突；
4. 从 `TASK-TEMPLATE.md` 创建任务文件；
5. 写清涉及文件、逐步实施、验证命令和完成标准。

### 执行中

- 任务状态改为 `in_progress`；
- 每完成一个可验证步骤，更新 checklist；
- 发现范围变化时先更新任务计划；
- 架构决策写 ADR；
- 阻塞时记录证据和下一步，不用猜测填补关键事实。

### 完成后

1. 运行任务文件中全部验证命令；
2. 检查 diff 和敏感文件；
3. 在 `docs/notes/idfgenx/reports/` 创建执行报告；
4. 把任务状态改为 `done`；
5. 更新 `STATUS.md`；
6. 经授权后提交和推送。

## 3. 任务状态

| 状态 | 含义 |
| --- | --- |
| `proposed` | 已提出，范围尚未冻结 |
| `ready` | 输入、步骤和验收已明确，可执行 |
| `in_progress` | 正在实施，同一任务只能有一个责任主体 |
| `blocked` | 存在明确外部阻塞，报告中必须有证据 |
| `review` | 实现完成，等待验证或人工评审 |
| `done` | 验证通过且报告已生成 |
| `canceled` | 经明确决策取消，保留原因 |

## 4. ID 命名

- 模块任务：`IDFGX-M0-001` 至 `IDFGX-M5-NNN`；
- 跨模块工程：`IDFGX-X-001`；
- 仓库/流程初始化：`IDFGX-SETUP-001`；
- 架构决策：`ADR-0001`；
- 报告：`YYYY-MM-DD-<task-id>-<short-slug>.md`。

## 5. 什么情况下必须建任务

以下工作必须创建任务和报告：

- 新增或修改业务代码；
- 修改 ScenarioSpec、Compiler、Validator 或数据规则；
- 数据 release、模型训练和正式评估；
- API、前端功能和部署改动；
- Bug 修复、依赖升级和性能优化；
- 影响项目范围、接口或结果解释的文档变更。

只读检查、简短答疑和无状态研究可以不建任务，但研究结论一旦影响实现，必须写入任务或 ADR。

## 6. 与总体方案的关系

- 项目设计：[总体方案](../IDFGenX方案规划.md)；
- 模块设计：[模块索引](../IDFGenX模块文档索引.md)；
- `MASTER_PLAN.md` 只负责实施顺序和任务状态，不重复大段技术论证；
- 模块范围变化时，先更新方案文档，再更新总计划和任务。
