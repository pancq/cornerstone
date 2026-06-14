import { ref } from 'vue';
import { getLocale } from '../i18n'
// AI服务配置
export interface AIServiceConfig {
 name: string;
 provider: 'deepseek' | 'qwen' | 'zhipu' | 'baichuan' | 'claude' | 'openai' | 'local';
 apiKey?: string;
 apiBase?: string;
 model: string;
 enabled: boolean;
}
// AI预测结果
export interface AIPrediction {
 id: string;
 type: 'root_cause' | 'trend' | 'summary' | 'query';
 title: string;
 content: string;
 confidence: number;
 suggestion: string;
 timestamp: string;
}
// 服务端 AI 预测 API
// 检查是否为问候语
function isGreeting(input: string): boolean {
 const greetings = ['你好', '您好', 'hello', 'hi', '哈喽', '嗨', '早安', '午安', '晚安', '您好啊', '你好啊'];
 return greetings.some(greeting => input.toLowerCase().includes(greeting.toLowerCase()));
}

// 生成问候语回复
function generateGreetingResponse(): AIPrediction {
 const greetings = [
 { content: '您好！我是智能运维助手，很高兴为您服务。请问有什么可以帮助您的？', suggestion: '您可以询问设备状态、预警信息或进行故障排查' },
 { content: '你好！欢迎使用智能预警系统。我可以帮您分析设备状态、预测趋势或解答运维相关问题。', suggestion: '试试问"设备状态如何？"或"帮我分析一下故障原因"' },
 { content: '您好！我是您的AI运维助手。请问需要查询什么信息？', suggestion: '您可以使用智能问答功能了解系统状态' }
 ];
 const response = greetings[Math.floor(Math.random() * greetings.length)];
 return {
 id: `gr-${Date.now()}`,
 type: 'query',
 title: '问候响应',
 content: response.content,
 confidence: 0.98,
 suggestion: response.suggestion,
 timestamp: new Date().toLocaleString(getLocale() || 'zh-CN')
 };
}

// 模拟AI预测响应（实际项目中调用后端API）
async function fetchAIPrediction(type: string, input: string): Promise<AIPrediction> {
 // 模拟延迟
 await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000));
 
 // 如果是问答类型且输入是问候语，返回问候响应
 if (type === 'query' && isGreeting(input)) {
 return generateGreetingResponse();
 }
 
 // 模拟不同类型的AI预测结果
 const predictions: Record<string, () => AIPrediction> = {
 root_cause: () => ({
 id: `rc-${Date.now()}`,
 type: 'root_cause',
 title: '根因分析结果',
 content: '根据系统数据分析，设备离线可能由以下原因导致：\n\n1. **网络连接问题**（60%可能性）\n - 检查网线连接状态\n - 确认交换机端口是否正常\n\n2. **电源故障**（25%可能性）\n - 检查设备供电状态\n - 确认UPS是否正常工作\n\n3. **设备硬件故障**（15%可能性）\n - 联系供应商进行硬件检测',
 confidence: 0.87,
 suggestion: '建议优先检查网络连接和端口状态，这是最可能的原因',
 timestamp: new Date().toLocaleString(getLocale() || 'zh-CN')
 }),
 trend: () => ({
 id: `tr-${Date.now()}`,
 type: 'trend',
 title: '趋势预测结果',
 content: '基于历史数据分析，预测结果如下：\n\n**IP池耗尽预测**：\n- 当前使用率：78%\n- 预计耗尽时间：23天后\n- 建议提前规划新子网\n\n**备份成功率趋势**：\n- 近7天成功率：72%\n- 呈下降趋势\n- 建议检查备份任务配置',
 confidence: 0.92,
 suggestion: '建议在15天内完成新子网规划，避免IP耗尽影响业务',
 timestamp: new Date().toLocaleString(getLocale() || 'zh-CN')
 }),
 summary: () => ({
 id: `sm-${Date.now()}`,
 type: 'summary',
 title: '智能摘要',
 content: '当前系统预警摘要：\n\n🔴 **紧急问题**（需立即处理）\n- 1台演示设备离线（SW-DEMO-CORE-01）\n- 2条演示专线断开\n\n🟡 **待关注问题**（本周内处理）\n- 3台演示设备保修即将到期\n- 2个演示子网容量超过80%\n- 备份成功率下降至72%\n\n🟢 **正常状态**\n- 其他设备运行正常\n- IP地址充足',
 confidence: 0.95,
 suggestion: '优先处理设备离线和专线断开问题，这可能影响核心业务',
 timestamp: new Date().toLocaleString(getLocale() || 'zh-CN')
 }),
 query: () => {
 const responses = [
 {
 content: '根据当前数据，需要关注的设备有：\n\n1. **SW-DEMO-CORE-01** - 离线状态，需立即排查\n2. **FW-DEMO-EDGE-01** - 保修即将到期（7天后）\n3. **RT-DEMO-WAN-01** - 正在维修中\n\n建议先处理离线设备，确保核心网络正常运行。',
 suggestion: '点击"查看设备"可跳转到详情页面'
 },
 {
 content: '当前系统运行状态整体良好，但存在以下需要关注的问题：\n\n1. 备份成功率有所下降（72%）\n2. 部分子网IP使用率较高\n\n建议定期监控备份状态，及时规划IP资源。',
 suggestion: '可在预警中心设置定期提醒'
 },
 {
 content: '设备离线可能的原因包括：\n\n1. 网络连接中断\n2. 电源故障\n3. 设备硬件问题\n4. 配置错误\n\n建议按照以下顺序排查：\n1. 检查物理连接\n2. 确认电源状态\n3. 查看设备日志',
 suggestion: '如果问题持续，请联系供应商技术支持'
 }
 ];
 const response = responses[Math.floor(Math.random() * responses.length)];
 return {
 id: `qu-${Date.now()}`,
 type: 'query',
 title: '智能问答结果',
 content: response.content,
 confidence: 0.85 + Math.random() * 0.1,
 suggestion: response.suggestion,
 timestamp: new Date().toLocaleString(getLocale() || 'zh-CN')
 };
 }
 };
 return predictions[type]?.() || predictions.summary();
}
// AI预测服务组合式函数
export function useAIPrediction() {
 const loading = ref(false);
 const prediction = ref<AIPrediction | null>(null);
 const error = ref<string | null>(null);
 // 执行根因分析
 async function analyzeRootCause(input: string): Promise<void> {
 loading.value = true;
 error.value = null;
 try {
 prediction.value = await fetchAIPrediction('root_cause', input);
 }
 catch (e) {
 error.value = 'AI分析失败，请稍后重试';
 console.error('AI prediction error:', e);
 }
 finally {
 loading.value = false;
 }
 }
 // 执行趋势预测
 async function predictTrend(input: string): Promise<void> {
 loading.value = true;
 error.value = null;
 try {
 prediction.value = await fetchAIPrediction('trend', input);
 }
 catch (e) {
 error.value = 'AI预测失败，请稍后重试';
 console.error('AI prediction error:', e);
 }
 finally {
 loading.value = false;
 }
 }
 // 生成智能摘要
 async function generateSummary(input: string): Promise<void> {
 loading.value = true;
 error.value = null;
 try {
 prediction.value = await fetchAIPrediction('summary', input);
 }
 catch (e) {
 error.value = 'AI摘要生成失败，请稍后重试';
 console.error('AI prediction error:', e);
 }
 finally {
 loading.value = false;
 }
 }
 // 自然语言查询
 async function queryAI(input: string): Promise<void> {
 loading.value = true;
 error.value = null;
 try {
 prediction.value = await fetchAIPrediction('query', input);
 }
 catch (e) {
 error.value = 'AI查询失败，请稍后重试';
 console.error('AI prediction error:', e);
 }
 finally {
 loading.value = false;
 }
 }
 // 清除结果
 function clearPrediction() {
 prediction.value = null;
 error.value = null;
 }
 return {
 loading,
 prediction,
 error,
 analyzeRootCause,
 predictTrend,
 generateSummary,
 queryAI,
 clearPrediction
 };
}
// 默认服务配置
const defaultServices: AIServiceConfig[] = [
 {
 name: 'DeepSeek',
 provider: 'deepseek',
 apiKey: '',
 apiBase: 'https://api.deepseek.com',
 model: 'deepseek-chat',
 enabled: true
 },
 {
 name: 'Tongyi Qwen',
 provider: 'qwen',
 apiKey: '',
 apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
 model: 'qwen-plus',
 enabled: false
 },
 {
 name: 'Zhipu GLM',
 provider: 'zhipu',
 apiKey: '',
 apiBase: 'https://open.bigmodel.cn/api/paas/v4',
 model: 'glm-4-flash',
 enabled: false
 },
 {
 name: 'Claude 3',
 provider: 'claude',
 apiKey: '',
 apiBase: 'https://api.anthropic.com',
 model: 'claude-3-5-sonnet-20241022',
 enabled: false
 },
 {
 name: 'GPT-4',
 provider: 'openai',
 apiKey: '',
 apiBase: 'https://api.openai.com',
 model: 'gpt-4o',
 enabled: false
 },
 {
 name: 'Local Model',
 provider: 'local',
 apiBase: 'http://localhost:8000/v1',
 model: 'qwen2.5-7b-instruct',
 enabled: false
 }
];

// AI服务配置管理
export function useAIServiceConfig() {
 // 从localStorage加载保存的配置，没有则使用默认配置
 const savedConfig = localStorage.getItem('ai_service_config');
 const services = ref<AIServiceConfig[]>(savedConfig ? JSON.parse(savedConfig) : defaultServices);
 
 // 默认不展开任何服务配置（空对象），用户点击后才展开
 const currentService = ref<AIServiceConfig>({
 name: '',
 provider: 'local',
 model: '',
 enabled: false
 });
 function setCurrentService(service: AIServiceConfig) {
 currentService.value = service;
 }
 function updateServiceConfig(index: number, config: Partial<AIServiceConfig>) {
 services.value[index] = { ...services.value[index], ...config };
 }
 function toggleService(index: number) {
 services.value[index].enabled = !services.value[index].enabled;
 // 自动保存配置到localStorage
 localStorage.setItem('ai_service_config', JSON.stringify(services.value));
 }
 // 添加自定义服务
 function addCustomService(config: Omit<AIServiceConfig, 'enabled'>) {
 const newService: AIServiceConfig = {
 ...config,
 enabled: false
 };
 services.value.push(newService);
 localStorage.setItem('ai_service_config', JSON.stringify(services.value));
 }
 // 删除服务
 function removeService(index: number) {
 services.value.splice(index, 1);
 localStorage.setItem('ai_service_config', JSON.stringify(services.value));
 // 如果删除的是当前选中的服务，清空选择
 if (currentService.value.name && services.value.findIndex(s => s.name === currentService.value.name) === -1) {
 currentService.value = {
 name: '',
 provider: 'local',
 model: '',
 enabled: false
 };
 }
 }
 return {
 services,
 currentService,
 setCurrentService,
 updateServiceConfig,
 toggleService,
 addCustomService,
 removeService
 };
}
