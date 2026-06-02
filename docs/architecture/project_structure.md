# V1 Demo 目录结构说明

## 1. 目标

本文件定义当前更适合 demo 阶段的精简目录结构。

目标不是一次性把正式工程骨架全部铺满，而是只保留当前真正需要的层级：

- 配置层
- SQL 分析层
- 特征结果层
- AI 提示词层
- 前后端展示层

## 2. 推荐目录树

```text
project-root/
  agent/
  backend/
    app/
      api/
      services/
  config/
    tokens/
      tokens.example.json
  data/
    raw/
    processed/
    features/
  docs/
    architecture/
      project_structure.md
    data-contracts/
      feature_layer_schema.json
      metrics_definition.md
  frontend/
    app/
    components/
    public/
  plan/
    project_overall_plan.md
    phase1_detailed_plan.md
  prompts/
    address_profile/
      system_prompt.md
  sql/
    templates/
      eth/
        01_token_candidate_pool.sql
        02_token_cost_basis.sql
        03_token_position_validation.sql
        04_token_pnl_snapshot.sql
  .env.example
  .gitignore
```

## 3. 保留理由

- `backend/`：保留最小后端层，避免把第三方 API Key 暴露到前端
- `frontend/`：保留单页 demo 的展示层
- `sql/`：保留统一模板和渲染后的查询文件
- `config/`：保留 token 配置入口，后续换 token 不改主逻辑
- `data/`：保留手动导出和特征结果存放位置
- `docs/`：保留方法说明和字段契约，适合作品集展示
- `prompts/`：保留地址画像提示词

## 4. 当前不预留的内容

以下内容在 demo 阶段先不单独拆目录，避免空目录过多：

- 后端 `clients`、`repositories`、`schemas`、`models`、`pipelines`
- 前端 `hooks`、`types`、`services` 以及更细的组件分层
- `tests/`
- `scripts/`
- `docs/product/`
- `prompts/event_attribution/`

需要时再按真实代码增长情况补齐即可。

## 5. 目录放置规则

- 统一模板 SQL 放在 `sql/templates/eth/`
- token 配置放在 `config/tokens/`
- 手动导出的原始或处理结果放在 `data/`
- 指标定义和字段契约放在 `docs/data-contracts/`
- 提示词放在 `prompts/address_profile/`
- 真实密钥只放本地 `.env`，仓库只保留 `.env.example`

## 6. 当前约束

- 第一阶段固定单链 `ethereum`
- 第一阶段只维护预设 token 配置
- 第一阶段以手动刷新和 demo 展示为主
- 真实 API Key 不进入仓库，不进入前端代码
