// src/store/QuestionStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
// 组合式 API 定义 Store（核心改造）
export const useQuestionStore = defineStore('question', () => {
  // ========== 1. 定义响应式状态（替代 state） ==========
  const generatedQuestion = ref<any>(null) // 生成的题目数据
  const checkResult = ref<any>(null)       // 幻觉校验结果
  const inputText = ref('')                // 输入的参考文本
  const questionType = ref('single')       // 选择的题型
  const illusionWarn = ref('')             // 幻觉拦截提示
  const validKs = ref<string[]>([])        // 有效知识点列表
  const showAnswerFlag = ref(false)        // 是否显示答案

  // ========== 2. 定义计算属性（可选，替代 getters） ==========
  // 示例：判断是否有生成的题目
  const hasGeneratedQuestion = computed(() => !!generatedQuestion.value)

  // ========== 3. 定义方法（替代 actions） ==========
  // 保存生成的题目
  const setGeneratedQuestion = (data: any) => {
    generatedQuestion.value = data
  }

  // 保存幻觉校验结果
  const setCheckResult = (data: any) => {
    checkResult.value = data
  }

  // 保存输入文本
  const setInputText = (text: string) => {
    inputText.value = text
  }

  // 保存题型
  const setQuestionType = (type: string) => {
    questionType.value = type
  }

  // 保存幻觉拦截提示
  const setIllusionWarn = (warn: string, validKsList: string[]) => {
    illusionWarn.value = warn
    validKs.value = validKsList
  }

  // 切换答案显示状态
  const toggleAnswerFlag = () => {
    showAnswerFlag.value = !showAnswerFlag.value
  }

  // 重置数据（仅生成新题目时调用）
  const resetIllusionState = () => {
    illusionWarn.value = ''
    validKs.value = []
  }

  // 重置所有数据（可选）
  const resetAll = () => {
    generatedQuestion.value = null
    checkResult.value = null
    illusionWarn.value = ''
    validKs.value = []
    showAnswerFlag.value = false
  }

  // ========== 4. 返回需要暴露的状态和方法 ==========
  return {
    // 状态
    generatedQuestion,
    checkResult,
    inputText,
    questionType,
    illusionWarn,
    validKs,
    showAnswerFlag,
    // 计算属性
    hasGeneratedQuestion,
    // 方法
    setGeneratedQuestion,
    setCheckResult,
    setInputText,
    setQuestionType,
    setIllusionWarn,
    toggleAnswerFlag,
    resetIllusionState,
    resetAll
  }
}, {
  // 可选：持久化（pinia-plugin-persistedstate v4：用 pick 指定字段，无 enabled/strategies）
  persist: {
    key: 'question-store',
    storage: localStorage,
    pick: ['generatedQuestion', 'checkResult', 'inputText', 'questionType']
  }
})