export interface FuncItem {
  icon: string
  label: string
  desc: string
  path: string
  adminOnly?: boolean
  external?: boolean
}

export interface FuncGroup {
  group: string
  items: FuncItem[]
}

export const APP_FUNCTIONS: FuncGroup[] = [
  {
    group: '主要作業',
    items: [
      { icon: '🏠', label: '首頁管理', desc: '可設定的作業連結入口頁', path: '/' },
      { icon: '📁', label: '投資紀錄', desc: '建立、查閱、刪除投資組合', path: '/portfolios' },
      { icon: '📈', label: '持股明細', desc: '進入投資組合後查看持股、損益', path: '/portfolios' },
      { icon: '📋', label: '功能總覽', desc: '系統所有作業功能的快速入口', path: '/all-functions' },
    ],
  },
  {
    group: '系統管理',
    items: [
      { icon: '👥', label: '帳號管理', desc: '新增 / 編輯 / 停用系統帳號', path: '/admin/users', adminOnly: true },
      { icon: '🗂️', label: '選單管理', desc: '設定 Portal 首頁顯示的作業連結', path: '/admin/menu', adminOnly: true },
    ],
  },
  {
    group: 'API 文件',
    items: [
      { icon: '📄', label: 'Swagger UI', desc: '互動式 API 文件，可直接測試所有端點', path: 'http://localhost:8001/docs', external: true },
      { icon: '📋', label: 'ReDoc', desc: '閱讀友善的 API 規格文件', path: 'http://localhost:8001/redoc', external: true },
    ],
  },
]
