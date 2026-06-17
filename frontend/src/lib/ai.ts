import { ref } from 'vue';
import api from '@/api/axios';
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

// 调用后端真实 API 获取 AI 预测
async function fetchAIPrediction(type: string, input: string): Promise<AIPrediction> {
 // 如果是问答类型且输入是问候语，返回本地问候响应（无需调后端）
 if (type === 'query' && isGreeting(input)) {
   const greetings = [
     { content: '您好！我是智能运维助手，很高兴为您服务。请问有什么可以帮助您的？', suggestion: '您可以询问设备状态、预警信息或进行故障排查' },
     { content: '你好！欢迎使用智能运维系统。我可以帮您分析设备状态、预测趋势或解答运维相关问题。', suggestion: '试试点上面的功能卡片，或直接输入问题' },
     { content: '您好！我是您的AI运维助手。请问需要查询什么信息？', suggestion: '可以使用智能问答功能了解系统状态' }
   ];
   const response = greetings[Math.floor(Math.random() * greetings.length)];
   return {
     id: `gr-${Date.now()}`,
     type: 'query',
     title: '问候响应',
     content: response.content,
     confidence: 0.98,
     suggestion: response.suggestion,
     timestamp: new Date().toLocaleString('zh-CN')
   };
 }

 // 映射类型到后端 API 路径
 const endpointMap: Record<string, string> = {
   root_cause: '/ai/root-cause',
   trend: '/ai/trend',
   summary: '/ai/summary',
   query: '/ai/search',
 };

 const endpoint = endpointMap[type] || '/ai/summary';

 try {
   const response = await api.post(endpoint, { question: input });

   if (type === 'query') {
     // /ai/search 返回格式不同
     const result = response.data?.data || response.data;
     const answerText = result?.answer_text || result?.data?.answer_text || '查询完成';
     const suggestionList = result?.suggestions || [];
     return {
       id: `qu-${Date.now()}`,
       type: 'query',
       title: '智能问答结果',
       content: answerText,
       confidence: 0.9,
       suggestion: suggestionList.length > 0 ? suggestionList.join('；') : '您可以继续提问',
       timestamp: new Date().toLocaleString('zh-CN'),
     };
   }

   // summary / trend / root_cause 统一返回 AIPredictionResponse 格式
   const data = response.data;
   return {
     id: data.id || `${type}-${Date.now()}`,
     type: data.type || type,
     title: data.title || '',
     content: data.content || '',
     confidence: data.confidence ?? 0.85,
     suggestion: data.suggestion || '',
     timestamp: data.timestamp || new Date().toLocaleString('zh-CN'),
   };
 } catch (e: any) {
   console.error(`AI ${type} API call failed:`, e);
   throw new Error(e?.response?.data?.detail || `AI ${type} 请求失败，请稍后重试`);
 }
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
