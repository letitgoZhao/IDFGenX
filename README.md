# IDFGenX

基于 Qwen3 + LoRA 的 EnergyPlus IDF 生成项目：用自然语言建筑描述生成 EnergyPlus 输入文件（IDF），并支持部署集成。

## 目录结构

```
IDFGenX/
├── src/                 # 核心代码（数据处理 / 训练 / 推理）
├── scripts/             # 训练与评测入口脚本
├── deploy/              # 部署集成（API / Docker）
├── configs/             # 训练与推理配置（待添加）
├── tests/               # 测试（待添加）
├── data/
│   ├── building/        # 建筑描述与标定数据 ✅ 上传
│   └── epw/             # EPW 气象文件 ✅ 上传
├── adapters/            # LoRA 适配层成品 ✅ 上传（含 adapter_config.json）
├── models/              # 基座模型权重 ❌ 不入库（体积大，可重新下载）
├── outputs/             # 训练中间产物 ❌ 不入库（checkpoint / 日志）
├── docs/
│   ├── reports/         # 实验报告 ✅ 上传
│   ├── notes/           # 学习笔记 ❌ 不入库
│   └── papers/          # 论文资源 ❌ 不入库
└── private/             # 私有资料 ❌ 不入库（待添加）
```

## 快速开始

### 1. 环境

- Python 3.10+，PyTorch + transformers + peft + bitsandbytes
- 8GB 显存建议使用 QLoRA（4-bit 量化 + LoRA，rank 16~32）

### 2. 下载基座模型

```bash
# 0.6B（快速实验 / 流程验证）
huggingface-cli download Qwen/Qwen3-0.6B --local-dir models/Qwen3-0.6B

# 2B（8GB 显存 QLoRA 微调的实用上限，效果更好）
huggingface-cli download Qwen/Qwen3-2B --local-dir models/Qwen3-2B
```

### 3. 准备数据 → 4. 训练 → 5. 部署

（待补充）

## 约定

- `models/`、`outputs/` 整个目录被 `.gitignore` 忽略，clone 后按上面命令重新下载模型
- 训练完成后把最优 LoRA 成品（`adapter_config.json` + `adapter_model.safetensors`）复制到 `adapters/` 再提交
- 单个文件超过 100MB（如高 rank 的 2B LoRA）需要配置 Git LFS
