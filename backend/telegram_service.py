import html
import http.client
import json
import os
from typing import Optional


def _esc(value: Optional[str]) -> str:
    """Экранирует спецсимволы для безопасного HTML-форматирования в Telegram."""
    if value is None:
        return ""
    return html.escape(str(value), quote=False)


def send_telegram_message(text_html: str) -> tuple[bool, str]:
    """
    Отправляет HTML-сообщение в Telegram через Bot API (sendMessage).
    Использует http.client.HTTPSConnection напрямую, минуя парсер URL и прокси.
    """
    bot_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip().strip('"').strip("'")
    if bot_token.lower().startswith("bot") and ":" in bot_token:
        bot_token = bot_token[3:]

    raw_chat_ids = (os.getenv("TELEGRAM_CHAT_ID") or "").strip().strip('"').strip("'")

    if not bot_token or not raw_chat_ids:
        print("\n" + "=" * 60)
        print("[TELEGRAM DEV-MODE] Сообщение (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID не заданы):")
        print(text_html)
        print("=" * 60 + "\n")
        return True, "Dev-режим: сообщение выведено в консоль сервера"

    chat_ids = [cid.strip() for cid in raw_chat_ids.split(",") if cid.strip()]
    endpoint_path = f"/bot{bot_token}/sendMessage"

    errors = []
    for chat_id in chat_ids:
        payload = json.dumps(
            {
                "chat_id": chat_id,
                "text": text_html,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            ensure_ascii=False,
        ).encode("utf-8")

        conn = None
        try:
            conn = http.client.HTTPSConnection("api.telegram.org", timeout=10)
            conn.request(
                "POST",
                endpoint_path,
                body=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            resp = conn.getresponse()
            raw_body = resp.read().decode("utf-8", errors="ignore")
            body = json.loads(raw_body) if raw_body else {}

            if resp.status != 200 or not body.get("ok"):
                desc = body.get("description") or f"HTTP {resp.status} {raw_body}"
                errors.append(f"chat {chat_id}: {desc}")
        except Exception as e:
            errors.append(f"chat {chat_id}: {str(e)}")
        finally:
            if conn:
                conn.close()

    if errors:
        err_msg = "; ".join(errors)
        print(f"[TELEGRAM ERROR] {err_msg}")
        return False, err_msg

    return True, "Уведомление успешно отправлено в Telegram"




def send_new_order_telegram(
    *,
    order_number: str,
    created_at_str: str,
    role: str,
    recipient_name: str,
    recipient_phone: str,
    delivery_text: str,
    total_byn: float,
    items: list[dict],
    company_name: Optional[str] = None,
    unp: Optional[str] = None,
    comment: Optional[str] = None,
) -> None:
    """Формирует и отправляет менеджеру карточку нового заказа в Telegram."""
    is_wholesale = role == "wholesale"
    client_badge = "🏢 <b>ОПТ (Юрлицо / ИП)</b>" if is_wholesale else "🛍 <b>Розница (Физлицо)</b>"

    lines = [
        f"🆕 <b>Новый заказ №{_esc(order_number)}</b>",
        f"🕒 {_esc(created_at_str)}",
        f"Тип клиента: {client_badge}",
        "",
    ]

    if is_wholesale and (company_name or unp):
        lines.append(f"🏛 Организация: <b>{_esc(company_name or '—')}</b>")
        lines.append(f"🔢 УНП: <code>{_esc(unp or '—')}</code>")

    lines.extend(
        [
            f"👤 Получатель: <b>{_esc(recipient_name)}</b>",
            f"📞 Телефон: <code>{_esc(recipient_phone)}</code>",
            f"🚚 Доставка: {_esc(delivery_text)}",
        ]
    )

    if comment:
        lines.append(f"💬 Комментарий: <i>{_esc(comment)}</i>")

    lines.append("")
    lines.append("📦 <b>Состав заказа:</b>")

    for idx, item in enumerate(items, start=1):
        sku = _esc(item.get("sku") or "")
        name = _esc(item.get("name") or "")
        qty = int(item.get("quantity") or 0)
        price = float(item.get("unit_price") or 0)
        subtotal = qty * price
        lines.append(
            f"{idx}. [{sku}] {name} — <b>{qty} шт.</b> × {price:.2f} = {subtotal:.2f} BYN"
        )

    lines.append("")
    lines.append(f"💰 <b>ИТОГО: {total_byn:.2f} BYN</b>")

    send_telegram_message("\n".join(lines))


def send_wholesale_request_telegram(
    *,
    company_name: str,
    unp: str,
    full_name: str,
    email: str,
    phone: str,
    legal_address: Optional[str] = None,
    source: str = "Регистрация",
) -> None:
    """Уведомляет менеджера о новой заявке юрлица на оптовый доступ по УНП."""
    lines = [
        "🏢 <b>Новая заявка на оптовый доступ (УНП)</b>",
        f"📌 Источник: {_esc(source)}",
        "",
        f"🏛 Организация: <b>{_esc(company_name)}</b>",
        f"🔢 УНП: <code>{_esc(unp)}</code>",
        f"👤 Контактное лицо: {_esc(full_name)}",
        f"📞 Телефон: <code>{_esc(phone)}</code>",
        f"✉️ Email: {_esc(email)}",
    ]

    if legal_address:
        lines.append(f"📍 Юр. адрес: {_esc(legal_address)}")

    lines.append("")
    lines.append("👉 Проверьте реквизиты и подтвердите статус в админ-панели («Заявки юрлиц»).")

    send_telegram_message("\n".join(lines))
