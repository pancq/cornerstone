export interface DeviceTypeConfig {
  color: string
  label: string
  bgOpacity: number
}

export interface LinkStatusConfig {
  color: string
  lineWidth: number
  lineDash: number[] | null
  label: string
}

export const DEVICE_TYPE_CONFIG: Record<string, DeviceTypeConfig> = {
  router: { color: '#E6A23C', label: '路由器', bgOpacity: 0.15 },
  'core-switch': { color: '#409EFF', label: '核心交换机', bgOpacity: 0.15 },
  'access-switch': { color: '#79BBFF', label: '接入交换机', bgOpacity: 0.15 },
  firewall: { color: '#F56C6C', label: '防火墙', bgOpacity: 0.15 },
  'load-balancer': { color: '#9B59B6', label: '负载均衡', bgOpacity: 0.15 },
  ap: { color: '#67C23A', label: '无线AP', bgOpacity: 0.15 },
  ac: { color: '#4CAF50', label: '无线控制器', bgOpacity: 0.15 },
  server: { color: '#36CFC9', label: '服务器', bgOpacity: 0.15 },
  pc: { color: '#8899AA', label: 'PC', bgOpacity: 0.15 },
  printer: { color: '#909399', label: '打印机', bgOpacity: 0.12 },
  nas: { color: '#2D5BE3', label: 'NAS/存储', bgOpacity: 0.15 },
  'ids-ips': { color: '#E85F5C', label: 'IDS/IPS', bgOpacity: 0.15 },
  vpn: { color: '#7B61FF', label: 'VPN网关', bgOpacity: 0.15 },
  waf: { color: '#FF7A45', label: 'WAF', bgOpacity: 0.15 },
  internet: { color: '#2E5FA1', label: '互联网', bgOpacity: 0.9 },
  isp: { color: '#606266', label: '运营商', bgOpacity: 0.10 },
  datacenter: { color: '#1F4E79', label: '数据中心', bgOpacity: 0.20 },
  site: { color: '#1D9E75', label: '站点', bgOpacity: 0.15 },
  unknown: { color: '#909399', label: '未知设备', bgOpacity: 0.10 },
}

export const LINK_STATUS_CONFIG: Record<string, LinkStatusConfig> = {
  up: { color: '#5B8DB8', lineWidth: 2, lineDash: null, label: '正常' },
  down: { color: '#F56C6C', lineWidth: 2, lineDash: [6, 3], label: '故障' },
  unknown: { color: '#606266', lineWidth: 1.5, lineDash: [4, 4], label: '未知' },
  degraded: { color: '#E6A23C', lineWidth: 2, lineDash: [8, 3], label: '降级' },
}

export const STATUS_DOT_COLOR: Record<string, string> = {
  online: '#67C23A',
  offline: '#F56C6C',
  warning: '#E6A23C',
  unknown: '#909399',
}

export const DEVICE_RANK: Record<string, number> = {
  internet: 0,
  isp: 0,
  router: 1,
  firewall: 1,
  'load-balancer': 1,
  'core-switch': 2,
  'access-switch': 3,
  ap: 3,
  server: 4,
  pc: 4,
  unknown: 3,
}