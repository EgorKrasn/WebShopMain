const API_URL = 'http://127.0.0.1:8000/api'

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
		let errorMessage = 'Ошибка при обращении к серверу'
		if (typeof data.detail === 'string') {
			errorMessage = data.detail
		} else if (Array.isArray(data.detail) && data.detail?.msg) {
			errorMessage = data.detail.msg.replace('Value error, ', '')
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
}