import type { EChartsOption } from 'echarts'
import type { EChartsType } from 'echarts'
import {
  EchartsChartView,
  ChartLibraryType,
  ChartWrapper
} from '@/views/chart/components/js/panel/types'
import { parseJson } from '@/views/chart/components/js/util'
import { getTheme } from '@/views/chart/components/js/panel/common/common_antv'
import { flow } from '@/views/chart/components/js/util'

export interface EChartsDrawOptions {
  chartObj?: EChartsWrapper
  container: string
  chart: Chart
  action?: (...args: any[]) => any
}

/**
 * ECharts 实例包装类
 */
export class EChartsWrapper extends ChartWrapper<EChartsType> {
  constructor(chartInstance: EChartsType) {
    super()
    this.chartInstance = chartInstance
  }

  destroy = () => {
    this.chartInstance?.dispose()
  }

  render = () => {
    this.chartInstance?.resize()
  }
}

/**
 * ECharts 图表抽象类
 */
export abstract class EChartsChartView<
  O extends EChartsOption = EChartsOption
> extends EchartsChartView {
  /**
   * 根据参数构建 ECharts 实例然后返回
   * @param drawOptions 图表配置参数
   * @return 生成的 ECharts 包装实例
   */
  abstract drawChart(drawOptions: EChartsDrawOptions): Promise<EChartsWrapper> | EChartsWrapper

  /**
   * 子类必须实现：构建 ECharts option 的配置流水线
   * @param chart 数据库图表对象
   * @param options 当前构建中的 ECharts option
   */
  protected abstract setupOptions(chart: Chart, options: O): O

  // ========== 通用配置方法（子类可 override） ==========

  protected configTheme(chart: Chart, options: O): O {
    const theme = getTheme(chart)
    return { ...options, ...theme } as unknown as O
  }

  protected configBasicStyle(chart: Chart, options: O): O {
    return options
  }

  protected configLabel(chart: Chart, options: O): O {
    return options
  }

  protected configTooltip(chart: Chart, options: O): O {
    return options
  }

  protected configLegend(chart: Chart, options: O): O {
    return options
  }

  protected configXAxis(chart: Chart, options: O): O {
    return options
  }

  protected configYAxis(chart: Chart, options: O): O {
    return options
  }

  protected configTitle(chart: Chart, options: O): O {
    return options
  }

  protected configEmptyDataStrategy(chart: Chart, options: O): O {
    // ECharts 原生支持 null 值，不需要 G2Plot 的数据过滤策略
    return options
  }

  protected constructor(name: string, defaultData: any[]) {
    super(name, defaultData)
  }
}
