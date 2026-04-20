import {defineStore} from 'pinia'
import {ref} from 'vue'
export const useKnowledgeStore = defineStore('knowledge', () => {
    const knowledgeText = ref('')
    const setKnowledgeText = (text: string) => {
        knowledgeText.value = text.trim()
    }
    return {
        knowledgeText,
        setKnowledgeText
    }
})