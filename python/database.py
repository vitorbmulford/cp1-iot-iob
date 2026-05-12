import re
import sqlite3
from contextlib import closing

from config import DB_PATH, ALUNOS_INICIAIS


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    uid TEXT NOT NULL UNIQUE,
    exercicio TEXT NOT NULL,
    repeticoes INTEGER NOT NULL CHECK (repeticoes > 0),
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS acessos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,
    uid TEXT NOT NULL,
    acessado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_acessos_aluno_data
ON acessos (aluno_id, acessado_em);
"""


def normalize_uid(uid):
    partes = re.findall(r'[0-9A-Fa-f]{2}', uid or '')
    if not partes:
        return None
    return ':'.join(parte.upper() for parte in partes)


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DB_PATH):
    with closing(connect(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def upsert_student(nome, uid, exercicio, repeticoes, ativo=1, db_path=DB_PATH):
    uid_normalizado = normalize_uid(uid)
    if not uid_normalizado:
        raise ValueError("UID invalido")

    with closing(connect(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO alunos (nome, uid, exercicio, repeticoes, ativo)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                nome = excluded.nome,
                exercicio = excluded.exercicio,
                repeticoes = excluded.repeticoes,
                ativo = excluded.ativo,
                atualizado_em = datetime('now', 'localtime')
            """,
            (nome, uid_normalizado, exercicio, int(repeticoes), int(ativo)),
        )
        conn.commit()


def seed_default_students(db_path=DB_PATH):
    init_db(db_path)
    for aluno in ALUNOS_INICIAIS:
        upsert_student(
            aluno["nome"],
            aluno["uid"],
            aluno["exercicio"],
            aluno["repeticoes"],
            aluno.get("ativo", 1),
            db_path,
        )


def get_student_by_uid(uid, db_path=DB_PATH):
    uid_normalizado = normalize_uid(uid)
    if not uid_normalizado:
        return None

    with closing(connect(db_path)) as conn:
        row = conn.execute(
            """
            SELECT id, nome, uid, exercicio, repeticoes
            FROM alunos
            WHERE uid = ? AND ativo = 1
            """,
            (uid_normalizado,),
        ).fetchone()

    return dict(row) if row else None


def record_access(aluno_id, uid, db_path=DB_PATH):
    uid_normalizado = normalize_uid(uid)
    if not uid_normalizado:
        raise ValueError("UID invalido")

    with closing(connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO acessos (aluno_id, uid) VALUES (?, ?)",
            (aluno_id, uid_normalizado),
        )
        conn.commit()
        return cursor.lastrowid


def list_students(db_path=DB_PATH):
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT id, nome, uid, exercicio, repeticoes, ativo
            FROM alunos
            ORDER BY nome
            """
        ).fetchall()
    return [dict(row) for row in rows]


def has_students(db_path=DB_PATH):
    with closing(connect(db_path)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM alunos").fetchone()[0]
    return total > 0
