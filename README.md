Нужны Docker и Docker Compose. Docker должен быть запущен.

В папке проекта:

```bash
docker compose up -d --build --wait --wait-timeout 180
```

Открыть [localhost:8501](http://localhost:8501). Загрузить test.csv или оставить встроенный пример, нажать «Отправить в Kafka». Через 10–30 секунд открыть «Результаты» и нажать «Посмотреть результаты».

Проверка:

```bash
docker compose exec -T scorer python -m scripts.smoke_test
```

Остановка:

```bash
docker compose down
```
