// Network device icon types and their metadata
export type IconType =
  | 'router'
  | 'core-switch'
  | 'access-switch'
  | 'firewall'
  | 'load-balancer'
  | 'ap'
  | 'ac'
  | 'sdwan'
  | 'server'
  | 'pc'
  | 'laptop'
  | 'printer'
  | 'nas'
  | 'camera'
  | 'ids-ips'
  | 'vpn'
  | 'waf'
  | 'sandbox'
  | 'internet'
  | 'isp'
  | 'datacenter'
  | 'site'
  | 'unknown'

export type IconStatus = 'online' | 'offline' | 'warning' | 'unknown'

export interface IconMeta {
  type: IconType
  label: string
  labelEn: string
  color: string
  group: IconGroup
}

export type IconGroup =
  | '核心网络设备'
  | '服务器与终端'
  | '安全设备'
  | '逻辑节点'
  | '未知'

// Icon metadata registry
export const ICON_META: Record<IconType, IconMeta> = {
  'router': {
    type: 'router',
    label: '路由器',
    labelEn: 'Router',
    color: '#F5A623',
    group: '核心网络设备',
  },
  'core-switch': {
    type: 'core-switch',
    label: '核心交换机',
    labelEn: 'Core Switch',
    color: '#79BBFF',
    group: '核心网络设备',
  },
  'access-switch': {
    type: 'access-switch',
    label: '接入交换机',
    labelEn: 'Access Switch',
    color: '#A5D6A7',
    group: '核心网络设备',
  },
  'firewall': {
    type: 'firewall',
    label: '防火墙',
    labelEn: 'Firewall',
    color: '#F48FB1',
    group: '安全设备',
  },
  'load-balancer': {
    type: 'load-balancer',
    label: '负载均衡',
    labelEn: 'Load Balancer',
    color: '#CE93D8',
    group: '核心网络设备',
  },
  'ap': {
    type: 'ap',
    label: '无线AP',
    labelEn: 'Wireless AP',
    color: '#AED581',
    group: '核心网络设备',
  },
  'ac': {
    type: 'ac',
    label: '无线控制器',
    labelEn: 'Wireless Controller',
    color: '#81C784',
    group: '核心网络设备',
  },
  'sdwan': {
    type: 'sdwan',
    label: 'SD-WAN',
    labelEn: 'SD-WAN',
    color: '#80DEEA',
    group: '核心网络设备',
  },
  'server': {
    type: 'server',
    label: '服务器',
    labelEn: 'Server',
    color: '#80DEEA',
    group: '服务器与终端',
  },
  'pc': {
    type: 'pc',
    label: 'PC/工作站',
    labelEn: 'PC/Workstation',
    color: '#BCAAA4',
    group: '服务器与终端',
  },
  'laptop': {
    type: 'laptop',
    label: '笔记本',
    labelEn: 'Laptop',
    color: '#BCAAA4',
    group: '服务器与终端',
  },
  'printer': {
    type: 'printer',
    label: '打印机',
    labelEn: 'Printer',
    color: '#BCAAA4',
    group: '服务器与终端',
  },
  'nas': {
    type: 'nas',
    label: 'NAS/存储',
    labelEn: 'NAS/Storage',
    color: '#79BBFF',
    group: '服务器与终端',
  },
  'camera': {
    type: 'camera',
    label: '网络摄像头',
    labelEn: 'Camera',
    color: '#CE93D8',
    group: '服务器与终端',
  },
  'ids-ips': {
    type: 'ids-ips',
    label: 'IDS/IPS',
    labelEn: 'IDS/IPS',
    color: '#EF9A9A',
    group: '安全设备',
  },
  'vpn': {
    type: 'vpn',
    label: 'VPN网关',
    labelEn: 'VPN Gateway',
    color: '#CE93D8',
    group: '安全设备',
  },
  'waf': {
    type: 'waf',
    label: 'WAF',
    labelEn: 'WAF',
    color: '#FFAB91',
    group: '安全设备',
  },
  'sandbox': {
    type: 'sandbox',
    label: '沙箱',
    labelEn: 'Sandbox',
    color: '#F48FB1',
    group: '安全设备',
  },
  'internet': {
    type: 'internet',
    label: '互联网/云',
    labelEn: 'Internet/Cloud',
    color: '#79BBFF',
    group: '逻辑节点',
  },
  'isp': {
    type: 'isp',
    label: '运营商',
    labelEn: 'ISP',
    color: '#BCAAA4',
    group: '逻辑节点',
  },
  'datacenter': {
    type: 'datacenter',
    label: '数据中心',
    labelEn: 'Datacenter',
    color: '#90A4AE',
    group: '逻辑节点',
  },
  'site': {
    type: 'site',
    label: '站点/办公室',
    labelEn: 'Site/Office',
    color: '#81C784',
    group: '逻辑节点',
  },
  'unknown': {
    type: 'unknown',
    label: '未知设备',
    labelEn: 'Unknown',
    color: '#BCAAA4',
    group: '未知',
  },
}

// Infer icon type from device type string (vendor + type + name keywords)
export function inferIconType(deviceType: string | null | undefined, vendor: string | null | undefined, name: string | null | undefined): IconType {
  const combined = `${deviceType || ''} ${vendor || ''} ${name || ''}`.toLowerCase()

  if (/firewall|防火墙|usg|asa|fortigate|hillstone|\bfw-/.test(combined)) return 'firewall'
  if (/router|路由|isr|asr|ne\s|\brt-/.test(combined)) return 'router'
  if (/core|核心|catalyst\s[789]|s57|s67/.test(combined)) return 'core-switch'
  if (/switch|交换机|\bsw-/.test(combined)) return 'access-switch'
  if (/load.?balance|负载均衡|f5|bigip/.test(combined)) return 'load-balancer'
  if (/sd.?wan|sdwan/.test(combined)) return 'sdwan'
  if (/server|服务器|proliant|poweredge|\bsrv-/.test(combined)) return 'server'
  if (/pc|工作站|desktop/.test(combined)) return 'pc'
  if (/laptop|notebook|笔记本/.test(combined)) return 'laptop'
  if (/printer|打印机/.test(combined)) return 'printer'
  if (/nas|存储|storage/.test(combined)) return 'nas'
  if (/camera|摄像头|ip.?cam/.test(combined)) return 'camera'
  if (/ids|ips|入侵/.test(combined)) return 'ids-ips'
  if (/vpn|虚拟专用网/.test(combined)) return 'vpn'
  if (/waf|web.?firewall/.test(combined)) return 'waf'
  if (/sandbox|沙箱/.test(combined)) return 'sandbox'
  if (/\bap\b|无线\s*ap|access\s*point/.test(combined)) return 'ap'
  if (/ac|无线\s*controller|无线控制器/.test(combined)) return 'ac'
  if (/internet|cloud|云/.test(combined)) return 'internet'
  if (/isp|运营商/.test(combined)) return 'isp'
  if (/datacenter|数据中心/.test(combined)) return 'datacenter'
  if (/site|站点|办公室/.test(combined)) return 'site'

  return 'unknown'
}

// Map backend status to icon status
export function mapStatus(backendStatus: string | null | undefined): IconStatus {
  switch (backendStatus) {
    case 'normal':
      return 'online'
    case 'warning':
    case 'critical':
      return 'warning'
    case 'offline':
      return 'offline'
    default:
      return 'unknown'
  }
}
