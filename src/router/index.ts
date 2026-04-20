import {createRouter, createWebHashHistory} from "vue-router"
import Home from "@/views/Home.vue"

import QuestionGenerator from "../views/QuestionGenerator.vue"
import KnowledgeGraph from "../views/KnowledgeGraph.vue"

const routes = [
    {
        path: '/',
        redirect: '/home'
    },
    {
        name: 'home',
        path: '/home',
        component: Home
    },
    {
        name: 'generator',
        path: '/generator',
        component: QuestionGenerator
    },
    {
        name: 'kg',
        path: '/kg',
        component: KnowledgeGraph
    }
]

const router = createRouter({
    // App 打包后常由 file:// 打开，hash 模式可避免 history 模式导致的白屏
    history: createWebHashHistory(),
    routes
})

export default router