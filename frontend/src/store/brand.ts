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
      const res = await fetch('/api/v1/settings/public/brand')
      if (!res.ok) return
      const result = await res.json()
      if (result) {
        brandNameZh.value = result.brand_name_zh || '基石'
        brandNameEn.value = result.brand_name_en || 'Cornerstone'
        brandSlogan.value = result.brand_slogan || '看得见，管得住'
        brandSubtitle.value = result.brand_subtitle || 'IT基础设施资源管理平台'
        brandLogoUrl.value = result.brand_logo_url || ''
      }
    } catch (e) {
      console.warn('品牌设置加载失败，使用默认值')
    } finally {
      loaded.value = true
    }
  }

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