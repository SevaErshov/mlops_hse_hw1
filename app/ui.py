import csv
import io
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import streamlit as st

from app.database import read_results
from app.kafka_utils import producer
from app.preprocessing import preprocess


st.set_page_config(page_title="Антифрод", layout="wide")
st.title("Скоринг транзакций")
send_tab, results_tab = st.tabs(["Отправить транзакции", "Результаты"])

with send_tab:
    uploaded = st.file_uploader("CSV в формате test.csv", type="csv")
    limit = st.number_input("Сколько строк отправить", min_value=1, max_value=10000, value=500)
    st.caption("Без файла будут отправлены строки из встроенного примера test.csv.")
    if st.button("Отправить в Kafka"):
        output = None
        sent = 0
        try:
            text = uploaded.getvalue().decode("utf-8-sig") if uploaded else Path("data/demo.csv").read_text()
            rows = []
            for index, row in enumerate(csv.DictReader(io.StringIO(text))):
                if index >= limit:
                    break
                preprocess(row)
                row["transaction_id"] = str(row.get("transaction_id") or uuid4())
                rows.append(row)
            if not rows:
                raise ValueError("Файл не содержит транзакций")
            output = producer()
            for row in rows:
                output.send("transactions", row).get(timeout=30)
                sent += 1
            st.success(f"Отправлено: {sent}. Через несколько секунд откройте результаты.")
        except Exception as error:
            st.error(f"Отправлено {sent} записей. Ошибка: {error}")
        finally:
            if output:
                output.close()

with results_tab:
    st.subheader("Результаты из PostgreSQL")
    if st.button("Посмотреть результаты"):
        try:
            fraud, scores = read_results()
            st.write("Последние 10 транзакций с fraud_flag = 1")
            if fraud:
                st.dataframe(pd.DataFrame(fraud, columns=["transaction_id", "score", "fraud_flag", "created_at"]), hide_index=True)
            else:
                st.info("Транзакций с флагом фрода пока нет.")
            st.write(f"Распределение скоров последних {len(scores)} транзакций")
            if scores:
                counts, edges = np.histogram(scores, bins=np.linspace(0, 1, 11))
                labels = [f"{edges[i]:.1f}–{edges[i+1]:.1f}" for i in range(10)]
                st.bar_chart(pd.DataFrame({"Количество": counts}, index=labels), x_label="Score", y_label="Транзакции")
            else:
                st.info("База пустая. Сначала отправьте транзакции.")
        except Exception as error:
            st.error(f"Не удалось прочитать результаты: {error}")
