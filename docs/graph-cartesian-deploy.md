# 笛卡尔关系图 — 后端增量部署指南

## 后端改动文件

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `core/core-backend/src/main/java/.../impl/others/GraphCartesianHandler.java` | 图表 Handler，合并维度/指标轴到 SQL 查询 |
| 修改 | `core/core-backend/src/main/java/.../manage/ChartDataManage.java` | `sqlData()` 方法增加 `graph-cartesian` 类型判断 |

## 部署策略

Spring Boot fat JAR 增量更新——只替换修改的 `.class` 文件，不重新构建整个 JAR。

## 环境要求

| 工具 | 版本 | 用途 |
|------|------|------|
| JDK | 21 | 编译 Java 源码（与容器内运行时版本一致） |
| `sshpass` | — | 免交互 SSH 登录 |
| 服务器 JAR | — | 提取 `BOOT-INF/classes/` 作为编译 classpath |

## 部署步骤

### 1. 从服务器提取 classpath

```bash
# 缓存 JAR 到宿主机
ssh root@192.168.0.222
docker cp dataease:/opt/apps/app.jar /tmp/app4compile.jar

# 提取 BOOT-INF/classes（项目预编译类）
mkdir /tmp/jar_classes_dl && cd /tmp/jar_classes_dl
jar xf /tmp/app4compile.jar BOOT-INF/classes/
tar czf /tmp/classes.tar.gz BOOT-INF/
# → /tmp/classes.tar.gz (≈ 35 MB 压缩后)
```

### 2. 本地下载 classpath 并编译

```bash
# 下载 classes 压缩包
scp root@192.168.0.222:/tmp/classes.tar.gz /tmp/classes.tar.gz
tar xzf /tmp/classes.tar.gz -C /tmp/jar_classes

# 解析 Maven 依赖到本地仓库（仅依赖解析，不编译源码）
mvn dependency:resolve -f core/pom.xml -pl core-backend -DskipTests

# 构建 classpath
M2_CP=$(find ~/.m2/repository -name "*.jar" -type f | tr '\n' ':')
CLASSES_CP="/tmp/jar_classes/BOOT-INF/classes"

# 编译（JDK 21）
/opt/homebrew/opt/openjdk@21/bin/javac \
  -cp "$CLASSES_CP:$M2_CP" \
  -d /tmp/de_classes_final \
  -parameters \
  core/core-backend/src/main/java/.../GraphCartesianHandler.java \
  core/core-backend/src/main/java/.../ChartDataManage.java
```

### 3. 打包并上传（⚠️ 关键：禁用 macOS xattr）

```bash
# 按 JAR 内部路径组织目录结构
rm -rf /tmp/deploy_proper
mkdir -p /tmp/deploy_proper/BOOT-INF/classes
cp -r /tmp/de_classes_final/io /tmp/deploy_proper/BOOT-INF/classes/

# ⚠️ COPYFILE_DISABLE=1 防止 macOS 生成 ._* 元数据文件
cd /tmp/deploy_proper
COPYFILE_DISABLE=1 tar czf /tmp/deploy_proper.tar.gz .

# 上传
scp /tmp/deploy_proper.tar.gz root@192.168.0.222:/tmp/
```

### 4. 服务器端注入 JAR

```bash
ssh root@192.168.0.222

# 从容器取出 JAR（即使容器已停止也可 docker cp）
docker cp dataease:/opt/apps/app.jar /tmp/app_final.jar

# ⚠️ 先删除历史遗留的 ._* 垃圾文件
for f in $(jar tf /tmp/app_final.jar | grep "\._"); do
  zip -d /tmp/app_final.jar "$f"
done

# 注入新 class 文件
cd /tmp && mkdir deploy && cd deploy && tar xzf /tmp/deploy_proper.tar.gz
jar uf /tmp/app_final.jar .

# 验证
jar tf /tmp/app_final.jar | grep "BOOT-INF.*GraphCartesian"
# 应输出: BOOT-INF/classes/io/dataease/chart/charts/impl/others/GraphCartesianHandler.class

# 放回容器并启动
docker cp /tmp/app_final.jar dataease:/opt/apps/app.jar
docker start dataease
```

### 5. 验证

```bash
# 等待 healthy
docker ps --format "{{.Names}} {{.Status}}" | grep dataease
# → dataease Up XX seconds (healthy)

# HTTP 检查
curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/
# → 200
```

## 常见问题

### 容器启动失败：`Incompatible class format`

```
BeanDefinitionStoreException: Incompatible class format in URL
[jar:file:/opt/apps/app.jar!/.../._GraphCartesianHandler.class]
```

原因：macOS 打包 tar 时自动生成了 `._*` 前缀的 AppleDouble 元数据文件，Spring 将其当作 class 文件扫描导致解析失败。

解决：
1. 打包时使用 `COPYFILE_DISABLE=1 tar czf ...`
2. 若已混入 JAR，用 `zip -d` 删除：

```bash
for f in $(jar tf /tmp/app.jar | grep "\._"); do
  zip -d /tmp/app.jar "$f"
done
```

### 编译错误：找不到符号 getXxx()

原因：Lombok 注解只在编译主文件时处理，`-sourcepath` 引入的其他源码文件不会触发 Lombok。

解决：**不要用 `-sourcepath`**，改用预编译的 `BOOT-INF/classes/` 作为 classpath。

### JDK 版本不匹配

宿主机 JDK 8，容器内 JDK 21。编译时必须使用 JDK 21：

```bash
# macOS 安装 JDK 21
brew install openjdk@21
# 路径: /opt/homebrew/opt/openjdk@21/bin/javac
```

### 容器停止后 docker cp 失败

`docker cp` 对停止的容器也有效，无需容器运行。

### Class 路径不正确

`jar uf -C /tmp/deploy .` 会在 JAR **根目录**下放置文件。  
必须将文件放在 `BOOT-INF/classes/` 下，Spring Boot 才识别：

```
/tmp/deploy/
└── BOOT-INF/
    └── classes/
        └── io/
            └── dataease/
                └── chart/
                    └── ...
```

## 快速命令汇总

```bash
# === 本地 ===
# 1. 编译
mvn dependency:resolve -f core/pom.xml -pl core-backend -DskipTests
M2_CP=$(find ~/.m2/repository -name "*.jar" -type f | tr '\n' ':')
/opt/homebrew/opt/openjdk@21/bin/javac -cp "/tmp/jar_classes/BOOT-INF/classes:$M2_CP" -d /tmp/de_classes_final -parameters GraphCartesianHandler.java ChartDataManage.java

# 2. 打包（关键：禁用 xattr）
rm -rf /tmp/deploy_proper
mkdir -p /tmp/deploy_proper/BOOT-INF/classes
cp -r /tmp/de_classes_final/io /tmp/deploy_proper/BOOT-INF/classes/
cd /tmp/deploy_proper && COPYFILE_DISABLE=1 tar czf /tmp/deploy_proper.tar.gz .

# 3. 上传
scp /tmp/deploy_proper.tar.gz root@192.168.0.222:/tmp/

# === 服务器 ===
# 4. 清理旧垃圾 + 注入新 class + 启动
docker cp dataease:/opt/apps/app.jar /tmp/app.jar
for f in $(jar tf /tmp/app.jar | grep "\._"); do zip -d /tmp/app.jar "$f"; done
cd /tmp && rm -rf deploy && mkdir deploy && cd deploy && tar xzf /tmp/deploy_proper.tar.gz
jar uf /tmp/app.jar .
docker cp /tmp/app.jar dataease:/opt/apps/app.jar && docker start dataease
```
