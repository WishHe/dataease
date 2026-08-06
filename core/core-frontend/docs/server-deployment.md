# 192.168.0.222 服务器部署信息

> 最后更新: 2026-08-01

---

## 服务器环境

| 项目 | 详情 |
|------|------|
| **IP** | 192.168.0.222 |
| **OS** | CentOS Linux 7 (Core) |
| **Docker** | 26.1.4 |
| **SSH** | `ssh root@192.168.0.222` |
| **SSH 密码** | `Sengee123` |
| **磁盘** | 40G（已用 9.7G，可用 28G） |

---

## Docker 容器列表

| 容器名 | 镜像 | 端口映射 | 用途 |
|--------|------|----------|------|
| `dataease` | `dataease:v2.10.25` | `8100→8100` | DataEase 后端服务 |
| `mysql-de` | `mysql:8.4.5` | 仅容器网络 `3306` | MySQL 数据库 |
| `milvus-standalone` | `milvus:v2.6.21` | `9091`, `19530` | 向量数据库 |
| `milvus-etcd` | `etcd:v3.5.25` | 仅容器网络 | Milvus 元数据存储 |
| `milvus-minio` | `minio` | `29000→9000`, `29001→9001` | 对象存储 |
| `dm8` | `dm8_single` | `15236→5236` | 达梦数据库 |

---

## MySQL 数据库

| 项目 | 详情 |
|------|------|
| **容器名** | `mysql-de` |
| **镜像** | `registry.cn-qingdao.aliyuncs.com/dataease/mysql:8.4.5` |
| **访问方式** | 仅 Docker 内部网络，未对外暴露端口 |
| **连接命令** | `docker exec mysql-de mysql -u root -p'Password123@mysql'` |
| **Root 密码** | `Password123@mysql` |
| **数据库名** | `dataease` |
| **字符集** | UTF-8 |

### 常用操作

```bash
# 进入 MySQL 容器
docker exec -it mysql-de mysql -u root -p'Password123@mysql' dataease

# 查看表结构
SHOW TABLES;
DESCRIBE core_sys_setting;

# 查询系统设置
SELECT pkey, pval FROM core_sys_setting ORDER BY sort;

# 备份数据库
docker exec mysql-de mysqldump -u root -p'Password123@mysql' dataease > dataease_backup.sql
```

---

## DataEase 后端

| 项目 | 详情 |
|------|------|
| **容器名** | `dataease` |
| **镜像** | `registry.cn-qingdao.aliyuncs.com/dataease/dataease:v2.10.25` |
| **端口** | `8100` |
| **版本** | v2.10.25 |
| **API 前缀** | `/de2api/` |
| **Swagger** | `http://192.168.0.222:8100/swagger-ui.html` |

### 常用操作

```bash
# 查看日志
docker logs -f dataease

# 重启服务
docker restart dataease

# 进入容器
docker exec -it dataease bash
```

---

## Nginx（前端）

| 项目 | 详情 |
|------|------|
| **端口** | `80`, `8080` |
| **前端部署路径** | nginx 直接代理（非 Docker） |
| **前端文件** | 需要通过 Maven 构建后部署到 nginx 目录 |

---

## 服务端口总览

| 端口 | 服务 | 说明 |
|------|------|------|
| 22 | SSH | 远程登录 |
| 80 | Nginx | HTTP（前端） |
| 8080 | Nginx | HTTP（前端） |
| 8100 | DataEase | 后端 API |
| 9091 | Milvus | 向量数据库 |
| 15236 | 达梦 DM8 | 国产数据库 |
| 19530 | Milvus | gRPC |

---

## 本地开发连接方式

前端开发时，Vite 代理将 `/api` 转发到 `http://192.168.0.222:8100/de2api`：

```ts
// core/core-frontend/config/dev.ts
{
  '/api': {
    target: 'http://192.168.0.222:8100',
    rewrite: path => path.replace(/^\/api/, 'de2api')
  }
}
```

```bash
# 启动前端开发服务器
cd core/core-frontend
npm run dev
# → http://localhost:8080
```

### 登录账号

| 用户名 | 密码 |
|--------|------|
| `admin` | `DataEase@123456` |
