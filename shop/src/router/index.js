import { createRouter, createWebHistory } from 'vue-router'

const EmptyRouteView = { render: () => null }

const ALLOWED_ADMIN_SECTIONS = [
	'wholesale',
	'orders',
	'archive',
	'products',
	'categories',
	'backup',
]

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{
			path: '/',
			name: 'home',
			component: EmptyRouteView,
		},
		{
			path: '/catalog',
			name: 'catalog',
			component: EmptyRouteView,
		},
		{
			path: '/product/:sku',
			name: 'product',
			component: EmptyRouteView,
		},
		{
			path: '/admin/:section?',
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

	if (to.name === 'admin' && to.params.section) {
		if (!ALLOWED_ADMIN_SECTIONS.includes(String(to.params.section))) {
			return { name: 'admin' }
		}
	}

	return true
})

export default router
