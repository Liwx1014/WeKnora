import { get } from '@/utils/request'
import type { AxiosResponse } from 'axios'

// ChatDB记录接口
export interface ChatDBRecord {
  id: number
  conversation_id: string
  user_id: string
  session_id: string
  log_data: any
  created_at: string
}

// API响应接口
export interface ChatDBResponse {
  success: boolean
  data: ChatDBRecord
}

// 获取所有记录的响应接口
export interface ChatDBListResponse {
  success: boolean
  data: ChatDBRecord[]
  count: number
  total: number
  limit: number
  offset: number
}

/**
 * 获取所有ChatDB记录
 * @param limit 每页数量，默认50
 * @param offset 偏移量，默认0
 * @returns Promise<ChatDBListResponse>
 */
export const getAllChatRecords = (limit: number = 50, offset: number = 0) => {
  return get(`/api/v1/chatdb/records?limit=${limit}&offset=${offset}`)
}

/**
 * 根据ID获取ChatDB记录
 * @param id 记录ID
 * @returns Promise<ChatDBResponse>
 */
export const getChatRecordById = (id: number) => {
  return get(`/api/v1/chatdb/record/${id}`)
}