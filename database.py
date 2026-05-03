"""
database.py — SERVIALAFT SAS
Gestión de empresas, usuarios y consultas en SQLite.
"""
import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "servialaft.db"


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_pwd(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    """Crea tablas e inserta empresa y superadmin por defecto si no existen."""
    with _conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS empresas (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre         TEXT    NOT NULL,
            nit            TEXT,
            plan           TEXT    DEFAULT 'basico',
            activo         INTEGER DEFAULT 1,
            fecha_registro TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT    UNIQUE NOT NULL,
            password_hash  TEXT    NOT NULL,
            nombre         TEXT    NOT NULL,
            empresa_id     INTEGER REFERENCES empresas(id),
            rol            TEXT    DEFAULT 'analista',
            activo         INTEGER DEFAULT 1,
            fecha_creacion TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS consultas (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora         TEXT    DEFAULT (datetime('now','localtime')),
            username           TEXT,
            empresa_id         INTEGER,
            empresa_consultada TEXT    DEFAULT '',
            modulo             TEXT,
            tipo_id            TEXT,
            nro_id             TEXT,
            nombre             TEXT,
            resultado          TEXT
        );
        """)

        # Empresa SERVIALAFT (id garantizado = 1)
        db.execute("""
            INSERT OR IGNORE INTO empresas (id, nombre, nit)
            VALUES (1, 'SERVIALAFT SAS', '900.XXX.XXX-X')
        """)

        # Superadmin por defecto
        db.execute("""
            INSERT OR IGNORE INTO usuarios
                (username, password_hash, nombre, empresa_id, rol)
            VALUES ('admin', ?, 'Super Administrador', 1, 'superadmin')
        """, (hash_pwd("admin123"),))


# ── Autenticación ─────────────────────────────────────────────────────────────
def verificar_usuario(username, password):
    with _conn() as db:
        row = db.execute("""
            SELECT u.id, u.username, u.nombre, u.rol,
                   u.empresa_id, e.nombre AS empresa_nombre
            FROM usuarios u
            LEFT JOIN empresas e ON u.empresa_id = e.id
            WHERE u.username = ?
              AND u.password_hash = ?
              AND u.activo = 1
        """, (username, hash_pwd(password))).fetchone()
    return dict(row) if row else None


# ── Empresas ──────────────────────────────────────────────────────────────────
def listar_empresas():
    with _conn() as db:
        return [dict(r) for r in db.execute(
            "SELECT * FROM empresas ORDER BY nombre"
        ).fetchall()]


def crear_empresa(nombre, nit, plan="basico"):
    with _conn() as db:
        db.execute(
            "INSERT INTO empresas (nombre, nit, plan) VALUES (?, ?, ?)",
            (nombre.strip(), nit.strip(), plan)
        )


def toggle_empresa(empresa_id, activo):
    with _conn() as db:
        db.execute(
            "UPDATE empresas SET activo=? WHERE id=?",
            (1 if activo else 0, empresa_id)
        )


# ── Usuarios ──────────────────────────────────────────────────────────────────
def listar_usuarios(empresa_id=None):
    with _conn() as db:
        if empresa_id:
            rows = db.execute("""
                SELECT u.*, e.nombre AS empresa_nombre
                FROM usuarios u
                LEFT JOIN empresas e ON u.empresa_id = e.id
                WHERE u.empresa_id = ?
                ORDER BY u.nombre
            """, (empresa_id,)).fetchall()
        else:
            rows = db.execute("""
                SELECT u.*, e.nombre AS empresa_nombre
                FROM usuarios u
                LEFT JOIN empresas e ON u.empresa_id = e.id
                ORDER BY e.nombre, u.nombre
            """).fetchall()
    return [dict(r) for r in rows]


def crear_usuario(username, password, nombre, empresa_id):
    with _conn() as db:
        db.execute("""
            INSERT INTO usuarios (username, password_hash, nombre, empresa_id, rol)
            VALUES (?, ?, ?, ?, 'analista')
        """, (username.strip(), hash_pwd(password), nombre.strip(), empresa_id))


def toggle_usuario(usuario_id, activo):
    with _conn() as db:
        db.execute(
            "UPDATE usuarios SET activo=? WHERE id=?",
            (1 if activo else 0, usuario_id)
        )


def reset_password(usuario_id, nueva_password):
    with _conn() as db:
        db.execute(
            "UPDATE usuarios SET password_hash=? WHERE id=?",
            (hash_pwd(nueva_password), usuario_id)
        )


# ── Consultas / logs ──────────────────────────────────────────────────────────
def registrar_consulta(username, empresa_id, modulo, tipo_id, nro_id,
                       nombre, resultado, empresa_consultada=""):
    with _conn() as db:
        db.execute("""
            INSERT INTO consultas
                (username, empresa_id, empresa_consultada, modulo,
                 tipo_id, nro_id, nombre, resultado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, empresa_id, empresa_consultada,
              modulo, tipo_id, nro_id, nombre, resultado))


def listar_consultas(empresa_id=None):
    with _conn() as db:
        if empresa_id:
            rows = db.execute(
                "SELECT * FROM consultas WHERE empresa_id=? ORDER BY fecha_hora DESC",
                (empresa_id,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM consultas ORDER BY fecha_hora DESC"
            ).fetchall()
    return [dict(r) for r in rows]
