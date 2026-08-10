<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useI18n } from '@/hooks/web/useI18n'
import { FormRules, FormInstance } from 'element-plus-secondary'
import { loginApi, queryDekey } from '@/api/login'
import { useCache } from '@/hooks/web/useCache'
import { useAppStoreWithOut } from '@/store/modules/app'
import { CustomPassword } from '@/components/custom-password'
import { useUserStoreWithOut } from '@/store/modules/user'
import { useAppearanceStoreWithOut } from '@/store/modules/appearance'
import { rsaEncryp } from '@/utils/encryption'
import router from '@/router'
import { ElMessage } from 'element-plus-secondary'
import { XpackComponent } from '@/components/plugin'
import { logoutHandler } from '@/utils/logout'
import { cleanPlatformFlag } from '@/utils/utils'
import xss from 'xss'
const { wsCache } = useCache()
const appStore = useAppStoreWithOut()
const userStore = useUserStoreWithOut()
const appearanceStore = useAppearanceStoreWithOut()
const { t } = useI18n()
const contentShow = ref(true)
const loading = ref(false)
const axiosFinished = ref(true)
const showFoot = ref(false)
const showSlogan = ref(true)
const loginLogoUrl = ref(null)
const msg = ref(null)
const slogan = ref(null)
const footContent = ref(null)
const loginErrorMsg = ref('')
const xpackLoginHandler = ref()
const showDempTips = ref(false)
const xpackInvalidPwd = ref()
const demoTips = computed(() => {
  if (!showDempTips.value) {
    return ''
  }
  return appearanceStore.getDemoTipsContent || ''
})
const state = reactive({
  loginForm: {
    username: '',
    password: ''
  },
  footContent: ''
})

const rules = reactive<FormRules>({
  username: [{ required: true, message: t('common.required'), trigger: 'blur' }],
  password: [{ required: true, message: t('common.required'), trigger: 'blur' }]
})

const activeName = ref('simple')

const getCurLocation = () => {
  let queryRedirectPath = '/workbranch/index'
  if (router.currentRoute.value.query.redirect) {
    queryRedirectPath = router.currentRoute.value.query.redirect as string
  }
  return queryRedirectPath
}
const enterHandler = e => {
  e.target.blur()
  e.stopPropagation()
  handleLogin()
}
const formRef = ref<FormInstance | undefined>()
const duringLogin = ref(true)
const handleLogin = () => {
  if (!formRef.value) return
  formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      const name = state.loginForm.username.trim()
      const pwd = state.loginForm.password
      if (!wsCache.get(appStore.getDekey)) {
        const res = await queryDekey()
        wsCache.set(appStore.getDekey, res.data)
      }
      const param = { name: rsaEncryp(name), pwd: rsaEncryp(pwd) }
      const isLdap = activeName.value === 'ldap'
      if (isLdap) {
        param['origin'] = 1
      }
      duringLogin.value = true
      cleanPlatformFlag()
      loginApi(param)
        .then(res => {
          const { token, exp, mfa } = res.data
          if (!isLdap && !xpackLoadFail.value && xpackInvalidPwd.value?.invokeMethod) {
            const param = {
              methodName: 'init',
              args: res.data
            }
            xpackInvalidPwd?.value.invokeMethod(param)
            return
          }
          if (!isLdap && mfa?.enabled) {
            xpackLoginHandler.value?.invokeMethod({ methodName: 'toMfa', args: mfa })
            duringLogin.value = false
            return
          }
          userStore.setToken(token)
          userStore.setExp(exp)
          userStore.setTime(Date.now())
          const queryRedirectPath = getCurLocation()
          router.push({ path: queryRedirectPath })
        })
        .catch(() => {
          duringLogin.value = false
        })
    }
  })
}
const invalidPwdCb = cbParam => {
  const val = cbParam['status']
  duringLogin.value = !!val
  if (val) {
    const mfa = cbParam['mfa']
    if (mfa?.enabled) {
      xpackLoginHandler.value?.invokeMethod({ methodName: 'toMfa', args: mfa })
      duringLogin.value = false
      return
    }
    const queryRedirectPath = getCurLocation()
    router.push({ path: queryRedirectPath })
  }
}
const xpackLoadFail = ref(false)
const loadingText = ref('加载中...')
const loginContainer = ref()

const preheat = ref(true)
const showLoginErrorMsg = () => {
  if (!loginErrorMsg.value) {
    return
  }
  if (loginErrorMsg.value.includes('pwd has been changed')) {
    ElMessage.error(t('user.password_changed_relogin'))
    return
  }
  if (loginErrorMsg.value.includes('token is empty')) {
    ElMessage.error('token为空！')
    return
  }
  if (loginErrorMsg.value.includes('token is Expired')) {
    ElMessage.error('登录信息已过期，请重新登录！')
    return
  }
  if (loginErrorMsg.value.includes('token is destroyed')) {
    ElMessage.error('登录信息已销毁，请重新登录！')
    return
  }
  if (loginErrorMsg.value.startsWith('user_disable')) {
    ElMessage.error('用户已被禁用，无法登录！')
    return
  }
  if (loginErrorMsg.value.startsWith('permission has been changed')) {
    ElMessage.error('默认组织已发生变更，请重新登录！')
    return
  }
  ElMessage.error(loginErrorMsg.value)
}

const loadArrearance = () => {
  showDempTips.value = appearanceStore.getShowDemoTips
  if (appearanceStore.getLogin) {
    loginLogoUrl.value = appearanceStore.getLogin
  }
  if (appearanceStore.getShowSlogan) {
    showSlogan.value = appearanceStore.getShowSlogan === 'true'
  }
  if (appearanceStore.getSlogan) {
    slogan.value = appearanceStore.getSlogan
  }
  if (appearanceStore.getFoot) {
    showFoot.value = appearanceStore.getFoot === 'true'
    if (showFoot.value) {
      const content = appearanceStore.getFootContent
      const myXss = new xss['FilterXSS']({
        css: {
          whiteList: {
            'background-color': true,
            'text-align': true,
            color: true,
            'margin-top': true,
            'margin-bottom': true,
            'line-height': true,
            'box-sizing': true,
            'padding-top': true,
            'padding-bottom': true,
            'font-size': true
          }
        },
        whiteList: {
          ...xss['whiteList'],
          p: ['style'],
          span: ['style']
        }
      })
      footContent.value = myXss.process(content)
    }
  }
}
const switchTab = (name: string) => {
  activeName.value = name || 'simple'
}
const autoCallback = (param: any) => {
  activeName.value = param.activeName || 'simple'
  preheat.value = param.preheat
  if (param.loadingText) {
    loadingText.value = param.loadingText
  }
}
const handlerFail = () => {
  const param = {
    activeName: 'simple',
    preheat: false
  }
  autoCallback(param)
}
onMounted(async () => {
  loadArrearance()
  duringLogin.value = false
  if (localStorage.getItem('DE-GATEWAY-FLAG')) {
    const msg = localStorage.getItem('DE-GATEWAY-FLAG')
    loginErrorMsg.value = decodeURIComponent(msg)
    showLoginErrorMsg()
    localStorage.removeItem('DE-GATEWAY-FLAG')
    logoutHandler(true)
  }
  if (!wsCache.get(appStore.getDekey)) {
    queryDekey().then(res => {
      wsCache.set(appStore.getDekey, res.data)
    })
  }
})
</script>

<template>
  <div
    v-if="preheat"
    ref="loginContainer"
    class="preheat-container"
    v-loading="true"
    :element-loading-text="loadingText"
    element-loading-background="#F5F6F7"
  />
  <div v-show="contentShow" class="login-background" v-loading="duringLogin">
    <div class="login-container" ref="loginContainer">
      <div class="login-form-content" v-loading="loading">
        <div class="login-form-center">
          <el-form
            ref="formRef"
            :model="state.loginForm"
            :rules="rules"
            size="default"
            :disabled="preheat"
          >
            <div class="login-logo">
              <img
                v-if="!loginLogoUrl && axiosFinished"
                src="/zoogen-login.svg"
                class="login-logo-icon"
                alt="logo"
              />
              <img v-if="loginLogoUrl && axiosFinished" :src="loginLogoUrl" alt="" />
            </div>
            <!-- <div v-if="showSlogan" class="login-welcome">
              {{ slogan || t('system.available_to_everyone') }}
            </div> -->
            <div class="login-form">
              <div
                class="default-login-tabs"
                v-if="activeName === 'simple' || activeName === 'ldap'"
              >
                <div class="login-form-title">
                  <span>{{
                    activeName === 'ldap' ? t('login.ldap_login') : t('login.account_login')
                  }}</span>
                </div>
                <el-form-item class="login-form-item login-input-module" prop="username">
                  <el-input
                    v-model="state.loginForm.username"
                    :placeholder="`${t('common.account')}${
                      activeName === 'simple' ? '/' + t('commons.email') : ''
                    }`"
                    autofocus
                  />
                </el-form-item>
                <el-form-item class="login-input-module" prop="password">
                  <CustomPassword
                    v-model="state.loginForm.password"
                    :placeholder="t('common.pwd')"
                    show-password
                    maxlength="30"
                    show-word-limit
                    autocomplete="new-password"
                    @keypress.enter.stop="enterHandler"
                  />
                </el-form-item>
                <div class="login-btn">
                  <el-button
                    type="primary"
                    class="submit"
                    size="default"
                    :disabled="duringLogin"
                    @click="handleLogin"
                  >
                    {{ t('login.btn') }}
                  </el-button>
                  <div v-if="showDempTips" class="demo-tips">
                    <span>{{ demoTips }}</span>
                  </div>
                </div>
              </div>

              <XpackComponent
                ref="xpackLoginHandler"
                jsname="L2NvbXBvbmVudC9sb2dpbi9IYW5kbGVy"
                @switch-tab="switchTab"
                @auto-callback="autoCallback"
                @load-fail="handlerFail"
              />
              <XpackComponent
                ref="xpackInvalidPwd"
                jsname="L2NvbXBvbmVudC9sb2dpbi9JbnZhbGlkUHdk"
                @load-fail="() => (xpackLoadFail = true)"
                @call-back="invalidPwdCb"
              />
            </div>

            <div class="login-msg">
              {{ msg }}
            </div>
          </el-form>
        </div>
        <div v-if="showFoot" class="dynamic-login-foot" v-html="footContent" />
      </div>
      <div class="login-footer">
        Copyright &copy; {{ new Date().getFullYear() }} DataYoo. All Rights Reserved.
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.preheat-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ed-color-primary);
  position: absolute;
  z-index: 100;
}
.login-background {
  height: 100vh;
  width: 100vw;
  // background: linear-gradient(135deg, #eaf3f4 0%, #d5e8ea 30%, #f0f4f5 60%, #e8edf0 100%);
  background: url(/login-bg.svg) no-repeat 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -180px;
    right: -120px;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(42, 139, 146, 0.08) 0%, transparent 70%);
    pointer-events: none;
  }
  &::after {
    content: '';
    position: absolute;
    bottom: -200px;
    left: -100px;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(42, 139, 146, 0.06) 0%, transparent 70%);
    pointer-events: none;
  }
}

.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  // justify-content: center;
  position: relative;
  z-index: 1;
  padding-top: 110px;

  .login-image-content {
    display: none;
  }

  .login-form-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;

    .login-form-center {
      width: 420px;
      padding: 48px 40px;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0px 8px 32px rgba(31, 35, 41, 0.06);
    }
  }

  .login-logo {
    text-align: center;
    margin-bottom: 24px;
    img {
      height: 36px;
      width: auto;
    }
  }

  .login-title {
    margin-top: 50px;
    font-size: 32px;
    letter-spacing: 0;
    text-align: center;
    color: #999999;

    @media only screen and (max-width: 1280px) {
      margin-top: 20px;
    }
  }

  .login-border {
    height: 2px;
    margin: 20px auto 20px;
    position: relative;
    width: 80px;
    background: var(--ed-color-primary);
    @media only screen and (max-width: 1280px) {
      margin: 20px auto 20px;
    }
  }

  .login-welcome {
    text-align: center;
    margin-top: 4px;
    color: #646a73;
    font-family: var(--de-custom_font, 'PingFang');
    font-size: 14px;
    font-style: normal;
    font-weight: 400;
    line-height: 20px;
    word-wrap: break-word;
  }

  .demo-tips {
    position: absolute;
    font-size: 18px;
    color: #f56c6c;
    letter-spacing: 0;
    line-height: 18px;
    text-align: center;
    top: 120px;
    @media only screen and (max-width: 1280px) {
      margin-top: 20px;
    }
  }

  .login-form {
    margin-top: 28px;
    padding: 0;

    .login-input-module {
      width: 100%;
      :deep(.ed-input) {
        height: 40px;
        line-height: 40px;
      }
      :deep(.ed-input__wrapper) {
        padding: 1px 12px;
        border-radius: 6px;
      }
    }

    .login-form-item {
      margin-top: 20px;
    }

    .ed-form-item--default {
      margin-bottom: 20px;
    }

    .login-form-title {
      margin-bottom: 4px;
      color: #1f2329;
      font-family: var(--de-custom_font, 'PingFang');
      font-size: 18px;
      font-weight: 500;
      line-height: 26px;
      text-align: center;
    }
  }

  :deep(.ed-divider__text) {
    color: #8f959e;
    font-family: var(--de-custom_font, 'PingFang');
    font-size: 12px;
    font-style: normal;
    font-weight: 400;
    line-height: 20px;
    padding: 0 8px;
  }

  .login-btn {
    position: relative;
    margin-top: 24px;
    .submit {
      width: 100%;
      height: 40px;
      line-height: 40px;
      border-radius: 6px;
    }
  }

  .login-msg {
    margin-top: 12px;
    color: #f56c6c;
    text-align: center;
    font-size: 13px;
  }

  .login-image {
    display: none;
  }

  .login-image-de {
    display: none;
  }
}

.login-footer {
  position: absolute;
  bottom: 28px;
  left: 0;
  width: 100%;
  text-align: center;
  color: #8f959e;
  font-family: var(--de-custom_font, 'PingFang');
  font-size: 13px;
  line-height: 20px;
  z-index: 1;
}

.dynamic-login-foot {
  visibility: visible;
  width: 100%;
  position: absolute;
  z-index: 302;
  bottom: 0;
  left: 0;
  height: auto;
  padding-top: 1px;
  zoom: 1;
  margin: 0;
}

.login-logo-icon {
  width: auto;
  height: 52px;
}

// 响应式: 窄屏时缩小表单宽度
@media only screen and (max-width: 480px) {
  .login-container .login-form-content .login-form-center {
    width: 92vw;
    padding: 32px 24px;
  }
}
</style>
