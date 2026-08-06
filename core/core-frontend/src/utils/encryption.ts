import CryptoJS from 'crypto-js/crypto-js'
import JSEncrypt from 'jsencrypt/bin/jsencrypt.min'
import { Base64 } from 'js-base64'
import { useCache } from '@/hooks/web/useCache'
import { useAppStoreWithOut } from '@/store/modules/app'

const appStore = useAppStoreWithOut()

const { wsCache } = useCache()

const rsaKey = '-pk_separator-'
const crypt = new JSEncrypt()

const aesDecrypt = (word, keyStr) => {
  const keyHex = CryptoJS.enc.Utf8.parse(keyStr)
  // 硬编码 IV "0000000000000000"，与后端 RsaUtils.ascEncrypt 中的 IV_KEY 保持一致
  const ivHex = CryptoJS.enc.Utf8.parse('0000000000000000')
  const decrypt = CryptoJS.AES.decrypt(word, keyHex, {
    iv: ivHex,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
  })
  return decrypt.toString(CryptoJS.enc.Utf8)
}

export const rsaEncryp = word => {
  const separator = Base64.encodeURI(rsaKey) + '='
  const dekey = wsCache.get(appStore.getDekey)
  const keyArray = dekey.split(separator)
  const k1 = keyArray[0]
  const k2 = keyArray[1]
  const pk = aesDecrypt(k1, k2)
  crypt.setKey(pk)
  return crypt.encrypt(word)
}

export const symmetricDecrypt = (data, keyStr) => {
  const cipherHex = CryptoJS.enc.Base64.parse(data)
  // 旧后端不预置 IV，使用硬编码 IV "0000000000000000" 解密
  const iv = CryptoJS.enc.Utf8.parse('0000000000000000')
  const key = CryptoJS.enc.Base64.parse(keyStr)
  const decrypted = CryptoJS.AES.decrypt({ ciphertext: cipherHex }, key, {
    iv: iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
  })
  return decrypted.toString(CryptoJS.enc.Utf8)
}
