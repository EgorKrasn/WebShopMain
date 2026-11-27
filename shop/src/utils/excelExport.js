import * as XLSX from 'xlsx'

const XLSX_MIME =
	'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

/**
 * Определяем iOS / iPadOS (включая iPad в режиме "Запросить настольный веб-сайт")
 */
function isIOSDevice() {
	if (typeof navigator === 'undefined') return false
	const ua = navigator.userAgent || ''
	return (
		/iPad|iPhone|iPod/.test(ua) ||
		(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
	)
}

/**
 * Преобразует книгу SheetJS (workbook) в объект Blob
 */
export function workbookToBlob(workbook) {
	const wbout = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
	return new Blob([wbout], { type: XLSX_MIME })
}

/**
 * Кроссплатформенное сохранение книги Excel (.xlsx),
 * корректно работающее на iPhone (iOS Safari), Android и ПК.
 */
export async function saveWorkbookCrossPlatform(workbook, filename) {
	const blob = workbookToBlob(workbook)

	// 1. Для iPhone / iPad (iOS Safari блокирует программный <a download> для Blob)
	if (isIOSDevice()) {
		try {
			const file = new File([blob], filename, { type: XLSX_MIME })
			if (navigator.canShare && navigator.canShare({ files: [file] })) {
				await navigator.share({
					files: [file],
					title: filename,
				})
				return
			}
		} catch (err) {
			// Если пользователь сам закрыл меню "Поделиться" — просто выходим
			if (err && err.name === 'AbortError') return
			console.warn('navigator.share не сработал, пробуем fallback:', err)
		}

		// Fallback для старых версий iOS Safari: открываем Blob во вкладке (Safari предложит "Открыть в..." / "Сохранить в Файлы")
		const blobUrl = URL.createObjectURL(blob)
		window.open(blobUrl, '_blank')
		setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000)
		return
	}

	// 2. Для ПК (Windows/macOS/Linux) и Android: классическое скачивание через Blob URL
	const url = URL.createObjectURL(blob)
	const link = document.createElement('a')
	link.href = url
	link.download = filename
	link.style.display = 'none'
	document.body.appendChild(link)
	link.click()
	link.remove()
	setTimeout(() => URL.revokeObjectURL(url), 10_000)
}
