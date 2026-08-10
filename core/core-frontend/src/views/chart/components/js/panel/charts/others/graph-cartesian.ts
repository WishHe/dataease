import {
  EChartsChartView,
  EChartsDrawOptions,
  EChartsWrapper
} from '@/views/chart/components/js/panel/types/impl/echarts'
import type { EChartsOption } from 'echarts'
import { init } from 'echarts'
import { cloneDeep } from 'lodash-es'
import { flow, hexColorToRGBA, parseJson } from '@/views/chart/components/js/util'
import { valueFormatter } from '@/views/chart/components/js/formatter'
import { useI18n } from '@/hooks/web/useI18n'
import {
  GRAPH_CARTESIAN_AXIS_TYPE,
  GRAPH_CARTESIAN_EDITOR_PROPERTY,
  GRAPH_CARTESIAN_EDITOR_PROPERTY_INNER
} from '@/views/chart/components/js/panel/charts/others/graph-cartesian-common'

const { t } = useI18n()
const DEFAULT_DATA: any[] = []

/**
 * 笛卡尔关系图
 *
 * 数据模型（一行 = 一条有向边 + 源节点位置信息）：
 * - xAxis 维度  → X 轴坐标 (category)
 * - yAxis 指标  → Y 轴坐标 (value)
 * - xAxisExt 维度 → 源：节点唯一标识 + link 起点 (dimensionList[1])
 * - extStack 维度 → 目的：link 终点 (dimensionList[2])，null 表示只有节点无边
 * - extBubble 指标 → 节点大小（可选）
 * - extLabel 指标  → 连线粗细（可选，值在 dynamicLabelValue 中）
 *
 * 多指标时数据按指标字段拆分为多行，需按「源」分组合并
 */
export class GraphCartesian extends EChartsChartView<EChartsOption> {
  properties = GRAPH_CARTESIAN_EDITOR_PROPERTY
  propertyInner = {
    ...GRAPH_CARTESIAN_EDITOR_PROPERTY_INNER,
    'label-selector': ['fontSize', 'color', 'labelFormatter']
  }
  axis: AxisType[] = [...GRAPH_CARTESIAN_AXIS_TYPE]
  axisConfig = {
    xAxis: {
      name: `${t('chart.drag_block_type_axis')} / ${t('chart.dimension')}`,
      type: 'd',
      limit: 1
    },
    yAxis: {
      name: `${t('chart.drag_block_value_axis')} / ${t('chart.quota')}`,
      type: 'q',
      limit: 1
    },
    xAxisExt: {
      name: `源 / ${t('chart.dimension')}`,
      type: 'd',
      limit: 1
    },
    extStack: {
      name: `目的 / ${t('chart.dimension')}`,
      type: 'd',
      limit: 1
    },
    extBubble: {
      name: `节点大小 / ${t('chart.quota')}`,
      type: 'q',
      limit: 1,
      allowEmpty: true
    },
    extLabel: {
      name: `连线粗细 / ${t('chart.quota')}`,
      type: 'q',
      limit: 1,
      allowEmpty: true
    }
  }

  drawChart(drawOptions: EChartsDrawOptions): Promise<EChartsWrapper> {
    const { chart, container, action } = drawOptions
    if (!chart.data?.data?.length) {
      return Promise.resolve(new EChartsWrapper(null))
    }

    const data: Array<any> = cloneDeep(chart.data.data)

    // 各指标字段 ID
    const yAxisFieldId = chart.yAxis?.[0]?.id
    const nodeSizeFieldId = chart.extBubble?.[0]?.id
    const linkWidthFieldId = chart.extLabel?.[0]?.id

    // ==========================================
    // 数据重组：多指标时按 quota 拆行，需按「源」分组合并
    // yAxis 行的 value = Y 坐标
    // extBubble 行的 value = 节点大小
    // extLabel 的值在 dynamicLabelValue 中
    // ==========================================

    // Step 1: 按 source 分组，收集各指标值
    type SourceGroup = {
      xVal: string
      yVal: number
      nodeSizeVal: number | undefined
      dimList: any[]
      quotaList: any[]
      dynamicLabelValues: Map<string, number> // target -> linkWidth
    }

    const sourceGroupMap = new Map<string, SourceGroup>()
    const xCategorySet = new Set<string>()
    const xCategories: string[] = []

    data.forEach(row => {
      const dimList = row.dimensionList
      if (!dimList || dimList.length < 3) return

      const xVal = dimList[0]?.value
      const source = dimList[1]?.value
      const target = dimList[2]?.value

      if (source == null || source === '') return

      // 初始化分组
      if (!sourceGroupMap.has(source)) {
        sourceGroupMap.set(source, {
          xVal: String(xVal ?? ''),
          yVal: row.value ?? 0,
          nodeSizeVal: undefined,
          dimList: dimList,
          quotaList: row.quotaList || [],
          dynamicLabelValues: new Map()
        })
      }

      const group = sourceGroupMap.get(source)
      if (!group) return

      // 判断当前行属于哪个指标（按 quotaList[0].id）
      const rowQuotaId = row.quotaList?.[0]?.id

      if (rowQuotaId === yAxisFieldId) {
        group.yVal = row.value ?? 0
      } else if (nodeSizeFieldId && rowQuotaId === nodeSizeFieldId) {
        group.nodeSizeVal = row.value
      }

      // 收集 X 轴分类（保序去重）
      if (xVal != null && xVal !== '' && !xCategorySet.has(String(xVal))) {
        xCategorySet.add(String(xVal))
        xCategories.push(String(xVal))
      }

      // 从 dynamicLabelValue 提取连线粗细（按 target 区分）
      const dynLabel = row.dynamicLabelValue
      if (dynLabel && Array.isArray(dynLabel) && target != null && target !== '') {
        dynLabel.forEach((dl: any) => {
          if (dl.fieldId === linkWidthFieldId && dl.value != null) {
            group.dynamicLabelValues.set(String(target), Number(dl.value))
          }
        })
      }
    })

    // Step 2: 构建节点
    const nodes: any[] = []
    sourceGroupMap.forEach((group, source) => {
      nodes.push({
        id: source,
        name: source,
        x: group.xVal,
        y: group.yVal,
        symbolSize: group.nodeSizeVal ?? 40,
        dimensionList: group.dimList,
        quotaList: group.quotaList
      })
    })

    // Step 3: 构建边（遍历原始数据，支持同一 source 多 target）
    const linkSet = new Set<string>()
    const linkWidths: number[] = []
    const edgeRows: Array<{
      source: string
      target: string
      linkWidth: number | undefined
    }> = []

    data.forEach(row => {
      const dimList = row.dimensionList
      if (!dimList || dimList.length < 3) return

      const source = dimList[1]?.value
      const target = dimList[2]?.value

      if (source == null || source === '' || target == null || target === '') return
      if (source === target) return

      const key = `${source}|||${target}`
      if (linkSet.has(key)) return
      linkSet.add(key)

      const group = sourceGroupMap.get(String(source))
      const lw = group?.dynamicLabelValues.get(String(target))

      edgeRows.push({ source: String(source), target: String(target), linkWidth: lw })
      if (lw != null) {
        linkWidths.push(lw)
      }
    })

    // 线宽映射到 2~10
    const minW = linkWidths.length ? Math.min(...linkWidths) : 0
    const maxW = linkWidths.length ? Math.max(...linkWidths) : 0
    const scaleWidth = (v: number | undefined): number => {
      if (v == null) return 2
      if (maxW === minW) return 4
      return 2 + ((v - minW) / (maxW - minW)) * 8
    }

    const links = edgeRows.map(e => ({
      source: e.source,
      target: e.target,
      value: e.linkWidth,
      lineStyle: {
        width: scaleWidth(e.linkWidth),
        color: '#2f4554'
      }
    }))

    // ==========================================
    // 构建 ECharts option
    // ==========================================
    const baseOption: EChartsOption = {
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: xCategories
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          type: 'graph',
          layout: 'none',
          coordinateSystem: 'cartesian2d',
          symbolSize: 40,
          label: {
            show: true,
            position: 'top'
          },
          edgeSymbol: ['circle', 'arrow'],
          edgeSymbolSize: [4, 10],
          data: nodes.map(n => ({
            id: n.id,
            name: n.name,
            x: n.x,
            y: n.y,
            value: [n.x, n.y],
            symbolSize: n.symbolSize,
            dimensionList: n.dimensionList,
            quotaList: n.quotaList
          })),
          links
        }
      ]
    }

    const option = this.setupOptions(chart, baseOption)

    // ==========================================
    // 初始化 ECharts 实例
    // ==========================================
    const dom = document.getElementById(container)
    if (!dom) {
      return Promise.resolve(new EChartsWrapper(null))
    }
    const existingInstance = (dom as any)._echart_instance_
    if (existingInstance) {
      existingInstance.dispose()
    }
    const echartInstance = init(dom)
    echartInstance.setOption(option)
    ;(dom as any)._echart_instance_ = echartInstance

    if (action) {
      echartInstance.on('click', (params: any) => {
        action(params)
      })
    }

    return Promise.resolve(new EChartsWrapper(echartInstance))
  }

  // ========== 配置方法 ==========

  protected configTheme(chart: Chart, options: EChartsOption): EChartsOption {
    return {
      backgroundColor: 'transparent',
      ...options
    }
  }

  protected configBasicStyle(chart: Chart, options: EChartsOption): EChartsOption {
    const basicStyle = parseJson(chart.customAttr).basicStyle
    if (!basicStyle) return options

    const color = (basicStyle.colors || []).map(c => hexColorToRGBA(c, basicStyle.alpha))
    const series = (options.series as any[])?.[0]
    if (series) {
      series.itemStyle = { color: color[0] || '#2a8b92' }
      if (basicStyle.lineWidth !== undefined) {
        series.lineStyle = { ...(series.lineStyle || {}), width: basicStyle.lineWidth }
        series.edgeSymbolSize = [
          basicStyle.lineSymbolSize || 4,
          (basicStyle.lineSymbolSize || 4) * 2.5
        ]
      }
    }
    return options
  }

  protected configLabel(chart: Chart, options: EChartsOption): EChartsOption {
    const labelAttr = parseJson(chart.customAttr).label
    const series = (options.series as any[])?.[0]
    if (!series) return options

    if (labelAttr?.show) {
      series.label = {
        ...(series.label || {}),
        show: true,
        position: labelAttr.position || 'top',
        color: labelAttr.color || '#333333',
        fontSize: labelAttr.fontSize || 12,
        formatter: (params: any) => {
          return params.name
        }
      }
    } else {
      series.label = { show: false }
    }
    return options
  }

  protected configTooltip(chart: Chart, options: EChartsOption): EChartsOption {
    const tooltipAttr = parseJson(chart.customAttr).tooltip
    if (tooltipAttr?.show === false) {
      return { ...options, tooltip: { show: false } }
    }

    const tooltip: any = {
      show: true,
      trigger: 'item',
      confine: true,
      backgroundColor: tooltipAttr?.backgroundColor || '#ffffff',
      textStyle: {
        color: tooltipAttr?.color || '#333333',
        fontSize: tooltipAttr?.fontSize || 12
      },
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          const d = params.data
          return `${d.source} → ${d.target}<br/>连线粗细：${d.value ?? '-'}`
        }
        const d = params.data
        const yVal = d.y ?? d.value?.[1] ?? ''
        if (tooltipAttr?.tooltipFormatter) {
          return `${d.name}<br/>${valueFormatter(yVal, tooltipAttr.tooltipFormatter)}`
        }
        return `${d.name}<br/>${yVal}`
      }
    }
    return { ...options, tooltip }
  }

  protected configLegend(chart: Chart, options: EChartsOption): EChartsOption {
    const legendStyle = parseJson(chart.customStyle).legend
    const series = options.series as any[]
    if (!series?.length) return options

    if (legendStyle?.show === false) {
      series[0].showAllSymbol = true
      return options
    }
    series[0].name = chart.title || 'graph'

    return {
      ...options,
      legend: {
        show: true,
        orient: legendStyle?.orient || 'horizontal',
        top: legendStyle?.vPosition === 'top' ? 0 : undefined,
        bottom: legendStyle?.vPosition === 'bottom' ? 0 : undefined,
        left: legendStyle?.hPosition || 'center',
        textStyle: {
          color: legendStyle?.color || '#333333',
          fontSize: legendStyle?.fontSize || 12
        }
      }
    }
  }

  protected configXAxis(chart: Chart, options: EChartsOption): EChartsOption {
    const xAxisStyle = parseJson(chart.customStyle).xAxis
    if (!xAxisStyle) return options

    const xAxis: any = (options.xAxis as any) || {}
    xAxis.show = xAxisStyle.show !== false
    xAxis.name = xAxisStyle.name || xAxis.name
    xAxis.position = xAxisStyle.position || 'bottom'

    if (xAxisStyle.axisLabel) {
      xAxis.axisLabel = {
        show: xAxisStyle.axisLabel.show !== false,
        color: xAxisStyle.axisLabel.color || '#333333',
        fontSize: xAxisStyle.axisLabel.fontSize || 12,
        rotate: xAxisStyle.axisLabel.rotate || 0
      }
    }
    if (xAxisStyle.axisLine) {
      xAxis.axisLine = {
        show: xAxisStyle.axisLine.show !== false,
        lineStyle: {
          color: xAxisStyle.axisLine.lineStyle?.color || '#cccccc',
          width: xAxisStyle.axisLine.lineStyle?.width || 1
        }
      }
    }
    if (xAxisStyle.splitLine) {
      xAxis.splitLine = {
        show: xAxisStyle.splitLine.show !== false,
        lineStyle: {
          color: xAxisStyle.splitLine.lineStyle?.color || '#cccccc',
          width: xAxisStyle.splitLine.lineStyle?.width || 1
        }
      }
    }
    return { ...options, xAxis }
  }

  protected configYAxis(chart: Chart, options: EChartsOption): EChartsOption {
    const yAxisStyle = parseJson(chart.customStyle).yAxis
    if (!yAxisStyle) return options

    const yAxis: any = (options.yAxis as any) || {}
    yAxis.show = yAxisStyle.show !== false
    yAxis.name = yAxisStyle.name || yAxis.name
    yAxis.position = yAxisStyle.position || 'left'

    if (yAxisStyle.axisLabel) {
      yAxis.axisLabel = {
        show: yAxisStyle.axisLabel.show !== false,
        color: yAxisStyle.axisLabel.color || '#333333',
        fontSize: yAxisStyle.axisLabel.fontSize || 12
      }
    }
    if (yAxisStyle.axisLine) {
      yAxis.axisLine = {
        show: yAxisStyle.axisLine.show !== false,
        lineStyle: {
          color: yAxisStyle.axisLine.lineStyle?.color || '#cccccc',
          width: yAxisStyle.axisLine.lineStyle?.width || 1
        }
      }
    }
    if (yAxisStyle.splitLine) {
      yAxis.splitLine = {
        show: yAxisStyle.splitLine.show !== false,
        lineStyle: {
          color: yAxisStyle.splitLine.lineStyle?.color || '#cccccc',
          width: yAxisStyle.splitLine.lineStyle?.width || 1
        }
      }
    }
    return { ...options, yAxis }
  }

  // ECharts 的 graph 类型原生支持 null 值，不需要 G2Plot 的 emptyDataStrategy
  protected configEmptyDataStrategy(chart: Chart, options: EChartsOption): EChartsOption {
    return options
  }

  protected setupOptions(chart: Chart, options: EChartsOption): EChartsOption {
    return flow(
      this.configTheme,
      this.configBasicStyle,
      this.configLabel,
      this.configTooltip,
      this.configLegend,
      this.configXAxis,
      this.configYAxis
    )(chart, options)
  }

  constructor(name = 'graph-cartesian') {
    super(name, DEFAULT_DATA)
  }
}
