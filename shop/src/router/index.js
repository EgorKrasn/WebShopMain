import { createRouter, createWebHistory } from 'vue-router'

const EmptyRouteView = { render: () => null }

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{
			path: '/',
			name: 'home',
			component: EmptyRouteView,
		},
		{
			path: '/product/:sku',
			name: 'product',
			component: EmptyRouteView,
		},
		{
			path: '/admin',
			name: 'admin',
			component: EmptyRouteView,
			meta: { requiresAuth: true },
		},
		{
			path: '/:pathMatch(.*)*',
			redirect: '/',
		},
	],
})

router.beforeEach(to => {
	if (to.meta.requiresAuth) {
		const token = localStorage.getItem('sandrintime_token')
		if (!token) {
			return { name: 'home' }
		}
	}
	return true
})

export default router
