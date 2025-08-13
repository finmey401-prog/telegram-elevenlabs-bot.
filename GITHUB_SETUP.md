# Пошаговая инструкция выгрузки на GitHub

## Шаг 1: Создание репозитория на GitHub

1. Перейдите на [github.com](https://github.com) и войдите в аккаунт
2. Нажмите кнопку "New repository" (зеленая кнопка)
3. Заполните форму:
   - **Repository name**: `telegram-economic-bot` (или любое другое название)
   - **Description**: `Telegram bot для экономической симуляционной игры`
   - **Visibility**: Public или Private (на ваш выбор)
   - **НЕ отмечайте**: "Add a README file", "Add .gitignore", "Choose a license"
4. Нажмите "Create repository"

## Шаг 2: Подготовка проекта

Ваш проект уже готов к загрузке! Созданы все необходимые файлы:
- ✅ `.gitignore` - исключает ненужные файлы
- ✅ `README.md` - подробная документация
- ✅ `LICENSE` - лицензия MIT
- ✅ `DEPLOYMENT.md` - инструкции по развертыванию

## Шаг 3: Загрузка через Replit

### Вариант А: Через GitHub Integration в Replit
1. В Replit откройте панель инструментов слева
2. Найдите иконку GitHub или Version Control
3. Нажмите "Connect to GitHub"
4. Выберите ваш аккаунт GitHub
5. Выберите созданный репозиторий
6. Нажмите "Push to GitHub"

### Вариант Б: Через командную строку Replit Shell
1. Откройте Shell в Replit (вкладка Shell внизу)
2. Выполните команды по порядку:

```bash
# Добавить удаленный репозиторий (замените YOUR_USERNAME и REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/telegram-economic-bot.git

# Добавить все файлы
git add .

# Создать коммит
git commit -m "Initial commit: Telegram Economic Simulation Bot"

# Отправить на GitHub
git push -u origin main
```

**Важно**: Замените `YOUR_USERNAME` на ваше имя пользователя GitHub, а `REPO_NAME` на название репозитория.

## Шаг 4: Настройка секретов (для деплоя)

Если планируете автоматический деплой через GitHub Actions:

1. В репозитории на GitHub перейдите в **Settings**
2. В левом меню выберите **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте секреты:
   - `TELEGRAM_BOT_TOKEN` - токен вашего бота
   - `DATABASE_URL` - URL базы данных для продакшена

## Шаг 5: Проверка

После загрузки проверьте:
- ✅ Все файлы загружены
- ✅ README.md отображается корректно
- ✅ Структура проекта сохранена
- ✅ Секретные файлы исключены (не видно токенов, паролей)

## Возможные проблемы

### Проблема: "Repository already exists"
**Решение**: Используйте другое имя репозитория или удалите существующий

### Проблема: "Authentication failed" 
**Решение**: 
- Проверьте правильность имени пользователя
- Возможно нужен Personal Access Token вместо пароля

### Проблема: Не загружаются некоторые файлы
**Решение**: Проверьте `.gitignore` - возможно файлы исключены

## Следующие шаги

После загрузки на GitHub вы можете:

1. **Настроить Continuous Integration** - автоматические тесты
2. **Добавить GitHub Actions** - автоматический деплой
3. **Пригласить коллабораторов** - для совместной разработки
4. **Создать Issues** - для отслеживания задач
5. **Настроить Webhook** - для автоматического деплоя

## Полезные ссылки

- [GitHub Docs](https://docs.github.com)
- [Git Tutorial](https://git-scm.com/docs/gittutorial)
- [Replit GitHub Integration](https://docs.replit.com/tutorials/11-github)

---

**После успешной загрузки ваш проект будет доступен всему миру!** 🚀