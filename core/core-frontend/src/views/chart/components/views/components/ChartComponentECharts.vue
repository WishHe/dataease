<script lang="ts" setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  shallowRef,
  toRefs
} from 'vue'
import { getData } from '@/api/chart'
import { ChartLibraryType } from '@/views/chart/components/js/panel/types'
import {
  EChartsChartView,
  EChartsWrapper
} from '@/views/chart/components/js/panel/types/impl/echarts'
import chartViewManager from '@/views/chart/components/js/panel'
import { dvMainStoreWithOut } from '@/store/modules/data-visualization/dvMain'
import ViewTrackBar from '@/components/visualization/ViewTrackBar.vue'
import { storeToRefs } from 'pinia'
import { defaultsDeep, cloneDeep } from 'lodash-es'
import ChartError from '@/views/chart/components/views/components/ChartError.vue'
import { BASE_VIEW_CONFIG } from '../../editor/util/chart'
import { customAttrTrans, customStyleTrans, recursionTransObj } from '@/utils/canvasStyle'
import { deepCopy } from '@/utils/utils'
import { trackBarStyleCheck } from '@/utils/canvasUtils'
import { useEmitt } from '@/hooks/web/useEmitt'
import { useI18n } from '@/hooks/web/useI18n'
import { hasNextDrillLevel } from '@/views/chart/components/views/util/drill'
import { ElMessage } from 'element-plus-secondary'

const { t } = useI18n()
const dvMainStore = dvMainStoreWithOut()
const { nowPanelTrackInfo, nowPanelJumpInfo, mobileInPc, inMobile } = storeToRefs(dvMainStore)
const { emitter } = useEmitt()

const props = defineProps({
  element: {
    type: Object,
    default() {
      return { propValue: null }
    }
  },
  view: {
    type: Object,
    default() {
      return { propValue: null }
    }
  },
  showPosition: {
    type: String,
    required: false,
    default: 'canvas'
  },
  scale: {
    type: Number,
    required: false,
    default: 1
  },
  suffixId: {
    type: String,
    required: false,
    default: 'common'
  },
  fontFamily: {
    type: String,
    required: false,
    default: 'inherit'
  },
  active: {
    type: Boolean,
    required: false,
    default: true
  }
})

const emit = defineEmits([
  'onPointClick',
  'onChartClick',
  'onDrillFilters',
  'onJumpClick',
  'resetLoading'
])

const { view, showPosition, scale, suffixId } = toRefs(props)

const isError = ref(false)
const errMsg = ref('')
const linkageActiveHistory = ref(false)

const state = reactive({
  trackBarStyle: {
    position: 'absolute',
    left: '50px',
    top: '50px'
  },
  linkageActiveParam: null as any,
  pointParam: null as any,
  data: { fields: [] }
})

let chartData = shallowRef<Partial<Chart['data']>>({
  fields: []
})

const containerId = 'container-' + showPosition.value + '-' + view.value.id + '-' + suffixId.value
const viewTrack = ref(null)

let myChart: EChartsWrapper | null = null

const clearLinkage = () => {
  linkageActiveHistory.value = false
  try {
    const instance = myChart?.chartInstance
    if (instance) {
      instance.dispatchAction({ type: 'downplay' })
      instance.dispatchAction({ type: 'unselect' })
    }
  } catch (e) {
    console.warn('clearLinkage error')
  }
}

const linkageActivePre = () => {
  if (linkageActiveHistory.value) {
    myChart?.chartInstance?.dispatchAction({ type: 'downplay' })
    myChart?.chartInstance?.dispatchAction({ type: 'unselect' })
  }
  nextTick(() => {
    linkageActive()
  })
}

const linkageActive = () => {
  linkageActiveHistory.value = true
  const instance = myChart?.chartInstance
  if (!instance) return

  const { name } = state.linkageActiveParam

  // 获取当前 option 中的 series data，匹配的 highlight
  const currentOption = instance.getOption()
  const seriesData = (currentOption.series as any[])?.[0]?.data || []

  // 对每个节点：匹配的 highlight，不匹配的 downplay
  seriesData.forEach((item: any) => {
    const itemName = item?.name ?? ''
    if (itemName === name) {
      instance.dispatchAction({ type: 'highlight', name: itemName })
    } else {
      instance.dispatchAction({ type: 'downplay', name: itemName })
    }
  })
}

// ========== 数据获取 ==========

const calcData = async (viewParam: any, callback?: () => void) => {
  if (viewParam.tableId || viewParam['dataFrom'] === 'template') {
    isError.value = false
    const v = JSON.parse(JSON.stringify(viewParam))
    getData(v)
      .then(async res => {
        if (res.code && res.code !== 0) {
          isError.value = true
          errMsg.value = res.msg
          callback?.()
        } else {
          chartData.value = res?.data as Partial<Chart['data']>
          emit('onDrillFilters', res?.drillFilters)
          dvMainStore.setViewDataDetails(viewParam.id, res)
          if (!res.drill && !res.chartExtRequest?.linkageFilters?.length) {
            dvMainStore.setViewOriginData(viewParam.id, chartData.value)
            emitter.emit('chart-data-change')
          }
          await renderChart(res, callback)
        }
      })
      .catch(() => {
        callback?.()
      })
  } else {
    callback?.()
  }
}

let curView: any

const renderChart = async (viewParam: any, callback?: () => void) => {
  if (!viewParam) return
  curView = viewParam

  const chart = deepCopy({
    ...defaultsDeep(viewParam, cloneDeep(BASE_VIEW_CONFIG)),
    data: chartData.value,
    ...(props.fontFamily && props.fontFamily !== 'inherit' ? { fontFamily: props.fontFamily } : {})
  })

  const chartView = chartViewManager.getChartView(viewParam.render, viewParam.type)
  recursionTransObj(customAttrTrans, chart.customAttr, scale.value, 'pc')
  recursionTransObj(customStyleTrans, chart.customStyle, scale.value, 'pc')

  if (chartView?.library === ChartLibraryType.ECHARTS) {
    await renderECharts(chart, chartView as EChartsChartView<any>)
  }
  // 不论成功失败都要调用 callback，否则 loading 不会停
  callback?.()
}

let ecTimer: number
const renderECharts = async (chart: any, chartView: EChartsChartView<any>) => {
  ecTimer && clearTimeout(ecTimer)
  ecTimer = setTimeout(async () => {
    try {
      myChart?.destroy()
      chart.container = containerId
      myChart = await chartView.drawChart({
        chartObj: myChart,
        container: containerId,
        chart: chart,
        action
      })
    } catch (e) {
      console.error('renderECharts error', e)
    }
  }, 50)
}

// ========== 交互事件 ==========

const action = (param: any) => {
  if (param.from) return

  state.pointParam = param

  state.linkageActiveParam = {
    category: param.data?.category ? param.data.category : param.name ? param.name : 'NO_DATA',
    name: param.name ? param.name : 'NO_DATA',
    group: param.data?.group ? param.data.group : 'NO_DATA'
  }

  if (trackMenu.value.length < 2) {
    if (view.value.drillFields.length > 0 && trackMenu.value.length === 0) {
      ElMessage.error(t('chart.last_layer'))
      return
    }
    trackClick(trackMenu.value[0])
  } else {
    const barStyleTemp = {
      left: param.event?.offsetX - 50 || 50,
      top: param.event?.offsetY + 10 || 50
    }
    trackBarStyleCheck(props.element, barStyleTemp, props.scale, trackMenu.value.length)
    state.trackBarStyle.left = barStyleTemp.left + 'px'
    state.trackBarStyle.top = barStyleTemp.top + 'px'
    viewTrack.value?.trackButtonClick(view.value.id)
  }
}

const trackClick = (trackAction: string) => {
  const param = state.pointParam
  if (!param?.data && !param?.name) return

  const checkName = param.name || param.data?.name
  const quotaList = param.data?.quotaList || []

  const linkageParam = {
    option: 'linkage',
    name: checkName,
    viewId: view.value.id,
    dimensionList: param.data?.dimensionList || [],
    quotaList: quotaList
  }
  const jumpParam = {
    option: 'jump',
    name: checkName,
    viewId: view.value.id,
    dimensionList: param.data?.dimensionList || [],
    quotaList: quotaList
  }
  const clickParams = {
    option: 'pointClick',
    name: checkName,
    viewId: view.value.id,
    dimensionList: param.data?.dimensionList || [],
    quotaList: quotaList
  }

  switch (trackAction) {
    case 'pointClick':
      emit('onPointClick', clickParams)
      break
    case 'linkageAndDrill':
      dvMainStore.addViewTrackFilter(linkageParam)
      emit('onChartClick', param)
      break
    case 'drill':
      emit('onChartClick', param)
      break
    case 'linkage':
      linkageActivePre()
      dvMainStore.addViewTrackFilter(linkageParam)
      break
    case 'jump':
      if (mobileInPc.value && !inMobile.value) return
      emit('onJumpClick', jumpParam)
      break
    default:
      break
  }
}

const trackMenu = computed(() => {
  let trackMenuInfo: string[] = []
  if (!['multiplexing', 'viewDialog'].includes(showPosition.value)) {
    const drillFields: string[] =
      curView?.drill && curView?.drillFilters?.length
        ? curView.drillFilters.map((item: any) => item.fieldId)
        : []

    let linkageCount = 0
    let jumpCount = 0

    chartData.value?.fields
      ?.filter((item: any) => !drillFields.includes(item.id))
      .forEach((item: any) => {
        const sourceInfo = view.value.id + '#' + item.id
        if (nowPanelTrackInfo.value[sourceInfo]) linkageCount++
        if (nowPanelJumpInfo.value[sourceInfo]) jumpCount++
      })

    if (view.value?.drillFields && curView?.drillFilters && curView.drillFilters.length > 0) {
      const lastItem = view.value?.drillFields[curView.drillFilters.length]
      const sourceInfo = view.value.id + '#' + lastItem.id
      if (nowPanelTrackInfo.value[sourceInfo]) linkageCount++
      if (nowPanelJumpInfo.value[sourceInfo]) jumpCount++
    }

    jumpCount &&
      view.value?.jumpActive &&
      (!mobileInPc.value || inMobile.value) &&
      trackMenuInfo.push('jump')
    linkageCount && view.value?.linkageActive && trackMenuInfo.push('linkage')
    hasNextDrillLevel(
      curView?.drillFields || view.value.drillFields,
      curView?.drillFilters?.length || 0
    ) && trackMenuInfo.push('drill')

    if (trackMenuInfo.length === 3 && props.element.actionSelection?.linkageActive === 'auto') {
      trackMenuInfo = ['jump', 'linkageAndDrill']
    } else if (
      trackMenuInfo.length === 2 &&
      props.element.actionSelection?.linkageActive === 'auto' &&
      !trackMenuInfo.includes('jump')
    ) {
      trackMenuInfo = ['linkageAndDrill']
    }
  }
  return trackMenuInfo
})

// ========== 生命周期 ==========

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  const containerDom = document.getElementById(containerId)
  if (containerDom) {
    resizeObserver = new ResizeObserver(() => {
      myChart?.render()
    })
    resizeObserver.observe(containerDom)
  }
})

onBeforeUnmount(() => {
  try {
    clearTimeout(ecTimer)
    myChart?.destroy()
    resizeObserver?.disconnect()
  } catch (e) {
    console.warn(e)
  }
})

defineExpose({
  calcData,
  renderChart,
  trackMenu,
  clearLinkage
})
</script>

<template>
  <div class="echarts-area" @wheel.stop>
    <view-track-bar
      ref="viewTrack"
      :track-menu="trackMenu"
      :font-family="fontFamily"
      class="track-bar"
      :style="state.trackBarStyle"
      @trackClick="trackClick"
    />
    <div
      :id="containerId"
      class="echarts-container"
      :style="{ width: '100%', height: '100%' }"
    ></div>
    <chart-error v-if="isError" :err-msg="errMsg" />
  </div>
</template>

<style lang="less" scoped>
.echarts-area {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.echarts-container {
  width: 100%;
  height: 100%;
}

.track-bar {
  z-index: 10;
}
</style>
