import { ref } from 'vue'

/**
 * Защищает модальное окно от случайного закрытия при выделении текста мышью
 * (когда mousedown был внутри окна, а mouseup — на фоне).
 */
export function useBackdropClose(onClose) {
	const isMouseDownOnBackdrop = ref(false)

	const onBackdropMouseDown = event => {
		isMouseDownOnBackdrop.value = event.target === event.currentTarget
	}

	const onBackdropMouseUp = event => {
		if (isMouseDownOnBackdrop.value && event.target === event.currentTarget) {
			onClose()
		}
		isMouseDownOnBackdrop.value = false
	}

	return {
		onBackdropMouseDown,
		onBackdropMouseUp,
	}
}
