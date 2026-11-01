import os
import json
import logging
from datetime import datetime, date
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("study_tracker_db")

# Diretório e arquivos locais (para modo fallback / offline)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
CERTAMES_FILE = os.path.join(DATA_DIR, "certames.json")
STUDY_TYPES_FILE = os.path.join(DATA_DIR, "study_types.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def get_database_url() -> str | None:
    """Recupera a URL de conexão do PostgreSQL de st.secrets ou variável de ambiente."""
    # 0. Tenta carregar diretamente do arquivo local .streamlit/secrets.toml
    secrets_file = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_file):
        try:
            import tomllib
            with open(secrets_file, "rb") as f:
                sec_data = tomllib.load(f)
                if "connections" in sec_data and "postgresql" in sec_data["connections"]:
                    cfg = sec_data["connections"]["postgresql"]
                    if isinstance(cfg, dict) and "url" in cfg:
                        return cfg["url"]
                    if isinstance(cfg, str):
                        return cfg
                if "DATABASE_URL" in sec_data:
                    return sec_data["DATABASE_URL"]
        except Exception:
            pass

    # 1. Tenta conexões nomeadas do Streamlit ([connections.postgresql])
    try:
        if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
            cfg = st.secrets["connections"]["postgresql"]
            if isinstance(cfg, dict) and "url" in cfg:
                return cfg["url"]
            if isinstance(cfg, str):
                return cfg
    except Exception:
        pass

    # 2. Tenta DATABASE_URL em st.secrets
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    # 3. Tenta variável de ambiente
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")

    # 4. Tenta session_state (para teste rápido manual na interface)
    if st.session_state.get("custom_db_url"):
        return st.session_state["custom_db_url"]

    return None

@st.cache_resource(show_spinner=False)
def _build_engine(db_url: str) -> Engine:
    """Cria e mantém o Engine do SQLAlchemy em cache indexado pela URL de conexão."""
    # Normaliza prefixo para o driver psycopg2 instalado
    if db_url.startswith("postgres://"):
        norm_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
        norm_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        norm_url = db_url
    
    # Garante suporte a SSL para Supabase / Neon
    engine = create_engine(
        norm_url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"} if "localhost" not in norm_url and "127.0.0.1" not in norm_url else {}
    )
    # Testa a conectividade
    with engine.connect() as conn:
        conn.execute(text("SELECT 1;"))
    return engine

def get_engine() -> Engine | None:
    """Recupera o engine do banco, registrando mensagens de erro em caso de falha."""
    db_url = get_database_url()
    if not db_url:
        return None
    try:
        return _build_engine(db_url)
    except Exception as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
        try:
            st.session_state["db_last_error"] = str(e)
        except Exception:
            pass
        return None

def is_db_connected() -> bool:
    """Verifica se o PostgreSQL está conectado e pronto para uso."""
    engine = get_engine()
    return engine is not None

def init_db(default_certames=None, default_study_types=None):
    """Cria as tabelas relacionais se não existirem e semeia dados iniciais."""
    engine = get_engine()
    if not engine:
        return False, "Banco de dados não configurado."

    ddl_certames = """
    CREATE TABLE IF NOT EXISTS certames (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        short_name VARCHAR(50),
        cargo VARCHAR(200),
        banca VARCHAR(100),
        exam_date DATE,
        daily_target_hours NUMERIC(4,2) DEFAULT 2.0,
        weekly_target_hours NUMERIC(4,2) DEFAULT 10.0,
        status VARCHAR(50) DEFAULT 'Ativo',
        subjects_json TEXT NOT NULL DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """

    ddl_study_types = """
    CREATE TABLE IF NOT EXISTS study_types (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    );
    """

    ddl_sessions = """
    CREATE TABLE IF NOT EXISTS study_sessions (
        id VARCHAR(50) PRIMARY KEY,
        certame_id VARCHAR(50) REFERENCES certames(id) ON UPDATE CASCADE ON DELETE SET NULL,
        certame_name VARCHAR(200),
        date DATE NOT NULL,
        block VARCHAR(100),
        subject VARCHAR(150),
        topic VARCHAR(255),
        study_type VARCHAR(100),
        duration_min INTEGER NOT NULL CHECK (duration_min > 0),
        questions_total INTEGER DEFAULT 0 CHECK (questions_total >= 0),
        questions_correct INTEGER DEFAULT 0 CHECK (questions_correct >= 0),
        accuracy_pct NUMERIC(5,2) DEFAULT 0.0,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_certame ON study_sessions(certame_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_date ON study_sessions(date);
    """

    try:
        with engine.begin() as conn:
            conn.execute(text(ddl_certames))
            conn.execute(text(ddl_study_types))
            conn.execute(text(ddl_sessions))

            # Se a tabela de certames estiver vazia, popula com os padrões
            res_c = conn.execute(text("SELECT COUNT(*) FROM certames;")).scalar()
            if res_c == 0 and default_certames:
                for c in default_certames:
                    conn.execute(
                        text("""
                            INSERT INTO certames (id, name, short_name, cargo, banca, exam_date, daily_target_hours, weekly_target_hours, status, subjects_json)
                            VALUES (:id, :name, :short_name, :cargo, :banca, :exam_date, :daily_target_hours, :weekly_target_hours, :status, :subjects_json)
                            ON CONFLICT (id) DO NOTHING;
                        """),
                        {
                            "id": c["id"],
                            "name": c["name"],
                            "short_name": c.get("short_name", c["id"]),
                            "cargo": c.get("cargo", ""),
                            "banca": c.get("banca", ""),
                            "exam_date": c.get("exam_date") if c.get("exam_date") else None,
                            "daily_target_hours": float(c.get("daily_target_hours", 2.0)),
                            "weekly_target_hours": float(c.get("weekly_target_hours", 10.0)),
                            "status": c.get("status", "Ativo"),
                            "subjects_json": json.dumps(c.get("subjects", {}), ensure_ascii=False)
                        }
                    )

            # Se a tabela de tipos de estudo estiver vazia, popula
            res_t = conn.execute(text("SELECT COUNT(*) FROM study_types;")).scalar()
            if res_t == 0 and default_study_types:
                for t in default_study_types:
                    conn.execute(
                        text("INSERT INTO study_types (name) VALUES (:name) ON CONFLICT (name) DO NOTHING;"),
                        {"name": t}
                    )
        return True, "Banco inicializado e estruturado com sucesso!"
    except Exception as e:
        logger.error(f"Erro ao inicializar DDL no PostgreSQL: {e}")
        return False, str(e)

# ==============================================================================
# CRUD: CERTAMES
# ==============================================================================

def db_load_certames(fallback_defaults=None):
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT id, name, short_name, cargo, banca, exam_date, daily_target_hours, weekly_target_hours, status, subjects_json FROM certames ORDER BY created_at ASC;"))
                rows = res.fetchall()
                if rows:
                    certames = []
                    for r in rows:
                        subjects = {}
                        if r[9]:
                            try:
                                subjects = json.loads(r[9])
                            except Exception:
                                subjects = {}
                        certames.append({
                            "id": r[0],
                            "name": r[1],
                            "short_name": r[2] or r[0],
                            "cargo": r[3] or "",
                            "banca": r[4] or "",
                            "exam_date": str(r[5]) if r[5] else None,
                            "daily_target_hours": float(r[6] or 2.0),
                            "weekly_target_hours": float(r[7] or 10.0),
                            "status": r[8] or "Ativo",
                            "subjects": subjects
                        })
                    return certames
        except Exception as e:
            logger.warning(f"Erro ao carregar certames do PostgreSQL (usando fallback JSON): {e}")

    # Fallback para JSON local
    ensure_data_dir()
    if os.path.exists(CERTAMES_FILE):
        try:
            with open(CERTAMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return fallback_defaults or []

def db_save_certame(certame_dict):
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO certames (id, name, short_name, cargo, banca, exam_date, daily_target_hours, weekly_target_hours, status, subjects_json)
                        VALUES (:id, :name, :short_name, :cargo, :banca, :exam_date, :daily_target_hours, :weekly_target_hours, :status, :subjects_json)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            short_name = EXCLUDED.short_name,
                            cargo = EXCLUDED.cargo,
                            banca = EXCLUDED.banca,
                            exam_date = EXCLUDED.exam_date,
                            daily_target_hours = EXCLUDED.daily_target_hours,
                            weekly_target_hours = EXCLUDED.weekly_target_hours,
                            status = EXCLUDED.status,
                            subjects_json = EXCLUDED.subjects_json;
                    """),
                    {
                        "id": certame_dict["id"],
                        "name": certame_dict["name"],
                        "short_name": certame_dict.get("short_name", certame_dict["id"]),
                        "cargo": certame_dict.get("cargo", ""),
                        "banca": certame_dict.get("banca", ""),
                        "exam_date": certame_dict.get("exam_date") if certame_dict.get("exam_date") else None,
                        "daily_target_hours": float(certame_dict.get("daily_target_hours", 2.0)),
                        "weekly_target_hours": float(certame_dict.get("weekly_target_hours", 10.0)),
                        "status": certame_dict.get("status", "Ativo"),
                        "subjects_json": json.dumps(certame_dict.get("subjects", {}), ensure_ascii=False)
                    }
                )
            return True, "Certame salvo no PostgreSQL com sucesso!"
        except Exception as e:
            logger.error(f"Erro ao salvar certame no DB: {e}")

    # Fallback local
    ensure_data_dir()
    certames = db_load_certames()
    idx = next((i for i, c in enumerate(certames) if c["id"] == certame_dict["id"]), -1)
    if idx >= 0:
        certames[idx] = certame_dict
    else:
        certames.append(certame_dict)
    with open(CERTAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(certames, f, ensure_ascii=False, indent=2)
    return True, "Certame salvo localmente (modo JSON)."

# ==============================================================================
# CRUD: SESSÕES DE ESTUDO
# ==============================================================================

def db_load_sessions(certame_id=None):
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                query = """
                SELECT id, certame_id, certame_name, date, block, subject, topic, study_type, duration_min, questions_total, questions_correct, accuracy_pct, notes
                FROM study_sessions
                """
                params = {}
                if certame_id:
                    query += " WHERE certame_id = :cid"
                    params["cid"] = certame_id
                query += " ORDER BY date ASC, created_at ASC;"

                res = conn.execute(text(query), params)
                rows = res.fetchall()
                sessions = []
                for r in rows:
                    sessions.append({
                        "id": r[0],
                        "certame_id": r[1] or "GERAL",
                        "certame_name": r[2] or r[1] or "Geral",
                        "date": str(r[3]),
                        "block": r[4] or "Geral",
                        "subject": r[5] or "Geral",
                        "topic": r[6] or "",
                        "study_type": r[7] or "Geral",
                        "duration_min": int(r[8]),
                        "questions_total": int(r[9] or 0),
                        "questions_correct": int(r[10] or 0),
                        "accuracy_pct": float(r[11] or 0.0),
                        "notes": r[12] or ""
                    })
                return sessions
        except Exception as e:
            logger.warning(f"Erro ao carregar sessões do PostgreSQL (usando fallback JSON): {e}")

    # Fallback para JSON local
    ensure_data_dir()
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    if certame_id:
                        return [s for s in data if s.get("certame_id") == certame_id]
                    return data
        except Exception:
            pass
    return []

def db_insert_session(session_dict):
    """Insere ou atualiza de forma atômica uma sessão de estudo."""
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO study_sessions (
                            id, certame_id, certame_name, date, block, subject, topic,
                            study_type, duration_min, questions_total, questions_correct, accuracy_pct, notes
                        ) VALUES (
                            :id, :certame_id, :certame_name, :date, :block, :subject, :topic,
                            :study_type, :duration_min, :questions_total, :questions_correct, :accuracy_pct, :notes
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            certame_id = EXCLUDED.certame_id,
                            certame_name = EXCLUDED.certame_name,
                            date = EXCLUDED.date,
                            block = EXCLUDED.block,
                            subject = EXCLUDED.subject,
                            topic = EXCLUDED.topic,
                            study_type = EXCLUDED.study_type,
                            duration_min = EXCLUDED.duration_min,
                            questions_total = EXCLUDED.questions_total,
                            questions_correct = EXCLUDED.questions_correct,
                            accuracy_pct = EXCLUDED.accuracy_pct,
                            notes = EXCLUDED.notes;
                    """),
                    {
                        "id": str(session_dict.get("id")),
                        "certame_id": session_dict.get("certame_id"),
                        "certame_name": session_dict.get("certame_name"),
                        "date": session_dict.get("date"),
                        "block": session_dict.get("block"),
                        "subject": session_dict.get("subject"),
                        "topic": session_dict.get("topic", ""),
                        "study_type": session_dict.get("study_type", "Geral"),
                        "duration_min": int(session_dict.get("duration_min", 1)),
                        "questions_total": int(session_dict.get("questions_total", 0)),
                        "questions_correct": int(session_dict.get("questions_correct", 0)),
                        "accuracy_pct": float(session_dict.get("accuracy_pct", 0.0)),
                        "notes": session_dict.get("notes", "")
                    }
                )
            return True, "Gravado com sucesso no PostgreSQL!"
        except Exception as e:
            logger.error(f"Erro ao inserir sessão no DB: {e}")
            return False, f"Erro PostgreSQL: {e}"

    # Fallback local
    ensure_data_dir()
    sessions = db_load_sessions()
    sessions = [s for s in sessions if str(s.get("id")) != str(session_dict.get("id"))]
    sessions.append(session_dict)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
    return True, "Gravado localmente (modo JSON)."

def db_delete_session(session_id):
    """Exclui uma sessão de estudo por ID."""
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM study_sessions WHERE id = :id;"), {"id": str(session_id)})
            return True, "Sessão removida do PostgreSQL!"
        except Exception as e:
            logger.error(f"Erro ao excluir sessão do DB: {e}")
            return False, str(e)

    # Fallback local
    ensure_data_dir()
    sessions = db_load_sessions()
    sessions = [s for s in sessions if str(s.get("id")) != str(session_id)]
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
    return True, "Sessão removida localmente (JSON)."

# ==============================================================================
# CRUD: MODALIDADES DE ESTUDO
# ==============================================================================

def db_load_study_types(fallback_defaults=None):
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT name FROM study_types ORDER BY id ASC;"))
                rows = res.fetchall()
                if rows:
                    return [r[0] for r in rows]
        except Exception as e:
            logger.warning(f"Erro ao carregar tipos de estudo do DB: {e}")

    # Fallback local
    ensure_data_dir()
    if os.path.exists(STUDY_TYPES_FILE):
        try:
            with open(STUDY_TYPES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    return fallback_defaults or []

def db_add_study_type(type_name):
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO study_types (name) VALUES (:name) ON CONFLICT (name) DO NOTHING;"),
                    {"name": type_name.strip()}
                )
            return True, "Modalidade adicionada no PostgreSQL!"
        except Exception as e:
            return False, str(e)

    # Fallback local
    types_list = db_load_study_types()
    if type_name.strip() not in types_list:
        types_list.append(type_name.strip())
        with open(STUDY_TYPES_FILE, "w", encoding="utf-8") as f:
            json.dump(types_list, f, ensure_ascii=False, indent=2)
    return True, "Modalidade adicionada localmente."

def db_delete_study_type(type_name):
    engine = get_engine()
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM study_types WHERE name = :name;"), {"name": type_name.strip()})
            return True, "Modalidade removida do PostgreSQL!"
        except Exception as e:
            return False, str(e)

    # Fallback local
    types_list = db_load_study_types()
    if type_name.strip() in types_list and len(types_list) > 1:
        types_list.remove(type_name.strip())
        with open(STUDY_TYPES_FILE, "w", encoding="utf-8") as f:
            json.dump(types_list, f, ensure_ascii=False, indent=2)
    return True, "Modalidade removida localmente."
