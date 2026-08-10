export const GRAPH_CARTESIAN_EDITOR_PROPERTY: EditorProperty[] = [
  'background-overall-component',
  'border-style',
  'basic-style-selector',
  'label-selector',
  'tooltip-selector',
  'x-axis-selector',
  'y-axis-selector',
  'title-selector',
  'legend-selector',
  'function-cfg',
  'jump-set',
  'linkage',
  'threshold'
]

export const GRAPH_CARTESIAN_EDITOR_PROPERTY_INNER: EditorPropertyInner = {
  'background-overall-component': ['all'],
  'border-style': ['all'],
  'basic-style-selector': ['colors', 'alpha', 'lineWidth', 'lineSymbol', 'lineSymbolSize'],
  'label-selector': ['fontSize', 'color', 'labelFormatter'],
  'tooltip-selector': ['fontSize', 'color', 'tooltipFormatter', 'show'],
  'x-axis-selector': [
    'name',
    'color',
    'fontSize',
    'position',
    'axisLabel',
    'axisLine',
    'splitLine'
  ],
  'y-axis-selector': [
    'name',
    'color',
    'fontSize',
    'position',
    'axisLabel',
    'axisLine',
    'splitLine'
  ],
  'title-selector': [
    'title',
    'fontSize',
    'color',
    'hPosition',
    'isItalic',
    'isBolder',
    'remarkShow',
    'fontFamily',
    'letterSpace',
    'fontShadow'
  ],
  'legend-selector': ['icon', 'orient', 'fontSize', 'color', 'hPosition', 'vPosition'],
  'function-cfg': ['slider', 'emptyDataStrategy'],
  threshold: ['lineThreshold']
}

/**
 * 轴类型：
 * - xAxis:     类别轴/维度（X 坐标）
 * - yAxis:     数据/指标（Y 坐标）
 * - xAxisExt:  源/维度（节点唯一标识 + link 起点）
 * - extStack:  目的/维度（link 终点，null 表示纯节点行）
 * - extBubble: 节点大小/指标（可选）
 * - extLabel:  连线粗细/指标（可选）
 */
export const GRAPH_CARTESIAN_AXIS_TYPE: AxisType[] = [
  'xAxis',
  'yAxis',
  'xAxisExt',
  'extStack',
  'extBubble',
  'extLabel',
  'filter',
  'drill',
  'extTooltip'
]
