# 🚀 Brevo - Швидкий Старт

## 30 секунд на налаштування

### Крок 1: Встановлення пакетів
```bash
pip install -r requirements.txt
```

### Крок 2: Отримання API ключа з Brevo
1. Посіт: https://www.brevo.com
2. Реєстрація → Email підтвердження
3. Параметри → API → v3 API Key (скопіюйте)

### Крок 3: Налаштування .env
```bash
cp .env.example .env
```

Відредагуйте `.env` (додайте свої значення):
```env
BREVO_API_KEY=хай_v3_api_key_від_brevo
BREVO_SENDER_EMAIL=noreply@vugriukraine.com
BREVO_SENDER_NAME=VugriUkraine
ORDER_NOTIFICATION_EMAIL=ваш_email@gmail.com
ADMIN_EMAIL=ваш_email@gmail.com
```

### Крок 4: Тестування
```bash
python scripts/test_brevo.py
```

Введіть ваш email → отримайте тестовий лист

## ✅ Це все!

Тепер:
- ✅ Реєстрація відправляє коди через Brevo
- ✅ Запити зворотного зв'язку йдуть адміну
- ✅ Замовлення сповіщуються через Brevo

## 📚 Докладніше

- Див. [BREVO_SETUP.md](BREVO_SETUP.md) для детального посібника
- Див. [BREVO_INTEGRATION_SUMMARY.md](BREVO_INTEGRATION_SUMMARY.md) для техдеталей

## 🐛 Проблеми?

1. **API ключ не працює?**
   - Переконайтесь, що скопійований без пробілів
   - Отримайте новий ключ в Brevo Dashboard

2. **Email не приходить?**
   - Запустіть: `python scripts/test_brevo.py`
   - Перевірте папку Spam

3. **"brevo_python package not installed"?**
   - Запустіть: `pip install brevo`

---

**Потрібна допомога?** Перевірте [BREVO_SETUP.md](BREVO_SETUP.md) → "Розв'язання проблем"
