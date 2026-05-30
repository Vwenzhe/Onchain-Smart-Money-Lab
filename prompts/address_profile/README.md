# 地址画像 Prompt 方案说明

本目录用于存放链上地址画像能力的可复用 Prompt 资产，适用于：

- 后端 API 单条调用
- 批处理脚本离线生成
- 后续前端或服务层统一复用

## 文件说明

- [system_prompt.md](file:///D:/aiwork/DprojectsAAA-project-1/prompts/address_profile/system_prompt.md)
  - 定义模型角色、证据边界、标签集合和安全约束
- [task_prompt.md](file:///D:/aiwork/DprojectsAAA-project-1/prompts/address_profile/task_prompt.md)
  - 定义任务模板、输出格式、兜底策略和标准示例

## 设计目标

- 输出稳定：字段固定为 `profile_label`、`risk_note`、`summary`
- 证据优先：只允许基于 `address_feature_snapshot` 输入判断
- 风格克制：避免夸张描述、无证据断言和过度外推
- 易于落地：同时适配批处理和 OpenAI 风格 API

## 推荐消息组装方式

建议按以下结构调用：

1. `system` 消息加载 `system_prompt.md`
2. `user` 消息加载 `task_prompt.md` 中的通用模板
3. 将 `{{ADDRESS_FEATURE_JSON}}` 替换为单条地址记录

## 推荐输出校验规则

调用侧建议至少做以下校验：

1. 输出必须可解析为 JSON
2. 只能包含 3 个字段：`profile_label`、`risk_note`、`summary`
3. 3 个字段都必须是非空字符串
4. `profile_label` 必须属于允许标签集合
5. 文本中不得出现交易建议、身份断言、价格预测
6. 允许客观描述持仓变化或仓位变化，但不得写成买卖或仓位操作建议

## 推荐标签集合

- `早期埋伏型`
- `趋势跟随型`
- `深度持有型`
- `高浮盈型`
- `高活跃轮动型`
- `待定观察型`

其中 `待定观察型` 是保守兜底标签，用于处理以下情况：

- 输入字段不足
- 特征信号冲突
- 输出格式异常
- 模型内容越界

## 工程建议

- 单次请求只处理一个地址，减少输出串扰
- 对解析失败或字段缺失场景保留一次低温重试
- 将固定兜底 JSON 写入服务层，而不是临时拼接
- 在日志中保留原始输入和原始模型输出，便于后续评估标签稳定性

## 当前接入注意

当前项目的 `LLMClient` 已收敛为 DeepSeek 的 `chat/completions` 调用方式，可直接按 `system + user` 两段消息接入。

如果后续希望进一步提高稳定性，可以继续增加：

- 标签判定前的规则预分类
- JSON Schema 校验
- 二次审查 Prompt
- 画像结果缓存与回放评估
