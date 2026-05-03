import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PortalView from '@/views/PortalView.vue'
import HomeView from '@/views/HomeView.vue'
import PortfolioDetailView from '@/views/PortfolioDetailView.vue'
import LoginView from '@/views/LoginView.vue'
import UsersView from '@/views/admin/UsersView.vue'
import MenuItemsView from '@/views/admin/MenuItemsView.vue'
import AllFunctionsView from '@/views/AllFunctionsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/', name: 'portal', component: PortalView },
    { path: '/all-functions', name: 'all-functions', component: AllFunctionsView },
    { path: '/portfolios', name: 'home', component: HomeView },
    { path: '/portfolios/:id', name: 'portfolio-detail', component: PortfolioDetailView },
    { path: '/admin/users', name: 'admin-users', component: UsersView, meta: { adminOnly: true } },
    { path: '/admin/menu', name: 'admin-menu', component: MenuItemsView, meta: { adminOnly: true } },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) return { name: 'login' }
  if (to.name === 'login' && auth.isAuthenticated) return { name: 'portal' }
  if (to.meta.adminOnly && !auth.isAdmin) return { name: 'portal' }
})

export default router
