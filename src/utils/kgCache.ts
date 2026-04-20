/**
 * 知识图谱缓存模块
 * 功能：统一管理图谱数据的缓存、预处理、失效逻辑
 */
class KGCache {
  cache: any;
  expireTime: number;
  constructor() {
    // 缓存容器
    this.cache = {
      allNodes: [],
      allEdges: [],
      loaded: false,
      updateTime: null // 记录缓存更新时间，用于失效判断
    };
    // 缓存有效期（可选，比如1小时）
    this.expireTime = 3600 * 1000;
  }

  /**
   * 初始化缓存（优先读缓存，无则请求接口）
   * @param {Function} requestFn - 接口请求函数（传入以解耦）
   */
  async init(requestFn: Function) {
    // 1. 检查缓存是否有效（未加载/已过期则重新请求）
    if (this.cache.loaded && this.isCacheValid()) {
      return this.getCache();
    }

    // 2. 请求接口并预处理数据
    try {
      const res = await requestFn();
      const processedData = this.processData(res.data);
      
      // 3. 更新缓存
      this.cache.allNodes = processedData.nodes;
      this.cache.allEdges = processedData.edges;
      this.cache.loaded = true;
      this.cache.updateTime = Date.now();

      // 可选：持久化到sessionStorage（页面刷新不丢失）
      this.persistToStorage();

      return processedData;
    } catch (err) {
      console.error('图谱数据加载失败:', err);
      // 降级：读取本地存储的缓存
      const storageCache = this.getFromStorage();
      if (storageCache) {
        this.cache = {
          ...this.cache,
          ...storageCache,
          loaded: true
        };
        return {
          nodes: storageCache.allNodes,
          edges: storageCache.allEdges
        };
      }
      throw err;
    }
  }

  /**
   * 数据预处理（统一格式、兜底空值）
   * @param {Object} rawData - 接口原始数据
   */
  processData(rawData: any) {
    const nodes = rawData.nodes.map((node: any) => ({
      ...node,
      id: Number(node.id), // 确保ID为数字，避免匹配出错
      type: node.type || '未分类',
      level: node.level || '未设置'
    }));

    const edges = rawData.edges.map((edge: any) => ({
      ...edge,
      source: Number(edge.source),
      target: Number(edge.target)
    }));

    return { nodes, edges };
  }

  /**
   * 检查缓存是否有效
   */
  isCacheValid() {
    if (!this.cache.updateTime) return false;
    return Date.now() - this.cache.updateTime < this.expireTime;
  }

  /**
   * 获取缓存数据
   */
  getCache() {
    return {
      nodes: this.cache.allNodes,
      edges: this.cache.allEdges
    };
  }

  /**
   * 清空缓存
   */
  clearCache() {
    this.cache = {
      allNodes: [],
      allEdges: [],
      loaded: false,
      updateTime: null
    };
    sessionStorage.removeItem('kgCache');
  }

  /**
   * 持久化到sessionStorage
   */
  persistToStorage() {
    sessionStorage.setItem('kgCache', JSON.stringify({
      allNodes: this.cache.allNodes,
      allEdges: this.cache.allEdges,
      updateTime: this.cache.updateTime
    }));
  }

  /**
   * 从sessionStorage读取缓存
   */
  getFromStorage() {
    const cacheStr = sessionStorage.getItem('kgCache');
    if (!cacheStr) return null;
    return JSON.parse(cacheStr);
  }
}

// 导出单例（全局唯一缓存实例）
export default new KGCache();