<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const go = (path: string) => {
  if (route.path !== path) router.push(path)
}
</script>

<template>
  <div class="app-shell">
    <header class="app-topbar">
      <div class="app-topbar__inner">
        <div class="app-brand" @click="go('/home')" style="cursor: pointer;">
          <span class="app-brand__dot" aria-hidden="true"></span>
          <span class="app-brand__name">智能出题系统</span>
        </div>

        <div style="display:flex; gap: 6px; align-items:center;">
          <el-button :type="route.path === '/home' ? 'primary' : 'default'" plain @click="go('/home')">
            首页
          </el-button>
          <el-button :type="route.path === '/generator' ? 'primary' : 'default'" plain @click="go('/generator')">
            开始出题
          </el-button>
          <el-button :type="route.path === '/kg' ? 'primary' : 'default'" plain @click="go('/kg')">
            知识图谱
          </el-button>
        </div>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>

</style>
