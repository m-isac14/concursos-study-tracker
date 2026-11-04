import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
try:
    import zoneinfo
    TZ_LOCAL = zoneinfo.ZoneInfo("America/Sao_Paulo")
except Exception:
    TZ_LOCAL = None

def get_current_date() -> date:
    """Retorna a data atual respeitando o fuso horário de Brasília (America/Sao_Paulo)."""
    if TZ_LOCAL:
        return datetime.now(TZ_LOCAL).date()
    return date.today()

def get_current_datetime() -> datetime:
    """Retorna o datetime atual respeitando o fuso horário de Brasília."""
    if TZ_LOCAL:
        return datetime.now(TZ_LOCAL)
    return datetime.now()
import json
import os
import time

from github_sync import (
    get_github_config,
    fetch_file_from_github,
    commit_file_to_github,
    sync_session_to_obsidian_idempotent
)
from database import (
    is_db_connected,
    init_db,
    db_load_certames,
    db_save_certame,
    db_load_sessions,
    db_insert_session,
    db_delete_session,
    db_load_study_types,
    db_add_study_type,
    db_delete_study_type,
    db_load_completed_blocks,
    db_set_completed_block,
    db_load_active_timer,
    db_save_active_timer
)

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA & DESIGN SYSTEM
# ==========================================
st.set_page_config(
    page_title="Passei Concurso | Performance & Gestão de Estudos — Isac",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Design System CSS (Slate, Soft White, Indigo & Emerald)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

    :root {
        --bg-page: #F8FAFC;
        --bg-card: #FFFFFF;
        --bg-subtle: #F1F5F9;
        --text-primary: #0F172A;
        --text-secondary: #334155;
        --text-muted: #64748B;
        --border-subtle: #E2E8F0;
        --accent-indigo: #4F46E5;
        --accent-indigo-light: #EEF2FF;
        --accent-indigo-border: #C7D2FE;
        --accent-emerald: #059669;
        --accent-emerald-light: #ECFDF5;
        --accent-emerald-border: #A7F3D0;
        --accent-amber: #D97706;
        --accent-amber-light: #FFFBEB;
        --accent-amber-border: #FDE68A;
        --accent-rose: #E11D48;
        --accent-rose-light: #FFF1F2;
        --accent-rose-border: #FECDD3;
        --shadow-sm: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.02);
        --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.03);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--text-primary);
    }

    /* Redução de padding excessivo e respiro equilibrado */
    .block-container {
        padding-top: 1.4rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1420px;
    }

    /* Sidebar elegante em Cinza Ardósia Claro */
    [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-left: 1.1rem !important;
        padding-right: 1.1rem !important;
    }

    /* Cartões nativos st.container(border=True) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-sm) !important;
        padding: 1rem 1.2rem !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #CBD5E1 !important;
    }

    /* Sanfonas (st.expander) limpas */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-sm) !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] details summary {
        font-weight: 600 !important;
        color: #1E293B !important;
        padding: 0.65rem 1rem !important;
    }

    /* Header Principal */
    .app-header {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.15rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-sm);
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
    }
    .header-left {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .header-eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #4F46E5;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .header-title {
        font-size: 1.55rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.025em;
        margin: 0;
        line-height: 1.2;
    }
    .header-subtitle {
        font-size: 0.88rem;
        color: #64748B;
        margin: 0;
    }
    .header-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: center;
    }

    /* Pills & Badges Semânticos */
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.28rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        line-height: 1.2;
        white-space: nowrap;
    }
    .pill-indigo {
        background-color: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #C7D2FE;
    }
    .pill-emerald {
        background-color: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .pill-amber {
        background-color: #FFFBEB;
        color: #D97706;
        border: 1px solid #FDE68A;
    }
    .pill-rose {
        background-color: #FFF1F2;
        color: #E11D48;
        border: 1px solid #FECDD3;
    }
    .pill-slate {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
    }

    /* Abas de Navegação Modernas (Pill-Nav Style) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F1F5F9;
        padding: 5px;
        border-radius: 11px;
        gap: 6px;
        border: 1px solid #E2E8F0;
        margin-bottom: 0.8rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        padding: 0 16px;
        border-radius: 8px;
        font-size: 0.86rem;
        font-weight: 500;
        color: #475569;
        background-color: transparent;
        border: none !important;
        transition: all 0.15s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0F172A;
        background-color: rgba(255, 255, 255, 0.6);
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #4F46E5 !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04) !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* KPI Cards no Topo */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem 1.15rem;
        box-shadow: var(--shadow-sm);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.35rem;
    }
    .kpi-label {
        font-size: 0.76rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.025em;
        line-height: 1.15;
        margin-bottom: 0.45rem;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #64748B;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.4rem;
    }
    .kpi-bar-bg {
        width: 100%;
        height: 5px;
        background-color: #F1F5F9;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 0.45rem;
    }
    .kpi-bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease;
    }

    /* Card Foco de Hoje & Blocos da Grade */
    .section-title {
        font-size: 0.98rem;
        font-weight: 600;
        color: #0F172A;
        margin: 0 0 0.65rem 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .block-item {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 3.5px solid #4F46E5;
        border-radius: 9px;
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.55rem;
    }
    .block-item.basica {
        border-left-color: #10B981;
    }
    .block-item.discursiva {
        border-left-color: #7C3AED;
    }
    .block-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.25rem;
    }
    .block-subject {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0F172A;
    }
    .block-topic {
        font-size: 0.8rem;
        color: #475569;
        margin: 0;
    }

    /* Barra Segmentada 70/30 */
    .seg-bar-wrap {
        margin-top: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .seg-bar-track {
        width: 100%;
        height: 10px;
        background-color: #F1F5F9;
        border-radius: 999px;
        overflow: hidden;
        display: flex;
        position: relative;
        border: 1px solid #E2E8F0;
    }
    .seg-bar-esp {
        background-color: #4F46E5;
        height: 100%;
    }
    .seg-bar-bas {
        background-color: #10B981;
        height: 100%;
    }

    /* Cronômetro Imersivo */
    .timer-container {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.5rem;
    }
    .timer-digits {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3.1rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: 0.04em;
        line-height: 1.1;
        margin: 0.35rem 0;
    }
    .timer-digits.running {
        color: #4F46E5;
    }
    .sidebar-timer-digits {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.65rem;
        font-weight: 700;
        color: #0F172A;
        text-align: center;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 9px;
        padding: 0.4rem 0.5rem;
        margin: 0.35rem 0 0.55rem 0;
        letter-spacing: 0.04em;
    }

    /* Botões refinados */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.15s ease !important;
    }
    .stProgress > div > div > div > div {
        background-color: #4F46E5 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CAMINHOS E ESTRUTURAS DE DADOS
# ==========================================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
CERTAMES_FILE = os.path.join(DATA_DIR, "certames.json")
STUDY_TYPES_FILE = os.path.join(DATA_DIR, "study_types.json")

DEFAULT_STUDY_TYPES = [
    "📹 Vídeoaula",
    "🎯 Questões / Simulado",
    "📖 PDF / Apostila",
    "⚖️ Lei Seca / Legislação",
    "✍️ Prática de Discursiva",
    "🧠 Revisão / Flashcards",
    "📝 Resumo / Mapa Mental"
]

COFRE_DIR_DEFAULT = r"G:\Meu Drive\cofre\06-Concursos-e-Estudos\registros-de-estudo"
COFRE_MATRIZ_DEFAULT = r"G:\Meu Drive\cofre\06-Concursos-e-Estudos\matriz-de-desempenho-e-materias.md"

DEFAULT_CERTAMES = [
    {
        "id": "DPDF",
        "name": "DPDF 2026/2027 — Analista TI (Redes)",
        "short_name": "DPDF",
        "cargo": "Analista de Apoio: Informática – Redes",
        "banca": "Instituto ACCESS",
        "exam_date": "2027-02-21",
        "daily_target_hours": 2.0,
        "weekly_target_hours": 10.0,
        "status": "Foco Total 🔥",
        "subjects": {
            "Conhecimentos Específicos (Peso 2)": [
                "Redes de Computadores",
                "Sistemas Operacionais e Serviços",
                "Hardware e Infraestrutura",
                "Armazenamento e Backup",
                "Virtualização e Nuvem",
                "Segurança da Informação",
                "Monitoramento e Continuidade",
                "Bancos de Dados em Infra",
                "Gestão e Governança de TI",
                "Fiscalização de Contratos de TIC",
            ],
            "Conhecimentos Básicos (Peso 1)": [
                "Regime Jurídico dos Servidores (LC 840/2011)",
                "LODF e LC nº 828/2010",
                "Língua Portuguesa",
                "Lei Maria da Penha (Lei 11.340/2006)",
                "Conhecimentos do DF e Mulheres",
                "Noções de Informática",
                "Noções de Primeiros Socorros",
            ],
            "Discursivas": [
                "Questão Discursiva Técnica TI (10 pts)",
                "Dissertação Geral (20 pts)",
            ]
        }
    },
    {
        "id": "CGU",
        "name": "CGU 2026/2027 — Auditor Federal (TI)",
        "short_name": "CGU",
        "cargo": "Auditor Federal de Finanças e Controle — TI",
        "banca": "Cebraspe (Provável)",
        "exam_date": "2027-06-30",
        "daily_target_hours": 2.0,
        "weekly_target_hours": 10.0,
        "status": "Planejado ⏳",
        "subjects": {
            "Conhecimentos Específicos TI": [
                "Engenharia de Software e Agilidade",
                "Banco de Dados e Big Data",
                "Segurança da Informação e Cibersegurança",
                "Governança e Gestão de TI (COBIT/ITIL)",
                "Ciência de Dados e Inteligência Artificial",
                "Infraestrutura, Redes e Nuvem"
            ],
            "Conhecimentos Básicos e Gerais": [
                "Língua Portuguesa e Redação Oficial",
                "Língua Inglesa",
                "Direito Constitucional",
                "Direito Administrativo",
                "Administração Pública e Políticas Públicas",
                "Auditoria Governamental e Controle Interno"
            ],
            "Discursivas": [
                "Estudo de Caso / Discursiva Técnica TI",
                "Dissertação de Controle Público"
            ]
        }
    },
    {
        "id": "DATAPREV",
        "name": "DATAPREV 2026 — Analista de TI",
        "short_name": "DATAPREV",
        "cargo": "Analista de Tecnologia da Informação",
        "banca": "FGV",
        "exam_date": "2026-12-31",
        "daily_target_hours": 2.0,
        "weekly_target_hours": 10.0,
        "status": "Stand-by ⏳",
        "subjects": {
            "Específicos": [
                "Desenvolvimento e Arquitetura de Software",
                "Bancos de Dados Relacionais e NoSQL",
                "DevOps, CI/CD e Contêineres",
                "Segurança da Informação",
                "Governança de TI"
            ],
            "Básicos": [
                "Língua Portuguesa (FGV)",
                "Raciocínio Lógico-Matemático",
                "Legislação e Ética Pública"
            ]
        }
    },
    {
        "id": "BASE_GERAL",
        "name": "Ciclo Base Contínuo — TI & Gerais",
        "short_name": "Base Geral",
        "cargo": "Aperfeiçoamento Contínuo",
        "banca": "Geral / Múltiplas",
        "exam_date": "",
        "daily_target_hours": 2.0,
        "weekly_target_hours": 10.0,
        "status": "Permanente 🌐",
        "subjects": {
            "Tecnologia da Informação": [
                "Redes de Computadores",
                "Sistemas Operacionais (Linux/Windows)",
                "Bancos de Dados e SQL",
                "Engenharia de Software",
                "Segurança da Informação",
                "Governança de TI",
                "Cloud Computing & DevOps"
            ],
            "Disciplinas Gerais": [
                "Língua Portuguesa",
                "Raciocínio Lógico-Matemático",
                "Direito Constitucional",
                "Direito Administrativo"
            ]
        }
    }
]

PLANO_SEMANAL_DPDF = [
    {
        "dia_idx": 0,
        "dia": "Segunda-feira",
        "bloco_1_materia": "Redes de Computadores",
        "bloco_1_topico": "TCP/IP, Protocolos e Roteamento",
        "bloco_1_tipo": "Específica (Peso 2)",
        "bloco_1_horas": 1.0,
        "bloco_2_materia": "Regime Jurídico dos Servidores (LC 840/2011)",
        "bloco_2_topico": "Carreiras, regime e jornada / Direitos e Vantagens",
        "bloco_2_tipo": "Básica (Peso 1)",
        "bloco_2_horas": 1.0,
        "foco": "Teoria objetiva + Resolução de questões de fixação"
    },
    {
        "dia_idx": 1,
        "dia": "Terça-feira",
        "bloco_1_materia": "Sistemas Operacionais e Serviços",
        "bloco_1_topico": "Linux, Unix, Windows Server, Shell & PowerShell",
        "bloco_1_tipo": "Específica (Peso 2)",
        "bloco_1_horas": 1.0,
        "bloco_2_materia": "Redes de Computadores",
        "bloco_2_topico": "VLAN, Trunking, VPN, Switches, QoS e Diagnóstico",
        "bloco_2_tipo": "Específica (Peso 2)",
        "bloco_2_horas": 1.0,
        "foco": "Prática intensiva com questões comentadas de infraestrutura"
    },
    {
        "dia_idx": 2,
        "dia": "Quarta-feira",
        "bloco_1_materia": "Segurança da Informação",
        "bloco_1_topico": "ISO 27001/27002, Criptografia, Firewalls e Ameaças",
        "bloco_1_tipo": "Específica (Peso 2)",
        "bloco_1_horas": 1.0,
        "bloco_2_materia": "Língua Portuguesa",
        "bloco_2_topico": "Interpretação de Texto, Sintaxe e Pontuação (Banca ACCESS)",
        "bloco_2_tipo": "Básica (Peso 1)",
        "bloco_2_horas": 1.0,
        "foco": "Resolução de provas anteriores da banca e análise de enunciados"
    },
    {
        "dia_idx": 3,
        "dia": "Quinta-feira",
        "bloco_1_materia": "Virtualização e Nuvem",
        "bloco_1_topico": "Docker, Kubernetes, Hipervisores, IaaS/PaaS/SaaS",
        "bloco_1_tipo": "Específica (Peso 2)",
        "bloco_1_horas": 1.0,
        "bloco_2_materia": "LODF e LC nº 828/2010",
        "bloco_2_topico": "Estrutura, competências e organização da Defensoria Pública do DF",
        "bloco_2_tipo": "Básica (Peso 1)",
        "bloco_2_horas": 1.0,
        "foco": "Fixação de artigos-chave, prazos, competências e estrutura da DPDF"
    },
    {
        "dia_idx": 4,
        "dia": "Sexta-feira",
        "bloco_1_materia": "Gestão e Governança de TI",
        "bloco_1_topico": "ITIL 4, COBIT 2019, PMBOK 7 e Fiscalização de Contratos (IN 94/Lei 14.133)",
        "bloco_1_tipo": "Específica (Peso 2)",
        "bloco_1_horas": 1.0,
        "bloco_2_materia": "Questão Discursiva Técnica TI (10 pts)",
        "bloco_2_topico": "Redação técnica sobre Redes, Nuvem, Segurança ou Governança",
        "bloco_2_tipo": "Discursiva Técnica (10 pts)",
        "bloco_2_horas": 1.0,
        "foco": "Redação estruturada no padrão de espelho de correção da banca"
    },
    {
        "dia_idx": 5,
        "dia": "Sábado (Opcional)",
        "bloco_1_materia": "Caderno de Erros no Obsidian",
        "bloco_1_topico": "Revisão atômica de pegadinhas e erros cometidos na semana",
        "bloco_1_tipo": "Consolidação / Revisão",
        "bloco_1_horas": 1.0,
        "bloco_2_materia": "Noções de Primeiros Socorros / Política para Mulheres",
        "bloco_2_topico": "Leitura rápida das normas complementares do DF",
        "bloco_2_tipo": "Básica (Peso 1)",
        "bloco_2_horas": 1.0,
        "foco": "Manutenção do ritmo sem pressão ou reposição de pendência"
    },
    {
        "dia_idx": 6,
        "dia": "Domingo",
        "bloco_1_materia": "Descanso & Recuperação",
        "bloco_1_topico": "Lazer e descanso mental",
        "bloco_1_tipo": "Recuperação",
        "bloco_1_horas": 0.0,
        "bloco_2_materia": "Planejamento da Semana",
        "bloco_2_topico": "Alinhamento das metas para a segunda-feira",
        "bloco_2_tipo": "Estratégia",
        "bloco_2_horas": 0.0,
        "foco": "Recarregar as energias para o ciclo semanal de 10 horas líquidas"
    }
]

# ==========================================
# 3. FUNÇÕES DE PERSISTÊNCIA LOCAL & NUVEM
# ==========================================
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_certames():
    return db_load_certames(DEFAULT_CERTAMES)

def save_certames(certames):
    ensure_data_dir()
    for c in certames:
        db_save_certame(c)
    with open(CERTAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(certames, f, ensure_ascii=False, indent=2)

def load_sessions():
    return db_load_sessions()

def save_sessions(sessions):
    ensure_data_dir()
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def load_study_types():
    return db_load_study_types(DEFAULT_STUDY_TYPES)

def save_study_types(types_list):
    ensure_data_dir()
    with open(STUDY_TYPES_FILE, "w", encoding="utf-8") as f:
        json.dump(types_list, f, ensure_ascii=False, indent=2)

def pull_from_github_and_merge():
    """Puxa a base de sessões do GitHub e mescla com as sessões locais."""
    gh_cfg = get_github_config()
    remote_data, sha, err = fetch_file_from_github(
        repo=gh_cfg["repo"],
        file_path="data/sessions.json",
        branch=gh_cfg["branch"],
        token=gh_cfg["token"]
    )
    if err:
        return False, err
    if remote_data is not None and isinstance(remote_data, list):
        local_sessions = load_sessions()
        local_map = {str(s.get("id")): s for s in local_sessions}
        for s in remote_data:
            local_map[str(s.get("id"))] = s
        merged = sorted(list(local_map.values()), key=lambda x: str(x.get("date")), reverse=False)
        save_sessions(merged)
        st.session_state.sessions = merged
        return True, f"{len(merged)} sessões sincronizadas com sucesso do GitHub!"
    return False, "Nenhum dado retornado do GitHub."

def push_to_github(commit_msg="refactor(data): sync sessions"):
    """Envia a lista atual de sessões para o repositório GitHub via API REST."""
    gh_cfg = get_github_config()
    if not gh_cfg["token"]:
        return False, "Token do GitHub não configurado."
    sessions = load_sessions()
    success, msg = commit_file_to_github(
        repo=gh_cfg["repo"],
        file_path="data/sessions.json",
        data_obj=sessions,
        commit_message=commit_msg,
        branch=gh_cfg["branch"],
        token=gh_cfg["token"]
    )
    return success, msg

# ==========================================
# 4. INICIALIZAÇÃO DO BANCO & SESSION_STATE
# ==========================================
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = True
    if is_db_connected():
        init_db(DEFAULT_CERTAMES, DEFAULT_STUDY_TYPES)

if "certames" not in st.session_state:
    st.session_state.certames = load_certames()
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()
if "study_types" not in st.session_state:
    st.session_state.study_types = load_study_types()
hoje_str_init = get_current_date().isoformat()
if "completed_blocks_date" not in st.session_state or st.session_state.completed_blocks_date != hoje_str_init:
    st.session_state.completed_blocks_date = hoje_str_init
    st.session_state.completed_blocks_today = db_load_completed_blocks(hoje_str_init)

if "initial_gh_pull_done" not in st.session_state:
    st.session_state.initial_gh_pull_done = True
    if not is_db_connected():
        gh_cfg_init = get_github_config()
        if gh_cfg_init["token"] and not st.session_state.sessions:
            pull_from_github_and_merge()

# Estado do cronômetro / pomodoro persistente (anti-perda por suspensão/fechamento)
if "timer_initialized" not in st.session_state:
    st.session_state.timer_initialized = True
    db_timer = db_load_active_timer()
    now_ts = time.time()
    
    st.session_state.timer_mode = db_timer.get("mode", "countup")  # 'countup' ou 'countdown'
    st.session_state.timer_target_seconds = int(db_timer.get("target_seconds") or 1500) # 25 min default
    
    if db_timer.get("is_running") and db_timer.get("last_heartbeat"):
        lh = db_timer["last_heartbeat"]
        st_ts = db_timer.get("start_timestamp") or lh
        gap = now_ts - lh
        if gap <= 90.0:
            # Reconexão rápida ou reload da aba: continua rolando sem perder nenhum segundo!
            st.session_state.timer_running = True
            st.session_state.timer_start = datetime.fromtimestamp(st_ts)
            st.session_state.elapsed_seconds = int(now_ts - st_ts)
            db_save_active_timer(True, st_ts, st.session_state.elapsed_seconds, now_ts)
        else:
            # O navegador foi fechado ou ficou inativo por muito tempo:
            st.session_state.timer_running = False
            recovered_secs = max(0, int(lh - st_ts))
            st.session_state.elapsed_seconds = recovered_secs
            st.session_state.timer_start = None
            db_save_active_timer(False, None, recovered_secs, None)
    else:
        st.session_state.timer_running = False
        st.session_state.timer_start = None
        st.session_state.elapsed_seconds = int(db_timer.get("elapsed_seconds") or 0)

if "timer_mode" not in st.session_state:
    st.session_state.timer_mode = "countup"
if "timer_target_seconds" not in st.session_state:
    st.session_state.timer_target_seconds = 1500
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

def get_current_elapsed_seconds():
    if st.session_state.timer_running and st.session_state.timer_start:
        return max(0, int((datetime.now() - st.session_state.timer_start).total_seconds()))
    return max(0, int(st.session_state.elapsed_seconds))

def get_countdown_display_seconds():
    """Retorna os segundos restantes (ou 0 se esgotado) para o modo regressivo."""
    elapsed = get_current_elapsed_seconds()
    target = st.session_state.get("timer_target_seconds", 1500)
    remaining = target - elapsed
    return max(0, remaining)

def format_hours_mins(hours_float: float, short: bool = False) -> str:
    """Converte horas decimais para formato amigável (ex: '2 horas e 12 minutos' ou '2h 12min')."""
    if hours_float is None or hours_float <= 0:
        return "0min" if short else "0 minutos"
    total_minutes = int(round(float(hours_float) * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    if short:
        if h > 0 and m > 0:
            return f"{h}h {m:02d}min"
        elif h > 0:
            return f"{h}h"
        return f"{m}min"
    else:
        if h > 0 and m > 0:
            h_str = "1 hora" if h == 1 else f"{h} horas"
            m_str = "1 minuto" if m == 1 else f"{m} minutos"
            return f"{h_str} e {m_str}"
        elif h > 0:
            return "1 hora" if h == 1 else f"{h} horas"
        return "1 minuto" if m == 1 else f"{m} minutos"

def format_hms(total_seconds):
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def sync_timer_to_form_inputs(total_seconds):
    total_mins = max(1, round(total_seconds / 60)) if total_seconds >= 30 else (total_seconds // 60)
    if total_mins > 0:
        st.session_state["reg_dur_horas"] = int(min(24, total_mins // 60))
        st.session_state["reg_dur_minutos"] = int(total_mins % 60)

def action_start_timer():
    st.session_state.timer_running = True
    start_dt = datetime.now() - timedelta(seconds=st.session_state.elapsed_seconds)
    st.session_state.timer_start = start_dt
    now_ts = time.time()
    st_ts = start_dt.timestamp()
    db_save_active_timer(True, st_ts, st.session_state.elapsed_seconds, now_ts)

def action_pause_timer():
    if st.session_state.timer_running and st.session_state.timer_start:
        st.session_state.elapsed_seconds = int((datetime.now() - st.session_state.timer_start).total_seconds())
    st.session_state.timer_running = False
    st.session_state.timer_start = None
    db_save_active_timer(False, None, st.session_state.elapsed_seconds, None)
    # Se estivesse em contagem regressiva e atingiu/ultrapassou o alvo, preenche o tempo alvo
    effective_seconds = st.session_state.elapsed_seconds
    if st.session_state.get("timer_mode") == "countdown":
        target = st.session_state.get("timer_target_seconds", 1500)
        effective_seconds = min(st.session_state.elapsed_seconds, target)
    sync_timer_to_form_inputs(effective_seconds)

def action_reset_timer():
    st.session_state.timer_running = False
    st.session_state.elapsed_seconds = 0
    st.session_state.timer_start = None
    st.session_state["reg_dur_horas"] = 1
    st.session_state["reg_dur_minutos"] = 0
    db_save_active_timer(False, None, 0, None)


# ==========================================
# 5. FUNÇÕES GRÁFICAS MINIMALISTAS (PLOTLY)
# ==========================================
def apply_clean_layout(fig, height=280, show_legend=False, margin=None):
    if margin is None:
        margin = dict(t=16, b=16, l=10, r=24)
    fig.update_layout(
        height=height,
        margin=margin,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=show_legend,
        font=dict(family="Inter, system-ui, sans-serif", color="#334155", size=12),
        xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont=dict(color="#64748B", size=11)),
        yaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont=dict(color="#1E293B", size=11)),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#1E293B",
            font=dict(family="Inter, sans-serif", size=12, color="#F8FAFC")
        )
    )
    return fig

def create_donut_7030(horas_esp, horas_bas, label_center="Específicas"):
    tot = horas_esp + horas_bas
    if tot <= 0:
        fig = go.Figure(go.Pie(
            labels=["Meta Específicas (70%)", "Meta Básicas (30%)"],
            values=[70, 30],
            hole=0.72,
            marker=dict(colors=["#E2E8F0", "#F1F5F9"], line=dict(color="#FFFFFF", width=2)),
            textinfo="none",
            hoverinfo="label"
        ))
        center_main = "70/30"
        center_sub = "Meta Alvo"
    else:
        pct_esp = (horas_esp / tot) * 100.0
        fig = go.Figure(go.Pie(
            labels=["Específicas / Técnicas", "Conhecimentos Básicos"],
            values=[horas_esp, horas_bas],
            hole=0.72,
            sort=False,
            direction="clockwise",
            marker=dict(colors=["#4F46E5", "#10B981"], line=dict(color="#FFFFFF", width=2)),
            textinfo="none",
            customdata=[format_hours_mins(horas_esp, short=True), format_hours_mins(horas_bas, short=True)],
            hovertemplate="<b>%{label}</b>: %{customdata} estudadas (%{percent})<extra></extra>"
        ))
        center_main = f"{pct_esp:.0f}%"
        center_sub = label_center

    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>{center_main}</b><br><span style='font-size:11px;color:#64748B'>{center_sub}</span>",
                x=0.5, y=0.5,
                font=dict(size=20, color="#0F172A", family="Inter, sans-serif"),
                showarrow=False
            )
        ]
    )
    return apply_clean_layout(fig, height=195, show_legend=False, margin=dict(t=8, b=8, l=8, r=8))

def create_spline_evolution(df_source, hoje_dt, meta_dia):
    ult_14 = hoje_dt - timedelta(days=13)
    dias_df = pd.DataFrame({"date": pd.date_range(ult_14, hoje_dt)})

    if not df_source.empty:
        df_rec = df_source[df_source["date"] >= ult_14]
        ag = df_rec.groupby("date").agg(
            hours=("hours", "sum"),
            q_tot=("questions_total", "sum"),
            q_cor=("questions_correct", "sum")
        ).reset_index()
        merged = pd.merge(dias_df, ag, on="date", how="left").fillna(0.0)
    else:
        merged = dias_df.copy()
        merged["hours"] = 0.0
        merged["q_tot"] = 0.0
        merged["q_cor"] = 0.0

    merged["dia_fmt"] = merged["date"].dt.strftime("%d/%m")
    hover_extra = []
    for _, r in merged.iterrows():
        if r["q_tot"] > 0:
            acc = (r["q_cor"] / r["q_tot"]) * 100.0
            hover_extra.append(f" • {acc:.0f}% de acerto ({int(r['q_cor'])}/{int(r['q_tot'])})")
        else:
            hover_extra.append("")
    merged["hover_extra"] = hover_extra

    fig = go.Figure()

    # Linha de meta diária sutil
    fig.add_hline(
        y=meta_dia,
        line_dash="dot",
        line_color="#10B981",
        line_width=1.5,
        annotation_text=f"Meta ({meta_dia:.0f}h)",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#059669")
    )

    # Curva suave (spline) com área sombreada semitransparente
    fig.add_trace(go.Scatter(
        x=merged["dia_fmt"],
        y=merged["hours"],
        mode="lines+markers",
        line=dict(shape="spline", smoothing=0.85, color="#4F46E5", width=3),
        fill="tozeroy",
        fillcolor="rgba(79, 70, 229, 0.10)",
        marker=dict(
            size=7,
            color=["#059669" if h >= meta_dia else "#4F46E5" for h in merged["hours"]],
            line=dict(width=2, color="#FFFFFF")
        ),
        customdata=list(zip(merged["dia_fmt"], [format_hours_mins(h, short=True) for h in merged["hours"]], merged["hover_extra"])),
        hovertemplate="<b>Dia %{customdata[0]}</b>: %{customdata[1]} estudadas%{customdata[2]}<extra></extra>"
    ))

    max_y = max(merged["hours"].max() if not merged.empty else 0, meta_dia) * 1.25
    fig = apply_clean_layout(fig, height=275, margin=dict(t=18, b=24, l=28, r=14))
    fig.update_yaxes(
        range=[0, max(2.5, max_y)],
        showgrid=True,
        gridcolor="rgba(226, 232, 240, 0.6)",
        ticksuffix="h"
    )
    return fig

def create_accuracy_gauge(taxa_geral, total_q, meta=80.0):
    bar_color = "#059669" if taxa_geral >= 80 else ("#D97706" if taxa_geral >= 65 else "#E11D48")
    if total_q == 0:
        bar_color = "#94A3B8"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(taxa_geral, 1),
        number=dict(suffix="%", font=dict(size=32, color="#0F172A", family="Inter, sans-serif")),
        delta=dict(
            reference=meta,
            increasing=dict(color="#059669"),
            decreasing=dict(color="#D97706"),
            suffix="% vs meta (80%)",
            font=dict(size=12)
        ),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#CBD5E1", tickvals=[0, 65, 80, 100]),
            bar=dict(color=bar_color, thickness=0.32),
            bgcolor="#F8FAFC",
            borderwidth=0,
            steps=[
                dict(range=[0, 65], color="#FFE4E6"),
                dict(range=[65, 80], color="#FEF3C7"),
                dict(range=[80, 100], color="#D1FAE5")
            ],
            threshold=dict(
                line=dict(color="#0F172A", width=3),
                thickness=0.8,
                value=meta
            )
        )
    ))
    return apply_clean_layout(fig, height=220, margin=dict(t=24, b=10, l=24, r=24))

def create_subject_bars(df_source):
    ag = df_source.groupby("subject").agg(
        hours=("hours", "sum"),
        q_tot=("questions_total", "sum"),
        q_cor=("questions_correct", "sum")
    ).reset_index()
    ag = ag.sort_values(by="hours", ascending=True).tail(10)

    labels_bar = []
    hover_acc = []
    for _, r in ag.iterrows():
        if r["q_tot"] > 0:
            acc = (r["q_cor"] / r["q_tot"]) * 100.0
            labels_bar.append(f" {format_hours_mins(r['hours'], short=True)} • {acc:.0f}%")
            hover_acc.append(f" • {acc:.0f}% de acerto")
        else:
            labels_bar.append(f" {format_hours_mins(r['hours'], short=True)}")
            hover_acc.append("")

    max_x = ag["hours"].max() if not ag.empty else 1.0

    fig = go.Figure(go.Bar(
        x=ag["hours"],
        y=ag["subject"],
        orientation="h",
        marker=dict(color="#4F46E5", cornerradius=6),
        text=labels_bar,
        textposition="outside",
        textfont=dict(size=11, color="#334155", family="Inter, sans-serif"),
        cliponaxis=False,
        customdata=list(zip([format_hours_mins(h, short=True) for h in ag["hours"]], hover_acc)),
        hovertemplate="<b>%{y}</b>: %{customdata[0]} estudadas%{customdata[1]}<extra></extra>"
    ))
    fig = apply_clean_layout(fig, height=max(240, len(ag) * 32 + 40), margin=dict(t=10, b=10, l=10, r=75))
    fig.update_xaxes(visible=False, range=[0, max_x * 1.28])
    return fig

def create_subject_accuracy_bars(df_source):
    q_df = df_source[df_source["questions_total"] > 0]
    if q_df.empty:
        return None
    ag = q_df.groupby("subject").agg(
        hours=("hours", "sum"),
        q_tot=("questions_total", "sum"),
        q_cor=("questions_correct", "sum")
    ).reset_index()
    ag["taxa"] = (ag["q_cor"] / ag["q_tot"] * 100.0).round(1)
    ag = ag.sort_values(by="taxa", ascending=True).tail(8)

    colors = ["#059669" if t >= 80 else ("#D97706" if t >= 65 else "#E11D48") for t in ag["taxa"]]
    labels = [f" {t:.0f}% ({int(c)}/{int(tot)})" for t, c, tot in zip(ag["taxa"], ag["q_cor"], ag["q_tot"])]

    fig = go.Figure(go.Bar(
        x=ag["taxa"],
        y=ag["subject"],
        orientation="h",
        marker=dict(color=colors, cornerradius=6),
        text=labels,
        textposition="outside",
        textfont=dict(size=11, color="#334155"),
        cliponaxis=False,
        customdata=ag["hours"],
        hovertemplate="<b>%{y}</b>: %{customdata:.1f}h estudadas • %{x:.1f}% de acerto<extra></extra>"
    ))
    fig.add_vline(x=80, line_dash="dot", line_color="#059669", line_width=1.5)
    fig = apply_clean_layout(fig, height=max(210, len(ag) * 30 + 35), margin=dict(t=8, b=8, l=10, r=85))
    fig.update_xaxes(visible=False, range=[0, 122])
    return fig

def create_modality_bars(df_source):
    ag = df_source.groupby("study_type").agg(
        hours=("hours", "sum"),
        q_tot=("questions_total", "sum"),
        q_cor=("questions_correct", "sum")
    ).reset_index().sort_values(by="hours", ascending=True)

    tot_h = ag["hours"].sum() if not ag.empty else 1.0
    labels = [f" {format_hours_mins(h, short=True)} ({(h/tot_h*100):.0f}%)" for h in ag["hours"]]
    hover_extra = [
        f" • {(c/t*100):.0f}% de acerto" if t > 0 else ""
        for t, c in zip(ag["q_tot"], ag["q_cor"])
    ]
    max_x = ag["hours"].max() if not ag.empty else 1.0

    fig = go.Figure(go.Bar(
        x=ag["hours"],
        y=ag["study_type"],
        orientation="h",
        marker=dict(color="#6366F1", cornerradius=6),
        text=labels,
        textposition="outside",
        textfont=dict(size=11, color="#334155"),
        cliponaxis=False,
        customdata=list(zip([format_hours_mins(h, short=True) for h in ag["hours"]], hover_extra)),
        hovertemplate="<b>%{y}</b>: %{customdata[0]} estudadas%{customdata[1]}<extra></extra>"
    ))
    fig = apply_clean_layout(fig, height=max(240, len(ag) * 34 + 40), margin=dict(t=10, b=10, l=10, r=80))
    fig.update_xaxes(visible=False, range=[0, max_x * 1.28])
    return fig

# ==========================================
# 6. SIDEBAR: SELETOR GLOBAL & STATUS RÁPIDO
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.65rem;margin-bottom:0.4rem;">
        <div style="background:#4F46E5;color:#FFFFFF;width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:700;box-shadow:0 2px 4px rgba(79,70,229,0.25);">🎯</div>
        <div>
            <div style="font-weight:700;font-size:1.05rem;color:#0F172A;line-height:1.2;">Passei Concurso</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Filtro Global de Visão
    opcoes_visao = ["🌐 Toda a Minha Trajetória (Consolidado)"] + [
        f"{c.get('status', '').split(' ')[-1]} {c['name']}" for c in st.session_state.certames
    ]
    # Posiciona DPDF como padrão inicial se ainda não selecionado
    if "visao_global_sel" not in st.session_state:
        st.session_state.visao_global_sel = opcoes_visao[1] if len(opcoes_visao) > 1 else opcoes_visao[0]

    visao_selecionada = st.selectbox(
        "🎯 Certame / Foco em Exibição:",
        opcoes_visao,
        key="visao_global_sel"
    )

    filtro_certame_id = None
    certame_ativo_obj = None

    if visao_selecionada != "🌐 Toda a Minha Trajetória (Consolidado)":
        idx_c = opcoes_visao.index(visao_selecionada) - 1
        certame_ativo_obj = st.session_state.certames[idx_c]
        filtro_certame_id = certame_ativo_obj["id"]
    else:
        st.caption("📊 Exibindo métricas acumuladas de todos os concursos cadastrados.")

    st.divider()

    # Mini Cronômetro / Pomodoro Sincronizado na Sidebar
    @st.fragment(run_every=1.0 if st.session_state.timer_running else None)
    def render_sidebar_timer_fragment():
        is_countdown = (st.session_state.get("timer_mode") == "countdown")
        elapsed_now = get_current_elapsed_seconds()
        is_run = st.session_state.timer_running
        target_secs = st.session_state.get("timer_target_seconds", 1500)
        
        # Se for contagem regressiva e atingiu o tempo
        if is_countdown and is_run and elapsed_now >= target_secs:
            action_pause_timer()
            st.rerun()

        disp_seconds = get_countdown_display_seconds() if is_countdown else elapsed_now
        mode_icon = "🍅 Pomodoro" if is_countdown else "⏱️ Cronômetro"
        
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:600;color:#334155;text-transform:uppercase;letter-spacing:0.04em;'>{mode_icon} Rápido</div>",
            unsafe_allow_html=True
        )
        digits_cls = "sidebar-timer-digits running" if is_run else "sidebar-timer-digits"
        st.markdown(f"<div class='{digits_cls}'>{format_hms(disp_seconds)}</div>", unsafe_allow_html=True)

        col_sb_t1, col_sb_t2 = st.columns(2)
        if not is_run:
            if col_sb_t1.button("▶️ Iniciar", key="sb_start_btn", use_container_width=True):
                action_start_timer()
                st.rerun()
        else:
            if col_sb_t1.button("⏸️ Pausar", key="sb_pause_btn", use_container_width=True):
                action_pause_timer()
                st.rerun()

        if col_sb_t2.button("🔄 Zerar", key="sb_reset_btn", use_container_width=True):
            action_reset_timer()
            st.rerun()

    render_sidebar_timer_fragment()

    st.divider()

    # Status de Sincronização (GitHub & Obsidian)
    gh_cfg = get_github_config()
    cofre_path = st.session_state.get("custom_cofre_path", COFRE_DIR_DEFAULT)
    cofre_conectado = os.path.exists(cofre_path)

    st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#334155;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:0.45rem;'>☁️ Status de Sincronização</div>", unsafe_allow_html=True)
    db_badge = '<span class="pill pill-emerald">🐘 PostgreSQL Ativo</span>' if is_db_connected() else '<span class="pill pill-slate">🐘 Modo JSON Local</span>'
    gh_badge = '<span class="pill pill-emerald">● GitHub Conectado</span>' if gh_cfg["token"] else '<span class="pill pill-rose">○ GitHub Desconectado</span>'
    obs_badge = '<span class="pill pill-indigo">● Cofre Obsidian Ativo</span>' if cofre_conectado else '<span class="pill pill-slate">○ Cofre Desconectado</span>'
    st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:0.35rem;margin-bottom:0.65rem;'>{db_badge}{gh_badge}{obs_badge}</div>", unsafe_allow_html=True)

    col_gh_s1, col_gh_s2 = st.columns(2)
    with col_gh_s1:
        if st.button("📥 Puxar", key="sb_pull", use_container_width=True, help="Baixa sessões do GitHub"):
            with st.spinner("Sincronizando..."):
                ok_p, msg_p = pull_from_github_and_merge()
            if ok_p:
                st.toast(msg_p, icon="✅")
            else:
                st.warning(msg_p)
    with col_gh_s2:
        if st.button("📤 Enviar", key="sb_push", use_container_width=True, help="Envia sessões para o GitHub"):
            with st.spinner("Enviando..."):
                ok_u, msg_u = push_to_github("chore(sync): manual sync from sidebar")
            if ok_u:
                st.toast(msg_u, icon="☁️")
            else:
                st.error(msg_u)

# ==========================================
# 7. PROCESSAMENTO DE DADOS E STREAK
# ==========================================
df_all = pd.DataFrame(st.session_state.sessions)
if not df_all.empty:
    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all["hours"] = df_all["duration_min"] / 60.0
    if "certame_id" not in df_all.columns:
        df_all["certame_id"] = "DPDF"
        df_all["certame_name"] = "DPDF 2026/2027"
    if "study_type" not in df_all.columns:
        df_all["study_type"] = "Geral"
    df_all["study_type"] = df_all["study_type"].fillna("Geral")

if filtro_certame_id is not None and not df_all.empty:
    df = df_all[df_all["certame_id"] == filtro_certame_id].copy()
else:
    df = df_all.copy()

hoje = pd.to_datetime(get_current_date())
inicio_semana = hoje - timedelta(days=hoje.weekday())
inicio_mes = hoje.replace(day=1)

def eh_basica(row):
    blk = str(row.get("block", "")).lower()
    sub = str(row.get("subject", "")).lower()
    return (
        "básico" in blk or "basico" in blk or "gerais" in blk
        or "portuguesa" in sub or "840" in sub or "lodf" in sub
        or "penha" in sub or "socorros" in sub or "mulheres" in sub
    )

def calcular_streak(df_ref):
    """Calcula a sequência atual de dias consecutivos estudados (Streak) e total de dias ativos."""
    if df_ref.empty:
        return 0, 0
    datas_unicas = sorted(set(df_ref["date"].dt.date), reverse=True)
    total_dias_ativos = len(datas_unicas)
    hoje_d = get_current_date()
    ontem_d = hoje_d - timedelta(days=1)

    if datas_unicas[0] < ontem_d:
        return 0, total_dias_ativos

    streak = 0
    cursor = hoje_d if datas_unicas[0] == hoje_d else ontem_d
    datas_set = set(datas_unicas)
    while cursor in datas_set:
        streak += 1
        cursor -= timedelta(days=1)
    return streak, total_dias_ativos

streak_atual, total_dias_estudados = calcular_streak(df_all if not df_all.empty else df)

if not df.empty:
    df["is_basica"] = df.apply(eh_basica, axis=1)
    df["tipo_bloco"] = df["is_basica"].apply(lambda x: "Básicas (Meta: 30%)" if x else "Específicas / Técnicas (Meta: 70%)")

    df_hoje = df[df["date"] == hoje]
    horas_hoje = df_hoje["hours"].sum() if not df_hoje.empty else 0.0
    materias_estudadas_hoje = set(df_hoje["subject"].unique()) if not df_hoje.empty else set()

    df_sem = df[df["date"] >= inicio_semana]
    horas_semana = df_sem["hours"].sum() if not df_sem.empty else 0.0
    horas_mes = df[df["date"] >= inicio_mes]["hours"].sum() if not df[df["date"] >= inicio_mes].empty else 0.0
    horas_total = df["hours"].sum()

    total_q_feitas = int(df["questions_total"].sum())
    total_q_acertos = int(df["questions_correct"].sum())
    taxa_geral = (total_q_acertos / total_q_feitas * 100.0) if total_q_feitas > 0 else 0.0

    # Cálculos 70/30 na semana atual
    horas_esp_sem = df_sem[~df_sem["is_basica"]]["hours"].sum() if not df_sem.empty else 0.0
    horas_bas_sem = df_sem[df_sem["is_basica"]]["hours"].sum() if not df_sem.empty else 0.0
    tot_sem_7030 = horas_esp_sem + horas_bas_sem
    pct_esp_sem = (horas_esp_sem / tot_sem_7030 * 100.0) if tot_sem_7030 > 0 else 0.0
    pct_bas_sem = (horas_bas_sem / tot_sem_7030 * 100.0) if tot_sem_7030 > 0 else 0.0

    # Cálculos 70/30 acumulado geral
    horas_esp_tot = df[~df["is_basica"]]["hours"].sum()
    horas_bas_tot = df[df["is_basica"]]["hours"].sum()
    tot_tot_7030 = horas_esp_tot + horas_bas_tot
    pct_esp_tot = (horas_esp_tot / tot_tot_7030 * 100.0) if tot_tot_7030 > 0 else 0.0
    pct_bas_tot = (horas_bas_tot / tot_tot_7030 * 100.0) if tot_tot_7030 > 0 else 0.0
else:
    horas_hoje = horas_semana = horas_mes = horas_total = 0.0
    materias_estudadas_hoje = set()
    total_q_feitas = total_q_acertos = 0
    taxa_geral = 0.0
    horas_esp_sem = horas_bas_sem = tot_sem_7030 = pct_esp_sem = pct_bas_sem = 0.0
    horas_esp_tot = horas_bas_tot = tot_tot_7030 = pct_esp_tot = pct_bas_tot = 0.0

# Cálculo de dias até a prova
dias_ate_prova = None
data_prova_fmt = "Meta Contínua"
banca_ativa = "Múltiplas Bancas"
cargo_ativo = "Carreira de TI & Controle"
status_ativo = "Visão Consolidada"

target_certame_for_countdown = certame_ativo_obj
if target_certame_for_countdown is None and st.session_state.certames:
    target_certame_for_countdown = st.session_state.certames[0]

if certame_ativo_obj:
    banca_ativa = certame_ativo_obj.get("banca", "A definir")
    cargo_ativo = certame_ativo_obj.get("cargo", "-")
    status_ativo = certame_ativo_obj.get("status", "Ativo")

if target_certame_for_countdown and target_certame_for_countdown.get("exam_date"):
    try:
        dt_p = datetime.strptime(target_certame_for_countdown["exam_date"], "%Y-%m-%d").date()
        dias_ate_prova = (dt_p - get_current_date()).days
        data_prova_fmt = dt_p.strftime("%d/%m/%Y")
    except Exception:
        pass

# ==========================================
# 8. CABEÇALHO PRINCIPAL (HEADER LIMPO)
# ==========================================
if filtro_certame_id is None:
    titulo_header = "Trajetória Consolidada de Estudos"
    sub_header = "Visão analítica integrada de horas líquidas, evolução em questões e equilíbrio 70/30"
    eyebrow_txt = "🌐 PAINEL DE CARREIRA • TODOS OS CERTAMES"
else:
    titulo_header = certame_ativo_obj["name"]
    sub_header = f"{cargo_ativo} • Meta: {certame_ativo_obj.get('weekly_target_hours', 10.0):.0f}h/semana (Regra 70/30)"
    eyebrow_txt = f"🎯 CERTAME EM FOCO • {status_ativo.upper()}"

prova_pill = (
    f'<span class="pill pill-indigo">📅 Prova: {data_prova_fmt} ({dias_ate_prova}d)</span>'
    if (dias_ate_prova is not None and dias_ate_prova >= 0)
    else f'<span class="pill pill-slate">📅 {data_prova_fmt}</span>'
)

st.markdown(f"""
<div class="app-header">
    <div class="header-left">
        <div class="header-eyebrow">{eyebrow_txt}</div>
        <h1 class="header-title">{titulo_header}</h1>
        <p class="header-subtitle">{sub_header}</p>
    </div>
    <div class="header-badges">
        <span class="pill pill-slate">🏛️ Banca: {banca_ativa}</span>
        {prova_pill}
        <span class="pill pill-emerald">⚖️ Ciclo 70/30 Ativo</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 9. ABAS DE NAVEGAÇÃO MODERNAS
# ==========================================
tab_dash, tab_plano, tab_reg, tab_hist, tab_certames = st.tabs([
    "📊 Dashboard & Insights",
    "🗓️ Plano de Estudos (70/30)",
    "⏱️ Registrar Sessão & Cronômetro",
    "📋 Histórico & Gestão",
    "⚙️ Certames & Sincronização"
])

# ------------------------------------------
# ABA 1: DASHBOARD & INSIGHTS
# ------------------------------------------
with tab_dash:
    meta_dia = certame_ativo_obj.get("daily_target_hours", 2.0) if certame_ativo_obj else 2.0
    meta_sem = certame_ativo_obj.get("weekly_target_hours", 10.0) if certame_ativo_obj else 10.0

    prog_sem_pct = min((horas_semana / meta_sem) * 100.0, 100.0) if meta_sem > 0 else 0.0
    prog_dia_pct = min((horas_hoje / meta_dia) * 100.0, 100.0) if meta_dia > 0 else 0.0

    # Status semântico de questões
    if total_q_feitas == 0:
        acc_pill_cls = "pill-slate"
        acc_pill_txt = "Sem questões"
        acc_bar_color = "#94A3B8"
    elif taxa_geral >= 80:
        acc_pill_cls = "pill-emerald"
        acc_pill_txt = "Meta ≥80% Atingida"
        acc_bar_color = "#10B981"
    elif taxa_geral >= 65:
        acc_pill_cls = "pill-amber"
        acc_pill_txt = "Faixa Competitiva"
        acc_bar_color = "#F59E0B"
    else:
        acc_pill_cls = "pill-rose"
        acc_pill_txt = "Abaixo de 65%"
        acc_bar_color = "#F43F5E"

    # 1. KPIs em Destaque no Topo (4 Colunas)
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-top">
                    <span class="kpi-label">🗓️ Horas na Semana</span>
                    <span class="pill pill-indigo">{prog_sem_pct:.0f}% da meta</span>
                </div>
                <div class="kpi-value">{format_hours_mins(horas_semana)} <span style="font-size:0.95rem;font-weight:500;color:#64748B;">/ {format_hours_mins(meta_sem)}</span></div>
            </div>
            <div>
                <div class="kpi-sub">
                    <span>Hoje: <b>{format_hours_mins(horas_hoje, short=True)}</b> (Meta {format_hours_mins(meta_dia, short=True)})</span>
                    <span>Mês: {format_hours_mins(horas_mes, short=True)}</span>
                </div>
                <div class="kpi-bar-bg">
                    <div class="kpi-bar-fill" style="width:{prog_sem_pct:.1f}%;background:#4F46E5;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        streak_pill = "pill-emerald" if streak_atual > 0 else "pill-slate"
        streak_status = "Consistência ativa" if streak_atual > 0 else "Estude hoje p/ iniciar"
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-top">
                    <span class="kpi-label">🔥 Dias Consecutivos</span>
                    <span class="pill {streak_pill}">{streak_status}</span>
                </div>
                <div class="kpi-value">{streak_atual} <span style="font-size:0.95rem;font-weight:500;color:#64748B;">dias seguidos</span></div>
            </div>
            <div>
                <div class="kpi-sub">
                    <span>Dias ativos: <b>{total_dias_estudados}d</b></span>
                    <span>Acumulado: <b>{format_hours_mins(horas_total, short=True)}</b></span>
                </div>
                <div class="kpi-bar-bg">
                    <div class="kpi-bar-fill" style="width:{min(streak_atual * 14.2, 100):.1f}%;background:#10B981;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-top">
                    <span class="kpi-label">🎯 Média de Acertos</span>
                    <span class="pill {acc_pill_cls}">{acc_pill_txt}</span>
                </div>
                <div class="kpi-value">{taxa_geral:.1f}% <span style="font-size:0.95rem;font-weight:500;color:#64748B;">({total_q_acertos}/{total_q_feitas})</span></div>
            </div>
            <div>
                <div class="kpi-sub">
                    <span>Questões feitas: <b>{total_q_feitas}</b></span>
                    <span>Alvo: <b>80%+</b></span>
                </div>
                <div class="kpi-bar-bg">
                    <div class="kpi-bar-fill" style="width:{min(taxa_geral, 100):.1f}%;background:{acc_bar_color};"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        if dias_ate_prova is not None and dias_ate_prova >= 0:
            semanas_rest = dias_ate_prova / 7.0
            horas_proj = int(semanas_rest * meta_sem)
            st.markdown(f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-top">
                        <span class="kpi-label">⏳ Contagem Regressiva</span>
                        <span class="pill pill-indigo">{data_prova_fmt}</span>
                    </div>
                    <div class="kpi-value">{dias_ate_prova} <span style="font-size:0.95rem;font-weight:500;color:#64748B;">dias até a prova</span></div>
                </div>
                <div>
                    <div class="kpi-sub">
                        <span>~{semanas_rest:.1f} semanas úteis</span>
                        <span>Orçamento: <b>~{horas_proj}h</b></span>
                    </div>
                    <div class="kpi-bar-bg">
                        <div class="kpi-bar-fill" style="width:{prog_dia_pct:.1f}%;background:#6366F1;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="kpi-card">
                <div>
                    <div class="kpi-top">
                        <span class="kpi-label">⏳ Ritmo Diário</span>
                        <span class="pill pill-indigo">{prog_dia_pct:.0f}% hoje</span>
                    </div>
                    <div class="kpi-value">{format_hours_mins(horas_hoje)} <span style="font-size:0.95rem;font-weight:500;color:#64748B;">/ {format_hours_mins(meta_dia)} hoje</span></div>
                </div>
                <div>
                    <div class="kpi-sub">
                        <span>Meta diária: <b>{format_hours_mins(meta_dia, short=True)}</b></span>
                        <span>Meta semanal: <b>{format_hours_mins(meta_sem, short=True)}</b></span>
                    </div>
                    <div class="kpi-bar-bg">
                        <div class="kpi-bar-fill" style="width:{prog_dia_pct:.1f}%;background:#6366F1;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # 2. Bloco "Foco de Hoje" + Termômetro 70/30 (Donut + Barra Segmentada)
    dia_idx_hoje = get_current_date().weekday()
    item_hoje = PLANO_SEMANAL_DPDF[dia_idx_hoje]

    col_foco, col_term = st.columns([1.35, 1.0])

    with col_foco:
        with st.container(border=True):
            b1_done = (item_hoje["bloco_1_materia"] in materias_estudadas_hoje) or (f"{dia_idx_hoje}_b1" in st.session_state.completed_blocks_today)
            b2_done = (item_hoje["bloco_2_materia"] in materias_estudadas_hoje) or (f"{dia_idx_hoje}_b2" in st.session_state.completed_blocks_today)

            status_hoje_badge = (
                '<span class="pill pill-emerald">✅ Meta de Hoje Concluída!</span>'
                if (b1_done and b2_done)
                else ('<span class="pill pill-indigo">⚡ 1 de 2 Blocos Concluídos</span>' if (b1_done or b2_done) else '<span class="pill pill-slate">📅 Programação do Dia</span>')
            )

            st.markdown(f"""
            <div class="section-title">
                <span>🎯 Foco de Hoje — {item_hoje['dia']}</span>
                {status_hoje_badge}
            </div>
            """, unsafe_allow_html=True)

            b1_pill_cls = "pill-emerald" if b1_done else "pill-indigo"
            b1_pill_txt = "✅ Concluído" if b1_done else f"Bloco 1 • {item_hoje['bloco_1_horas']:.0f}h • {item_hoje['bloco_1_tipo']}"

            b2_cls_box = "basica" if "Básica" in item_hoje["bloco_2_tipo"] else ("discursiva" if "Discursiva" in item_hoje["bloco_2_tipo"] else "")
            b2_pill_cls = "pill-emerald" if b2_done else ("pill-emerald" if "Básica" in item_hoje["bloco_2_tipo"] else "pill-indigo")
            b2_pill_txt = "✅ Concluído" if b2_done else f"Bloco 2 • {item_hoje['bloco_2_horas']:.0f}h • {item_hoje['bloco_2_tipo']}"

            st.markdown(f"""
            <div class="block-item">
                <div class="block-item-header">
                    <span class="block-subject">1️⃣ {item_hoje['bloco_1_materia']}</span>
                    <span class="pill {b1_pill_cls}">{b1_pill_txt}</span>
                </div>
                <p class="block-topic">📌 {item_hoje['bloco_1_topico']}</p>
            </div>
            <div class="block-item {b2_cls_box}">
                <div class="block-item-header">
                    <span class="block-subject">2️⃣ {item_hoje['bloco_2_materia']}</span>
                    <span class="pill {b2_pill_cls}">{b2_pill_txt}</span>
                </div>
                <p class="block-topic">📌 {item_hoje['bloco_2_topico']}</p>
            </div>
            <div style="font-size:0.8rem;color:#475569;background:#F8FAFC;padding:0.5rem 0.75rem;border-radius:8px;border:1px dashed #CBD5E1;margin-top:0.4rem;">
                💡 <b>Diretriz Metodológica:</b> {item_hoje['foco']}
            </div>
            """, unsafe_allow_html=True)

    with col_term:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title">
                <span>⚖️ Termômetro da Regra 70/30 (Semana)</span>
                <span class="pill pill-slate">Alvo: 7h Esp / 3h Bás</span>
            </div>
            """, unsafe_allow_html=True)

            c_d1, c_d2 = st.columns([1.05, 1.15])
            with c_d1:
                fig_d7030 = create_donut_7030(horas_esp_sem, horas_bas_sem, label_center="Específicas")
                st.plotly_chart(fig_d7030, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_donut_7030")

            with c_d2:
                esp_w = pct_esp_sem if tot_sem_7030 > 0 else 70.0
                bas_w = pct_bas_sem if tot_sem_7030 > 0 else 30.0
                st.markdown(f"""
                <div style="padding-top:0.35rem;">
                    <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.2rem;">
                        <span style="color:#4F46E5;font-weight:600;">● Específicas ({pct_esp_sem:.0f}%)</span>
                        <span style="color:#0F172A;font-weight:600;">{format_hours_mins(horas_esp_sem, short=True)} <span style="color:#64748B;font-weight:400;">/ 7h</span></span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.45rem;">
                        <span style="color:#059669;font-weight:600;">● Básicas ({pct_bas_sem:.0f}%)</span>
                        <span style="color:#0F172A;font-weight:600;">{format_hours_mins(horas_bas_sem, short=True)} <span style="color:#64748B;font-weight:400;">/ 3h</span></span>
                    </div>
                    <div class="seg-bar-wrap">
                        <div class="seg-bar-track">
                            <div class="seg-bar-esp" style="width:{esp_w:.1f}%;"></div>
                            <div class="seg-bar-bas" style="width:{bas_w:.1f}%;"></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#64748B;margin-top:0.2rem;">
                            <span>0%</span>
                            <span>Meta Ideal: 70% / 30%</span>
                            <span>100%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if tot_sem_7030 == 0:
                    st.caption("Registre sua primeira sessão da semana para calibrar o termômetro.")
                elif 60 <= pct_esp_sem <= 80:
                    st.markdown('<span class="pill pill-emerald" style="width:100%;justify-content:center;">✅ Equilíbrio 70/30 dentro da faixa ideal!</span>', unsafe_allow_html=True)
                elif pct_esp_sem > 80:
                    st.markdown('<span class="pill pill-amber" style="width:100%;justify-content:center;">⚠️ Lembre-se de reservar 30% às Básicas</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="pill pill-indigo" style="width:100%;justify-content:center;">🎯 Priorize Específicas (75,7% dos pontos)</span>', unsafe_allow_html=True)

    # 3. Grid 2x2 de Gráficos Minimalistas
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title">
                <span>📈 Evolução Temporal & Consistência (Últimos 14 Dias)</span>
                <span class="pill pill-indigo">Curva de Rendimento</span>
            </div>
            """, unsafe_allow_html=True)
            fig_evol = create_spline_evolution(df, hoje, meta_dia)
            st.plotly_chart(fig_evol, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_evol")

    with col_g2:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title">
                <span>🎯 Taxa de Acerto & Faixa de Segurança</span>
                <span class="pill pill-emerald">Meta: 80%+</span>
            </div>
            """, unsafe_allow_html=True)
            if df.empty or total_q_feitas == 0:
                fig_gauge = create_accuracy_gauge(0.0, 0, meta=80.0)
                st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_gauge_empty")
                st.caption("Resolva questões e registre os acertos para visualizar seu velocímetro de segurança e o ranking por disciplina.")
            else:
                cg_left, cg_right = st.columns([0.95, 1.25])
                with cg_left:
                    fig_gauge = create_accuracy_gauge(taxa_geral, total_q_feitas, meta=80.0)
                    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_gauge_full")
                with cg_right:
                    fig_acc_sub = create_subject_accuracy_bars(df)
                    if fig_acc_sub:
                        st.plotly_chart(fig_acc_sub, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_acc_sub")

    if not df.empty:
        col_g3, col_g4 = st.columns(2)

        with col_g3:
            with st.container(border=True):
                st.markdown("""
                <div class="section-title">
                    <span>📖 Horas Líquidas & Aproveitamento por Disciplina</span>
                    <span class="pill pill-slate">Top Disciplinas</span>
                </div>
                """, unsafe_allow_html=True)
                fig_sub_bars = create_subject_bars(df)
                st.plotly_chart(fig_sub_bars, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_sub_bars")

        with col_g4:
            with st.container(border=True):
                st.markdown("""
                <div class="section-title">
                    <span>🏷️ Distribuição por Modalidade de Estudo</span>
                    <span class="pill pill-slate">Formato de Estudo</span>
                </div>
                """, unsafe_allow_html=True)
                fig_mod_bars = create_modality_bars(df)
                st.plotly_chart(fig_mod_bars, use_container_width=True, config={"displayModeBar": False}, key="chart_dash_mod_bars")

# ------------------------------------------
# ABA 2: PLANO DE ESTUDOS (GRADE 70/30)
# ------------------------------------------
with tab_plano:
    # 1. Comparativo Semana vs Trajetória Acumulada
    col_p_top1, col_p_top2 = st.columns(2)

    with col_p_top1:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title">
                <span>🗓️ Equilíbrio 70/30 na Semana Atual</span>
                <span class="pill pill-indigo">Meta: 7,0h Esp • 3,0h Bás</span>
            </div>
            """, unsafe_allow_html=True)
            cp1, cp2 = st.columns([1, 1.2])
            with cp1:
                st.plotly_chart(create_donut_7030(horas_esp_sem, horas_bas_sem, "Semanal"), use_container_width=True, config={"displayModeBar": False}, key="chart_plan_donut_sem")
            with cp2:
                st.markdown(f"""
                <div style="padding-top:0.5rem;font-size:0.85rem;color:#334155;">
                    <p style="margin-bottom:0.4rem;">🔹 <b>Específicas (Peso 2 + Discursivas):</b> <br><code>{format_hours_mins(horas_esp_sem)}</code> realizadas de <code>7 horas</code> ({pct_esp_sem:.1f}%)</p>
                    <p style="margin-bottom:0.4rem;">🔸 <b>Conhecimentos Básicos (Peso 1):</b> <br><code>{format_hours_mins(horas_bas_sem)}</code> realizadas de <code>3 horas</code> ({pct_bas_sem:.1f}%)</p>
                    <p style="margin-bottom:0;color:#64748B;font-size:0.78rem;">Total na semana: <b>{format_hours_mins(tot_sem_7030)}</b> líquidas</p>
                </div>
                """, unsafe_allow_html=True)

    with col_p_top2:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title">
                <span>🌐 Equilíbrio 70/30 no Acumulado Geral</span>
                <span class="pill pill-emerald">Histórico Consolidado</span>
            </div>
            """, unsafe_allow_html=True)
            cp3, cp4 = st.columns([1, 1.2])
            with cp3:
                st.plotly_chart(create_donut_7030(horas_esp_tot, horas_bas_tot, "Acumulado"), use_container_width=True, config={"displayModeBar": False}, key="chart_plan_donut_tot")
            with cp4:
                st.markdown(f"""
                <div style="padding-top:0.5rem;font-size:0.85rem;color:#334155;">
                    <p style="margin-bottom:0.4rem;">🔹 <b>Total em Específicas:</b> <br><code>{format_hours_mins(horas_esp_tot)}</code> acumuladas ({pct_esp_tot:.1f}%)</p>
                    <p style="margin-bottom:0.4rem;">🔸 <b>Total em Básicas:</b> <br><code>{format_hours_mins(horas_bas_tot)}</code> acumuladas ({pct_bas_tot:.1f}%)</p>
                    <p style="margin-bottom:0;color:#64748B;font-size:0.78rem;">Total acumulado no filtro: <b>{format_hours_mins(tot_tot_7030)}</b></p>
                </div>
                """, unsafe_allow_html=True)

    with st.expander("⚖️ A Matemática da Aprovação — Por que 70% Específicas e 30% Básicas na DPDF?", expanded=False):
        c_mat1, c_mat2 = st.columns([1.2, 1.0])
        with c_mat1:
            st.markdown("""
            A pontuação máxima do certame **DPDF (Analista de TI — Redes)** é de **169,0 pontos**:
            - **Conhecimentos Específicos (Objetiva):** 49 questões × peso 2 = **98,0 pontos** (58,0% da nota total)
            - **3 Questões Discursivas Técnicas de TI:** 3 × 10 = **30,0 pontos** (17,8% da nota total)
            - **Núcleo Técnico Somado:** **128,0 de 169,0 pontos (75,7% de todo o concurso!)**
            - **1 Dissertação Geral:** **20,0 pontos** (11,8%)
            - **Conhecimentos Básicos (Objetiva):** 21 questões × peso 1 = **21,0 pontos** (12,4%)
            """)
        with c_mat2:
            st.info("""
            **🎯 Diretriz Tática (Regra 70/30):**
            Dedicar **7h/semana** às matérias técnicas (onde cada acerto vale o dobro e sustenta as 3 discursivas) e **3h/semana** de estudo cirúrgico em Básicas (LC 840, LODF/LC 828, Maria da Penha e Português) para superar com folga o corte de 50%.
            """)

    st.write("")
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">
        <div>
            <h3 style="margin:0;font-size:1.1rem;font-weight:700;color:#0F172A;">📅 Grade Semanal de Estudos (Segunda a Domingo)</h3>
            <p style="margin:0;font-size:0.82rem;color:#64748B;">Ciclo de 2h diárias dividido em Bloco 1 (1h) e Bloco 2 (1h). Marque os blocos concluídos hoje para acompanhar seu progresso!</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Cartões Limpos por Dia em Grid (2 colunas para Segunda a Sábado, card inteiro para Domingo)
    dia_atual_idx = get_current_date().weekday()

    for row_start in range(0, 6, 2):
        cols_dias = st.columns(2)
        for offset in range(2):
            idx_item = row_start + offset
            item = PLANO_SEMANAL_DPDF[idx_item]
            is_hoje = (item["dia_idx"] == dia_atual_idx)

            b1_auto = is_hoje and (item["bloco_1_materia"] in materias_estudadas_hoje)
            b2_auto = is_hoje and (item["bloco_2_materia"] in materias_estudadas_hoje)
            b1_checked = b1_auto or (f"{idx_item}_b1" in st.session_state.completed_blocks_today)
            b2_checked = b2_auto or (f"{idx_item}_b2" in st.session_state.completed_blocks_today)
            dia_concluido = b1_checked and b2_checked

            with cols_dias[offset]:
                with st.container(border=True):
                    if dia_concluido:
                        top_badge = '<span class="pill pill-emerald">✅ Concluído hoje!</span>'
                    elif is_hoje:
                        top_badge = '<span class="pill pill-indigo">🔥 Dia de Hoje</span>'
                    else:
                        top_badge = f'<span class="pill pill-slate">{item["bloco_1_horas"] + item["bloco_2_horas"]:.0f}h previstas</span>'

                    st.markdown(f"""
                    <div class="section-title">
                        <span style="font-size:1rem;font-weight:700;color:{'#4F46E5' if is_hoje else '#0F172A'};">{item['dia']}</span>
                        {top_badge}
                    </div>
                    <div class="block-item">
                        <div class="block-item-header">
                            <span class="block-subject">{item['bloco_1_materia']}</span>
                            <span class="pill pill-indigo">Bloco 1 • {item['bloco_1_horas']:.0f}h • {item['bloco_1_tipo']}</span>
                        </div>
                        <p class="block-topic">{item['bloco_1_topico']}</p>
                    </div>
                    <div class="block-item {'basica' if 'Básica' in item['bloco_2_tipo'] else ('discursiva' if 'Discursiva' in item['bloco_2_tipo'] else '')}">
                        <div class="block-item-header">
                            <span class="block-subject">{item['bloco_2_materia']}</span>
                            <span class="pill {'pill-emerald' if 'Básica' in item['bloco_2_tipo'] else 'pill-indigo'}">Bloco 2 • {item['bloco_2_horas']:.0f}h • {item['bloco_2_tipo']}</span>
                        </div>
                        <p class="block-topic">{item['bloco_2_topico']}</p>
                    </div>
                    <div style="font-size:0.76rem;color:#64748B;margin-top:0.25rem;margin-bottom:0.35rem;">
                        🎯 <b>Foco:</b> {item['foco']}
                    </div>
                    """, unsafe_allow_html=True)

                    if is_hoje:
                        chk_c1, chk_c2 = st.columns(2)
                        with chk_c1:
                            c1_val = st.checkbox("Concluir Bloco 1", value=b1_checked, key=f"chk_plan_{idx_item}_b1")
                            if c1_val != (f"{idx_item}_b1" in st.session_state.completed_blocks_today):
                                if c1_val:
                                    st.session_state.completed_blocks_today.add(f"{idx_item}_b1")
                                else:
                                    st.session_state.completed_blocks_today.discard(f"{idx_item}_b1")
                                db_set_completed_block(str(hoje), f"{idx_item}_b1", c1_val)
                        with chk_c2:
                            c2_val = st.checkbox("Concluir Bloco 2", value=b2_checked, key=f"chk_plan_{idx_item}_b2")
                            if c2_val != (f"{idx_item}_b2" in st.session_state.completed_blocks_today):
                                if c2_val:
                                    st.session_state.completed_blocks_today.add(f"{idx_item}_b2")
                                else:
                                    st.session_state.completed_blocks_today.discard(f"{idx_item}_b2")
                                db_set_completed_block(str(hoje), f"{idx_item}_b2", c2_val)

                        if c1_val and c2_val:
                            st.markdown('<div style="background:#ECFDF5;border:1px solid #A7F3D0;color:#059669;padding:0.4rem 0.7rem;border-radius:8px;font-size:0.78rem;font-weight:600;text-align:center;">🎉 Excelente! Os dois blocos de hoje foram concluídos com consistência!</div>', unsafe_allow_html=True)

    # Card de Domingo + Fases da Preparação
    item_dom = PLANO_SEMANAL_DPDF[6]
    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
            <div>
                <span style="font-weight:700;color:#0F172A;">🌿 {item_dom['dia']} — {item_dom['bloco_1_materia']} & {item_dom['bloco_2_materia']}</span>
                <span style="font-size:0.82rem;color:#64748B;margin-left:0.6rem;">• {item_dom['foco']}</span>
            </div>
            <span class="pill pill-slate">Recuperação & Planejamento</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.markdown("<h3 style='margin:0.4rem 0 0.6rem 0;font-size:1.05rem;font-weight:700;color:#0F172A;'>🚀 Fases da Preparação até 21/02/2027</h3>", unsafe_allow_html=True)
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title"><span>🧱 Fase 1: Edificação</span><span class="pill pill-indigo">Sem 1–8 • Nov/Dez</span></div>
            <ul style="font-size:0.82rem;color:#334155;padding-left:1.1rem;margin:0;">
                <li>Fechar núcleos densos de Redes, Linux, Windows Server e Segurança.</li>
                <li>Varrer LC 840/2011, LODF/LC 828 e Maria da Penha.</li>
                <li>Treinar 1 questão discursiva técnica toda sexta-feira.</li>
            </ul>
            """, unsafe_allow_html=True)
    with cf2:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title"><span>⚡ Fase 2: Intensiva</span><span class="pill pill-amber">Sem 9–13 • Jan/2027</span></div>
            <ul style="font-size:0.82rem;color:#334155;padding-left:1.1rem;margin:0;">
                <li>Baterias intensivas da banca Instituto ACCESS e bancas similares.</li>
                <li>Simulação de discursivas sob cronômetro (3 questões técnicas + dissertação).</li>
                <li>Alimentação ativa do Caderno de Erros no Obsidian.</li>
            </ul>
            """, unsafe_allow_html=True)
    with cf3:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title"><span>🎯 Fase 3: Reta Final</span><span class="pill pill-emerald">Sem 14–16 • Fev/2027</span></div>
            <ul style="font-size:0.82rem;color:#334155;padding-left:1.1rem;margin:0;">
                <li>Revisão atômica focada exclusivamente nos pontos críticos e prazos.</li>
                <li>2 simulados completos nos horários oficiais (manhã 4h30 / tarde 3h).</li>
                <li>Ajuste fino de redação e artigos de corte.</li>
            </ul>
            """, unsafe_allow_html=True)

# ------------------------------------------
# ABA 3: REGISTRAR SESSÃO & CRONÔMETRO
# ------------------------------------------
with tab_reg:
    # Feedback persistente de sessão salva
    if st.session_state.get("feedback_registro"):
        fb = st.session_state["feedback_registro"]
        if fb.get("status") == "success":
            st.success(fb.get("mensagem", "Sessão salva com sucesso!"))
            st.toast(fb.get("toast", "✅ Estudo salvo com sucesso!"), icon="🎉")
        elif fb.get("status") == "warning":
            st.warning(fb.get("mensagem", "Sessão registrada com ressalvas."))
        elif fb.get("status") == "error":
            st.error(fb.get("mensagem", "Erro ao salvar a sessão."))
        del st.session_state["feedback_registro"]

    gh_cfg_status = get_github_config()
    if not is_db_connected() and not cofre_conectado and not gh_cfg_status["token"]:
        st.warning(
            "⚠️ **Atenção: Modo Nuvem Volátil (Sem Persistência)** — "
            "Este aplicativo está rodando na nuvem sem conexão de escrita com o GitHub ou PostgreSQL. "
            "Qualquer sessão registrada agora será **perdida se o servidor reiniciar ou for atualizado**. "
            "Para salvar seus estudos permanentemente, configure o **PostgreSQL (Supabase)** ou `GITHUB_TOKEN` nos Secrets do Streamlit Cloud "
            "(veja o passo a passo na aba **⚙️ Certames & Sincronização**) ou execute o app localmente no seu computador via `iniciar_estudos.bat`."
        )

    # 1. Cronômetro / Pomodoro Visualmente Centralizado e Imersivo
    @st.fragment(run_every=1.0 if st.session_state.timer_running else None)
    def render_immersive_timer():
        is_countdown = (st.session_state.get("timer_mode") == "countdown")
        elapsed_now = get_current_elapsed_seconds()
        is_run = st.session_state.timer_running
        target_secs = st.session_state.get("timer_target_seconds", 1500)
        
        # Auto-conclusão do Pomodoro se o tempo esgotou
        pomodoro_finished = False
        if is_countdown and is_run and elapsed_now >= target_secs:
            action_pause_timer()
            pomodoro_finished = True
            st.rerun()
        
        # Heartbeat a cada ~5 segundos durante a execução para salvar progresso contínuo
        if is_run and st.session_state.timer_start:
            now_ts = time.time()
            last_hb = st.session_state.get("_timer_last_hb_ts", 0)
            if now_ts - last_hb >= 5.0:
                st.session_state["_timer_last_hb_ts"] = now_ts
                st_ts = st.session_state.timer_start.timestamp()
                db_save_active_timer(True, st_ts, elapsed_now, now_ts)

        # Seletor de Modo & Presets
        col_m1, col_m2 = st.columns([1.5, 3])
        with col_m1:
            modo_opcao = st.radio(
                "Modo de Marcação:",
                options=["⏱️ Cronômetro Progressivo", "🍅 Pomodoro / Regressivo"],
                index=1 if is_countdown else 0,
                horizontal=True,
                key="timer_mode_radio"
            )
            novo_modo = "countdown" if "Pomodoro" in modo_opcao else "countup"
            if novo_modo != st.session_state.get("timer_mode"):
                st.session_state.timer_mode = novo_modo
                action_reset_timer()
                st.rerun()

        with col_m2:
            if novo_modo == "countdown":
                sub_p1, sub_p2 = st.columns([2, 1.2])
                with sub_p1:
                    preset = st.radio(
                        "Tempo Foco:",
                        options=["25 min (Clássico)", "50 min (Longo)", "90 min (Avançado)", "Customizado"],
                        index=0 if target_secs == 1500 else (1 if target_secs == 3000 else (2 if target_secs == 5400 else 3)),
                        horizontal=True,
                        key="pomodoro_preset_radio"
                    )
                    preset_map = {
                        "25 min (Clássico)": 1500,
                        "50 min (Longo)": 3000,
                        "90 min (Avançado)": 5400
                    }
                    if preset in preset_map:
                        novo_target = preset_map[preset]
                        if novo_target != target_secs:
                            st.session_state.timer_target_seconds = novo_target
                            action_reset_timer()
                            st.rerun()
                with sub_p2:
                    if preset == "Customizado":
                        custom_m = st.number_input("Minutos:", min_value=1, max_value=360, value=max(1, target_secs // 60), step=5, key="pomo_custom_min")
                        if custom_m * 60 != target_secs:
                            st.session_state.timer_target_seconds = int(custom_m * 60)
                            action_reset_timer()
                            st.rerun()
            else:
                st.markdown("<div style='font-size:0.8rem;color:#64748B;padding-top:1.6rem;'>Conta o tempo livre de estudo progressivamente e transfere para a sessão ao pausar.</div>", unsafe_allow_html=True)

        # Display do tempo
        if is_countdown:
            disp_seconds = get_countdown_display_seconds()
            pct_progresso = min(1.0, max(0.0, elapsed_now / target_secs)) if target_secs > 0 else 0.0
            if is_run:
                status_pill = f'<span class="pill pill-emerald">● Pomodoro em andamento ({int(pct_progresso * 100)}%)</span>'
            elif elapsed_now >= target_secs:
                status_pill = '<span class="pill pill-emerald">🎉 Pomodoro Concluído! Tempo aplicado ao formulário</span>'
            elif elapsed_now > 0:
                status_pill = '<span class="pill pill-amber">⏸️ Pomodoro Pausado</span>'
            else:
                status_pill = f'<span class="pill pill-indigo">🍅 Pomodoro de {target_secs // 60} minutos pronto</span>'
            digits_cls = "timer-digits running" if is_run else "timer-digits"
            sub_info = f"Tempo restante do bloco de {target_secs // 60} minutos. Ao terminar, preenche a duração da sessão."
        else:
            disp_seconds = elapsed_now
            status_pill = (
                '<span class="pill pill-emerald">● Cronômetro em andamento</span>'
                if is_run
                else ('<span class="pill pill-amber">⏸️ Pausado — Tempo transferido ao formulário</span>' if elapsed_now > 0 else '<span class="pill pill-slate">⏱️ Pronto para iniciar sessão</span>')
            )
            digits_cls = "timer-digits running" if is_run else "timer-digits"
            sub_info = "Ao pausar, os minutos cronometrados preenchem automaticamente a duração da sessão abaixo."

        st.markdown(f"""
        <div class="timer-container">
            <div>{status_pill}</div>
            <div class="{digits_cls}">{format_hms(disp_seconds)}</div>
            <div style="font-size:0.78rem;color:#64748B;">{sub_info}</div>
        </div>
        """, unsafe_allow_html=True)

        if is_countdown:
            st.progress(pct_progresso)

        _, ct1, ct2, ct3, _ = st.columns([1.4, 1.1, 1.1, 1.1, 1.4])
        with ct1:
            if not is_run:
                btn_label = "▶️ Iniciar Bloco" if is_countdown else "▶️ Iniciar / Retomar"
                if st.button(btn_label, key="main_timer_start", type="primary", use_container_width=True):
                    action_start_timer()
                    st.rerun()
            else:
                btn_label = "⏸️ Pausar Bloco" if is_countdown else "⏸️ Pausar & Aplicar"
                if st.button(btn_label, key="main_timer_pause", type="primary", use_container_width=True):
                    action_pause_timer()
                    st.rerun()
        with ct2:
            effective_time = min(elapsed_now, target_secs) if is_countdown else elapsed_now
            if st.button("📥 Usar Tempo Agora", key="main_timer_apply", use_container_width=True, disabled=(elapsed_now == 0)):
                sync_timer_to_form_inputs(effective_time)
                st.rerun()
        with ct3:
            reset_lbl = "🔄 Reiniciar Bloco" if is_countdown else "🔄 Zerar Cronômetro"
            if st.button(reset_lbl, key="main_timer_reset", use_container_width=True):
                action_reset_timer()
                st.rerun()

    render_immersive_timer()

    st.write("")

    # 2. Formulário de Registro em Cartão Limpo e Reativo
    with st.container(border=True):
        st.markdown("""
        <div class="section-title">
            <span>📝 Dados da Sessão de Estudo</span>
            <span class="pill pill-indigo">Cascateamento Reativo & Cálculo em Tempo Real</span>
        </div>
        """, unsafe_allow_html=True)

        # Linha 1 de Seletores: Certame, Tipo de Matéria (Bloco) e Disciplina
        opcoes_certames_form = {c["id"]: c["name"] for c in st.session_state.certames}
        idx_default = 0
        if filtro_certame_id and filtro_certame_id in opcoes_certames_form:
            idx_default = list(opcoes_certames_form.keys()).index(filtro_certame_id)

        col_sel1, col_sel2, col_sel3 = st.columns([1.1, 1.1, 1.3])
        with col_sel1:
            certame_escolhido_id = st.selectbox(
                "🏛️ Certame Alvo:",
                options=list(opcoes_certames_form.keys()),
                format_func=lambda x: opcoes_certames_form[x],
                index=idx_default,
                key="reg_certame_id"
            )

        c_obj_form = next((c for c in st.session_state.certames if c["id"] == certame_escolhido_id), st.session_state.certames[0])
        blocos_disponiveis = list(c_obj_form.get("subjects", {}).keys())

        with col_sel2:
            bloco_selecionado = st.selectbox(
                "📂 Tipo de Matéria / Bloco:",
                blocos_disponiveis if blocos_disponiveis else ["Geral"],
                key=f"reg_bloco_{certame_escolhido_id}"
            )

        raw_disciplinas = c_obj_form.get("subjects", {}).get(bloco_selecionado, {})
        if isinstance(raw_disciplinas, dict):
            materias_disponiveis = list(raw_disciplinas.keys())
        elif isinstance(raw_disciplinas, list):
            materias_disponiveis = raw_disciplinas
        else:
            materias_disponiveis = ["Geral"]

        with col_sel3:
            disciplina_selecionada = st.selectbox(
                "📖 Disciplina:",
                materias_disponiveis if materias_disponiveis else ["Geral"],
                key=f"reg_disc_{certame_escolhido_id}_{bloco_selecionado}"
            )

        # Linha 2: Tópico Oficial (com busca rápida), Complemento/Manual, Modalidade e Data
        topicos_disponiveis = []
        if isinstance(raw_disciplinas, dict):
            topicos_cand = raw_disciplinas.get(disciplina_selecionada, [])
            if isinstance(topicos_cand, list):
                topicos_disponiveis = topicos_cand

        col_top_a, col_top_b, col_mod, col_dt = st.columns([1.5, 1.0, 1.0, 0.8])
        with col_top_a:
            if topicos_disponiveis:
                topico_escolhido = st.selectbox(
                    "📌 Tópico do Edital (digite p/ filtrar):",
                    options=topicos_disponiveis + ["✏️ Outro (digitar manualmente)"],
                    key=f"reg_top_sel_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}"
                )
            else:
                topico_escolhido = "✏️ Outro (digitar manualmente)"
                st.text_input(
                    "📌 Tópico Específico:",
                    value=disciplina_selecionada,
                    disabled=True,
                    key=f"reg_top_placeholder_{certame_escolhido_id}"
                )

        with col_top_b:
            if topico_escolhido == "✏️ Outro (digitar manualmente)":
                topico_custom = st.text_input(
                    "✏️ Tópico Personalizado:",
                    key=f"reg_top_custom_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}",
                    placeholder="Ex: Bateria de questões comentadas"
                )
                topico_final = topico_custom.strip() if topico_custom.strip() else disciplina_selecionada
            else:
                complemento = st.text_input(
                    "➕ Complemento (opcional):",
                    key=f"reg_top_comp_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}",
                    placeholder="Ex: Art. 1º ao 35, resumo..."
                )
                topico_final = f"{topico_escolhido} — {complemento.strip()}" if complemento.strip() else topico_escolhido

        with col_mod:
            tipo_estudo_selecionado = st.selectbox(
                "🏷️ Modalidade:",
                options=st.session_state.study_types,
                key=f"reg_tipo_estudo_{certame_escolhido_id}"
            )

        with col_dt:
            data_sessao = st.date_input("📅 Data:", value=get_current_date(), key="reg_data_sessao")

        st.divider()

        # Linha 3: Duração & Questões com Cálculo Automático em Tempo Real
        minutos_cron_atual = get_current_elapsed_seconds() // 60
        if "reg_dur_horas" not in st.session_state:
            st.session_state["reg_dur_horas"] = (minutos_cron_atual // 60) if minutos_cron_atual > 0 else 1
        if "reg_dur_minutos" not in st.session_state:
            st.session_state["reg_dur_minutos"] = (minutos_cron_atual % 60) if minutos_cron_atual > 0 else 0

        c_h, c_m, c_q1, c_q2, c_calc = st.columns([0.8, 0.8, 0.9, 0.9, 1.4])
        with c_h:
            dur_horas = st.number_input("⏱️ Horas:", min_value=0, max_value=24, step=1, key="reg_dur_horas")
        with c_m:
            dur_minutos = st.number_input("⏱️ Minutos:", min_value=0, max_value=59, step=5, key="reg_dur_minutos")
        with c_q1:
            q_total = st.number_input("🎯 Total Questões:", min_value=0, max_value=500, value=0, step=1, key="reg_q_total")
        with c_q2:
            q_corretas = st.number_input("✅ Acertos:", min_value=0, max_value=500, value=0, step=1, key="reg_q_corretas")

        duracao_total_min = (int(dur_horas) * 60) + int(dur_minutos)
        dur_str = f"{dur_horas}h {dur_minutos:02d}min" if dur_horas > 0 else f"{dur_minutos} min"

        with c_calc:
            if q_total > 0 and q_corretas <= q_total:
                acc_live = (q_corretas / q_total) * 100.0
                if acc_live >= 80:
                    bg_c, bd_c, tx_c, st_txt = "#ECFDF5", "#A7F3D0", "#059669", "🟢 Excelente (≥80%)"
                elif acc_live >= 65:
                    bg_c, bd_c, tx_c, st_txt = "#FFFBEB", "#FDE68A", "#D97706", "🟡 Competitivo (65–79%)"
                else:
                    bg_c, bd_c, tx_c, st_txt = "#FFF1F2", "#FECDD3", "#E11D48", "🔴 Reforçar (<65%)"
                st.markdown(f"""
                <div style="background:{bg_c};border:1px solid {bd_c};border-radius:10px;padding:0.45rem 0.75rem;text-align:center;">
                    <div style="font-size:0.7rem;font-weight:600;color:{tx_c};text-transform:uppercase;">{st_txt}</div>
                    <div style="font-size:1.25rem;font-weight:700;color:{tx_c};line-height:1.2;">{acc_live:.1f}% <span style="font-size:0.78rem;font-weight:500;">({q_corretas}/{q_total})</span></div>
                    <div style="font-size:0.72rem;color:#475569;">Tempo líquido: <b>{dur_str}</b></div>
                </div>
                """, unsafe_allow_html=True)
            elif q_total > 0 and q_corretas > q_total:
                st.markdown("""
                <div style="background:#FFF1F2;border:1px solid #FECDD3;border-radius:10px;padding:0.55rem 0.75rem;text-align:center;color:#E11D48;font-size:0.8rem;font-weight:600;">
                    ⚠️ Acertos maior que o total de questões!
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:0.5rem 0.75rem;text-align:center;">
                    <div style="font-size:0.7rem;font-weight:600;color:#64748B;text-transform:uppercase;">Resumo da Sessão</div>
                    <div style="font-size:1.15rem;font-weight:700;color:#0F172A;line-height:1.25;">{dur_str} <span style="font-size:0.78rem;font-weight:500;color:#64748B;">({duracao_total_min} min)</span></div>
                    <div style="font-size:0.72rem;color:#64748B;">Sessão teórica / sem questões</div>
                </div>
                """, unsafe_allow_html=True)

        notas = st.text_area(
            "🧠 Anotações, Artigos-Chave ou Pegadinhas de Banca (enviado ao Obsidian):",
            placeholder="Registre observações importantes, artigos da lei ou pontos de revisão...",
            height=80,
            key="reg_notas"
        )

        col_sub_left, col_sub_right = st.columns([1.5, 1.0])
        with col_sub_left:
            sync_cofre = st.checkbox(
                "Sincronizar automaticamente com o Cofre Obsidian e GitHub Cloud",
                value=True,
                key="reg_sync_cofre"
            )
        with col_sub_right:
            submitted = st.button("💾 Salvar Sessão de Estudo", use_container_width=True, type="primary")

        if submitted:
            if duracao_total_min <= 0:
                st.error("❌ A duração do estudo precisa ser de pelo menos 1 minuto!")
            elif q_total > 0 and q_corretas > q_total:
                st.error("❌ O número de acertos não pode ser maior que o total de questões!")
            else:
                try:
                    acc = round((q_corretas / q_total * 100), 1) if q_total > 0 else 0.0
                    nova_sessao = {
                        "id": get_current_datetime().strftime("%Y%m%d%H%M%S"),
                        "certame_id": certame_escolhido_id,
                        "certame_name": opcoes_certames_form[certame_escolhido_id],
                        "date": str(data_sessao),
                        "block": bloco_selecionado,
                        "subject": disciplina_selecionada,
                        "topic": topico_final,
                        "study_type": tipo_estudo_selecionado,
                        "duration_min": int(duracao_total_min),
                        "questions_total": int(q_total),
                        "questions_correct": int(q_corretas),
                        "accuracy_pct": acc,
                        "notes": notas
                    }

                    st.session_state.sessions.append(nova_sessao)
                    save_sessions(st.session_state.sessions)
                    ok_db, res_db = db_insert_session(nova_sessao)

                    if get_current_elapsed_seconds() > 0:
                        st.session_state.timer_running = False
                        st.session_state.elapsed_seconds = 0
                        st.session_state.timer_start = None
                        db_save_active_timer(False, None, 0, None)

                    msg_cofre = ""
                    if sync_cofre and cofre_conectado:
                        ok_c, res_c = sync_session_to_obsidian_idempotent(nova_sessao, cofre_path)
                        msg_cofre = f" | 🧠 Obsidian: {res_c}" if ok_c else f" | ⚠️ Obsidian: {res_c}"

                    msg_storage = ""
                    if is_db_connected():
                        msg_storage = " | 🐘 PostgreSQL: Salvo com sucesso"
                    else:
                        gh_cfg_save = get_github_config()
                        if gh_cfg_save["token"]:
                            commit_txt = f"feat(estudo): {dur_str} em {nova_sessao['subject']} ({nova_sessao['certame_id']})"
                            ok_gh, res_gh = commit_file_to_github(
                                repo=gh_cfg_save["repo"],
                                file_path="data/sessions.json",
                                data_obj=st.session_state.sessions,
                                commit_message=commit_txt,
                                branch=gh_cfg_save["branch"],
                                token=gh_cfg_save["token"]
                            )
                            msg_storage = f" | ☁️ GitHub: {res_gh}" if ok_gh else f" | ⚠️ GitHub: {res_gh}"
                        else:
                            msg_storage = " | ℹ️ Salvo localmente (JSON)"

                    msg_completa = f"✅ **Sessão registrada!** {dur_str} de **{tipo_estudo_selecionado}** em **{disciplina_selecionada}** ({opcoes_certames_form[certame_escolhido_id]}).{msg_cofre}{msg_storage}"
                    st.session_state["feedback_registro"] = {
                        "status": "success",
                        "mensagem": msg_completa,
                        "toast": f"Sessão de {disciplina_selecionada} salva!"
                    }
                except Exception as e:
                    st.session_state["feedback_registro"] = {
                        "status": "error",
                        "mensagem": f"❌ **Falha ao salvar a sessão:** {str(e)}",
                        "toast": "Erro ao salvar!"
                    }
                st.rerun()

# ------------------------------------------
# ABA 4: HISTÓRICO & GESTÃO
# ------------------------------------------
with tab_hist:
    if df_all.empty:
        with st.container(border=True):
            st.info("💡 Nenhuma sessão registrada até o momento. Utilize a aba **⏱️ Registrar Sessão & Cronômetro** para lançar seu primeiro estudo!")
    else:
        with st.container(border=True):
            st.markdown("""
            <div class="section-title">
                <span>🔍 Busca Rápida & Filtros do Histórico</span>
                <div style="display:flex;gap:0.35rem;flex-wrap:wrap;">
                    <span class="pill pill-emerald">🟢 ≥ 80% Segurança</span>
                    <span class="pill pill-amber">🟡 65–79% Atenção</span>
                    <span class="pill pill-rose">🔴 &lt; 65% Crítico</span>
                    <span class="pill pill-slate">⚪ Teoria</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            cf_busca, cf_cert, cf_mat, cf_mod, cf_lim = st.columns([1.4, 1.0, 1.1, 1.0, 0.7])
            with cf_busca:
                termo_busca = st.text_input("Buscar por tópico, matéria ou nota:", placeholder="Ex: TCP/IP, LC 840, Docker...", key="hist_search")
            with cf_cert:
                filtro_c_hist = st.multiselect("Certame:", options=sorted(df_all["certame_name"].unique()), key="hist_f_cert")
            with cf_mat:
                filtro_mat = st.multiselect("Disciplina:", options=sorted(df_all["subject"].unique()), key="hist_f_mat")
            with cf_mod:
                tipos_opcoes = sorted([t for t in df_all["study_type"].dropna().unique() if t])
                filtro_tipo = st.multiselect("Modalidade:", options=tipos_opcoes, key="hist_f_mod")
            with cf_lim:
                page_size = st.selectbox("Exibir:", options=[15, 30, 50, 100], index=0, key="hist_page_size")

            df_view = df_all.sort_values(by=["date", "id"], ascending=[False, False]).copy()
            if termo_busca.strip():
                q_str = termo_busca.strip().lower()
                mask_txt = (
                    df_view["subject"].astype(str).str.lower().str.contains(q_str, na=False)
                    | df_view["topic"].astype(str).str.lower().str.contains(q_str, na=False)
                    | df_view["notes"].astype(str).str.lower().str.contains(q_str, na=False)
                )
                df_view = df_view[mask_txt]
            if filtro_c_hist:
                df_view = df_view[df_view["certame_name"].isin(filtro_c_hist)]
            if filtro_mat:
                df_view = df_view[df_view["subject"].isin(filtro_mat)]
            if filtro_tipo:
                df_view = df_view[df_view["study_type"].isin(filtro_tipo)]

            # Formatação visual das taxas de acerto com tags semânticas
            def format_accuracy_tag(row):
                qt = int(row.get("questions_total", 0))
                qc = int(row.get("questions_correct", 0))
                acc = float(row.get("accuracy_pct", 0.0))
                if qt <= 0:
                    return "⚪ Teoria"
                if acc >= 80.0:
                    return f"🟢 {acc:.1f}% ({qc}/{qt})"
                if acc >= 65.0:
                    return f"🟡 {acc:.1f}% ({qc}/{qt})"
                return f"🔴 {acc:.1f}% ({qc}/{qt})"

            df_view["status_acerto"] = df_view.apply(format_accuracy_tag, axis=1)

            total_rows = len(df_view)
            total_pages = max(1, (total_rows + page_size - 1) // page_size)

            col_info_p, col_nav_p = st.columns([3, 1])
            with col_info_p:
                horas_f = df_view["hours"].sum() if not df_view.empty else 0.0
                q_f = int(df_view["questions_total"].sum()) if not df_view.empty else 0
                st.caption(f"Exibindo **{min(total_rows, page_size)}** de **{total_rows}** sessões filtradas • Total no filtro: **{format_hours_mins(horas_f)}** líquidas e **{q_f}** questões.")
            with col_nav_p:
                if total_pages > 1:
                    page_num = st.number_input("Página:", min_value=1, max_value=total_pages, value=1, step=1, key="hist_page_num")
                else:
                    page_num = 1

            start_idx = (page_num - 1) * page_size
            df_page = df_view.iloc[start_idx : start_idx + page_size]

            st.dataframe(
                df_page.assign(duracao_fmt=df_page["hours"].apply(lambda h: format_hours_mins(h, short=True)))[["date", "certame_name", "subject", "topic", "study_type", "duracao_fmt", "status_acerto", "notes"]],
                column_config={
                    "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "certame_name": "Certame",
                    "subject": "Disciplina",
                    "topic": "Tópico Estudado",
                    "study_type": "Modalidade",
                    "duracao_fmt": "Duração",
                    "status_acerto": "Desempenho (Questões)",
                    "notes": "Anotações / Caderno de Erros"
                },
                use_container_width=True,
                hide_index=True
            )

        # Exportação e Gestão Pontual
        col_ex1, col_ex2, col_ex3 = st.columns([1, 1, 1.4])
        with col_ex1:
            csv_data = df_all.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Exportar CSV", data=csv_data, file_name=f"estudos_geral_{get_current_date()}.csv", mime="text/csv", use_container_width=True)
        with col_ex2:
            json_data = json.dumps(st.session_state.sessions, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("📥 Backup JSON", data=json_data, file_name=f"backup_estudos_{get_current_date()}.json", mime="application/json", use_container_width=True)
        with col_ex3:
            with st.expander("🗑️ Excluir uma sessão lançada por engano"):
                opcoes_del_sess = {
                    str(s.get("id")): f"{s.get('date')} • {s.get('subject')} ({s.get('duration_min')} min)"
                    for s in reversed(st.session_state.sessions)
                }
                id_del = st.selectbox("Selecione a sessão:", options=list(opcoes_del_sess.keys()), format_func=lambda x: opcoes_del_sess[x], key="del_sess_sel")
                if st.button("Confirmar Exclusão da Sessão", key="btn_del_sess", use_container_width=True):
                    db_delete_session(id_del)
                    st.session_state.sessions = [s for s in st.session_state.sessions if str(s.get("id")) != str(id_del)]
                    save_sessions(st.session_state.sessions)
                    st.toast("Sessão removida com sucesso!", icon="🗑️")
                    st.rerun()

# ------------------------------------------
# ABA 5: GERENCIAR CERTAMES & SINCRONIZAÇÃO
# ------------------------------------------
with tab_certames:
    # 1. Painel de Sincronização (Obsidian & GitHub) com Spinners e Feedback Pontual
    with st.container(border=True):
        st.markdown("""
        <div class="section-title">
            <span>🔄 Central de Sincronização — GitHub Cloud ↔ Cofre Obsidian</span>
            <span class="pill pill-indigo">Persistência Híbrida Idempotente</span>
        </div>
        """, unsafe_allow_html=True)

        col_sy1, col_sy2, col_sy3 = st.columns(3)
        with col_sy1:
            if st.button("📥 Puxar do GitHub & Gravar no Obsidian", use_container_width=True, type="primary"):
                with st.spinner("Consultando GitHub API e sincronizando notas no Cofre..."):
                    ok_pull, msg_pull = pull_from_github_and_merge()
                    count_obs = 0
                    if cofre_conectado:
                        for s in st.session_state.sessions:
                            ok_s, _ = sync_session_to_obsidian_idempotent(s, cofre_path)
                            if ok_s:
                                count_obs += 1
                if ok_pull:
                    st.success(f"✅ {msg_pull} ({count_obs} sessões verificadas no Obsidian)")
                    st.toast("Sincronização completa concluída!", icon="🧠")
                else:
                    st.warning(f"⚠️ Aviso GitHub: {msg_pull}")

        with col_sy2:
            if st.button("📤 Enviar Histórico Local para o GitHub", use_container_width=True):
                with st.spinner("Comitando sessions.json no repositório GitHub..."):
                    ok_push, msg_push = push_to_github(f"feat(data): backup completo de {len(st.session_state.sessions)} sessões")
                if ok_push:
                    st.success(f"☁️ {msg_push}")
                    st.toast("Backup enviado ao GitHub!", icon="☁️")
                else:
                    st.error(f"❌ Falha ao enviar: {msg_push}")

        with col_sy3:
            if st.button("🧠 Forçar Re-sincronização Local com Obsidian", use_container_width=True):
                if cofre_conectado:
                    with st.spinner("Verificando arquivos .md no Cofre do Obsidian..."):
                        count_obs_only = 0
                        for s in st.session_state.sessions:
                            ok_s, _ = sync_session_to_obsidian_idempotent(s, cofre_path)
                            if ok_s:
                                count_obs_only += 1
                    st.success(f"🧠 {count_obs_only} sessões sincronizadas em `{cofre_path}`!")
                    st.toast("Cofre Obsidian atualizado!", icon="✅")
                else:
                    st.warning("⚠️ Diretório do Cofre não acessível localmente neste dispositivo.")

    st.write("")

    # 2. Sanfonas (st.expander) para manter a página limpa por padrão
    with st.expander("🏛️ Certames Cadastrados & Conteúdo Programático Oficial", expanded=True):
        cols_cert_cards = st.columns(2)
        for idx_c, c in enumerate(st.session_state.certames):
            with cols_cert_cards[idx_c % 2]:
                with st.container(border=True):
                    n_blocos = len(c.get("subjects", {}))
                    st.markdown(f"""
                    <div class="section-title">
                        <span>📌 {c['name']}</span>
                        <span class="pill pill-indigo">{c.get('status', 'Ativo')}</span>
                    </div>
                    <div style="font-size:0.82rem;color:#334155;margin-bottom:0.4rem;">
                        <b>Cargo:</b> {c.get('cargo', '-')} <br>
                        <b>Banca:</b> {c.get('banca', '-')} • <b>Prova:</b> {c.get('exam_date') or 'Contínuo'} <br>
                        <b>Metas:</b> {c.get('daily_target_hours', 2.0):.0f}h/dia | {c.get('weekly_target_hours', 10.0):.0f}h/semana ({n_blocos} blocos)
                    </div>
                    """, unsafe_allow_html=True)
                    for blk, mats in c.get("subjects", {}).items():
                        if isinstance(mats, dict):
                            st.caption(f"📂 **{blk}:** {', '.join(list(mats.keys())[:6])}{'...' if len(mats) > 6 else ''}")
                        elif isinstance(mats, list):
                            st.caption(f"📂 **{blk}:** {', '.join(mats[:6])}{'...' if len(mats) > 6 else ''}")

    with st.expander("➕ Cadastrar Novo Concurso / Certame", expanded=False):
        with st.form("form_novo_certame"):
            c_nc1, c_nc2 = st.columns(2)
            with c_nc1:
                novo_id = st.text_input("Sigla / ID Único (ex: 'TCU', 'BACEN', 'STJ'):").strip().upper()
                novo_nome = st.text_input("Nome Completo (ex: 'TCU 2026/2027 — Auditor de TI'):")
                novo_cargo = st.text_input("Cargo / Especialidade (ex: 'Auditor Federal de Controle Externo'):")
            with c_nc2:
                nova_banca = st.text_input("Banca Examinadora (ex: 'Cebraspe', 'FGV', 'FCC'):")
                nova_data = st.date_input("Data Prevista da Prova:", value=get_current_date() + timedelta(days=90))
                novo_status = st.selectbox("Status:", ["Foco Total 🔥", "Planejado ⏳", "Stand-by ⏳", "Concluído / Histórico 📁"])

            materias_raw = st.text_area(
                "Disciplinas (uma por linha ou separadas por vírgula):",
                placeholder="Redes de Computadores\nBanco de Dados\nLíngua Portuguesa\nDireito Constitucional"
            )

            btn_novo_c = st.form_submit_button("💾 Cadastrar Novo Certame", use_container_width=True, type="primary")
            if btn_novo_c:
                if not novo_id or not novo_nome:
                    st.error("Informe a sigla e o nome completo do certame.")
                elif any(c["id"] == novo_id for c in st.session_state.certames):
                    st.error("Já existe um certame cadastrado com essa sigla/ID.")
                else:
                    lista_mats = [m.strip() for m in materias_raw.replace("\n", ",").split(",") if m.strip()]
                    if not lista_mats:
                        lista_mats = ["Conhecimentos Gerais", "Conhecimentos Específicos"]

                    novo_certame_dict = {
                        "id": novo_id,
                        "name": novo_nome,
                        "short_name": novo_id,
                        "cargo": novo_cargo,
                        "banca": nova_banca,
                        "exam_date": str(nova_data),
                        "daily_target_hours": 2.0,
                        "weekly_target_hours": 10.0,
                        "status": novo_status,
                        "subjects": {
                            "Conhecimentos": {m: [f"1. Estudo geral de {m}"] for m in lista_mats}
                        }
                    }
                    st.session_state.certames.append(novo_certame_dict)
                    save_certames(st.session_state.certames)
                    st.success(f"✅ Certame **{novo_nome}** adicionado com sucesso!")
                    st.rerun()

    with st.expander("🏷️ Gerenciar Modalidades & Tipos de Estudo", expanded=False):
        chips_html = "".join([f'<span class="pill pill-slate" style="margin:0.2rem;">{st_name}</span>' for st_name in st.session_state.study_types])
        st.markdown(f"<div style='margin-bottom:0.8rem;'><b>Modalidades Ativas:</b><br>{chips_html}</div>", unsafe_allow_html=True)

        c_mgt1, c_mgt2 = st.columns(2)
        with c_mgt1:
            st.markdown("##### ➕ Adicionar Nova Modalidade")
            EMOJIS_SUGERIDOS = ["📹", "🎯", "📖", "⚖️", "✍️", "🧠", "📝", "🎧", "📚", "💻", "🔥", "⚡", "💡", "📑", "🔍", "🎓"]
            c_em, c_nm = st.columns([1, 2.5])
            with c_em:
                emoji_escolhido = st.selectbox("Ícone:", options=EMOJIS_SUGERIDOS, key="tab4_emoji_sel")
            with c_nm:
                novo_tipo_tab4 = st.text_input("Nome da Modalidade:", placeholder="Ex: Podcast / Áudio", key="tab4_novo_tipo")

            if st.button("Salvar Nova Modalidade", use_container_width=True, key="tab4_btn_add"):
                nome_limpo = novo_tipo_tab4.strip()
                if nome_limpo:
                    if any(ord(char) > 127 and char in emoji_escolhido for char in nome_limpo):
                        val_t4 = nome_limpo
                    else:
                        val_t4 = f"{emoji_escolhido} {nome_limpo}"

                    if val_t4 not in st.session_state.study_types:
                        st.session_state.study_types.append(val_t4)
                        save_study_types(st.session_state.study_types)
                        st.toast(f"Modalidade '{val_t4}' adicionada!", icon="🏷️")
                        st.rerun()
                    else:
                        st.warning("Esta modalidade já está cadastrada.")
                else:
                    st.error("Informe o nome da modalidade.")

        with c_mgt2:
            st.markdown("##### 🗑️ Excluir Modalidade Existente")
            tipo_del_tab4 = st.selectbox("Selecione a modalidade a remover:", options=st.session_state.study_types, key="tab4_sel_del")
            if st.button("Excluir Modalidade Selecionada", use_container_width=True, key="tab4_btn_del"):
                if len(st.session_state.study_types) > 1:
                    st.session_state.study_types.remove(tipo_del_tab4)
                    save_study_types(st.session_state.study_types)
                    st.toast(f"Modalidade '{tipo_del_tab4}' removida!", icon="🗑️")
                    st.rerun()
                else:
                    st.error("O sistema deve manter pelo menos uma modalidade cadastrada.")

    expanded_cfg = (not is_db_connected() and not gh_cfg["token"] and not cofre_conectado)
    with st.expander("🔑 Configurações de Conexão (PostgreSQL Nuvem, GitHub & Obsidian)", expanded=expanded_cfg):
        c_cfg1, c_cfg2 = st.columns(2)
        with c_cfg1:
            st.markdown("##### 🐘 Banco Relacional PostgreSQL (Supabase / Neon) [Recomendado]")
            if is_db_connected():
                st.success("✅ **PostgreSQL Conectado!** Estudos, certames e modalidades são gravados de forma atômica no banco de dados na nuvem.")
                if st.button("🔄 Reconectar / Atualizar Conexão do Banco", key="btn_reconn_db"):
                    st.cache_resource.clear()
                    st.rerun()
            else:
                st.info("ℹ️ PostgreSQL não conectado. Operando em modo de arquivos JSON.")
                if st.session_state.get("db_last_error"):
                    st.error(f"❌ **Diagnóstico de Conexão:** {st.session_state['db_last_error']}")
                    err_txt = str(st.session_state["db_last_error"])
                    if any(s in err_txt for s in ["Network is unreachable", "getaddrinfo", "not known", "timed out", "timeout"]):
                        st.warning("💡 **Dica IPv4 vs IPv6:** O Streamlit Cloud opera em rede IPv4. A *Direct Connection* (`db.xxx.supabase.co`) exige rede IPv6. No Supabase, clique no botão **Connect** no topo do painel e selecione a aba **Connection Pooler** (ou Session / porta 6543) para obter a URL compatível com IPv4!")

                if st.button("🔄 Tentar Reconectar Agora", key="btn_retry_conn"):
                    st.cache_resource.clear()
                    st.rerun()
                st.markdown("""
                **Como conectar seu PostgreSQL gratuito (Supabase ou Neon):**
                1. Crie seu projeto no [supabase.com](https://supabase.com) ou [neon.tech](https://neon.tech);
                2. Copie a **URI de Conexão** (formato `postgresql://postgres:[SENHA]@...`);
                3. No Streamlit Cloud (**Settings > Secrets**) ou no PC (`.streamlit/secrets.toml`), cole:
                ```toml
                [connections.postgresql]
                url = "postgresql://postgres:SUA_SENHA@db.xxxx.supabase.co:5432/postgres"
                ```
                """)
                url_test = st.text_input("Ou cole a Connection String para testar agora:", type="password", placeholder="postgresql://postgres:senha@host:5432/postgres", key="cfg_db_url_input")
                if st.button("🔌 Conectar ao PostgreSQL", key="btn_test_db"):
                    if url_test.strip():
                        st.session_state["custom_db_url"] = url_test.strip()
                        st.cache_resource.clear()
                        st.rerun()

            st.write("")
            st.markdown("##### 🐙 Backup Secundário no GitHub (Opcional)")
            token_input = st.text_input(
                "GitHub Personal Access Token (PAT):",
                value=st.session_state.get("custom_github_token", ""),
                type="password",
                placeholder="ghp_...",
                help="Opcional quando conectado ao PostgreSQL."
            )
            if token_input:
                st.session_state["custom_github_token"] = token_input
            st.markdown("[🔗 Gerar Token no GitHub](https://github.com/settings/tokens/new?scopes=repo&description=Concursos+Study+Tracker)")
        with c_cfg2:
            st.markdown("##### 🧠 Caminho Local do Cofre Obsidian (Apenas no Computador)")
            novo_cofre_path = st.text_input("Diretório Local do Cofre Obsidian:", value=cofre_path)
            if novo_cofre_path:
                st.session_state["custom_cofre_path"] = novo_cofre_path
            if cofre_conectado:
                st.success("✅ Diretório do cofre conectado localmente neste PC.")
            else:
                st.info("ℹ️ Cofre não acessível diretamente (comportamento esperado se estiver rodando na nuvem).")

    with st.expander("📋 Snippets Prontos do Dataview para o Obsidian", expanded=False):
        st.markdown("**1. Todas as Sessões da Trajetória:**")
        st.code("""```dataview
TABLE file.mtime AS "Registrado em", certame AS "Certame", date AS "Data do Estudo"
FROM "06-Concursos-e-Estudos/registros-de-estudo"
SORT file.mtime DESC
LIMIT 15
```""", language="markdown")

        st.markdown("**2. Apenas Sessões Focadas na DPDF:**")
        st.code("""```dataview
TABLE date AS "Data", file.mtime AS "Última Modificação"
FROM "06-Concursos-e-Estudos/registros-de-estudo" AND #dpdf
SORT file.mtime DESC
LIMIT 10
```""", language="markdown")
