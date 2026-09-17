# 旅行计划项目目录

用户指定的 GitHub 本地项目目录为 `/Users/glonk/Desktop/travelplan-Cloudflare`，关联 `Glonkkkkk/travel-plan`。后续旅行网页修改在此目录进行，保留现有 Git 历史及 origin 配置。

`trip-data.json` 是行程数据源；路线图派生字段由 `npm run build:map` 生成。修改完成后运行 `npm run build`，静态部署输出为 `dist/`。

Cloudflare Worker 为 `plain-mud-90b8`，已由用户绑定 GitHub。提交并推送到配置的生产分支将触发部署；本地修改本身不会发布。

旧目录 `/Users/glonk/Documents/ChatGPT/旅行计划/2026-贵阳大理泸沽湖重庆` 仅为迁移前副本，不再作为后续修改入口。避免从旧副本覆盖本目录较新的改动。
