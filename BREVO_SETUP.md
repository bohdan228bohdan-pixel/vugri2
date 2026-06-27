# Налаштування Brevo для VugriUkraine

Цей посібник описує, як налаштувати Brevo (SendinBlue) для відправки листів верифікації та сповіщень в систему VugriUkraine.

## Крок 1: Реєстрація та отримання API ключа в Brevo

1. Перейдіть на [brevo.com](https://www.brevo.com)
2. Натисніть на **"Реєстрація"** або **"Sign up"**
3. Заповніть форму реєстрації:
   - Email
   - Пароль
   - Підтвердіть поділ цілей (виберіть "E-commerce" або інше, яке вам підходить)
4. Підтвердіть свій email
5. Увійдіть в акаунт Brevo

## Крок 2: Отримання API ключа

1. Натисніть на свій профіль (верхній правий кут) → **"Параметри акаунта"** або **"Account Settings"**
2. Перейдіть в розділ **"API"** або **"API Keys"** → **"API Credentials"**
3. Скопіюйте **v3 API key** (це довгий рядок)
4. Збережіть цей ключ в безпечному місці

## Крок 3: Налаштування відправника

1. В Brevo перейдіть до **"Параметри"** → **"Адреси відправників"** або **"Senders"**
2. Додайте нову адресу відправника:
   - **Email**: Введіть email, з якого будуть відправляються листи (наприклад: noreply@vugriukraine.com або ваша основна email)
   - **Назва**: VugriUkraine (або інша назва вашого бізнесу)
3. Підтвердіть цю адресу через email

## Крок 4: Додавання змінних середовища

Додайте змінні в `.env` файл у кореневій папці проекту:

```env
# Brevo configuration
BREVO_API_KEY=ваш_v3_api_key_тут
BREVO_SENDER_EMAIL=noreply@vugriukraine.com
BREVO_SENDER_NAME=VugriUkraine
```

Примітка: Замініть `ваш_v3_api_key_тут` на справжній API ключ з Brevo, а `noreply@vugriukraine.com` на вашу адресу відправника.

## Крок 5: Встановлення залежностей

Запустіть команду для встановлення брево:

```bash
pip install -r requirements.txt
```

Вже доданий `brevo==5.12.1` в requirements.txt.

## Крок 6: Налаштування Django settings

Settings.py вже налаштовані для використання Brevo. Переконайтеся, що в `.env` є:

```env
DJANGO_DEFAULT_FROM_EMAIL=noreply@vugriukraine.com
ORDER_NOTIFICATION_EMAIL=admin@vugriukraine.com
ADMIN_EMAIL=admin@vugriukraine.com
```

## Крок 7: Тестування

### Тест 1: Верифікація реєстрації
1. Перейдіть на сайт: http://localhost:8000/register/
2. Заповніть форму реєстрації з тестовим email
3. Повинен прийти лист на цей email з кодом підтвердження з Brevo

### Тест 2: Запит зворотного зв'язку
1. Перейдіть на сторінку Contacts або заповніть форму запиту зворотного зв'язку
2. Перевірте, чи адміністратор отримав лист про запит
3. Email повинен прийти від Brevo

## Крок 8: Продакшн налаштування (для Render.com)

Якщо ви розгортаєте на Render.com:

1. Перейдіть в **Dashboard** → виберіть ваш сервіс
2. Перейдіть в **Environment**
3. Додайте змінні:
   - `BREVO_API_KEY` → ваш API ключ
   - `BREVO_SENDER_EMAIL` → email відправника
   - `BREVO_SENDER_NAME` → назва відправника
   - `ORDER_NOTIFICATION_EMAIL` → email адміністратора для замовлень
   - `ADMIN_EMAIL` → email адміністратора

4. Натисніть **Save** та перезавантажте сервіс

## Функції, що використовують Brevo

### 1. send_verification_email()
Відправляє код верифікації під час реєстрації користувача.

**Файл**: `seafood/brevo_email.py`
**Використовується в**: `seafood/views.py` → `register()`

### 2. send_callback_request_notification_email()
Відправляє сповіщення адміністратору про новий запит зворотного зв'язку.

**Файл**: `seafood/brevo_email.py`
**Використовується в**: `seafood/views.py` → `request_callback()`

### 3. send_email_via_brevo()
Універсальна функція для відправки будь-яких листів через Brevo API.

**Файл**: `seafood/brevo_email.py`
**Параметри**:
- `subject` - тема листа
- `recipient_email` - email одержувача
- `html_content` - HTML версія листа
- `text_content` - текстова версія листа
- `tags` - теги для категоризації

## Розв'язання проблем

### Проблема: "API key is not configured"
**Розв'язок**: 
- Перевірте, що `BREVO_API_KEY` встановлено в `.env`
- Перезавантажте сервер Django
- На Render.com: перезавантажте сервіс

### Проблема: Email не надходить
**Розв'язок**:
- Перевірте папку "Spam" або "Promotion"
- Переконайтеся, що адреса відправника підтверджена в Brevo
- Перевірте логи Django на помилки

### Проблема: "brevo_python package is not installed"
**Розв'язок**:
```bash
pip install brevo
pip install -r requirements.txt
```

### Проблема: 401 або 403 помилка від Brevo
**Розв'язок**:
- Перевірте, що API ключ правильно скопійований (без пробілів)
- API ключ може бути інвалідним - отримайте новий в Brevo

## Посилання

- [Brevo API документація](https://developers.brevo.com/docs/getting-started)
- [Python SDK для Brevo](https://github.com/getbrevo/brevo-python)

---

**Версія**: 1.0
**Остаточне оновлення**: 2026-06-27
