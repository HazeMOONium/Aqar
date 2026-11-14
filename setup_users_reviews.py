"""Creates the `users` and `reviews` tables (NOT included in the original dump.sql)
on the remote MySQL server. Idempotent - safe to run multiple times.
Run:  python setup_users_reviews.py
"""
from db import get_connection

DDL = [
    """CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        email VARCHAR(150) NOT NULL UNIQUE,
        password_hash CHAR(64) NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
    """CREATE TABLE IF NOT EXISTS reviews (
        review_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        project_name VARCHAR(300) NOT NULL,
        rating TINYINT NOT NULL,
        comment TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uq_user_project (user_id, project_name),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (project_name) REFERENCES DEVELOPMENT_PROJECT(Name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci""",
]


def main():
    cn = get_connection()
    cur = cn.cursor()
    for ddl in DDL:
        cur.execute(ddl)
    cn.commit()
    cur.execute("SHOW TABLES")
    print("Tables:", [r[0] for r in cur.fetchall()])
    cur.close()
    cn.close()


if __name__ == "__main__":
    main()
