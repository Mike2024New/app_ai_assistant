# App AI Assistant

**AI ассистент, оффлайн "умная колонка", можно говорить с ней голосом.**

> Если вы пользователь то скачайте [релиз](https://github.com/Mike2024New/app_ai_assistant/releases), всё поставится
> автоматически.

---

## О проекте

app_ai_assistant — готовое приложение на базе экосистемы srv-сервисов.

### Что делает

- Слушает микрофон (через [srv_stt_vosk](https://github.com/Mike2024New/srv_stt_vosk))
- Понимает смысл через LLM (через [srv_llm](https://github.com/Mike2024New/srv_llm))
- Отвечает голосом (через [srv_tts_silero](https://github.com/Mike2024New/srv_tts_silero))

### Как работает

- Всё локально, без интернета, приватно
- Стриминг на всех этапах, ответ начинает звучать с минимальной задержкой (зависит от модели и железа)
- Прерывание на лету — можно перебить ассистента новой фразой

### Для кого

- Тех, кому нужен приватный ассистент — разговоры останутся вашей тайной
- Тех, кто хочет максимально простую установку (установка и сборка одной командой `python start.py`)

---

## Быстрый старт (для разработчиков)

### 1. Клонирование

```bash
git clone git@github.com:Mike2024New/app_ai_assistant.git app_ai_assistant
cd app_ai_assistant
```

### 2. Создать виртуальное окружение

> Важно! Папка с виртуальным окружением должна называться `.venv`

```bash
# Windows
python -m venv .venv && .venv\Scripts\activate

# Linux
python3 -m venv .venv && source .venv/bin/activate
```

### 3. Установить зависимости

`python start.py` # автоматически подхватятся все зависимости с которыми работает пакет. А также будет выполнена сборка
exe/bin.

---

## Связанные репозитории

- [srv_llm](https://github.com/Mike2024New/srv_llm) - мозг приложения.
- [srv_tts_silero](https://github.com/Mike2024New/srv_tts_silero) - голос приложения.
- [srv_stt_vosk](https://github.com/Mike2024New/srv_stt_vosk) - уши приложения.
- [infrastructure2](https://github.com/Mike2024New/infrastructure2) — набор утилит (сервер, логи, сборка)

---

## Лицензии

- Этот проект распространяется под лицензией MIT. Подробнее в файле [LICENSE](LICENSE).

---

## Примечания

- Проект использует утилиты из репозитория [infrastructure2](https://github.com/Mike2024New/infrastructure2).
- Доступен [релиз](https://github.com/Mike2024New/app_ai_assistant/releases).

> Если ни фига не понятно, то отправьте этот текст в ваш любимый ИИ, ставлю 5 шерифов 🤠🤠🤠🤠🤠 из 5, что он разберется и
> скажет что делать.

> Не силен в грамматике, мог забыть где-то поставить запятые, поэтому ставлю их здесь (,,,,,,,,,,,,,,,,,,,,,,,), с
> запасом.