<template>
  <div class="kg-page">
    <!-- 返回出题页面的按钮：独立布局，确保显示 -->
    <div class="kg-header">
      <el-button 
        type="primary" 
        icon="el-icon-arrow-left"
        @click="goToQuestionPage"
      >
        返回出题页面
      </el-button>
    </div>

    <!-- 图谱卡片：适配剩余高度，避免溢出 -->
    <el-card 
      class="kg-card"
    >
      <!-- 搜索工具栏：固定高度，避免挤压 -->
      <div class="kg-toolbar">
        <div style="display: flex; gap: 5px; align-items: center;">
          <span>节点名称：</span>
          <el-input
            v-model="keywordSearch"
            placeholder="输入节点名称"
            style="width: 200px;"
            @keyup.enter="handleSearch"
            clearable
          />
        </div>

        <div style="display: flex; gap: 5px; align-items: center;">
          <span>节点类型：</span>
          <el-select
            v-model="typeSearch"
            placeholder="选择类型"
            style="width: 200px;"
            clearable
          >
            <el-option label="具体知识点" value="具体知识点" />
            <el-option label="子知识点" value="子知识点" />
            <el-option label="属性" value="属性" />
          </el-select>
        </div>

        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
        <el-button @click="clearCache">清空缓存</el-button>
        <el-button @click="zoomIn">放大 +</el-button>
        <el-button @click="zoomOut">缩小 -</el-button>
        <el-button @click="resetZoom">重置视图</el-button>
      </div>

      <!-- 图谱容器：适配卡片剩余高度，确保滚动/缩放正常 -->
      <div 
        id="graph" 
        class="kg-graph"
      ></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import * as d3 from 'd3';
import request from '../api';
// @ts-ignore 
import kgCache from '../utils/kgCache';
import { throttle } from '../utils/tool';
import { useKnowledgeStore } from '../store/KnowledgeStore';
const knowledgeStore = useKnowledgeStore();
// ========== 1. 状态定义（替代 Options API 的 data） ==========
const keywordSearch = ref('');
const typeSearch = ref('');
const simulation = ref<any>(null);
const svg = ref<any>(null);
const g = ref<any>(null);
const zoom = ref<any>(null);
const fullNodes = ref<any[]>([]);
const fullEdges = ref<any[]>([]);

// ========== 2. 工具函数 ==========
// 统一ID为数字
const toNumber = (x: any) => Number(x);

// 从Proxy对象中提取真实ID
const getEdgeId = (val: any) => {
  if (typeof val === 'object' && val !== null && 'id' in val) {
    return toNumber(val.id);
  }
  return toNumber(val);
};

// ========== 3. 核心业务逻辑 ==========
// 跳转出题页面
const router = useRouter();
const goToQuestionPage = () => {
  router.push('/generator'); // 改用Vue Router跳转（替代window.location）
};

// 初始化D3容器
const initD3Container = () => {
  const graphContainer = document.getElementById('graph');
  if (!graphContainer) return;
  
  const width = graphContainer.clientWidth;
  const height = graphContainer.clientHeight;

  // 初始化SVG
  svg.value = d3.select('#graph')
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('preserveAspectRatio', 'xMidYMid meet');

  // 初始化分组容器
  g.value = svg.value.append('g');

  // 初始化缩放行为
  zoom.value = d3.zoom()
    .scaleExtent([0.1, 5])
    .on('zoom', (e: any) => {
      if (g.value) g.value.attr('transform', e.transform);
    });

  svg.value.call(zoom.value);
};

// 搜索逻辑（节流处理）
const handleSearch = throttle(() => {
  try {
    console.log('\n===== 触发搜索 =====');
    console.log('搜索条件：节点名称="%s"，节点类型="%s"', keywordSearch.value, typeSearch.value);
    renderGraph();
  } catch (err) {
    console.error('搜索报错：', err);
  }
}, 200);

// 渲染图谱核心逻辑
const renderGraph = () => {
  // 1. 筛选核心节点
  console.log('从Pinia读取知识点，自动搜索：', keywordSearch.value);
  let coreNodes = fullNodes.value.filter(node => {
    const matchName = keywordSearch.value
      ? node.label?.toLowerCase().includes(keywordSearch.value.trim().toLowerCase())
      : true;

    const matchType = typeSearch.value
      ? node.type === typeSearch.value
      : true;

    return matchName && matchType;
  });

  console.log('\n===== 核心节点筛选结果 =====');
  console.log('筛选出核心节点数量：', coreNodes.length);
  if (coreNodes.length > 0) {
    console.log('核心节点列表：', coreNodes);
    console.log('核心节点ID列表：', coreNodes.map(n => n.id));
  } else {
    console.log('无匹配的核心节点');
    drawGraph([], []);
    return;
  }

  // 2. 收集核心节点ID
  const coreIds = new Set(coreNodes.map(n => n.id));
  console.log('核心节点ID集合：', coreIds);
  
  // 3. 筛选子一级关联边
  const directEdges = fullEdges.value.filter(edge => {
    const sourceId = getEdgeId(edge.source);
    const targetId = getEdgeId(edge.target);
    return coreIds.has(sourceId) || coreIds.has(targetId);
  });

  console.log('\n===== 子一级关联边筛选结果 =====');
  console.log('筛选出子一级边数量：', directEdges.length);
  if (directEdges.length > 0) {
    console.log('子一级边列表：', directEdges);
  } else {
    console.log('无匹配的子一级关联边');
  }

  // 4. 收集子一级关联节点ID
  const directNodeIds = new Set();
  coreIds.forEach(id => directNodeIds.add(id));
  directEdges.forEach(e => {
    const sourceId = getEdgeId(e.source);
    const targetId = getEdgeId(e.target);
    if (!coreIds.has(sourceId)) directNodeIds.add(sourceId);
    if (!coreIds.has(targetId)) directNodeIds.add(targetId);
  });

  // 5. 筛选子一级关联节点
  const directNodes = fullNodes.value.filter(n => directNodeIds.has(n.id));

  // 6. 打印最终渲染数据
  console.log('\n===== 最终渲染（子一级）数据 =====');
  console.log('核心节点数：%d，子一级关联节点数：%d，总渲染节点数：%d', 
    coreNodes.length, 
    directNodes.length - coreNodes.length, 
    directNodes.length
  );
  console.log('渲染边数：', directEdges.length);
  console.log('子一级关联节点列表：', directNodes.filter(n => !coreIds.has(n.id)));

  // 7. 绘制图谱
  drawGraph(directNodes, directEdges);
};

// 绘制图谱（D3核心）
const drawGraph = (nodes: any[], edges: any[]) => {
  // 清空原有内容
  if (g.value) g.value.selectAll('*').remove();
  if (simulation.value) simulation.value.stop();

  // 无数据时显示提示
  if (nodes.length === 0) {
    console.log('\n===== 绘制结果 =====');
    console.log('无数据可绘制，显示空提示');
    const graphContainer = document.getElementById('graph');
    if (!graphContainer) return;
    
    const width = graphContainer.clientWidth;
    const height = graphContainer.clientHeight;
    
    g.value.append('text')
      .attr('x', width / 2 - 80)
      .attr('y', height / 2)
      .text('暂无匹配数据')
      .attr('font-size', 16)
      .attr('fill', '#999');
    return;
  }

  // 打印绘制信息
  console.log('\n===== 开始绘制子一级图谱 =====');
  console.log('绘制节点数：%d，绘制边数：%d', nodes.length, edges.length);

  // 获取容器尺寸
  const graphContainer = document.getElementById('graph');
  if (!graphContainer) return;
  const width = graphContainer.clientWidth;
  const height = graphContainer.clientHeight;

  // 初始化力导向模拟
  simulation.value = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id((d: any) => d.id).distance(150).strength(1))
    .force('charge', d3.forceManyBody().strength(-1000))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide(35))
    .alpha(1)
    .restart();

  // 绘制边
  const links = g.value.append('g')
    .selectAll('line')
    .data(edges)
    .enter()
    .append('line')
    .attr('stroke', '#888')
    .attr('stroke-width', 2)
    .attr('stroke-opacity', 0.9);

  // 收集核心节点ID（用于样式区分）
  const coreIds = new Set(fullNodes.value.filter(n => 
    (keywordSearch.value ? n.label?.toLowerCase().includes(keywordSearch.value.trim().toLowerCase()) : true) &&
    (typeSearch.value ? n.type === typeSearch.value : true)
  ).map(n => n.id));

  // 绘制节点
  const node = g.value.append('g')
    .selectAll('circle')
    .data(nodes)
    .enter()
    .append('circle')
    .attr('r', (d: any) => coreIds.has(d.id) ? 12 : 9)
    .attr('fill', (d: any) => {
      if (coreIds.has(d.id)) {
        switch(d.type) {
          case '具体知识点': return '#2f5496';
          case '子知识点': return '#67b747';
          case '属性': return '#e6a844';
          default: return '#4891c2';
        }
      } else {
        switch(d.type) {
          case '具体知识点': return '#5470c6';
          case '子知识点': return '#91cc75';
          case '属性': return '#fac858';
          default: return '#73c0de';
        }
      }
    })
    .attr('stroke', (d: any) => coreIds.has(d.id) ? '#fff' : 'none')
    .attr('stroke-width', (d: any) => coreIds.has(d.id) ? 2 : 0)
    .call(d3.drag()
      .on('start', (e: any, d: any) => {
        if (!e.active) simulation.value.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (e: any, d: any) => { d.fx = e.x; d.fy = e.y; })
      .on('end', (e: any, d: any) => {
        if (!e.active) simulation.value.alphaTarget(0);
        d.fx = null; d.fy = null;
      })
    );

  // 绘制文字标签
  const texts = g.value.append('g')
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text((d: any) => d.label)
    .attr('font-size', (d: any) => coreIds.has(d.id) ? 14 : 12)
    .attr('dx', 15)
    .attr('dy', 4)
    .attr('fill', (d: any) => coreIds.has(d.id) ? '#000' : '#333')
    .attr('pointer-events', 'none');

  // 实时更新位置
  simulation.value.on('tick', () => {
    links
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y);

    node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);
    texts.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);
  });
};

// 重置搜索
const resetSearch = () => {
  console.log('\n===== 重置搜索 =====');
  keywordSearch.value = '';
  typeSearch.value = '';
  drawGraph(fullNodes.value, fullEdges.value);
};

// 清空缓存
const clearCache = () => {
  console.log('\n===== 清空缓存并刷新 =====');
  kgCache.clearCache();
  location.reload();
};

// 缩放控制
const zoomIn = () => { 
  console.log('执行放大操作（1.3倍）');
  svg.value.transition().duration(300).call(zoom.value.scaleBy, 1.3); 
};
const zoomOut = () => { 
  console.log('执行缩小操作（0.7倍）');
  svg.value.transition().duration(300).call(zoom.value.scaleBy, 0.7); 
};
const resetZoom = () => {
  console.log('执行重置视图操作');
  drawGraph(fullNodes.value, fullEdges.value);
  svg.value.transition().duration(500).call(
    zoom.value.transform,
    d3.zoomIdentity
  );
};

// ========== 4. 生命周期钩子 ==========
// 页面挂载时初始化

onMounted(async () => {
  try {
    // 1. 加载图谱数据
    const { nodes, edges } = await kgCache.init(() => request('get', '/kg/all'));

    // 统一ID为数字
    fullNodes.value = nodes.map((n: any) => ({ ...n, id: toNumber(n.id) }));
    fullEdges.value = edges.map((e: any) => ({
      ...e,
      source: toNumber(e.source),
      target: toNumber(e.target)
    }));

    console.log('全量边示例：', fullEdges.value.slice(0, 5));

    // 2. 初始化D3容器
    initD3Container();

    // 3. 读取Pinia中的知识点并自动搜索
    
    if (knowledgeStore.knowledgeText) {
      keywordSearch.value = knowledgeStore.knowledgeText;
      
      // 重点：不直接调用 handleSearch，改用 nextTick 或直接 renderGraph
      setTimeout(() => {
        renderGraph();
      }, 0);
    } else {
      renderGraph(); // 无知识点则渲染全量数据
    }
  } catch (err) {
    console.error('mounted 执行报错：', err);
  }
});

// 页面卸载时停止模拟
onUnmounted(() => {
  if (simulation.value) simulation.value.stop();
});
</script>

<style scoped>
/* 全局样式优化 */
* {
  box-sizing: border-box;
}

.kg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kg-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
  flex-wrap: wrap;
  padding: 0 4px;
}

.kg-graph {
  width: 100%;
  height: calc(100% - 54px);
  background: rgba(15, 23, 42, 0.03);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

/* 按钮样式优化 */
.el-button {
  margin: 0 !important;
}

/* 节点交互样式 */
circle { 
  cursor: move; 
  transition: fill 0.2s, stroke 0.2s; 
}
circle:hover { 
  fill: #ff7a45; 
  stroke: #fff !important;
  stroke-width: 2px !important;
}

/* 文字样式优化 */
text { 
  white-space: nowrap; 
  font-family: "Microsoft YaHei", sans-serif; 
  user-select: none;
}

/* 卡片内边距调整 */
.el-card__body {
  padding: 10px !important;
}
</style>