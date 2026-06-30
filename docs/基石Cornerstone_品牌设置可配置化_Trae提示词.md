# 基石 Cornerstone · 品牌设置可配置化
## 用于开源场景的白标支持
## Trae 开发提示词

---

## 背景说明

当前系统名称「基石」「Cornerstone」「看得见，管得住」等品牌文字硬编码在多处前端代码中。
为支持开源后第三方部署自定义品牌（白标），本次将这些文字改为可配置项，并设置默认值为现有品牌内容。

设计原则：**默认保留现有品牌，允许使用者自行修改，不影响现有用户的使用体验。**

---

## 一、品牌设置与公司信息分离

当前「系统设置」已有「公司信息」卡片（公司名称、IT部门等），本次新增独立的「品牌设置」卡片，两者概念不同：

```
品牌设置  → 控制"这是什么系统"（系统本身的名称和标语）
公司信息  → 控制"谁在使用这个系统"（部署方的公司信息）
```

---

## 二、后端实现

### 配置项

在现有 `settings` 表中新增以下 key，设置默认值：

```python
BRAND_SETTINGS_DEFAULTS = {
    "brand_name_zh":     "基石",                  # 系统中文名称
    "brand_name_en":     "Cornerstone",           # 系统英文名称
    "brand_slogan":      "看得见，管得住",          # 系统标语
    "brand_subtitle":    "IT基础设施资源管理平台",  # 系统副标题
    "brand_logo_url":    "",                       # 自定义Logo（为空时使用默认Logo）
}
```

### API 接口

追加到 `backend/src/api/settings.py`：

```
GET  /api/v1/settings/brand
     获取品牌设置，若数据库中无记录则返回默认值（不报错）
     返回：
     {
         "brand_name_zh": "基石",
         "brand_name_en": "Cornerstone",
         "brand_slogan": "看得见，管得住",
         "brand_subtitle": "IT基础设施资源管理平台",
         "brand_logo_url": ""
     }

PUT  /api/v1/settings/brand
     保存品牌设置
     权限：仅 super_admin
     Body: 同上结构
     校验：brand_name_zh 和 brand_name_en 不可为空，
           若提交空值则恢复为默认值，不允许系统名称完全为空

POST /api/v1/settings/brand/reset
     重置为默认品牌设置（恢复"基石 Cornerstone"）
     权限：仅 super_admin
```

### 公开接口（未登录也可访问）

新增一个无需鉴权的接口，供登录页获取品牌信息：

```
GET /api/v1/public/brand
    公开接口，无需登录即可访问
    返回品牌名称、Slogan、Logo URL（不返回任何敏感信息）
    用于登录页动态显示品牌
```

---

## 三、前端实现

### 1. 系统设置页面新增「品牌设置」卡片

**文件**：`frontend/src/features/system/Settings.vue`（或对应系统设置页面）

放置在「公司信息」卡片下方：

```
卡片标题：品牌设置

提示文字（卡片顶部灰色小字）：
「以下设置控制系统本身的名称和标语，适用于二次部署或品牌定制场景」

字段：
- 系统中文名称（必填，默认"基石"）
- 系统英文名称（必填，默认"Cornerstone"）
- 系统标语（选填，默认"看得见，管得住"）
- 系统副标题（选填，默认"IT基础设施资源管理平台"）
- 系统Logo（选填，图片上传，留空使用默认Logo）

底部按钮：
[保存]  [恢复默认]

「恢复默认」点击后二次确认：
「将恢复为"基石 Cornerstone"默认品牌设置，确认继续？」
```

### 2. 全局品牌状态管理

新建 `frontend/src/store/brand.ts`：

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useBrandStore = defineStore('brand', () => {
  const brandNameZh = ref('基石')
  const brandNameEn = ref('Cornerstone')
  const brandSlogan = ref('看得见，管得住')
  const brandSubtitle = ref('IT基础设施资源管理平台')
  const brandLogoUrl = ref('')
  const loaded = ref(false)

  async function loadBrand() {
    try {
      // 优先使用公开接口（未登录场景，如登录页）
      const res = await fetch('/api/v1/public/brand').then(r => r.json())
      if (res.code === 0) {
        brandNameZh.value = res.data.brand_name_zh || '基石'
        brandNameEn.value = res.data.brand_name_en || 'Cornerstone'
        brandSlogan.value = res.data.brand_slogan || '看得见，管得住'
        brandSubtitle.value = res.data.brand_subtitle || 'IT基础设施资源管理平台'
        brandLogoUrl.value = res.data.brand_logo_url || ''
      }
    } catch (e) {
      // 接口失败时静默使用默认值，不影响系统正常使用
      console.warn('品牌设置加载失败，使用默认值')
    } finally {
      loaded.value = true
    }
  }

  // 浏览器标签页标题动态更新
  function updateDocumentTitle(pageTitle?: string) {
    document.title = pageTitle
      ? `${pageTitle} - ${brandNameZh.value}`
      : `${brandNameZh.value} · ${brandSubtitle.value}`
  }

  return {
    brandNameZh, brandNameEn, brandSlogan, brandSubtitle, brandLogoUrl,
    loaded, loadBrand, updateDocumentTitle
  }
})
```

在 `App.vue` 的 `onMounted` 中调用 `loadBrand()`，应用启动时加载一次。

### 3. 替换所有硬编码品牌文字

全局搜索代码中硬编码的品牌文字，替换为从 `useBrandStore` 读取：

```bash
# 搜索命令（供参考，了解需要替换的范围）
grep -rn "基石\|Cornerstone\|看得见，管得住" frontend/src/ --include="*.vue"
```

**需要替换的关键位置**：

**登录页** `frontend/src/features/auth/Login.vue`：
```html
<!-- 替换前 -->
<h1>基石</h1>
<p>Cornerstone</p>
<h2>看得见，管得住</h2>

<!-- 替换后 -->
<script setup>
import { useBrandStore } from '@/store/brand'
const brandStore = useBrandStore()
onMounted(() => brandStore.loadBrand())
</script>

<h1>{{ brandStore.brandNameZh }}</h1>
<p>{{ brandStore.brandNameEn }}</p>
<h2>{{ brandStore.brandSlogan }}</h2>
<p class="subtitle">每一项基础设施，都在掌控之中</p>
```

**侧边栏顶部 Logo 区域**：
```html
<!-- 替换前 -->
<div class="logo">基石 <span>Cornerstone</span></div>

<!-- 替换后 -->
<div class="logo">
  {{ brandStore.brandNameZh }}
  <span>{{ brandStore.brandNameEn }}</span>
</div>
```

**浏览器标签页标题**（在路由守卫中统一处理）：
```typescript
// frontend/src/app/router.ts
router.afterEach((to) => {
  const brandStore = useBrandStore()
  brandStore.updateDocumentTitle(to.meta.title as string)
})
```

**月报 PDF 标题**（后端 `report_generator.py`，已从 company_name 读取，本次额外读取品牌名）：
```python
# 在 draw_cover_page 中，报告主标题部分改为从配置读取
report_title = brand_settings.get('brand_subtitle', 'IT基础设施资源管理平台')
c.drawCentredString(width / 2, height * 0.73, report_title)
```

后端在 `collect_report_data` 中追加读取品牌设置：
```python
brand = await get_brand_settings(db)  # 类似 get_company_info 的实现
data.brand_name = brand.get('brand_name_zh', '基石')
data.report_title = brand.get('brand_subtitle', 'IT基础设施资源管理平台')
```

---

## 四、Logo 自定义上传

复用现有 Logo 上传功能（系统设置中已有 Logo 上传与共享逻辑），扩展为：

```
GET  /api/v1/settings/logo       获取当前Logo（已有接口，不变）
POST /api/v1/settings/logo       上传Logo（已有接口，不变）
DELETE /api/v1/settings/logo     删除Logo，恢复默认（已有接口，不变）
```

前端登录页和侧边栏 Logo 显示逻辑：
```typescript
// 优先使用自定义Logo，为空时使用项目内置默认Logo
const logoSrc = computed(() =>
  brandStore.brandLogoUrl || '/assets/default-logo.svg'
)
```

---

## 五、开源准备：默认演示数据脱敏

借此机会，检查并清理代码中的真实测试数据，替换为通用占位数据：

```bash
grep -rln "快乐茄\|北京快乐茄" backend/ frontend/ --include="*.py" --include="*.ts" --include="*.vue"
```

找到的所有「快乐茄」相关硬编码测试数据，替换为通用占位符，如：
```
公司名称示例：示例科技有限公司 / Acme Corporation
站点示例：上海总部 / 北京分公司（保留地名类示例，因为通用且不涉及具体公司）
```

---

## 开发顺序

**Step 1**：后端 `settings` 表新增品牌配置项 + 默认值
**Step 2**：GET/PUT `/settings/brand` 接口 + 公开接口 `/public/brand`
**Step 3**：前端 `useBrandStore` 品牌状态管理
**Step 4**：系统设置页面新增「品牌设置」卡片
**Step 5**：登录页替换硬编码品牌文字
**Step 6**：侧边栏 Logo 区域替换硬编码品牌文字
**Step 7**：浏览器标签页标题动态更新（路由守卫）
**Step 8**：月报 PDF 标题读取品牌设置
**Step 9**：清理代码中的「快乐茄」测试数据，替换为通用占位符

---

## 注意事项

- 所有品牌设置项必须有默认值，接口异常或未配置时**自动降级为"基石 Cornerstone"**，不能导致页面空白或报错
- 公开接口 `/api/v1/public/brand` 不返回任何用户数据或敏感信息，仅返回品牌展示字段
- 品牌名称和公司信息是两个独立概念，不要在数据结构或UI上混淆
- Logo上传逻辑复用现有实现，不重复开发
- 「恢复默认」操作需要二次确认，避免误触
- 替换硬编码文字时，逐个文件替换并验证，不要用全局批量替换（避免误改注释或其他无关文本）
- 开源场景下，README 中需要说明：「系统名称、Logo、标语均可在 系统设置-品牌设置 中自定义，默认使用'基石 Cornerstone'品牌」
