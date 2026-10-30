import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Central de Estudos | Trajetória Concursos — Isac",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #90A4AE;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #1E222D;
        border: 1px solid #2E3648;
        border-radius: 10px;
        padding: 15px 20px;
        margin-bottom: 10px;
    }
    .certame-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CAMINHOS E ARQUIVOS
# ==========================================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
CERTAMES_FILE = os.path.join(DATA_DIR, "certames.json")

COFRE_DIR_DEFAULT = r"G:\Meu Drive\cofre\06-Concursos-e-Estudos\registros-de-estudo"
COFRE_MATRIZ_DEFAULT = r"G:\Meu Drive\cofre\06-Concursos-e-Estudos\matriz-de-desempenho-e-materias.md"

# ==========================================
# CERTAMES PADRÃO INICIAIS
# ==========================================
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

# ==========================================
# FUNÇÕES DE PERSISTÊNCIA
# ==========================================
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_certames():
    ensure_data_dir()
    if os.path.exists(CERTAMES_FILE):
        try:
            with open(CERTAMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CERTAMES
    else:
        save_certames(DEFAULT_CERTAMES)
        return DEFAULT_CERTAMES

def save_certames(certames):
    ensure_data_dir()
    with open(CERTAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(certames, f, ensure_ascii=False, indent=2)

def load_sessions():
    ensure_data_dir()
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_sessions(sessions):
    ensure_data_dir()
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def sync_session_to_obsidian(session, cofre_dir):
    """Grava o registro no Cofre Obsidian como nota markdown estruturada para Dataview."""
    if not os.path.exists(cofre_dir):
        return False, f"Diretório do cofre não encontrado: {cofre_dir}"
    
    sess_date = session["date"]
    file_path = os.path.join(cofre_dir, f"{sess_date}.md")
    certame_tag = session.get("certame_id", "Geral").lower()
    
    entry = f"""
### ⏱️ [{session.get('certame_id', 'Geral')}] {session['subject']} — {session['duration_min']} min
- **Certame:** {session.get('certame_name', session.get('certame_id', 'Geral'))}
- **Bloco:** {session['block']}
- **Tópico:** {session.get('topic', '-')}
- **Duração:** {session['duration_min']} minutos ({session['duration_min']/60:.2f}h)
- **Questões:** {session.get('questions_correct', 0)} / {session.get('questions_total', 0)} acertos ({session.get('accuracy_pct', 0)}%)
"""
    if session.get("notes"):
        entry += f"- **Notas / Pegadinhas:** {session['notes']}\n"

    if os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        content = f"""---
tags:
  - registro-estudo
  - concursos
  - {certame_tag}
date: {sess_date}
certame: {session.get('certame_id', 'Geral')}
---

# 📅 Registro de Estudo — {sess_date}

Voltar para: [[06-Concursos-e-Estudos/00-HUB-CONCURSOS|00-HUB-CONCURSOS.md]] | [[06-Concursos-e-Estudos/plano-de-estudo-dpdf-2027|plano-de-estudo-dpdf-2027.md]]
{entry}
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    return True, "Sincronizado com sucesso!"

# Inicializa estado
if "certames" not in st.session_state:
    st.session_state.certames = load_certames()
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()

# Estado do cronômetro
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

# ==========================================
# SIDEBAR: SELETOR DE CERTAME & CRONÔMETRO
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("Central de Estudos")
    st.caption("Second Brain de Concursos Públicos — Isac")
    
    st.divider()
    
    # 🎯 FILTRO GLOBAL DE VISÃO
    opcoes_visao = ["🌐 Toda a Minha Trajetória (Visão Consolidada)"] + [
        f"{c.get('status', '').split(' ')[-1]} {c['name']}" for c in st.session_state.certames
    ]
    visao_selecionada = st.selectbox("🎯 Foco / Certame em Exibição:", opcoes_visao)
    
    filtro_certame_id = None
    certame_ativo_obj = None
    
    if visao_selecionada != "🌐 Toda a Minha Trajetória (Visão Consolidada)":
        # Extrai certame selecionado
        idx_c = opcoes_visao.index(visao_selecionada) - 1
        certame_ativo_obj = st.session_state.certames[idx_c]
        filtro_certame_id = certame_ativo_obj["id"]
        
        # Info do certame ativo
        st.markdown(f"**Banca:** {certame_ativo_obj.get('banca', 'A definir')}")
        st.markdown(f"**Cargo:** {certame_ativo_obj.get('cargo', '-')}")
        
        # Contagem regressiva se tiver data
        if certame_ativo_obj.get("exam_date"):
            try:
                dt_prova = datetime.strptime(certame_ativo_obj["exam_date"], "%Y-%m-%d")
                delta = dt_prova - datetime.now()
                if delta.total_seconds() > 0:
                    st.info(f"⏳ **Faltam {delta.days} dias e {delta.seconds//3600}h** para a prova ({dt_prova.strftime('%d/%m/%Y')})")
                else:
                    st.success("🎉 Data da prova atingida!")
            except Exception:
                pass
    else:
        st.info("📊 Exibindo **métricas acumuladas de toda a trajetória** (todos os certames somados).")
        
    st.divider()
    
    # Cronômetro da Sessão
    st.subheader("⏱️ Cronômetro da Sessão")
    col_t1, col_t2 = st.columns(2)
    
    if not st.session_state.timer_running:
        if col_t1.button("▶️ Iniciar", use_container_width=True):
            st.session_state.timer_running = True
            st.session_state.timer_start = datetime.now() - timedelta(seconds=st.session_state.elapsed_seconds)
            st.rerun()
    else:
        if col_t1.button("⏸️ Pausar", use_container_width=True):
            st.session_state.timer_running = False
            st.session_state.elapsed_seconds = int((datetime.now() - st.session_state.timer_start).total_seconds())
            st.rerun()
            
    if col_t2.button("🔄 Zerar", use_container_width=True):
        st.session_state.timer_running = False
        st.session_state.elapsed_seconds = 0
        st.session_state.timer_start = None
        st.rerun()
        
    if st.session_state.timer_running and st.session_state.timer_start:
        cur_elapsed = int((datetime.now() - st.session_state.timer_start).total_seconds())
    else:
        cur_elapsed = st.session_state.elapsed_seconds
        
    minutos_cronometro = cur_elapsed // 60
    segundos_cronometro = cur_elapsed % 60
    st.markdown(f"### `{minutos_cronometro:02d}:{segundos_cronometro:02d}`")
    
    st.divider()
    st.subheader("⚙️ Conexão Obsidian")
    cofre_path = st.text_input("Pasta do Cofre:", value=COFRE_DIR_DEFAULT)
    cofre_conectado = os.path.exists(cofre_path)
    if cofre_conectado:
        st.success("🟢 Cofre conectado!")
    else:
        st.warning("🟡 Modo nuvem (sem acesso direto ao disco)")

# ==========================================
# PROCESSAMENTO DE DADOS
# ==========================================
df_all = pd.DataFrame(st.session_state.sessions)
if not df_all.empty:
    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all["hours"] = df_all["duration_min"] / 60.0
    if "certame_id" not in df_all.columns:
        df_all["certame_id"] = "DPDF"
        df_all["certame_name"] = "DPDF 2026/2027"

# Filtra conforme a visão selecionada
if filtro_certame_id is not None and not df_all.empty:
    df = df_all[df_all["certame_id"] == filtro_certame_id].copy()
else:
    df = df_all.copy()

hoje = pd.to_datetime(date.today())
inicio_semana = hoje - timedelta(days=hoje.weekday())
inicio_mes = hoje.replace(day=1)

if not df.empty:
    horas_hoje = df[df["date"] == hoje]["hours"].sum() if not df[df["date"] == hoje].empty else 0.0
    horas_semana = df[df["date"] >= inicio_semana]["hours"].sum() if not df[df["date"] >= inicio_semana].empty else 0.0
    horas_mes = df[df["date"] >= inicio_mes]["hours"].sum() if not df[df["date"] >= inicio_mes].empty else 0.0
    horas_total = df["hours"].sum()
    
    total_q_feitas = df["questions_total"].sum()
    total_q_acertos = df["questions_correct"].sum()
    taxa_geral = (total_q_acertos / total_q_feitas * 100.0) if total_q_feitas > 0 else 0.0
else:
    horas_hoje = horas_semana = horas_mes = horas_total = 0.0
    total_q_feitas = total_q_acertos = taxa_geral = 0.0

# ==========================================
# CABEÇALHO PRINCIPAL
# ==========================================
if filtro_certame_id is None:
    titulo_principal = "🌐 Trajetória Completa nos Concursos"
    sub_principal = "Visão panorâmica consolidada de todas as horas, matérias e simulados realizados ao longo da sua preparação"
else:
    titulo_principal = f"🎯 {certame_ativo_obj['name']}"
    sub_principal = f"Painel dedicado | Cargo: {certame_ativo_obj.get('cargo', '-')} | Banca: {certame_ativo_obj.get('banca', '-')}"

st.markdown(f'<p class="main-title">{titulo_principal}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{sub_principal}</p>', unsafe_allow_html=True)

# ==========================================
# ABAS DE NAVEGAÇÃO
# ==========================================
tab_dash, tab_reg, tab_hist, tab_certames, tab_obsidian = st.tabs([
    "📊 Dashboard & Insights",
    "⏱️ Registrar Sessão",
    "📋 Histórico & Gestão",
    "🏛️ Gerenciar Certames",
    "🧠 Integração com Obsidian"
])

# ------------------------------------------
# TAB 1: DASHBOARD & INSIGHTS
# ------------------------------------------
with tab_dash:
    meta_dia = certame_ativo_obj.get("daily_target_hours", 2.0) if certame_ativo_obj else 2.0
    meta_sem = certame_ativo_obj.get("weekly_target_hours", 10.0) if certame_ativo_obj else 10.0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="📅 Horas Hoje", 
            value=f"{horas_hoje:.1f}h", 
            delta=f"{(horas_hoje - meta_dia):.1f}h da meta ({meta_dia:.0f}h)"
        )
        prog_dia = min(horas_hoje / meta_dia, 1.0) if meta_dia > 0 else 0.0
        st.progress(prog_dia, text=f"{prog_dia*100:.0f}% da meta diária")
        
    with c2:
        st.metric(
            label="🗓️ Horas na Semana", 
            value=f"{horas_semana:.1f}h", 
            delta=f"{(horas_semana - meta_sem):.1f}h da meta ({meta_sem:.0f}h)"
        )
        prog_sem = min(horas_semana / meta_sem, 1.0) if meta_sem > 0 else 0.0
        st.progress(prog_sem, text=f"{prog_sem*100:.0f}% da meta semanal")
        
    with c3:
        st.metric(label="📆 Horas no Mês", value=f"{horas_mes:.1f}h")
        st.caption(f"Total acumulado: **{horas_total:.1f}h**")
        
    with c4:
        st.metric(
            label="🎯 Questões Resolvidas", 
            value=f"{int(total_q_feitas)}", 
            delta=f"{taxa_geral:.1f}% de acertos"
        )
        st.caption(f"{int(total_q_acertos)} acertos no total")
        
    st.divider()
    
    if df.empty:
        st.info("💡 Nenhuma sessão encontrada para este filtro. Use a aba **⏱️ Registrar Sessão** para começar!")
    else:
        # Se estiver na visão geral, mostra comparativo entre certames
        if filtro_certame_id is None and not df_all.empty:
            st.subheader("🏛️ Distribuição de Horas por Certame (Trajetória Total)")
            certame_horas = df_all.groupby("certame_name")["hours"].sum().reset_index()
            fig_cert = px.bar(
                certame_horas,
                x="hours",
                y="certame_name",
                orientation="h",
                labels={"hours": "Horas Estudadas", "certame_name": "Certame / Projeto"},
                color="hours",
                color_continuous_scale="Teal"
            )
            fig_cert.update_layout(margin=dict(t=10, b=10, l=10, r=10), coloraxis_showscale=False)
            st.plotly_chart(fig_cert, use_container_width=True)
            st.divider()

        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📚 Horas por Bloco / Categoria")
            bloco_horas = df.groupby("block")["hours"].sum().reset_index()
            fig_bloco = px.pie(
                bloco_horas, 
                values="hours", 
                names="block",
                hole=0.45,
                color="block",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bloco.update_traces(textinfo="percent+label")
            fig_bloco.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_bloco, use_container_width=True)
            
        with col_g2:
            st.subheader("📖 Horas por Disciplina")
            materia_horas = df.groupby("subject")["hours"].sum().sort_values(ascending=True).reset_index()
            fig_mat = px.bar(
                materia_horas, 
                x="hours", 
                y="subject", 
                orientation="h",
                labels={"hours": "Horas Líquidas", "subject": "Disciplina"},
                color="hours",
                color_continuous_scale="Blues"
            )
            fig_mat.update_layout(margin=dict(t=10, b=10, l=10, r=10), coloraxis_showscale=False)
            st.plotly_chart(fig_mat, use_container_width=True)
            
        st.divider()
        col_g3, col_g4 = st.columns(2)
        
        with col_g3:
            st.subheader("🎯 Rendimento em Questões (%)")
            q_df = df[df["questions_total"] > 0]
            if not q_df.empty:
                mat_q = q_df.groupby("subject").agg({
                    "questions_total": "sum",
                    "questions_correct": "sum"
                }).reset_index()
                mat_q["taxa"] = (mat_q["questions_correct"] / mat_q["questions_total"] * 100).round(1)
                mat_q = mat_q.sort_values(by="taxa", ascending=True)
                
                cores = ["#EF5350" if t < 65 else "#FFCA28" if t < 80 else "#66BB6A" for t in mat_q["taxa"]]
                
                fig_taxa = go.Figure(go.Bar(
                    x=mat_q["taxa"],
                    y=mat_q["subject"],
                    orientation="h",
                    marker_color=cores,
                    text=[f"{t}% ({int(c)}/{int(tot)})" for t, c, tot in zip(mat_q["taxa"], mat_q["questions_correct"], mat_q["questions_total"])],
                    textposition="auto"
                ))
                fig_taxa.update_layout(
                    xaxis=dict(title="Taxa de Acertos (%)", range=[0, 100]),
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_taxa, use_container_width=True)
            else:
                st.caption("Nenhuma questão com acertos registrada ainda neste filtro.")
                
        with col_g4:
            st.subheader("📈 Consistência Diária (Últimos 14 Dias)")
            ult_14 = hoje - timedelta(days=13)
            df_recente = df[df["date"] >= ult_14]
            dias_completos = pd.DataFrame({"date": pd.date_range(ult_14, hoje)})
            
            if not df_recente.empty:
                horas_por_dia = df_recente.groupby("date")["hours"].sum().reset_index()
                merged = pd.merge(dias_completos, horas_por_dia, on="date", how="left").fillna(0)
            else:
                merged = dias_completos.copy()
                merged["hours"] = 0.0
                
            merged["formatted_date"] = merged["date"].dt.strftime("%d/%m")
            
            fig_consist = px.bar(
                merged,
                x="formatted_date",
                y="hours",
                labels={"formatted_date": "Dia", "hours": "Horas"},
                color="hours",
                color_continuous_scale=["#263238", "#1E88E5", "#00E676"]
            )
            fig_consist.add_hline(y=meta_dia, line_dash="dash", line_color="#FFB300", annotation_text=f"Meta ({meta_dia:.0f}h)")
            fig_consist.update_layout(margin=dict(t=10, b=10, l=10, r=10), coloraxis_showscale=False)
            st.plotly_chart(fig_consist, use_container_width=True)

# ------------------------------------------
# TAB 2: REGISTRAR SESSÃO
# ------------------------------------------
with tab_reg:
    st.subheader("📝 Registrar Sessão de Estudo")
    
    with st.form("form_registro_sessao", clear_on_submit=False):
        c_f0, c_f1 = st.columns(2)
        with c_f0:
            # Seleção do Certame
            opcoes_certames_form = {c["id"]: c["name"] for c in st.session_state.certames}
            idx_default = 0
            if filtro_certame_id and filtro_certame_id in opcoes_certames_form:
                idx_default = list(opcoes_certames_form.keys()).index(filtro_certame_id)
                
            certame_escolhido_id = st.selectbox(
                "Certame Alvo:", 
                options=list(opcoes_certames_form.keys()), 
                format_func=lambda x: opcoes_certames_form[x],
                index=idx_default
            )
            data_sessao = st.date_input("Data do Estudo:", value=date.today())
            
        with c_f1:
            # Obtém matérias do certame escolhido
            c_obj_form = next((c for c in st.session_state.certames if c["id"] == certame_escolhido_id), st.session_state.certames[0])
            blocos_disponiveis = list(c_obj_form.get("subjects", {}).keys())
            bloco_selecionado = st.selectbox("Bloco / Área:", blocos_disponiveis if blocos_disponiveis else ["Geral"])
            
            materias_disponiveis = c_obj_form.get("subjects", {}).get(bloco_selecionado, ["Geral"])
            disciplina_selecionada = st.selectbox("Disciplina:", materias_disponiveis)
            
        topico = st.text_input("Tópico Específico (ex: 'LC 840 - Regime Disciplinar' ou 'Modelo OSI x TCP/IP'):")
        
        c_q1, c_q2, c_q3 = st.columns(3)
        with c_q1:
            tempo_sugerido = minutos_cronometro if minutos_cronometro > 0 else 60
            duracao = st.number_input("Duração em Minutos:", min_value=1, max_value=600, value=int(tempo_sugerido), step=5)
        with c_q2:
            q_total = st.number_input("Questões Feitas:", min_value=0, max_value=300, value=0, step=1)
        with c_q3:
            q_corretas = st.number_input("Questões Acertadas:", min_value=0, max_value=300, value=0, step=1)
            
        notas = st.text_area("Anotações, Pontos Fortes, Pegadinhas de Banca:", placeholder="Registre observações importantes para o seu Second Brain...")
        sync_cofre = st.checkbox("Sincronizar imediatamente com o Cofre Obsidian", value=True)
        
        submitted = st.form_submit_button("💾 Salvar Sessão", use_container_width=True)
        
        if submitted:
            if q_total > 0 and q_corretas > q_total:
                st.error("O número de acertos não pode ser maior que o total de questões!")
            else:
                acc = round((q_corretas / q_total * 100), 1) if q_total > 0 else 0.0
                nova_sessao = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "certame_id": certame_escolhido_id,
                    "certame_name": opcoes_certames_form[certame_escolhido_id],
                    "date": str(data_sessao),
                    "block": bloco_selecionado,
                    "subject": disciplina_selecionada,
                    "topic": topico,
                    "duration_min": int(duracao),
                    "questions_total": int(q_total),
                    "questions_correct": int(q_corretas),
                    "accuracy_pct": acc,
                    "notes": notas
                }
                
                st.session_state.sessions.append(nova_sessao)
                save_sessions(st.session_state.sessions)
                
                if minutos_cronometro > 0:
                    st.session_state.timer_running = False
                    st.session_state.elapsed_seconds = 0
                    st.session_state.timer_start = None
                    
                msg_cofre = ""
                if sync_cofre and cofre_conectado:
                    ok, res = sync_session_to_obsidian(nova_sessao, cofre_path)
                    msg_cofre = f" e {res}" if ok else f" (Aviso Cofre: {res})"
                    
                st.success(f"✅ Sessão registrada para **{opcoes_certames_form[certame_escolhido_id]}** ({duracao} min em {disciplina_selecionada}){msg_cofre}!")
                st.rerun()

# ------------------------------------------
# TAB 3: HISTÓRICO & GESTÃO
# ------------------------------------------
with tab_hist:
    st.subheader("📋 Histórico Unificado de Sessões")
    
    if df_all.empty:
        st.info("Nenhuma sessão registrada até o momento.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_c_hist = st.multiselect("Filtrar por Certame:", options=sorted(df_all["certame_name"].unique()))
        with col_f2:
            filtro_mat = st.multiselect("Filtrar por Disciplina:", options=sorted(df_all["subject"].unique()))
        with col_f3:
            filtro_bloco = st.multiselect("Filtrar por Bloco:", options=sorted(df_all["block"].unique()))
            
        df_view = df_all.copy()
        if filtro_c_hist:
            df_view = df_view[df_view["certame_name"].isin(filtro_c_hist)]
        if filtro_mat:
            df_view = df_view[df_view["subject"].isin(filtro_mat)]
        if filtro_bloco:
            df_view = df_view[df_view["block"].isin(filtro_bloco)]
            
        st.dataframe(
            df_view[["date", "certame_name", "block", "subject", "topic", "duration_min", "hours", "questions_total", "questions_correct", "accuracy_pct", "notes"]],
            column_config={
                "date": st.column_config.DateColumn("Data"),
                "certame_name": "Certame",
                "block": "Bloco",
                "subject": "Disciplina",
                "topic": "Tópico",
                "duration_min": "Minutos",
                "hours": st.column_config.NumberColumn("Horas", format="%.2f h"),
                "questions_total": "Total Q.",
                "questions_correct": "Acertos",
                "accuracy_pct": st.column_config.NumberColumn("Aproveitamento", format="%.1f %%"),
                "notes": "Observações"
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        with col_exp1:
            csv_data = df_all.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Histórico Geral (CSV)", data=csv_data, file_name=f"estudos_geral_{date.today()}.csv", mime="text/csv", use_container_width=True)
        with col_exp2:
            json_data = json.dumps(st.session_state.sessions, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("📥 Baixar Backup Geral (JSON)", data=json_data, file_name=f"backup_estudos_{date.today()}.json", mime="application/json", use_container_width=True)
        with col_exp3:
            if st.button("🔄 Ressincronizar Todo o Histórico com o Cofre", use_container_width=True):
                if cofre_conectado:
                    count = 0
                    for s in st.session_state.sessions:
                        sync_session_to_obsidian(s, cofre_path)
                        count += 1
                    st.success(f"✅ {count} sessões sincronizadas com o Cofre em {cofre_path}!")
                else:
                    st.error("Cofre não encontrado no caminho especificado.")

# ------------------------------------------
# TAB 4: GERENCIAR CERTAMES
# ------------------------------------------
with tab_certames:
    st.subheader("🏛️ Meus Certames & Projetos de Concurso")
    st.markdown("Aqui você pode gerenciar todos os concursos que acompanha ou criar novos certames conforme novos editais forem saindo.")
    
    # Exibe lista de certames cadastrados
    for c in st.session_state.certames:
        with st.expander(f"📌 {c['name']} — Status: **{c.get('status', 'Ativo')}**"):
            st.markdown(f"- **ID:** `{c['id']}`")
            st.markdown(f"- **Cargo:** {c.get('cargo', '-')}")
            st.markdown(f"- **Banca:** {c.get('banca', '-')}")
            st.markdown(f"- **Data da Prova:** {c.get('exam_date', 'Não definida')}")
            st.markdown(f"- **Metas:** {c.get('daily_target_hours', 2.0)}h/dia | {c.get('weekly_target_hours', 10.0)}h/semana")
            st.markdown("**Disciplinas Cadastradas:**")
            for blk, mats in c.get("subjects", {}).items():
                st.markdown(f"  * **{blk}:** {', '.join(mats)}")
                
    st.divider()
    st.subheader("➕ Adicionar Novo Concurso / Certame")
    with st.form("form_novo_certame"):
        c_nc1, c_nc2 = st.columns(2)
        with c_nc1:
            novo_id = st.text_input("Sigla / ID Único (ex: 'TCU', 'BACEN', 'STJ'):").strip().upper()
            novo_nome = st.text_input("Nome Completo (ex: 'TCU 2026/2027 — Auditor de TI'):")
            novo_cargo = st.text_input("Cargo / Especialidade (ex: 'Auditor Federal de Controle Externo'):")
        with c_nc2:
            nova_banca = st.text_input("Banca Examinadora (ex: 'Cebraspe', 'FGV', 'FCC'):")
            nova_data = st.date_input("Data Prevista da Prova (opcional):", value=date.today() + timedelta(days=90))
            novo_status = st.selectbox("Status:", ["Foco Total 🔥", "Planejado ⏳", "Stand-by ⏳", "Concluído / Histórico 📁"])
            
        materias_raw = st.text_area(
            "Disciplinas (uma por linha ou separadas por vírgula):", 
            placeholder="Redes de Computadores\nBanco de Dados\nLíngua Portuguesa\nDireito Constitucional"
        )
        
        btn_novo_c = st.form_submit_button("Cadastrar Novo Certame", use_container_width=True)
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
                        "Conhecimentos": lista_mats
                    }
                }
                st.session_state.certames.append(novo_certame_dict)
                save_certames(st.session_state.certames)
                st.success(f"✅ Certame **{novo_nome}** adicionado com sucesso!")
                st.rerun()

# ------------------------------------------
# TAB 5: INTEGRAÇÃO OBSIDIAN & DATAVIEW
# ------------------------------------------
with tab_obsidian:
    st.subheader("🧠 Integração Viva com o seu Second Brain (Obsidian)")
    st.markdown(f"""
    Cada sessão salva nesta plataforma central é gravada com a etiqueta do certame correspondente em:  
    `{COFRE_DIR_DEFAULT}\\<DATA>.md`
    
    Isso permite que você faça consultas no Obsidian para ver tanto a **sua trajetória inteira** quanto **filtros por certame específico** usando o **Dataview**.
    """)
    
    st.divider()
    st.subheader("📋 Snippets Prontos do Dataview para Colar no Obsidian")
    
    st.markdown("**1. Todas as Sessões da Trajetória (Visão Geral de Concurseiro):**")
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

    st.markdown("**3. Apenas Sessões da CGU:**")
    st.code("""```dataview
TABLE date AS "Data", file.mtime AS "Última Modificação"
FROM "06-Concursos-e-Estudos/registros-de-estudo" AND #cgu
SORT file.mtime DESC
LIMIT 10
```""", language="markdown")
