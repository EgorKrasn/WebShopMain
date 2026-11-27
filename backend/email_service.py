import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str = "",
    attachment_bytes: Optional[bytes] = None,
    attachment_filename: Optional[str] = None,
) -> bool:
    """
    Отправляет Email через SMTP (SSL или STARTTLS) из переменных .env.
    Если SMTP_USER не настроен, работает в Dev-режиме: выводит письмо в консоль сервера.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.by").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "СандринТайм").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user or "noreply@sandrintime.by").strip()

    if not to_email or "@" not in to_email:
        return False

    # Dev-режим для локальной разработки без настроенного SMTP
    if not smtp_user or not smtp_password:
        print("\n" + "=" * 60)
        print(f"[DEV EMAIL] Кому: {to_email}")
        print(f"[DEV EMAIL] Тема: {subject}")
        if attachment_filename:
            print(f"[DEV EMAIL] Вложение: {attachment_filename} ({len(attachment_bytes or b'')} байт)")
        print("-" * 60)
        print(text_body or html_body)
        print("=" * 60 + "\n")
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{smtp_from_name} <{smtp_from_email}>"
    msg["To"] = to_email

    fallback_text = text_body or "Для просмотра письма включите отображение HTML."
    msg.set_content(fallback_text)
    msg.add_alternative(html_body, subtype="html")

    if attachment_bytes and attachment_filename:
        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=attachment_filename,
        )

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] Не удалось отправить письмо на {to_email}: {exc}")
        raise


def send_password_reset_code_email(to_email: str, full_name: str, code: str) -> bool:
    subject = f"Код восстановления пароля: {code} — СандринТайм"
    text_body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Ваш одноразовый код для сброса пароля в интернет-магазине «СандринТайм»: {code}\n"
        f"Код действителен в течение 15 минут.\n\n"
        f"Если вы не запрашивали смену пароля, просто проигнорируйте это письмо."
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px; color: #0f172a;">
      <h2 style="margin: 0 0 12px; color: #0f172a;">Восстановление пароля</h2>
      <p style="margin: 0 0 16px; font-size: 14px; color: #334155;">
        Здравствуйте, <strong>{full_name}</strong>! Вы запросили сброс пароля для входа в личный кабинет «СандринТайм».
      </p>
      <div style="background-color: #f1f5f9; border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 16px;">
        <span style="display: block; font-size: 12px; color: #64748b; margin-bottom: 4px;">Одноразовый код подтверждения:</span>
        <strong style="font-size: 30px; letter-spacing: 6px; color: #0f172a;">{code}</strong>
      </div>
      <p style="margin: 0; font-size: 12.5px; color: #64748b;">
        Код действителен 15 минут. Если вы не запрашивали восстановление доступа, просто проигнорируйте это письмо.
      </p>
    </div>
    """
    return send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)


def send_order_notification_email(
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
    client_email: Optional[str] = None,
):
    items_rows_html = "".join(
        f"""
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{i['sku']}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{i['name']}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: center;">{i['quantity']} шт.</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">{i['unit_price']:.2f} BYN</td>
        </tr>
        """
        for i in items
    )

    items_lines_text = "\n".join(
        f"- [{i['sku']}] {i['name']} — {i['quantity']} шт. x {i['unit_price']:.2f} BYN"
        for i in items
    )

    role_label = f"Опт ({company_name}, УНП {unp})" if role == "wholesale" else "Розница"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 620px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px; color: #0f172a;">
      <h2 style="margin: 0 0 8px;">Заявка №{order_number} оформлена</h2>
      <p style="margin: 0 0 16px; font-size: 13px; color: #64748b;">Дата оформления: {created_at_str} • Тип: {role_label}</p>

      <div style="background-color: #f8fafc; padding: 14px; border-radius: 12px; font-size: 13.5px; margin-bottom: 16px;">
        <div><strong>Получатель:</strong> {recipient_name} ({recipient_phone})</div>
        <div style="margin-top: 4px;"><strong>Доставка:</strong> {delivery_text}</div>
        {f'<div style="margin-top: 4px;"><strong>Комментарий:</strong> {comment}</div>' if comment else ''}
      </div>

      <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 16px;">
        <thead>
          <tr style="background-color: #f1f5f9;">
            <th style="padding: 8px; text-align: left;">Артикул</th>
            <th style="padding: 8px; text-align: left;">Товар</th>
            <th style="padding: 8px; text-align: center;">Кол-во</th>
            <th style="padding: 8px; text-align: right;">Цена</th>
          </tr>
        </thead>
        <tbody>
          {items_rows_html}
        </tbody>
      </table>

      <div style="text-align: right; font-size: 16px; font-weight: bold;">
        Итого по товарам: {total_byn:.2f} BYN
      </div>
    </div>
    """

    text_body = (
        f"Заявка №{order_number} от {created_at_str} ({role_label})\n"
        f"Получатель: {recipient_name}, тел.: {recipient_phone}\n"
        f"Доставка: {delivery_text}\n"
        f"Состав заказа:\n{items_lines_text}\n"
        f"Итого: {total_byn:.2f} BYN"
    )

    # 1. Письмо клиенту (если авторизован и указан email)
    if client_email:
        try:
            send_email(
                to_email=client_email,
                subject=f"Ваша заявка №{order_number} принята — СандринТайм",
                html_body=html_body,
                text_body=text_body,
            )
        except Exception:
            pass

    # 2. Уведомление менеджеру/администратору магазина
    manager_email = os.getenv("ORDER_NOTIFY_EMAIL") or os.getenv("ADMIN_EMAIL", "")
    if manager_email and manager_email != client_email:
        try:
            send_email(
                to_email=manager_email.strip(),
                subject=f"Новый заказ №{order_number} ({role_label}) на {total_byn:.2f} BYN",
                html_body=html_body,
                text_body=text_body,
            )
        except Exception:
            pass
