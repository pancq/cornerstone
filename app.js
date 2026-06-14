const STORE_KEY = "cornerstone-state-v1";

const navItems = [
  { id: "dashboard", label: "资源总览", icon: "▦" },
  { id: "circuits", label: "专线管理", icon: "⇄" },
  { id: "ipam", label: "IP 地址管理", icon: "⌘" },
  { id: "devices", label: "设备台账", icon: "▣" },
  { id: "backups", label: "配置备份", icon: "⇣" },
  { id: "alerts", label: "预警中心", icon: "!" },
  { id: "system", label: "系统管理", icon: "⚙" },
];

const today = new Date();
today.setHours(0, 0, 0, 0);

const seedState = {
  sites: [
    { id: "site-a", name: "Demo Site A", location: "Example Campus A", contact: "Demo Admin" },
    { id: "site-b", name: "Demo Site B", location: "Example Campus B", contact: "Demo Operator" },
    { id: "site-lab", name: "Demo Lab", location: "Example Lab", contact: "Demo Viewer" },
  ],
  circuits: [
    {
      id: "cir-001",
      name: "Demo Site A Internet Circuit",
      provider: "Demo ISP A",
      type: "互联网专线",
      siteId: "site-a",
      bandwidth: 1000,
      monthlyCost: 18800,
      contractStart: "2025-07-01",
      contractEnd: "2026-06-12",
      circuitNo: "DEMO-INET-001",
      supportPhone: "010-0000-1001",
      status: "正常",
      note: "Demo primary internet circuit",
      updatedBy: "admin",
      updatedAt: "2026-05-18 10:12",
    },
    {
      id: "cir-002",
      name: "Demo Site A-B MPLS Circuit",
      provider: "Demo ISP B",
      type: "MPLS",
      siteId: "site-b",
      bandwidth: 500,
      monthlyCost: 22600,
      contractStart: "2025-04-20",
      contractEnd: "2026-05-28",
      circuitNo: "DEMO-MPLS-002",
      supportPhone: "010-0000-1002",
      status: "正常",
      note: "Demo private WAN circuit",
      updatedBy: "ops",
      updatedAt: "2026-05-20 15:34",
    },
    {
      id: "cir-003",
      name: "Demo Lab SD-WAN Backup",
      provider: "Demo ISP C",
      type: "SD-WAN",
      siteId: "site-lab",
      bandwidth: 200,
      monthlyCost: 5200,
      contractStart: "2024-11-01",
      contractEnd: "2026-11-01",
      circuitNo: "DEMO-SDWAN-003",
      supportPhone: "010-0000-1003",
      status: "故障",
      note: "Demo degraded backup link",
      updatedBy: "ops",
      updatedAt: "2026-05-21 09:06",
    },
  ],
  aggregates: [
    { id: "agg-demo-mgmt", network: "192.0.2.0/24", name: "Demo management address pool" },
    { id: "agg-demo-lab", network: "198.51.100.0/24", name: "Demo lab address pool" },
  ],
  prefixes: [
    { id: "pre-demo-office", aggregateId: "agg-demo-mgmt", network: "192.0.2.0/26", siteId: "site-a", vlan: "10", usage: "Demo office network" },
    { id: "pre-demo-mgmt", aggregateId: "agg-demo-mgmt", network: "192.0.2.64/26", siteId: "site-a", vlan: "20", usage: "Demo management network" },
    { id: "pre-demo-branch", aggregateId: "agg-demo-mgmt", network: "192.0.2.128/26", siteId: "site-b", vlan: "30", usage: "Demo branch network" },
    { id: "pre-demo-lab", aggregateId: "agg-demo-lab", network: "198.51.100.0/26", siteId: "site-lab", vlan: "120", usage: "Demo lab network" },
  ],
  ipAddresses: [
    { id: "ip-001", address: "192.0.2.65", prefixId: "pre-demo-mgmt", deviceId: "dev-001", usage: "Demo core switch management", owner: "Demo NetOps", status: "已分配" },
    { id: "ip-002", address: "192.0.2.66", prefixId: "pre-demo-mgmt", deviceId: "dev-002", usage: "Demo firewall management", owner: "Demo SecOps", status: "已分配" },
    { id: "ip-003", address: "192.0.2.129", prefixId: "pre-demo-branch", deviceId: "dev-003", usage: "Demo branch router management", owner: "Demo NetOps", status: "已分配" },
    { id: "ip-004", address: "198.51.100.10", prefixId: "pre-demo-lab", deviceId: "", usage: "Demo reserved lab host", owner: "Demo Lab", status: "预留" },
  ],
  devices: [
    {
      id: "dev-001",
      name: "SW-DEMO-CORE-01",
      type: "交换机",
      brand: "Cisco",
      model: "Catalyst 9300",
      sn: "DEMO-SW-0001",
      siteId: "site-a",
      location: "Demo Rack A-U12",
      mgmtIpId: "ip-001",
      status: "在线",
      purchaseDate: "2024-03-12",
      warrantyEnd: "2026-06-18",
      purchaseAmount: 82000,
      owner: "Demo NetOps",
      note: "Demo core switch",
    },
    {
      id: "dev-002",
      name: "FW-DEMO-EDGE-01",
      type: "防火墙",
      brand: "Huawei",
      model: "USG6655E",
      sn: "DEMO-FW-0001",
      siteId: "site-a",
      location: "Demo Rack B-U06",
      mgmtIpId: "ip-002",
      status: "在线",
      purchaseDate: "2023-08-20",
      warrantyEnd: "2026-05-30",
      purchaseAmount: 128000,
      owner: "Demo SecOps",
      note: "Demo internet edge firewall",
    },
    {
      id: "dev-003",
      name: "RT-DEMO-WAN-01",
      type: "路由器",
      brand: "H3C",
      model: "MSR 5660",
      sn: "DEMO-RT-0001",
      siteId: "site-b",
      location: "Demo Rack C-U08",
      mgmtIpId: "ip-003",
      status: "维修",
      purchaseDate: "2022-10-01",
      warrantyEnd: "2026-12-01",
      purchaseAmount: 64000,
      owner: "Demo NetOps",
      note: "Demo WAN edge router",
    },
  ],
  credentials: [
    { id: "cred-001", deviceId: "dev-001", protocol: "SSH", username: "demo-netops", port: 22, retention: 30 },
    { id: "cred-002", deviceId: "dev-002", protocol: "SSH", username: "demo-secops", port: 22, retention: 30 },
    { id: "cred-003", deviceId: "dev-003", protocol: "Telnet", username: "demo-legacy", port: 23, retention: 15 },
  ],
  backups: [
    {
      id: "bak-001",
      deviceId: "dev-001",
      createdAt: "2026-05-20 02:00:12",
      trigger: "自动定时",
      operator: "system",
      status: "成功",
      size: 1186,
      note: "每日备份",
      content: "hostname SW-DEMO-CORE-01\ninterface Vlan20\n ip address 192.0.2.65 255.255.255.192\nspanning-tree mode rapid-pvst\nntp server 192.0.2.10\nline vty 0 4\n transport input ssh",
    },
    {
      id: "bak-002",
      deviceId: "dev-001",
      createdAt: "2026-05-21 02:00:14",
      trigger: "自动定时",
      operator: "system",
      status: "成功",
      size: 1224,
      note: "每日备份",
      content: "hostname SW-DEMO-CORE-01\ninterface Vlan20\n ip address 192.0.2.65 255.255.255.192\nspanning-tree mode rapid-pvst\nntp server 192.0.2.10\nntp server 192.0.2.11\nline vty 0 4\n transport input ssh",
    },
    {
      id: "bak-003",
      deviceId: "dev-002",
      createdAt: "2026-05-21 02:01:03",
      trigger: "自动定时",
      operator: "system",
      status: "失败",
      size: 0,
      note: "SSH 超时",
      content: "",
    },
  ],
  users: [
    { id: "user-001", username: "admin", email: "admin@example.com", role: "超级管理员", isActive: true },
    { id: "user-002", username: "ops", email: "ops@example.com", role: "IT运维工程师", isActive: true },
    { id: "user-003", username: "viewer", email: "manager@example.com", role: "只读查看者", isActive: true },
  ],
  auditLogs: [
    { id: "log-001", user: "ops", action: "更新专线状态", resource: "Demo Lab SD-WAN Backup", detail: "状态由 正常 改为 故障", createdAt: "2026-05-21 09:06" },
    { id: "log-002", user: "system", action: "配置备份", resource: "FW-DEMO-EDGE-01", detail: "备份失败：Demo SSH timeout", createdAt: "2026-05-21 02:01" },
  ],
};

let state = loadState();
let currentView = "dashboard";
let currentQuery = "";
let activeForm = null;

const content = document.querySelector("#content");
const pageTitle = document.querySelector("#page-title");
const eyebrow = document.querySelector("#eyebrow");
const nav = document.querySelector("#nav");
const dialog = document.querySelector("#record-dialog");
const form = document.querySelector("#record-form");
const formFields = document.querySelector("#form-fields");
const csvFile = document.querySelector("#csv-file");

function loadState() {
  const saved = localStorage.getItem(STORE_KEY);
  return saved ? JSON.parse(saved) : structuredClone(seedState);
}

function saveState() {
  localStorage.setItem(STORE_KEY, JSON.stringify(state));
}

function uid(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function renderNav() {
  nav.innerHTML = navItems
    .map(
      (item) => `
        <button type="button" class="${item.id === currentView ? "active" : ""}" data-view="${item.id}" title="${item.label}" aria-label="${item.label}">
          <span class="nav-icon">${item.icon}</span>
          <span>${item.label}</span>
        </button>
      `,
    )
    .join("");
}

function setView(view) {
  currentView = view;
  const item = navItems.find((entry) => entry.id === view);
  pageTitle.textContent = item.label;
  eyebrow.textContent = view;
  renderNav();
  render();
}

function render() {
  const renderers = {
    dashboard: renderDashboard,
    circuits: renderCircuits,
    ipam: renderIpam,
    devices: renderDevices,
    backups: renderBackups,
    alerts: renderAlerts,
    system: renderSystem,
  };
  renderers[currentView]();
}

function siteName(siteId) {
  return state.sites.find((site) => site.id === siteId)?.name || "-";
}

function deviceName(deviceId) {
  return state.devices.find((device) => device.id === deviceId)?.name || "-";
}

function ipAddress(ipId) {
  return state.ipAddresses.find((ip) => ip.id === ipId)?.address || "-";
}

function daysUntil(dateText) {
  const date = new Date(`${dateText}T00:00:00+08:00`);
  return Math.ceil((date - today) / 86400000);
}

function statusTag(value) {
  const cls = {
    正常: "ok",
    在线: "ok",
    成功: "ok",
    已分配: "ok",
    预留: "warn",
    故障: "danger",
    离线: "danger",
    失败: "danger",
    维修: "warn",
    停用: "warn",
    报废: "danger",
  }[value] || "";
  return `<span class="tag ${cls}">${value}</span>`;
}

function money(value) {
  return value ? Number(value).toLocaleString("zh-CN") : "-";
}

function filterByQuery(items, fields) {
  const query = currentQuery.trim().toLowerCase();
  if (!query) return items;
  return items.filter((item) =>
    fields.some((field) => String(field(item) || "").toLowerCase().includes(query)),
  );
}

function table(columns, rows) {
  if (!rows.length) return `<div class="empty-state">暂无匹配记录</div>`;
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${columns.map((col) => `<th>${col.title}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows
            .map(
              (row) =>
                `<tr>${columns.map((col) => `<td>${col.render ? col.render(row) : row[col.key] || "-"}</td>`).join("")}</tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderDashboard() {
  const alerts = collectAlerts();
  const online = state.devices.filter((device) => device.status === "在线").length;
  const successfulToday = state.backups.filter((backup) => backup.createdAt.startsWith("2026-05-21") && backup.status === "成功").length;
  const failedToday = state.backups.filter((backup) => backup.createdAt.startsWith("2026-05-21") && backup.status === "失败").length;
  const ipTotal = state.prefixes.length * 254;
  const ipUsed = state.ipAddresses.filter((ip) => ip.status === "已分配").length;

  content.innerHTML = `
    <div class="metric-grid">
      ${metric("专线总数", state.circuits.length, `${state.circuits.filter((item) => item.status === "正常").length} 条正常运行`)}
      ${metric("IP 使用率", `${Math.round((ipUsed / ipTotal) * 100)}%`, `${ipUsed}/${ipTotal} 已分配`)}
      ${metric("在线设备", online, `${state.devices.length - online} 台需关注`)}
      ${metric("今日备份", `${successfulToday}/${failedToday}`, "成功 / 失败")}
    </div>
    <div class="split">
      <section class="panel">
        <div class="panel-head"><h2>子网使用率</h2><span class="tag blue">${state.prefixes.length} 个子网</span></div>
        ${state.prefixes.map((prefix) => usageRow(prefix)).join("")}
      </section>
      <section class="panel">
        <div class="panel-head"><h2>近期预警</h2><span class="tag warn">${alerts.length}</span></div>
        ${alertList(alerts.slice(0, 6))}
      </section>
    </div>
    <section class="panel">
      <div class="panel-head"><h2>最近操作</h2><span class="muted">审计日志</span></div>
      <ul class="activity-list">
        ${state.auditLogs
          .slice(0, 5)
          .map((log) => `<li><span><strong>${log.action}</strong> · ${log.resource}<br><span class="muted">${log.detail}</span></span><span class="muted">${log.createdAt}</span></li>`)
          .join("")}
      </ul>
    </section>
  `;
}

function metric(label, value, helper) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong><small>${helper}</small></div>`;
}

function usageRow(prefix) {
  const used = state.ipAddresses.filter((ip) => ip.prefixId === prefix.id).length;
  const percent = Math.round((used / 254) * 100);
  return `
    <div class="usage-row">
      <span>${prefix.network}</span>
      <div class="bar"><span style="width:${percent}%"></span></div>
      <span>${percent}%</span>
    </div>
  `;
}

function renderCircuits() {
  const rows = filterByQuery(state.circuits, [
    (item) => item.name,
    (item) => item.provider,
    (item) => item.type,
    (item) => siteName(item.siteId),
    (item) => item.circuitNo,
  ]);
  content.innerHTML = `
    ${moduleHead("专线列表", "新增专线", "circuits")}
    ${table(
      [
        { title: "专线名称", render: (row) => `<strong>${row.name}</strong><br><span class="muted">${row.circuitNo || "-"}</span>` },
        { title: "运营商", key: "provider" },
        { title: "类型", key: "type" },
        { title: "站点", render: (row) => siteName(row.siteId) },
        { title: "带宽", render: (row) => `${row.bandwidth} Mbps` },
        { title: "月租", render: (row) => `¥${money(row.monthlyCost)}` },
        { title: "合同到期", render: (row) => `${row.contractEnd}<br><span class="muted">${daysUntil(row.contractEnd)} 天</span>` },
        { title: "状态", render: (row) => statusTag(row.status) },
        { title: "操作", render: (row) => rowActions("circuits", row.id) },
      ],
      rows,
    )}
  `;
}

function renderIpam() {
  const prefixRows = filterByQuery(state.prefixes, [
    (item) => item.network,
    (item) => item.usage,
    (item) => siteName(item.siteId),
    (item) => item.vlan,
  ]);
  const ipRows = filterByQuery(state.ipAddresses, [
    (item) => item.address,
    (item) => item.usage,
    (item) => item.owner,
    (item) => deviceName(item.deviceId),
  ]);
  content.innerHTML = `
    <section class="panel">
      <div class="panel-head">
        <h2>地址空间</h2>
        <div class="toolbar">
          <button class="ghost-button" type="button" data-import="ips">CSV 导入 IP</button>
          <button class="primary-button" type="button" data-add="prefixes">新增子网</button>
          <button class="primary-button" type="button" data-add="ipAddresses">分配 IP</button>
        </div>
      </div>
      <div class="record-grid">
        ${state.prefixes
          .map(
            (prefix) => `
              <article class="record-card">
                <h3>${prefix.network}</h3>
                <dl>
                  <dt>站点</dt><dd>${siteName(prefix.siteId)}</dd>
                  <dt>VLAN</dt><dd>${prefix.vlan || "-"}</dd>
                  <dt>用途</dt><dd>${prefix.usage || "-"}</dd>
                  <dt>使用率</dt><dd>${state.ipAddresses.filter((ip) => ip.prefixId === prefix.id).length}/254</dd>
                </dl>
                <div class="address-map">${ipMap(prefix)}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
    <section class="panel">
      <div class="panel-head"><h2>子网规划</h2></div>
      ${table(
        [
          { title: "子网", key: "network" },
          { title: "地址段", render: (row) => state.aggregates.find((agg) => agg.id === row.aggregateId)?.network || "-" },
          { title: "站点", render: (row) => siteName(row.siteId) },
          { title: "VLAN", key: "vlan" },
          { title: "用途", key: "usage" },
          { title: "操作", render: (row) => rowActions("prefixes", row.id) },
        ],
        prefixRows,
      )}
    </section>
    <section class="panel">
      <div class="panel-head"><h2>IP 分配</h2></div>
      ${table(
        [
          { title: "IP 地址", render: (row) => `<strong>${row.address}</strong>` },
          { title: "子网", render: (row) => state.prefixes.find((prefix) => prefix.id === row.prefixId)?.network || "-" },
          { title: "设备", render: (row) => deviceName(row.deviceId) },
          { title: "用途", key: "usage" },
          { title: "负责人", key: "owner" },
          { title: "状态", render: (row) => statusTag(row.status) },
          { title: "操作", render: (row) => rowActions("ipAddresses", row.id) },
        ],
        ipRows,
      )}
    </section>
  `;
}

function ipMap(prefix) {
  const count = state.ipAddresses.filter((ip) => ip.prefixId === prefix.id).length;
  return Array.from({ length: 64 }, (_, index) => {
    const cls = index < count ? "used" : index === count ? "reserved" : "";
    return `<span class="ip-cell ${cls}" title="${prefix.network} #${index + 1}"></span>`;
  }).join("");
}

function renderDevices() {
  const rows = filterByQuery(state.devices, [
    (item) => item.name,
    (item) => item.type,
    (item) => item.brand,
    (item) => item.model,
    (item) => item.sn,
    (item) => siteName(item.siteId),
    (item) => ipAddress(item.mgmtIpId),
  ]);
  content.innerHTML = `
    ${moduleHead("设备列表", "新增设备", "devices", `<button class="ghost-button" type="button" data-import="devices">CSV 导入设备</button>`)}
    ${table(
      [
        { title: "设备", render: (row) => `<strong>${row.name}</strong><br><span class="muted">${row.brand} ${row.model}</span>` },
        { title: "类型", key: "type" },
        { title: "序列号", key: "sn" },
        { title: "站点", render: (row) => siteName(row.siteId) },
        { title: "位置", key: "location" },
        { title: "管理 IP", render: (row) => ipAddress(row.mgmtIpId) },
        { title: "保修到期", render: (row) => `${row.warrantyEnd}<br><span class="muted">${daysUntil(row.warrantyEnd)} 天</span>` },
        { title: "状态", render: (row) => statusTag(row.status) },
        { title: "操作", render: (row) => rowActions("devices", row.id) },
      ],
      rows,
    )}
  `;
}

function renderBackups() {
  const rows = filterByQuery(state.backups, [
    (item) => deviceName(item.deviceId),
    (item) => item.trigger,
    (item) => item.operator,
    (item) => item.note,
  ]);
  content.innerHTML = `
    ${moduleHead(
      "备份历史",
      "手动备份",
      "backups",
      `<button class="ghost-button" type="button" id="compare-latest">对比最近版本</button>`,
    )}
    ${table(
      [
        { title: "设备", render: (row) => deviceName(row.deviceId) },
        { title: "备份时间", key: "createdAt" },
        { title: "触发方式", key: "trigger" },
        { title: "操作人", key: "operator" },
        { title: "文件大小", render: (row) => `${row.size} B` },
        { title: "状态", render: (row) => statusTag(row.status) },
        { title: "备注", key: "note" },
        {
          title: "操作",
          render: (row) => `
            <div class="actions">
              <button class="ghost-button" type="button" data-view-config="${row.id}">查看</button>
              <button class="ghost-button" type="button" data-download="${row.id}">下载</button>
              ${rowActions("backups", row.id)}
            </div>
          `,
        },
      ],
      rows,
    )}
  `;
}

function renderAlerts() {
  const alerts = collectAlerts();
  content.innerHTML = `
    <section class="panel">
      <div class="panel-head"><h2>预警中心</h2><span class="tag warn">${alerts.length} 条</span></div>
      ${alertList(alerts)}
    </section>
  `;
}

function renderSystem() {
  content.innerHTML = `
    <div class="split">
      <section class="panel">
        <div class="panel-head">
          <h2>用户管理</h2>
          <button class="primary-button" type="button" data-add="users">新增用户</button>
        </div>
        ${table(
          [
            { title: "用户名", key: "username" },
            { title: "邮箱", key: "email" },
            { title: "角色", key: "role" },
            { title: "状态", render: (row) => statusTag(row.isActive ? "正常" : "停用") },
            { title: "操作", render: (row) => rowActions("users", row.id) },
          ],
          state.users,
        )}
      </section>
      <section class="panel">
        <div class="panel-head">
          <h2>站点管理</h2>
          <button class="primary-button" type="button" data-add="sites">新增站点</button>
        </div>
        ${table(
          [
            { title: "站点", key: "name" },
            { title: "位置", key: "location" },
            { title: "联系人", key: "contact" },
            { title: "操作", render: (row) => rowActions("sites", row.id) },
          ],
          state.sites,
        )}
      </section>
    </div>
    <section class="panel">
      <div class="panel-head"><h2>操作日志</h2></div>
      ${table(
        [
          { title: "时间", key: "createdAt" },
          { title: "用户", key: "user" },
          { title: "操作", key: "action" },
          { title: "资源", key: "resource" },
          { title: "详情", key: "detail" },
        ],
        state.auditLogs,
      )}
    </section>
  `;
}

function moduleHead(title, addLabel, collection, extra = "") {
  return `
    <section class="panel">
      <div class="panel-head">
        <h2>${title}</h2>
        <div class="toolbar">
          ${extra}
          <button class="primary-button" type="button" data-add="${collection}">${addLabel}</button>
        </div>
      </div>
    </section>
  `;
}

function rowActions(collection, id) {
  return `
    <div class="actions">
      <button class="ghost-button" type="button" data-edit="${collection}:${id}">编辑</button>
      <button class="danger-button" type="button" data-delete="${collection}:${id}">删除</button>
    </div>
  `;
}

function collectAlerts() {
  const circuitAlerts = state.circuits
    .map((item) => ({ type: "专线合同", title: item.name, due: item.contractEnd, days: daysUntil(item.contractEnd), level: daysUntil(item.contractEnd) <= 7 ? "danger" : "warn" }))
    .filter((item) => item.days >= 0 && item.days <= 30);
  const warrantyAlerts = state.devices
    .map((item) => ({ type: "设备保修", title: item.name, due: item.warrantyEnd, days: daysUntil(item.warrantyEnd), level: daysUntil(item.warrantyEnd) <= 7 ? "danger" : "warn" }))
    .filter((item) => item.days >= 0 && item.days <= 30);
  const backupAlerts = state.backups
    .filter((item) => item.status === "失败")
    .map((item) => ({ type: "备份失败", title: deviceName(item.deviceId), due: item.createdAt, days: 0, level: "danger" }));
  const subnetAlerts = state.prefixes
    .map((prefix) => {
      const used = state.ipAddresses.filter((ip) => ip.prefixId === prefix.id).length;
      return { type: "子网容量", title: prefix.network, due: `${Math.round((used / 254) * 100)}%`, days: 0, level: used / 254 >= 0.8 ? "danger" : "ok" };
    })
    .filter((item) => item.level === "danger");
  return [...circuitAlerts, ...warrantyAlerts, ...backupAlerts, ...subnetAlerts];
}

function alertList(alerts) {
  if (!alerts.length) return `<div class="empty-state">当前没有待处理预警</div>`;
  return `
    <ul class="alert-list">
      ${alerts
        .map(
          (alert) => `
          <li>
            <span><strong>${alert.type}</strong> · ${alert.title}<br><span class="muted">${alert.due}</span></span>
            <span class="tag ${alert.level}">${alert.days ? `${alert.days} 天` : "立即处理"}</span>
          </li>
        `,
        )
        .join("")}
    </ul>
  `;
}

const schemas = {
  circuits: {
    title: "专线",
    defaults: { provider: "电信", type: "互联网专线", status: "正常" },
    fields: [
      field("name", "专线名称", "text", true),
      selectField("provider", "运营商", ["电信", "联通", "移动", "其他"]),
      selectField("type", "专线类型", ["互联网专线", "MPLS", "裸光纤", "SD-WAN"]),
      relationField("siteId", "接入站点", "sites"),
      field("bandwidth", "带宽（Mbps）", "number", true),
      field("monthlyCost", "月租费用（元）", "number"),
      field("contractStart", "合同开始日期", "date", true),
      field("contractEnd", "合同到期日期", "date", true),
      field("circuitNo", "电路编号"),
      field("supportPhone", "客服电话"),
      selectField("status", "运行状态", ["正常", "故障", "停用"]),
      field("note", "备注", "textarea"),
    ],
  },
  prefixes: {
    title: "子网",
    fields: [
      relationField("aggregateId", "地址段", "aggregates", "network"),
      field("network", "子网前缀", "text", true),
      relationField("siteId", "所属站点", "sites"),
      field("vlan", "VLAN"),
      field("usage", "用途"),
    ],
  },
  ipAddresses: {
    title: "IP 地址",
    defaults: { status: "已分配" },
    fields: [
      field("address", "IP 地址", "text", true),
      relationField("prefixId", "所属子网", "prefixes", "network"),
      relationField("deviceId", "绑定设备", "devices", "name", false),
      field("usage", "用途"),
      field("owner", "负责人"),
      selectField("status", "状态", ["已分配", "预留"]),
    ],
  },
  devices: {
    title: "设备",
    defaults: { status: "在线", type: "交换机" },
    fields: [
      field("name", "设备名称", "text", true),
      selectField("type", "设备类型", ["交换机", "路由器", "防火墙", "服务器", "AP", "其他"]),
      field("brand", "品牌"),
      field("model", "型号"),
      field("sn", "序列号"),
      relationField("siteId", "所在站点", "sites"),
      field("location", "机柜/位置"),
      relationField("mgmtIpId", "管理 IP", "ipAddresses", "address", false),
      selectField("status", "运行状态", ["在线", "离线", "维修", "报废"]),
      field("purchaseDate", "采购日期", "date"),
      field("warrantyEnd", "保修到期日期", "date"),
      field("purchaseAmount", "采购金额（元）", "number"),
      field("owner", "负责人"),
      field("note", "备注", "textarea"),
    ],
  },
  backups: {
    title: "配置备份",
    defaults: { trigger: "手动触发", operator: "ops", status: "成功" },
    fields: [
      relationField("deviceId", "设备", "devices", "name"),
      selectField("trigger", "触发方式", ["自动定时", "手动触发"]),
      field("operator", "操作人"),
      selectField("status", "备份状态", ["成功", "失败"]),
      field("note", "备注"),
      field("content", "配置内容", "textarea"),
    ],
  },
  users: {
    title: "用户",
    defaults: { role: "IT运维工程师", isActive: true },
    fields: [
      field("username", "用户名", "text", true),
      field("email", "邮箱", "email", true),
      selectField("role", "角色", ["超级管理员", "IT运维工程师", "只读查看者"]),
      selectField("isActive", "状态", [
        ["true", "启用"],
        ["false", "停用"],
      ]),
    ],
  },
  sites: {
    title: "站点",
    fields: [field("name", "站点名称", "text", true), field("location", "位置"), field("contact", "联系人")],
  },
};

function field(name, label, type = "text", required = false) {
  return { name, label, type, required };
}

function selectField(name, label, options) {
  return { name, label, type: "select", options, required: true };
}

function relationField(name, label, collection, labelKey = "name", required = true) {
  return { name, label, type: "relation", collection, labelKey, required };
}

function openForm(collection, id = null) {
  const schema = schemas[collection];
  const record = id ? state[collection].find((item) => item.id === id) : { id: uid(collection.slice(0, 3)), ...(schema.defaults || {}) };
  activeForm = { collection, id, record };
  document.querySelector("#dialog-kicker").textContent = collection;
  document.querySelector("#dialog-title").textContent = `${id ? "编辑" : "新增"}${schema.title}`;
  formFields.innerHTML = schema.fields.map((item) => renderField(item, record)).join("");
  dialog.showModal();
}

function renderField(item, record) {
  const value = record[item.name] ?? "";
  const required = item.required ? "required" : "";
  const full = item.type === "textarea" ? " full" : "";
  if (item.type === "textarea") {
    return `<div class="form-field${full}"><label>${item.label}</label><textarea name="${item.name}" ${required}>${escapeHtml(value)}</textarea></div>`;
  }
  if (item.type === "select") {
    return `<div class="form-field"><label>${item.label}</label><select name="${item.name}" ${required}>${item.options.map((option) => optionHtml(option, value)).join("")}</select></div>`;
  }
  if (item.type === "relation") {
    const options = state[item.collection].map((option) => [option.id, option[item.labelKey]]);
    return `<div class="form-field"><label>${item.label}</label><select name="${item.name}" ${required}><option value="">未选择</option>${options.map((option) => optionHtml(option, value)).join("")}</select></div>`;
  }
  return `<div class="form-field"><label>${item.label}</label><input name="${item.name}" type="${item.type}" value="${escapeHtml(value)}" ${required} /></div>`;
}

function optionHtml(option, value) {
  const pair = Array.isArray(option) ? option : [option, option];
  return `<option value="${pair[0]}" ${String(value) === String(pair[0]) ? "selected" : ""}>${pair[1]}</option>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}

function saveForm() {
  const { collection, id, record } = activeForm;
  const data = Object.fromEntries(new FormData(form).entries());
  for (const key of ["bandwidth", "monthlyCost", "purchaseAmount"]) {
    if (key in data) data[key] = Number(data[key] || 0);
  }
  if ("isActive" in data) data.isActive = data.isActive === "true";
  if (collection === "ipAddresses" && hasIpConflict(data.address, id)) {
    alert("IP 地址已存在，系统已阻止重复分配。");
    return false;
  }
  if (collection === "backups") {
    data.createdAt = new Date().toLocaleString("zh-CN", { hour12: false }).replace(/\//g, "-");
    data.size = new Blob([data.content || ""]).size;
  }
  const next = { ...record, ...data, updatedBy: "ops", updatedAt: new Date().toLocaleString("zh-CN", { hour12: false }).replace(/\//g, "-") };
  if (id) {
    state[collection] = state[collection].map((item) => (item.id === id ? next : item));
    addLog("编辑记录", schemaTitle(collection), next.name || next.address || next.network || next.username || next.id);
  } else {
    state[collection].unshift(next);
    addLog("新增记录", schemaTitle(collection), next.name || next.address || next.network || next.username || next.id);
  }
  saveState();
  render();
  return true;
}

function schemaTitle(collection) {
  return schemas[collection]?.title || collection;
}

function addLog(action, resourceType, resource) {
  state.auditLogs.unshift({
    id: uid("log"),
    user: "ops",
    action,
    resource: `${resourceType}：${resource}`,
    detail: "通过本地控制台完成",
    createdAt: new Date().toLocaleString("zh-CN", { hour12: false }).replace(/\//g, "-"),
  });
}

function hasIpConflict(address, editingId) {
  return state.ipAddresses.some((ip) => ip.address === address && ip.id !== editingId);
}

function deleteRecord(collection, id) {
  const item = state[collection].find((record) => record.id === id);
  if (!item || !confirm("确认删除这条记录？")) return;
  state[collection] = state[collection].filter((record) => record.id !== id);
  addLog("删除记录", schemaTitle(collection), item.name || item.address || item.network || item.username || item.id);
  saveState();
  render();
}

function compareLatest() {
  const grouped = state.backups
    .filter((backup) => backup.status === "成功")
    .reduce((map, backup) => {
      map[backup.deviceId] = map[backup.deviceId] || [];
      map[backup.deviceId].push(backup);
      return map;
    }, {});
  const pair = Object.values(grouped)
    .map((items) => items.sort((a, b) => b.createdAt.localeCompare(a.createdAt)).slice(0, 2))
    .find((items) => items.length === 2);
  if (!pair) {
    alert("没有可对比的同设备成功备份版本。");
    return;
  }
  openDiff(pair[1], pair[0]);
}

function openDiff(oldBackup, newBackup) {
  const oldLines = oldBackup.content.split("\n");
  const newLines = newBackup.content.split("\n");
  const removed = oldLines.filter((line) => !newLines.includes(line));
  const added = newLines.filter((line) => !oldLines.includes(line));
  document.querySelector("#diff-summary").innerHTML = `
    <span class="tag danger">删除 ${removed.length} 行</span>
    <span class="tag ok">新增 ${added.length} 行</span>
    <span class="tag blue">${deviceName(newBackup.deviceId)}</span>
  `;
  document.querySelector("#diff-view").innerHTML = `
    <div class="diff-pane">
      <h3>${oldBackup.createdAt}</h3>
      ${oldLines.map((line) => `<div class="diff-line ${removed.includes(line) ? "remove" : ""}">${escapeHtml(line)}</div>`).join("")}
    </div>
    <div class="diff-pane">
      <h3>${newBackup.createdAt}</h3>
      ${newLines.map((line) => `<div class="diff-line ${added.includes(line) ? "add" : ""}">${escapeHtml(line)}</div>`).join("")}
    </div>
  `;
  document.querySelector("#diff-dialog").showModal();
}

function downloadBackup(id) {
  const backup = state.backups.find((item) => item.id === id);
  const blob = new Blob([backup.content || backup.note || ""], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${deviceName(backup.deviceId)}-${backup.createdAt.replace(/[: ]/g, "-")}.txt`;
  link.click();
  URL.revokeObjectURL(url);
}

function viewConfig(id) {
  const backup = state.backups.find((item) => item.id === id);
  alert(backup.content || backup.note || "无配置内容");
}

function importCsv(kind) {
  csvFile.dataset.kind = kind;
  csvFile.click();
}

function handleCsv(file, kind) {
  const reader = new FileReader();
  reader.onload = () => {
    const rows = String(reader.result)
      .trim()
      .split(/\r?\n/)
      .map((line) => line.split(",").map((cell) => cell.trim()));
    const [headers, ...body] = rows;
    body.forEach((row) => {
      const record = Object.fromEntries(headers.map((header, index) => [header, row[index] || ""]));
      if (kind === "ips" && record.address && !hasIpConflict(record.address)) {
        state.ipAddresses.unshift({ id: uid("ip"), status: "已分配", ...record });
      }
      if (kind === "devices" && record.name) {
        state.devices.unshift({ id: uid("dev"), status: "在线", type: "交换机", ...record });
      }
    });
    addLog("CSV 导入", kind === "ips" ? "IP 地址" : "设备", `${body.length} 条`);
    saveState();
    render();
  };
  reader.readAsText(file);
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  if (target.dataset.view) setView(target.dataset.view);
  if (target.dataset.closeDialog) document.querySelector(`#${target.dataset.closeDialog}`)?.close();
  if (target.dataset.add) openForm(target.dataset.add);
  if (target.dataset.edit) {
    const [collection, id] = target.dataset.edit.split(":");
    openForm(collection, id);
  }
  if (target.dataset.delete) {
    const [collection, id] = target.dataset.delete.split(":");
    deleteRecord(collection, id);
  }
  if (target.dataset.import) importCsv(target.dataset.import);
  if (target.id === "compare-latest") compareLatest();
  if (target.dataset.download) downloadBackup(target.dataset.download);
  if (target.dataset.viewConfig) viewConfig(target.dataset.viewConfig);
});

form.addEventListener("submit", (event) => {
  if (event.submitter?.id !== "save-record") return;
  event.preventDefault();
  if (saveForm()) dialog.close();
});

csvFile.addEventListener("change", () => {
  const [file] = csvFile.files;
  if (file) handleCsv(file, csvFile.dataset.kind);
  csvFile.value = "";
});

document.querySelector("#global-search").addEventListener("input", (event) => {
  currentQuery = event.target.value;
  render();
});

document.querySelector("#reset-data").addEventListener("click", () => {
  if (!confirm("确认恢复初始演示数据？")) return;
  state = structuredClone(seedState);
  saveState();
  render();
});

renderNav();
render();
