<template>
  <!-- 模板部分完全不变，无需修改 -->
  <div class="question-generator-container" style="display: flex; gap: 20px; padding: 20px; height: calc(100vh - 60px);">
    <!-- 左侧：配置区 -->
    <div class="left-panel" style="flex: 1; display: flex; flex-direction: column; gap: 20px;">
      <!-- 输入文本区 -->
      <el-card>
        <template #header>
          <span>输入文本</span>
        </template>
        <el-input
          type="textarea"
          v-model="questionStore.inputText"
          placeholder="输入需要AI出题的参考文本内容，点击【生成题目】可通过AI生成题目"
          :rows="15"
        />
        <!-- 幻觉拦截提示（直接用Store的状态） -->
        <div v-if="questionStore.illusionWarn" class="illusion-warn" style="margin: 10px 0; padding: 10px; background: #fef0f0; border: 1px solid #fbc4c4; border-radius: 4px; color: #f56c6c;">
          <i class="el-icon-warning"></i> {{ questionStore.illusionWarn }}
          <div v-if="questionStore.validKs.length > 0" style="margin-top: 5px; font-size: 12px;">
            ✅ 有效知识点：{{ questionStore.validKs.join('、') }}
          </div>
        </div>
        <!-- 跳转并传递知识点状态的按钮 -->
        <el-button type="primary" @click="viewKnowledgeGraph">查看相关知识图谱</el-button>
      </el-card>

      <!-- 题型选择 + 操作按钮 -->
      <el-card>
        <template #header>
          <span>请选择题目类型</span>
        </template>
        <div style="display: flex; flex-direction: column; gap: 15px;">
          <el-select v-model="questionStore.questionType" placeholder="请选择题型" style="width: 100%;">
            <el-option label="单选题" value="single" />
            <el-option label="多选题" value="multiple" />
            <el-option label="填空题" value="blank" />
            <el-option label="编程题" value="code" />
          </el-select>
          <el-button type="primary" @click="generateQuestion" :loading="loading">
            生成题目
          </el-button>
          <el-button @click="updateQuestion" :disabled="!questionStore.hasGeneratedQuestion">
            更新题目
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 右侧：预览区 -->
    <div class="right-panel" style="flex: 1.5; overflow-y: auto;">
      <el-card>
        <template #header>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="题目效果展示" name="preview" />
            <el-tab-pane label="幻觉校验结果" name="illusion-check" />
            <el-tab-pane label="历史题目" name="history" />
          </el-tabs>
        </template>

        <!-- 预览模式 -->
        <div v-if="activeTab === 'preview'">
          <div v-if="!questionStore.hasGeneratedQuestion" style="text-align: center; color: #999; padding: 40px 0;">
            请在左侧输入内容并点击【生成题目】
          </div>
          <div v-else>
            <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 20px;">
              【标题】{{ questionStore.generatedQuestion.title }}
            </h3>
            <div style="margin-bottom: 20px; font-size: 16px;">
              <strong>【题目】</strong>{{ questionStore.generatedQuestion.content }}
            </div>

            <!-- 选项（仅单选/多选展示） -->
            <div v-if="['single', 'multiple'].includes(questionStore.questionType)" style="margin-bottom: 20px;">
              <strong>【选项】</strong>
              <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
                <div v-for="(opt, idx) in questionStore.generatedQuestion.options" :key="idx">
                  <el-radio v-if="questionStore.questionType === 'single'" v-model="userAnswer" :label="opt.key" style="margin-right: 10px;">
                    {{ opt.key }}. {{ opt.value }}
                  </el-radio>
                  <el-checkbox v-else v-model="userAnswer" :label="opt.key" style="margin-right: 10px;">
                    {{ opt.key }}. {{ opt.value }}
                  </el-checkbox>
                </div>
              </div>
            </div>

            <!-- 元信息展示 -->
            <el-button type="primary" @click="showAnswer">显示答案</el-button>
            <el-descriptions :column="1" border style="margin: 20px 0;">
              <el-descriptions-item label="【难度】">{{ questionStore.generatedQuestion.difficulty }}</el-descriptions-item>
              <el-descriptions-item label="【知识点】">{{ questionStore.generatedQuestion.knowledgePoint }}</el-descriptions-item>
              <el-descriptions-item label="【章节】">{{ questionStore.generatedQuestion.chapter }}</el-descriptions-item>
              <el-descriptions-item label="【答案】" v-show="questionStore.showAnswerFlag">{{ questionStore.generatedQuestion.answer }}</el-descriptions-item>
            </el-descriptions>

            <!-- 解析 -->
            <div>
              <strong>【解析】</strong>
              <p style="margin-top: 10px; line-height: 1.6;">{{ questionStore.generatedQuestion.analysis }}</p>
            </div>
          </div>
        </div>

        <!-- 幻觉校验结果标签页 -->
        <div v-if="activeTab === 'illusion-check'">
          <div v-if="!questionStore.checkResult" style="text-align: center; color: #999; padding: 40px 0;">
            请先生成题目，自动生成幻觉校验结果
          </div>
          <div v-else style="padding: 10px;">
            <h4 style="font-size: 16px; font-weight: bold; margin-bottom: 15px;">📊 知识点幻觉校验结果</h4>
            
            <!-- 匹配率进度条 -->
            <div style="margin: 15px 0;">
              <span>知识点匹配率（图谱覆盖率）：{{ questionStore.checkResult.match_rate }}%</span>
              <el-progress 
                :percentage="questionStore.checkResult.match_rate" 
                :status="questionStore.checkResult.has_illusion ? 'warning' : 'success'"
                style="margin-top: 8px;"
              />
            </div>

            <!-- 校验提示 -->
            <el-alert
              :title="questionStore.checkResult.suggestion"
              :type="questionStore.checkResult.has_illusion ? 'warning' : 'success'"
              show-icon
              style="margin: 15px 0;"
            />

            <!-- 知识点明细 -->
            <div style="margin-top: 15px;">
              <div v-if="questionStore.checkResult.valid_ks.length" style="color: #67c23a; margin-bottom: 8px;">
                <i class="el-icon-circle-check"></i> <strong>有效知识点（来自知识图谱）：</strong>
                {{ questionStore.checkResult.valid_ks.join('、') }}
              </div>
              <div v-if="questionStore.checkResult.illusion_ks.length" style="color: #f56c6c;">
                <i class="el-icon-circle-close"></i> <strong>幻觉知识点（图谱中无）：</strong>
                {{ questionStore.checkResult.illusion_ks.join('、') }}
              </div>
            </div>
          </div>
        </div>

        <!-- 历史题目 -->
        <div v-else-if="activeTab === 'history'">
          <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px;">
            <el-input
              v-model="historyKeyword"
              placeholder="按标题/知识点/章节搜索"
              clearable
              style="flex: 1;"
            />
            <el-button type="primary" @click="loadHistory" :loading="historyLoading">刷新</el-button>
          </div>

          <el-table
            v-loading="historyLoading"
            :data="filteredHistory"
            height="520"
            stripe
            style="width: 100%;"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
            <el-table-column prop="knowledge_point" label="知识点" min-width="160" show-overflow-tooltip />
            <el-table-column prop="chapter" label="章节" width="90" />
            <el-table-column prop="difficulty" label="难度" width="90" />
            <el-table-column prop="created_at" label="生成时间" min-width="170" show-overflow-tooltip />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openHistoryDetail(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="!historyLoading && filteredHistory.length === 0" style="text-align: center; color: #999; padding: 18px 0;">
            暂无历史题目
          </div>

          <el-drawer v-model="historyDrawerOpen" title="历史题目详情" size="55%">
            <div v-if="historySelected">
              <h3 style="font-size: 18px; font-weight: 700; margin: 0 0 12px 0;">
                【标题】{{ historySelected.title }}
              </h3>

              <el-descriptions :column="1" border>
                <el-descriptions-item label="【ID】">{{ historySelected.id }}</el-descriptions-item>
                <el-descriptions-item label="【难度】">{{ historySelected.difficulty }}</el-descriptions-item>
                <!-- 只显示部分知识点 -->
                <el-descriptions-item label="【知识点】">{{ historySelected.knowledge_point}}</el-descriptions-item>

                <el-descriptions-item label="【章节】">{{ historySelected.chapter }}</el-descriptions-item>
                <el-descriptions-item label="【生成时间】">{{ historySelected.created_at }}</el-descriptions-item>
                <!-- <el-descriptions-item label="【知识点列表 ks】">
                  
                  {{ Array.isArray(historySelected.ks) ? historySelected.ks.slice(0, 3).join('、') : ''}}
                </el-descriptions-item> -->
              </el-descriptions>

              <div style="margin-top: 14px;">
                <strong>【题目】</strong>
                <div style="margin-top: 8px; line-height: 1.7;">{{ historySelected.content }}</div>
              </div>

              <div v-if="Array.isArray(historySelected.options) && historySelected.options.length" style="margin-top: 14px;">
                <strong>【选项】</strong>
                <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 6px;">
                  <div v-for="(opt, idx) in historySelected.options" :key="idx">
                    <span v-if="opt && typeof opt === 'object' && 'key' in opt">{{ opt.key }}. {{ opt.value }}</span>
                    <span v-else>{{ opt }}</span>
                  </div>
                </div>
              </div>

              <div style="margin-top: 14px;">
                <strong>【答案】</strong>
                <div style="margin-top: 8px;">{{ historySelected.answer }}</div>
              </div>

              <div style="margin-top: 14px;">
                <strong>【解析】</strong>
                <div style="margin-top: 8px; line-height: 1.7;">{{ historySelected.analysis }}</div>
              </div>
            </div>
          </el-drawer>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api'
import { useKnowledgeStore } from '../store/KnowledgeStore'
import { useQuestionStore } from '../store/QuestionStore' // 引入组合式Store
import router from '../router'

// ========== 核心：初始化组合式Store ==========
const questionStore = useQuestionStore()

// ========== 仅保留无需持久化的临时变量 ==========
const activeTab = ref('preview')   // 标签页状态（无需持久化）
const loading = ref(false)         // 加载状态（无需持久化）
const userAnswer = ref('')         // 用户答案（预览用，无需持久化）

type QuestionHistoryItem = {
  id: number
  title: string
  content: string
  options: any[]
  answer: string
  difficulty: number
  knowledge_point: string
  chapter: number
  analysis: string
  ks: any[]
  created_at: string
}

const historyLoading = ref(false)
const historyQuestions = ref<QuestionHistoryItem[]>([])
const historyKeyword = ref('')
const historyDrawerOpen = ref(false)
const historySelected = ref<QuestionHistoryItem | null>(null)

const filteredHistory = computed(() => {
  const kw = historyKeyword.value.trim().toLowerCase()
  if (!kw) return historyQuestions.value
  return historyQuestions.value.filter(q => {
    const title = (q.title || '').toLowerCase()
    const kp = (q.knowledge_point || '').toLowerCase()
    const chapter = String(q.chapter ?? '')
    return title.includes(kw) || kp.includes(kw) || chapter.includes(kw)
  })
})

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const res = await request<{ code: number; msg: string; data: QuestionHistoryItem[] }>('get', '/generate-question/history')
    const list = Array.isArray(res) ? res : (res?.data ?? [])
    historyQuestions.value = Array.isArray(list) ? list : []
  } catch (e) {
    console.error('获取历史题目失败：', e)
    const msg = (e as any)?.message
    if (!msg) ElMessage.error('获取历史题目失败')
  } finally {
    historyLoading.value = false
  }
}

const openHistoryDetail = (row: QuestionHistoryItem) => {
  historySelected.value = row
  historyDrawerOpen.value = true
}

// ========== 跳转图谱页逻辑（不变） ==========
const viewKnowledgeGraph = () => {
  try {
    if (!questionStore.inputText) {
      ElMessage.warning('请先输入参考文本')
      return
    }

    const knowledgeStore = useKnowledgeStore()
    const point = questionStore.inputText
    if (!point) {
      ElMessage.warning('知识点不存在')
      return
    }

    knowledgeStore.setKnowledgeText(point)
    router.push('/kg')
  } catch (err) {
    console.error('查看图谱报错：', err)
    ElMessage.error('打开知识图谱失败')
  }
}

// ========== 显示答案逻辑（直接调用Store方法） ==========
const showAnswer = () => {
  if (!questionStore.hasGeneratedQuestion) {
    ElMessage.warning('请先生成题目')
    return
  }
  questionStore.toggleAnswerFlag()
}

// ========== 生成题目逻辑（适配组合式Store） ==========
const generateQuestion = async () => {
  // 重置幻觉相关状态（保留题目数据）
  questionStore.resetIllusionState()

  if (!questionStore.inputText.trim()) {
    ElMessage.error('请输入参考文本内容')
    return
  }

  loading.value = true
  try {
    // 1. 调用生成接口
    const res = await request('post', '/generate-question/generate', {
      text: questionStore.inputText,
      type: questionStore.questionType
    }, {
      headers: { 'Content-Type': 'application/json' }
    })

    // 2. 处理幻觉拦截
    if (res.code === 403) {
      questionStore.setIllusionWarn(res.msg, res.valid_ks || [])
      ElMessage.warning('检测到幻觉知识点，禁止生成题目！')
      return
    }

    // 3. 生成成功，更新Store
    if (res.code === 200) {
      questionStore.setGeneratedQuestion(res.data)
      ElMessage.success('题目生成成功')

      // 4. 调用幻觉校验接口
      const checkRes = await request('post', '/generate-question/check-illusion', {
        question_content: questionStore.generatedQuestion.content
      }, {
        headers: { 'Content-Type': 'application/json' }
      })

      if (checkRes.code === 200) {
        questionStore.setCheckResult(checkRes.data)
        activeTab.value = 'illusion-check' // 切换到校验标签页
      }
    }
  } catch (error) {
    console.error('生成题目失败：', error)
    ElMessage.error('题目生成失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

// ========== 其他函数（不变） ==========
const updateQuestion = () => {
  ElMessage.info('更新题目功能开发中...')
}

watch(activeTab, (tab) => {
  if (tab === 'history' && historyQuestions.value.length === 0 && !historyLoading.value) {
    loadHistory()
  }
})
</script>

<style scoped lang="less">
.question-generator-container {
  display: flex;
  width: 100%;
  background-color: #f5f7fa;
}

.left-panel, .right-panel {
  background-color: #fff;
  border-radius: 8px;
}

.el-textarea__inner {
  resize: none;
}

.illusion-warn {
  font-size: 13px;
  line-height: 1.5;
}
</style>