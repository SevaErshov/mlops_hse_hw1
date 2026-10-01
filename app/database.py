import os

import psycopg2


def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://fraud:fraud@postgres:5432/fraud"), connect_timeout=10)


def save_score(connection, row):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO transaction_scores (transaction_id, score, fraud_flag)
                VALUES (%s, %s, %s)
                ON CONFLICT (transaction_id) DO NOTHING
            """, (row["transaction_id"], row["score"], row["fraud_flag"]))


def read_results():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT transaction_id, score, fraud_flag, created_at
                FROM transaction_scores WHERE fraud_flag = 1
                ORDER BY id DESC LIMIT 10
            """)
            fraud = cursor.fetchall()
            cursor.execute("SELECT score FROM transaction_scores ORDER BY id DESC LIMIT 100")
            scores = [row[0] for row in cursor.fetchall()]
        return fraud, scores
    finally:
        connection.close()
