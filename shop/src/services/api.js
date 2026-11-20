const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0'




async function request(endpoint, options = {}) {
	const token = localStorage.getItem('sandrintime_token')

	const headers = {
		'Content-Type': 'application/json',
		...(token ? { Authorization: `Bearer ${token}` } : {}),
		...options.headers,
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers,
	})

	const data = await response.json().catch(() => ({}))

	if (!response.ok) {
		if (response.status === 401 && token) {
			localStorage.removeItem('sandrintime_token')
		}

		if (response.status === 429) {
			throw new Error(
				'Слишком много запросов. Пожалуйста, подождите минуту и попробуйте снова.',
			)
		}

		let errorMessage = 'Ошибка при обращении к серверу'
		if (typeof data.detail === 'string') {
			errorMessage = data.detail
		} else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
			errorMessage = data.detail[0].msg.replace('Value error, ', '')
		}
		throw new Error(errorMessage)
	}

	return data
}

export const api = {
	getProducts() {
		return request('/products')
	},
	register(payload) {
		return request('/auth/register', {
			method: 'POST',
			body: JSON.stringify(payload),
		})
	},
	login(payload) {
		return request('/auth/login', {
			method: 'POST',
			body: JSON.stringify(payload),
		})
	},
	createOrder(payload) {
		return request('/orders', {
			method: 'POST',
			body: JSON.stringify(payload),
		})
	},
	switchRole(payload) {
		return request('/auth/role', {
			method: 'PATCH',
			body: JSON.stringify(payload),
		})
	},
	getOrders() {
		return request('/orders')
	},
	checkUnp(unp) {
		return request(`/unp/${unp}`)
	},
	getCategories() {
		return request('/categories')
	},
	// --- АДМИН-ПАНЕЛЬ ---
	adminGetWholesaleRequests() {
		return request('/admin/wholesale-requests')
	},
	adminReviewWholesale(userId, decision) {
		return request(`/admin/users/${userId}/wholesale-status`, {
			method: 'PATCH',
			body: JSON.stringify({ decision }),
		})
	},
	adminGetOrders(statusFilter = 'active', limit = 20, offset = 0) {
		const params = new URLSearchParams({
			status_filter: statusFilter,
			limit: String(limit),
			offset: String(offset),
		})
		return request(`/admin/orders?${params.toString()}`)
	},
	adminDeleteOrder(orderId) {
		return request(`/admin/orders/${orderId}`, {
			method: 'DELETE',
		})
	},

	adminUpdateOrder(orderId, payload) {
		return request(`/admin/orders/${orderId}`, {
			method: 'PATCH',
			body: JSON.stringify(payload),
		})
	},
	adminCreateProduct(payload) {
		return request('/admin/products', {
			method: 'POST',
			body: JSON.stringify(payload),
		})
	},
	adminUpdateProduct(productId, payload) {
		return request(`/admin/products/${productId}`, {
			method: 'PUT',
			body: JSON.stringify(payload),
		})
	},
	adminDeleteProduct(productId) {
		return request(`/admin/products/${productId}`, {
			method: 'DELETE',
		})
	},
	async adminUploadImage(file) {
		const formData = new FormData()
		formData.append('file', file)
		const token = localStorage.getItem('sandrintime_token')
		const response = await fetch(`${API_URL}/admin/upload-image`, {
			method: 'POST',
			headers: token ? { Authorization: `Bearer ${token}` } : {},
			body: formData,
		})
		const data = await response.json().catch(() => ({}))
		if (!response.ok) {
			throw new Error(data.detail || 'Ошибка загрузки изображения')
		}
		return data
	},
	adminCreateCategory(payload) {
		return request('/admin/categories', {
			method: 'POST',
			body: JSON.stringify(payload),
		})
	},
	adminUpdateCategory(categoryId, payload) {
		return request(`/admin/categories/${categoryId}`, {
			method: 'PUT',
			body: JSON.stringify(payload),
		})
	},
	adminDeleteCategory(categoryId) {
		return request(`/admin/categories/${categoryId}`, {
			method: 'DELETE',
		})
	},
}
