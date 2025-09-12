// src/utils/request.js
import axios from "axios";
import { generateRandomString } from "./index";

// 从localStorage获取设置
function getSettings() {
  const settingsStr = localStorage.getItem("WeKnora_settings");
  if (settingsStr) {
    try {
      return JSON.parse(settingsStr);
    } catch (e) {
      console.error("解析设置失败:", e);
    }
  }
  return {
    endpoint: import.meta.env.VITE_IS_DOCKER ? "" : "http://localhost:8080",
    apiKey: "",
    knowledgeBaseId: "",
  };
}

// API基础URL，优先使用设置中的endpoint
const settings = getSettings();
const BASE_URL = settings.endpoint;

// 测试数据
let testData: {
  tenant: {
    id: number;
    name: string;
    api_key: string;
  };
  knowledge_bases: Array<{
    id: string;
    name: string;
    description: string;
  }>;
} | null = null;

// 创建Axios实例
const instance = axios.create({
  baseURL: BASE_URL, // 使用配置的API基础URL
  timeout: 30000, // 请求超时时间
  headers: {
    "Content-Type": "application/json",
    "X-Request-ID": `${generateRandomString(12)}`,
  },
});

// 设置测试数据
export function setTestData(data: typeof testData) {
  testData = data;
  if (data?.tenant?.api_key) {
    // 只有在用户没有手动设置API Key时，才使用测试数据中的API Key
    const currentSettings = getSettings();
    if (!currentSettings.apiKey) {
      instance.defaults.headers["X-API-Key"] = data.tenant.api_key;
      console.log('已自动设置API Key:', data.tenant.api_key);
    }
  }
}

// 获取测试数据
export function getTestData() {
  return testData;
}

instance.interceptors.request.use(
  (config) => {
    // 每次请求前检查是否有更新的设置
    const currentSettings = getSettings();
    
    // 更新BaseURL (如果有变化)
    if (currentSettings.endpoint && config.baseURL !== currentSettings.endpoint) {
      config.baseURL = currentSettings.endpoint;
    }
    
    // 更新API Key (优先级：用户设置 > 测试数据 > 无)
    if (currentSettings.apiKey) {
      config.headers["X-API-Key"] = currentSettings.apiKey;
    } else if (testData?.tenant?.api_key) {
      // 使用测试数据中的API Key
      config.headers["X-API-Key"] = testData.tenant.api_key;
    }
    // 如果都没有，则不设置API Key，让后端返回401错误
    
    config.headers["X-Request-ID"] = `${generateRandomString(12)}`;
    return config;
  },
  (error) => {}
);

instance.interceptors.response.use(
  (response) => {
    // 根据业务状态码处理逻辑
    const { status, data } = response;
    if (status === 200 || status === 201) {
      return data;
    } else {
      return Promise.reject(data);
    }
  },
  (error: any) => {
    if (!error.response) {
      return Promise.reject({ message: "网络错误，请检查您的网络连接" });
    }
    const { status, data } = error.response;
    
    // 处理特定的HTTP状态码
    if (status === 401) {
      // 检查是否已加载测试数据
      if (!testData?.tenant?.api_key) {
        return Promise.reject({ 
          error: "认证失败", 
          message: "系统正在初始化API Key，请稍后重试。如果问题持续存在，请检查系统配置。" 
        });
      } else {
        return Promise.reject({ 
          error: "认证失败", 
          message: "API Key无效或已过期，请检查设置中的API Key配置" 
        });
      }
    } else if (status === 403) {
      return Promise.reject({ 
        error: "权限不足", 
        message: "当前API Key没有访问此资源的权限" 
      });
    } else if (status === 404) {
      return Promise.reject({ 
        error: "资源不存在", 
        message: "请求的资源不存在" 
      });
    } else if (status >= 500) {
      return Promise.reject({ 
        error: "服务器错误", 
        message: "服务器内部错误，请稍后重试" 
      });
    }
    
    return Promise.reject(data);
  }
);

export function get(url: string) {
  return instance.get(url);
}

export async function getDown(url: string) {
  let res = await instance.get(url, {
    responseType: "blob",
  });
  return res
}

export function postUpload(url: string, data = {}) {
  return instance.post(url, data, {
    headers: {
      "Content-Type": "multipart/form-data",
      "X-Request-ID": `${generateRandomString(12)}`,
    },
  });
}

export function postChat(url: string, data = {}) {
  return instance.post(url, data, {
    headers: {
      "Content-Type": "text/event-stream;charset=utf-8",
      "X-Request-ID": `${generateRandomString(12)}`,
    },
  });
}

export function post(url: string, data = {}) {
  return instance.post(url, data);
}

export function put(url: string, data = {}) {
  return instance.put(url, data);
}

export function del(url: string) {
  return instance.delete(url);
}
