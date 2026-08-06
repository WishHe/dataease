/**
 * DataEase 前端一键部署
 *
 * 用法: node build/deploy.js
 */

const path = require('path')
const inquirer = require('inquirer')
const ora = require('ora')
const ProgressBar = require('progress')
const { NodeSSH } = require('node-ssh')
const fs = require('fs')

const ssh = new NodeSSH()
const ROOT = path.resolve(__dirname, '..')
const JAR_FILE = path.join(ROOT, 'dist/frontend.jar')

const log = {
  info: m => console.log(`\x1b[36m${m}\x1b[0m`),
  ok: m => console.log(`\x1b[32m${m}\x1b[0m`),
  err: m => console.log(`\x1b[31m${m}\x1b[0m`),
  yel: m => console.log(`\x1b[33m${m}\x1b[0m`)
}

const envList = [
  {
    name: '192.168.0.222 (测试)',
    host: '192.168.0.222',
    port: 22,
    username: 'root',
    password: 'Sengee123',
    container: 'dataease',
    jarPath: '/opt/apps/app.jar'
  }
]

const nowDate = () => {
  const d = new Date()
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
}

let cfg

// 1. 连服务器
async function connect() {
  const s = ora('连接服务器...').start()
  try {
    await ssh.connect({ host: cfg.host, port: cfg.port, username: cfg.username, password: cfg.password })
    s.succeed('SSH 连接成功')
  } catch (e) {
    s.fail('SSH 连接失败: ' + e.message)
    process.exit(1)
  }
}

// 2. 备份
async function backup() {
  const name = `app.jar.bak.${nowDate()}`
  const s = ora('备份 JAR...').start()
  const r = await ssh.execCommand(`docker cp ${cfg.container}:${cfg.jarPath} /tmp/${name}`)
  if (r.code === 0) s.succeed(`已备份: /tmp/${name}`)
  else { s.fail(r.stderr); process.exit(1) }
}

// 3. 上传
async function upload() {
  log.yel('上传 frontend.jar ...')
  let bar = null
  const total = fs.statSync(JAR_FILE).size
  await ssh.putFile(JAR_FILE, '/tmp/frontend.jar', null, {
    step: (t, chunk, total) => {
      if (!bar) bar = new ProgressBar('  [:bar] :percent :etas', { complete: '=', incomplete: ' ', width: 30, total })
      bar.tick(chunk)
    },
    concurrency: 1
  })
  log.ok('上传完成')
}

// 4. 更新 JAR（删旧 static → 注入新 static）
async function updateJar() {
  const s = ora('更新 JAR...').start()

  // 从容器拷贝 app.jar 到宿主机
  s.text = '拷贝 JAR...'
  let r = await ssh.execCommand(`docker cp ${cfg.container}:${cfg.jarPath} /tmp/app_tmp.jar`)
  if (r.code !== 0) { s.fail(r.stderr); process.exit(1) }

  // 删除旧 static 文件
  s.text = '删除旧前端文件...'
  r = await ssh.execCommand(`jar tf /tmp/app_tmp.jar | grep 'BOOT-INF/classes/static/' | xargs -r -I{} jar -f /tmp/app_tmp.jar -d "{}"`)
  // xargs fails if no matches, that's ok

  // 解压 frontend.jar → 注入 app.jar
  s.text = '注入新前端文件...'
  r = await ssh.execCommand(`mkdir -p /tmp/fe && cd /tmp/fe && jar xf /tmp/frontend.jar && jar uf /tmp/app_tmp.jar -C /tmp/fe .`)
  if (r.code !== 0) { s.fail(r.stderr); process.exit(1) }

  // 放回容器
  s.text = '放回容器...'
  r = await ssh.execCommand(`docker cp /tmp/app_tmp.jar ${cfg.container}:${cfg.jarPath}`)
  if (r.code !== 0) { s.fail(r.stderr); process.exit(1) }

  // 清理
  await ssh.execCommand('rm -rf /tmp/app_tmp.jar /tmp/frontend.jar /tmp/fe')

  s.succeed('JAR 更新完成')
}

// 5. 重启
async function restart() {
  const s = ora('重启容器...').start()
  await ssh.execCommand(`docker restart ${cfg.container}`)
  s.succeed('容器已重启')
}

// 6. 等就绪
async function waitReady() {
  const s = ora('等待就绪...').start()
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 2000))
    const r = await ssh.execCommand("curl -s -o /dev/null -w '%{http_code}' http://localhost:8100/")
    if (r.stdout?.trim() === '200') { s.succeed('前端可访问'); return }
    s.text = `等待... (${(i + 1) * 2}s)`
  }
  s.warn('超时，请手动检查')
}

// 主流程
(async () => {
  const { env } = await inquirer.prompt([{ type: 'list', message: '选择部署环境:', name: 'env', prefix: '☆', choices: envList.map(e => e.name) }])
  cfg = envList.find(e => e.name === env)

  if (!fs.existsSync(JAR_FILE)) {
    log.err('frontend.jar 不存在，请先执行: node build/build-jar.js')
    process.exit(1)
  }

  log.yel(`\n目标: ${cfg.name}\n`)

  await connect()
  await backup()
  await upload()
  await updateJar()
  await restart()
  await waitReady()

  log.ok(`\n部署完成! http://${cfg.host}:8100/`)
  ssh.dispose()
})()
