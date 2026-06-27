# Brevo Integration Summary — VugriUkraine

## Що було зроблено

Ваш Django сайт VugriUkraine успішно переналаштований для використання **Brevo** (SendinBlue) замість стандартної SMTP верифікації для відправки листів.

### Список змін:

#### 1. **Залежності** (`requirements.txt`)
- ✅ Додано пакет `brevo==5.12.1`

#### 2. **Конфігурація** (`vugri/settings.py`)
- ✅ Додано змінні для Brevo:
  - `BREVO_API_KEY` - ваш API ключ
  - `BREVO_SENDER_EMAIL` - email відправника
  - `BREVO_SENDER_NAME` - назва відправника (за замовченням "VugriUkraine")

#### 3. **Новий модуль** (`seafood/brevo_email.py`)
- ✅ Створено універсальне рішення для відправки листів через Brevo:
  - `send_email_via_brevo()` - базова функція для будь-яких листів
  - `send_verification_email()` - верифікація реєстрації
  - `send_callback_request_notification_email()` - запит зворотного зв'язку

#### 4. **Форми** (`seafood/forms.py`)
- ✅ Створено новий файл з `CallbackRequestForm` для запитів зворотного зв'язку

#### 5. **Моделі** (`seafood/models.py`)
- ✅ Додано модель `CallbackRequest` для збереження запитів зворотного зв'язку

#### 6. **Представлення** (`seafood/views.py`)
- ✅ Оновлено `register()` - використовує Brevo для верифікації
- ✅ Оновлено `request_callback()` - сповіщення адміну через Brevo
- ✅ Оновлено відправку сповіщень про замовлення через Brevo

#### 7. **Документація**
- ✅ Створено `BREVO_SETUP.md` - повний посібник налаштування
- ✅ Оновлено `.env.example` - приклад змінних середовища
- ✅ Створено `scripts/test_brevo.py` - скрипт для тестування

## Що змінилося для користувачів

### Реєстрація
```
Було: Email через Gmail SMTP (часто блокується)
↓
Тепер: Email через Brevo API (надійніше, більше можливостей)
```

### Верифікація email
- 6-значний код приходить на email через Brevo
- Красивий HTML формат листа замість простого тексту
- Теги для категоризації в Brevo

### Запити зворотного зв'язку
- Адміністратор отримує сповіщення через Brevo
- Форматований HTML email з усіма деталями

### Сповіщення про замовлення
- Замовлення надсилаються адміністратору через Brevo
- Кожен адміністратор отримує власну копію

## Наступні кроки

### 1. Установка Brevo SDK
```bash
pip install -r requirements.txt
```

### 2. Реєстрація на Brevo
1. Перейдіть на https://www.brevo.com
2. Зареєструйтесь
3. Отримайте v3 API key

### 4. Налаштування .env
```bash
cp .env.example .env
```

Заповніть в `.env`:
```env
BREVO_API_KEY=your_v3_api_key_from_brevo
BREVO_SENDER_EMAIL=noreply@vugriukraine.com
BREVO_SENDER_NAME=VugriUkraine
ORDER_NOTIFICATION_EMAIL=admin@vugriukraine.com
ADMIN_EMAIL=admin@vugriukraine.com
```

### 5. Тестування
```bash
python scripts/test_brevo.py
```

### 6. Розгортання на Render.com
- Додайте змінні середовища в **Dashboard → Environment**
- Перезавантажте сервіс

## Структура проекту

```
vugri/
├── seafood/
│   ├── brevo_email.py          # ← NEW: Brevo email functions
│   ├── forms.py                # ← NEW: Callback request form
│   ├── models.py               # ← UPDATED: Added CallbackRequest
│   ├── views.py                # ← UPDATED: Using Brevo
│   └── ...
├── vugri/
│   ├── settings.py             # ← UPDATED: Brevo config
│   └── ...
├── scripts/
│   └── test_brevo.py           # ← NEW: Test script
├── BREVO_SETUP.md              # ← NEW: Setup guide
├── .env.example                # ← UPDATED: Environment example
└── requirements.txt            # ← UPDATED: Added brevo package
```

## Функції, що використовують Brevo

| Функція | Файл | Використовується в |
|---------|------|-------------------|
| `send_verification_email()` | brevo_email.py | `register()` view |
| `send_callback_request_notification_email()` | brevo_email.py | `request_callback()` view |
| `send_email_via_brevo()` | brevo_email.py | Order notifications |

## Технічні деталі

### Брево API
- **Версія SDK**: 5.12.1
- **Метод**: Transactional Emails API
- **Автентифікація**: v3 API Key
- **Формат**: JSON

### Теги для категоризації
- `verification` - верифікація email
- `registration` - реєстрація користувача
- `callback` - запит зворотного зв'язку
- `admin-notification` - сповіщення адміну
- `order` - замовлення

## Розв'язання проблем

### Перевірка конфігурації
```python
from django.conf import settings
print(settings.BREVO_API_KEY)
print(settings.BREVO_SENDER_EMAIL)
```

### Email не надходить
1. Перевірте папку Spam
2. Переконайтеся, що адреса відправника підтверджена в Brevo
3. Запустіть `python scripts/test_brevo.py`

### 401/403 помилки
- API ключ неправильно скопійований
- Отримайте новий ключ в Brevo Dashboard

## Посилання

- 📖 [BREVO_SETUP.md](BREVO_SETUP.md) - Повний посібник
- 🔗 [Brevo API Docs](https://developers.brevo.com/docs)
- 🐍 [Python SDK](https://github.com/getbrevo/brevo-python)

---

**Статус**: ✅ Готово до використання
**Дата**: 2026-06-27
**Версія**: 1.0
