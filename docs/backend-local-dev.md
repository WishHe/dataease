# DataEase 后端本地编译与启动

> 最后更新: 2026-08-09  
> 适用版本: `2.10.26`（仓库 `pom.xml` / 分支 `dev-v2`）  
> 远程部署信息另见: [core/core-frontend/docs/server-deployment.md](../core/core-frontend/docs/server-deployment.md)

---

## 1. 工程结构（后端相关）

| 路径 | 说明 |
|------|------|
| `pom.xml` | 根工程，模块仅声明 `sdk`；Java **21**；Spring Boot **3.5.15** |
| `sdk/` | 公共 SDK、API、扩展（先于 core 安装到本地仓库） |
| `core/pom.xml` | 聚合 `core-frontend` + `core-backend`（需在 `core` 目录单独构建） |
| `core/core-backend/` | 后端主工程，入口 `io.dataease.CoreApplication` |
| `drivers/` | JDBC 驱动 jar（运行时需放到 `/opt/dataease2.0/drivers`） |
| `de-xpack/` | 企业版子模块（当前仓库为空目录，社区/desktop 可忽略） |

打包产物：

```text
core/core-backend/target/CoreApplication.jar
```

服务默认端口：**8100**，API 前缀一般为 `/de2api/`。

---

## 2. 运行环境要求

| 项目 | 要求 | 本机参考 |
|------|------|----------|
| JDK | **21**（`java.version` / CI 均为 21） | Homebrew: `openjdk@21` |
| Maven | 3.9+ | Homebrew: `maven` |
| 前端静态资源 | standalone/desktop 打包会从 `core/core-frontend/dist` 拷贝到后端 `static` | 已有 `dist` 时可跳过前端构建 |
| 运行目录 | `/opt/dataease2.0/`（日志、H2、驱动等） | 需可写 |

### 切换 JDK 21

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
java -version   # 应显示 21.x
mvn -version    # Java version 也应为 21
```

不要用 JDK 17 编译；JDK 26 非项目声明版本，不建议用。

---

## 3. Maven 仓库配置

私服依赖（如 `calcite-core:classifier=de`、`dataease-license-sdk`、`quartz-spring-boot-starter`）在 **fit2cloud**，不在阿里云公共仓。

推荐用户级配置 `~/.m2/settings.xml`：

- 阿里云镜像：`https://maven.aliyun.com/repository/public`
- `mirrorOf` 使用 `*,!fit2cloud-public`，避免镜像拦截私服
- 增加并激活 `fit2cloud-public`：`https://repository.fit2cloud.com/repository/fit2cloud-public/`

若曾因镜像失败产生 `*.lastUpdated`，可删除对应目录下标记后重试，例如：

```bash
find ~/.m2/repository/org/apache/calcite/calcite-core/1.35.33 -name '*.lastUpdated' -delete
find ~/.m2/repository/io/dataease/dataease-license-sdk -name '*.lastUpdated' -delete
```

---

## 4. Profile 说明

在 `core/core-backend/pom.xml` 中定义：

| Profile | 用途 | 数据源 | 备注 |
|---------|------|--------|------|
| `standalone`（默认） | 单机版开发/部署 | MariaDB/MySQL（见 `application-standalone.yml`） | 需本机或远程可达的 MySQL |
| `desktop` | 桌面/简易本地 | 内嵌 H2 | **本地无数据库时推荐** |
| `distributed` | 企业分布式 | 依赖 `distributed` / xpack | 需企业组件 |

`application.yml` 中 `spring.profiles.active` 由打包过滤为 `@profiles.active@`，以 Maven Profile 为准。

### standalone 默认库配置（源码）

```yaml
# application-standalone.yml
url: jdbc:mariadb://localhost:3306/dataease10?...
username: root
password: 123456
```

### desktop 默认库配置（源码）

```yaml
# application-desktop.yml
url: jdbc:h2:/opt/dataease2.0/desktop;...
username: sa
password: 123456
server.address: 127.0.0.1
```

---

## 5. 本地编译

在仓库根目录：

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"

# 1) 安装 sdk
cd /Users/doautumn/fang/datayoo/dataease
mvn clean install -DskipTests

# 2) 只打后端（推荐 desktop；跳过 frontend 模块的 npm）
cd core
mvn clean package -Pdesktop -pl core-backend -am -Dmaven.test.skip=true
```

说明：

- 根 `pom` 不包含 `core`，必须分两步或进入 `core` 再打包。
- 若执行 `cd core && mvn clean package`（不带 `-pl`），会触发 `core-frontend` 的 Node/npm 构建。
- CI 参考：`.github/workflows/desktop_build.yml`（JDK 21 → 根 `mvn clean install` → `core` 下 `-Pdesktop`）。

---

## 6. 运行前准备

```bash
# 运行目录（日志 / H2 / 驱动）
sudo mkdir -p /opt/dataease2.0/{logs/dataease,desktop,drivers,custom-drivers,drivers/plugin,cache,conf,data}
sudo chown -R "$(whoami)" /opt/dataease2.0

# 拷贝 JDBC 驱动
cp /Users/doautumn/fang/datayoo/dataease/drivers/*.jar /opt/dataease2.0/drivers/
```

驱动路径配置项：`dataease.path.driver`（默认 `/opt/dataease2.0/drivers`）。未放置驱动时，启动日志可能出现各类 `ClassNotFoundException`（SQL Server、Oracle、PG 等），一般不影响服务起来，但对应数据源不可用。

---

## 7. 启动后端

### 方式 A：desktop（本地推荐）

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"

cd /Users/doautumn/fang/datayoo/dataease/core/core-backend
java -jar target/CoreApplication.jar
```

验证：

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8100/
# 期望 200
```

H2 Console（desktop）：`http://127.0.0.1:8100/h2-console`  
JDBC URL：`jdbc:h2:/opt/dataease2.0/desktop`

### 方式 B：IDE 运行

1. 使用 JDK 21  
2. 主类：`io.dataease.CoreApplication`  
3. 工作目录建议：`core/core-backend`  
4. Active profile：`desktop` 或 `standalone`（与依赖库一致）  
5. 先完成根目录 `mvn clean install`，保证 `sdk` 已安装

### 方式 C：standalone（需 MySQL/MariaDB）

1. 准备库：创建 `dataease10`（或改 yml 中的库名/账号）  
2. 打包：

```bash
cd /Users/doautumn/fang/datayoo/dataease/core
mvn clean package -Pstandalone -pl core-backend -am -Dmaven.test.skip=true
java -jar core-backend/target/CoreApplication.jar
```

本机若无 MySQL，不要用此模式。

---

## 8. 远程库说明（192.168.0.222）

该机已部署 Docker 版 DataEase + MySQL，**不是**宿主机直接暴露的 MariaDB。

| 项目 | 值 |
|------|-----|
| SSH | `ssh root@192.168.0.222`（密码与运维约定一致） |
| MySQL 容器 | `mysql-de`（MySQL 8.4.5） |
| 库名 | `dataease` |
| Root 密码 | 见服务器 `.env` / `conf/mysql.env`（安装时默认形如 `Password123@mysql`） |
| 3306 | **未映射到宿主机**，本机无法直连 `192.168.0.222:3306` |
| 进库 | `docker exec -it mysql-de mysql -uroot -p'<密码>' dataease` |
| 线上服务 | `http://192.168.0.222:8100` |

本地后端默认不要直接指向该库，以免污染线上数据。若确需联调，应先做端口映射或 SSH 隧道，并单独评估风险。

---

## 9. 常见问题

| 现象 | 原因 / 处理 |
|------|-------------|
| 依赖 `calcite-core:de` / `dataease-license-sdk` 解析失败 | 阿里云 `mirrorOf=*` 挡住 fit2cloud；按第 3 节改 settings |
| `Unable to locate a Java Runtime` / 编译版本不对 | 未切到 JDK 21 |
| standalone 启动连库失败 | 本机无 MySQL，或库名/密码与 yml 不一致；可改用 `-Pdesktop` |
| 日志写失败 / H2 打不开 | `/opt/dataease2.0` 不存在或无写权限 |
| 数据源驱动 ClassNotFound | 未拷贝 `drivers/*.jar` 到 `/opt/dataease2.0/drivers` |
| 整仓 package 很慢 | 触发了 frontend npm；只用 `-pl core-backend -am` |
| Redis | `application.yml` 配了 `127.0.0.1:6379`，health 默认关闭；desktop 本地可先不启 Redis |

---

## 10. 快速命令备忘

```bash
# 环境
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"

# 编译
cd /Users/doautumn/fang/datayoo/dataease && mvn clean install -DskipTests
cd core && mvn clean package -Pdesktop -pl core-backend -am -Dmaven.test.skip=true

# 启动
cd core-backend && java -jar target/CoreApplication.jar

# 停服务（按进程名）
pkill -f 'CoreApplication.jar'
```
