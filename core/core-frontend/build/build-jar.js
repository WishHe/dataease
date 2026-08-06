/**
 * 将前端 dist/ 打包为 JAR（路径: BOOT-INF/classes/static/）
 *
 * 用法: node build/build-jar.js
 * 产物: dist/frontend.jar
 */

const { execSync } = require('child_process')
const path = require('path')
const fs = require('fs')

const ROOT = path.resolve(__dirname, '..')
const DIST = path.join(ROOT, 'dist')
const OUTPUT = path.join(DIST, 'frontend.jar')

const log = { info: m => console.log(`\x1b[36m${m}\x1b[0m`), ok: m => console.log(`\x1b[32m${m}\x1b[0m`), err: m => { console.log(`\x1b[31m${m}\x1b[0m`); process.exit(1) } }

console.log('\x1b[33m=== DataEase 前端 JAR 打包 ===\x1b[0m\n')

// 1. 构建
log.info('[1/2] npm run build:base')
execSync('npm run build:base', { cwd: ROOT, stdio: 'inherit' })
if (!fs.existsSync(path.join(DIST, 'index.html'))) log.err('构建失败')

// 2. 打包为 JAR
log.info('\n[2/2] 打包 frontend.jar')
const TMP = path.join(ROOT, 'build/.tmp_jar')
fs.rmSync(TMP, { recursive: true, force: true })
fs.mkdirSync(path.join(TMP, 'BOOT-INF/classes/static'), { recursive: true })
execSync(`cp -r ${DIST}/* ${path.join(TMP, 'BOOT-INF/classes/static')}/`, { stdio: 'pipe' })
execSync(`jar cfM0 ${OUTPUT} -C ${TMP} .`, { cwd: ROOT, stdio: 'pipe' })
fs.rmSync(TMP, { recursive: true, force: true })

const size = (fs.statSync(OUTPUT).size / 1024 / 1024).toFixed(1)
log.ok(`\n完成: dist/frontend.jar (${size} MB)`)
