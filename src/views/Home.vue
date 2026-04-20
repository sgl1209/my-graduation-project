<template>
  <div class="home-container page">
    <section class="hero surface">
      <h1 class="hero__title">智能出题系统</h1>
      <p class="hero__desc">
        输入参考文本，选择题型，一键生成题目，并通过知识图谱进行知识点校验，让出题更稳定、更可控。
      </p>

      <div class="hero__actions">
        <el-button type="primary" size="large" icon="EditPen" @click="$router.push('/generator')">
          开始出题
        </el-button>
        <el-button size="large" @click="$router.push('/kg')">
          查看知识图谱
        </el-button>
      </div>
    </section>

    <section class="surface" style="padding: 18px 18px;">
      <el-row :gutter="12">
        <el-col :xs="24" :sm="8">
          <div style="font-weight: 700; margin-bottom: 6px;">1. 输入文本</div>
          <div style="color: var(--app-muted); line-height: 1.7;">
            粘贴或输入参考材料，系统将基于内容组织题干与答案。
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div style="font-weight: 700; margin-bottom: 6px;">2. 选择题型</div>
          <div style="color: var(--app-muted); line-height: 1.7;">
            单选/多选/填空/编程题均可生成，支持后续更新题目。
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div style="font-weight: 700; margin-bottom: 6px;">3. 校验知识点</div>
          <div style="color: var(--app-muted); line-height: 1.7;">
            结合知识图谱查看覆盖率与幻觉提示，降低无依据知识点。
          </div>
        </el-col>
      </el-row>
    </section>
  </div>
</template>

<script setup lang="ts">

</script>
