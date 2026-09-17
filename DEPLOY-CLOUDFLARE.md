# GitHub → Cloudflare 自动部署

本项目是 Cloudflare Worker 静态网站。已由用户连接 GitHub 仓库 Glonkkkkk/travel-plan。

1. 将本项目源代码放入 GitHub 仓库根目录，可使用私有仓库。不要只上传 dist 或部署 ZIP；需要 package.json、scripts、assets、trip-data.json 与 wrangler.jsonc 等源文件。
2. 在 Cloudflare 打开现有 Worker `plain-mud-90b8`，进入 Settings → Builds，连接 GitHub 仓库（界面入口可能显示 Connect Git）。授权 Cloudflare 访问选定仓库。
3. 生产分支选择 main；根目录 `/`；部署命令 `npx wrangler deploy`。wrangler.jsonc 已配置部署前自动运行 `npm run build`，面板的构建命令可以留空；若已经填写相同命令，也可以使用。
4. 保持 wrangler.jsonc 的 name 与现有 Worker 名称一致。首次构建成功后，在 Deployments 查看部署结果，再访问公开网址检查。
5. 以后修改 trip-data.json 或页面代码，提交并推送至生产分支，即触发重新构建与部署。仅在本机修改而未推送，不会更新网站。

不需要把 Cloudflare 密钥写入仓库。离线 PDF/HTML 是独立快照，不会随网站推送自动更新。
自动部署不会改变 workers.dev 在不同网络下的可访问性。

官方文档：https://developers.cloudflare.com/workers/ci-cd/builds/
静态资源：https://developers.cloudflare.com/workers/static-assets/binding/
