# IDFGX-M1-004 执行报告

已冻结十个矩形 M0 支持域场景桶。S1–S5/C1–C4 可训练；C5 为 Hard/OOD 评估专用。非矩形、复杂屋顶和真实 HVAC 明确拒绝，不进入正向 SFT。

验证：`test_scenarios` 3/3 通过；`unittest discover -v` 84/84 通过（58.381 秒）。未创建 release、Prompt 或采样器。

后续：IDFGX-M1-005 消费该配置实现分层/LHS/Sobol 采样；IDFGX-M1-006 定义 DisclosurePlan。
