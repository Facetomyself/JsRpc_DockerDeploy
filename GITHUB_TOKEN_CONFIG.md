# GitHub Token 持久化配置说明

此文件包含了GitHub Personal Access Token的持久化配置。

## 配置内容
- credential.helper = store (全局配置)
- 凭据文件: ~/.git-credentials

## 如何使用
配置完成后，可以直接使用以下命令而无需输入token：
- git push fork main
- git pull fork main
- git fetch fork

## 安全注意事项
- 此token具有完整的仓库访问权限
- 请妥善保管，不要泄露给他人
- 如需撤销，前往GitHub Settings > Developer settings > Personal access tokens删除

## 验证方法
运行以下命令测试配置是否生效：
git ls-remote fork

