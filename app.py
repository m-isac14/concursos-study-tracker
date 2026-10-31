import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os

from github_sync import (
    get_github_config,
    fetch_file_from_github,
    commit_file_to_github,
    sync_session_to_obsidian_idempotent
)

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
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CAMINHOS E ARQUIVOS LOCAIS
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
# FUNÇÕES DE PERSISTÊNCIA LOCAL & NUVEM
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

# Inicializa estado
if "certames" not in st.session_state:
    st.session_state.certames = load_certames()
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()

# Auto-pull na inicialização se ainda não foi feito e se houver token
if "initial_gh_pull_done" not in st.session_state:
    st.session_state.initial_gh_pull_done = True
    gh_cfg_init = get_github_config()
    if gh_cfg_init["token"] and not st.session_state.sessions:
        pull_from_github_and_merge()

# Estado do cronômetro
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

# ==========================================
# SIDEBAR: SELETOR, CRONÔMETRO E GITHUB
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
        idx_c = opcoes_visao.index(visao_selecionada) - 1
        certame_ativo_obj = st.session_state.certames[idx_c]
        filtro_certame_id = certame_ativo_obj["id"]
        
        st.markdown(f"**Banca:** {certame_ativo_obj.get('banca', 'A definir')}")
        st.markdown(f"**Cargo:** {certame_ativo_obj.get('cargo', '-')}")
        
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
    
    # ☁️ PONTE GITHUB (PERSISTÊNCIA EM NUVEM)
    st.subheader("☁️ Nuvem & GitHub Bridge")
    gh_cfg = get_github_config()
    
    if gh_cfg["token"]:
        st.success(f"🟢 Nuvem Conectada (`{gh_cfg['repo']}`)")
    else:
        st.caption(f"🟡 Repositório: `{gh_cfg['repo']}` (Modo Leitura)")
        
    col_gh_act1, col_gh_act2 = st.columns(2)
    with col_gh_act1:
        if st.button("📥 Puxar Nuvem", use_container_width=True, help="Baixa sessões salvas no GitHub"):
            ok_p, msg_p = pull_from_github_and_merge()
            if ok_p:
                st.success(msg_p)
                st.rerun()
            else:
                st.warning(msg_p)
                
    with col_gh_act2:
        if st.button("📤 Enviar Nuvem", use_container_width=True, help="Envia sessões locais para o GitHub"):
            ok_u, msg_u = push_to_github("manual sync from sidebar")
            if ok_u:
                st.success(msg_u)
            else:
                st.error(msg_u)
                
    with st.expander("🔑 Token de Acesso do GitHub (PAT)"):
        token_input = st.text_input(
            "GitHub Token:", 
            value=st.session_state.get("custom_github_token", ""), 
            type="password",
            placeholder="ghp_...",
            help="Cole um Personal Access Token com permissão 'repo' para permitir commits na nuvem."
        )
        if token_input:
            st.session_state["custom_github_token"] = token_input
        st.markdown("[Criar Token com 1 clique](https://github.com/settings/tokens/new?scopes=repo&description=Concursos+Study+Tracker)")

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
    
    c_f0, c_f1 = st.columns(2)
    with c_f0:
        opcoes_certames_form = {c["id"]: c["name"] for c in st.session_state.certames}
        idx_default = 0
        if filtro_certame_id and filtro_certame_id in opcoes_certames_form:
            idx_default = list(opcoes_certames_form.keys()).index(filtro_certame_id)
            
        certame_escolhido_id = st.selectbox(
            "Certame Alvo:", 
            options=list(opcoes_certames_form.keys()), 
            format_func=lambda x: opcoes_certames_form[x],
            index=idx_default,
            key="reg_certame_id"
        )
        data_sessao = st.date_input("Data do Estudo:", value=date.today(), key="reg_data_sessao")
        
    with c_f1:
        c_obj_form = next((c for c in st.session_state.certames if c["id"] == certame_escolhido_id), st.session_state.certames[0])
        blocos_disponiveis = list(c_obj_form.get("subjects", {}).keys())
        bloco_selecionado = st.selectbox(
            "Bloco / Área:", 
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
            
        disciplina_selecionada = st.selectbox(
            "Disciplina:", 
            materias_disponiveis if materias_disponiveis else ["Geral"],
            key=f"reg_disc_{certame_escolhido_id}_{bloco_selecionado}"
        )
        
    # Extração e seleção automática do tópico oficial do edital
    topicos_disponiveis = []
    if isinstance(raw_disciplinas, dict):
        topicos_cand = raw_disciplinas.get(disciplina_selecionada, [])
        if isinstance(topicos_cand, list):
            topicos_disponiveis = topicos_cand

    if topicos_disponiveis:
        col_top1, col_top2 = st.columns([1.6, 1.0])
        with col_top1:
            topico_escolhido = st.selectbox(
                "Tópico Oficial do Edital (Conteúdo Programático):",
                options=topicos_disponiveis + ["✏️ Outro (digitar manualmente)"],
                key=f"reg_top_sel_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}",
                help="Selecione o tópico específico previsto no edital ou escolha digitar um tema personalizado."
            )
        with col_top2:
            if topico_escolhido == "✏️ Outro (digitar manualmente)":
                topico_custom = st.text_input(
                    "Digite o Tópico Manualmente:",
                    key=f"reg_top_custom_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}",
                    placeholder="Ex: Simulado geral de bancas"
                )
                topico_final = topico_custom.strip() if topico_custom.strip() else disciplina_selecionada
            else:
                complemento = st.text_input(
                    "Subtópico / Complemento (opcional):",
                    key=f"reg_top_comp_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}",
                    placeholder="Ex: Teoria, resumo, flashcards..."
                )
                if complemento.strip():
                    topico_final = f"{topico_escolhido} — {complemento.strip()}"
                else:
                    topico_final = topico_escolhido
    else:
        topico_final = st.text_input(
            "Tópico Específico:", 
            placeholder="Ex: 'Modelo OSI x TCP/IP' ou 'LC 840 - Regime Disciplinar'",
            key=f"reg_top_manual_{certame_escolhido_id}_{bloco_selecionado}_{disciplina_selecionada}"
        )
        if not topico_final.strip():
            topico_final = disciplina_selecionada
    
    c_q1, c_q2, c_q3 = st.columns(3)
    with c_q1:
        tempo_sugerido = minutos_cronometro if minutos_cronometro > 0 else 60
        duracao = st.number_input(
            "Duração em Minutos:", 
            min_value=1, 
            max_value=600, 
            value=int(tempo_sugerido), 
            step=5,
            key="reg_duracao"
        )
    with c_q2:
        q_total = st.number_input("Questões Feitas:", min_value=0, max_value=300, value=0, step=1, key="reg_q_total")
    with c_q3:
        q_corretas = st.number_input("Questões Acertadas:", min_value=0, max_value=300, value=0, step=1, key="reg_q_corretas")
        
    notas = st.text_area(
        "Anotações, Pontos Fortes, Pegadinhas de Banca:", 
        placeholder="Registre observações importantes para o seu Second Brain...",
        key="reg_notas"
    )
    sync_cofre = st.checkbox(
        "Sincronizar com o Cofre Obsidian (se disponível localmente)", 
        value=True, 
        key="reg_sync_cofre"
    )
    
    st.write("")
    submitted = st.button("💾 Salvar Sessão", use_container_width=True, type="primary")
    
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
                "topic": topico_final,
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
                
            # 1. Sincronização Local com o Obsidian (se cofre acessível)
            msg_cofre = ""
            if sync_cofre and cofre_conectado:
                ok_c, res_c = sync_session_to_obsidian_idempotent(nova_sessao, cofre_path)
                msg_cofre = f" | 🧠 Obsidian: {res_c}" if ok_c else f" | ⚠️ Obsidian: {res_c}"
            
            # 2. Sincronização em Nuvem via GitHub API
            msg_gh = ""
            gh_cfg_save = get_github_config()
            if gh_cfg_save["token"]:
                commit_txt = f"feat(estudo): {nova_sessao['duration_min']}min em {nova_sessao['subject']} ({nova_sessao['certame_id']})"
                ok_gh, res_gh = commit_file_to_github(
                    repo=gh_cfg_save["repo"],
                    file_path="data/sessions.json",
                    data_obj=st.session_state.sessions,
                    commit_message=commit_txt,
                    branch=gh_cfg_save["branch"],
                    token=gh_cfg_save["token"]
                )
                msg_gh = f" | ☁️ GitHub: {res_gh}" if ok_gh else f" | ⚠️ GitHub: {res_gh}"
            else:
                msg_gh = " | ℹ️ Nuvem: sem token para auto-commit (salvo localmente)"
                
            st.success(f"✅ Sessão registrada para **{opcoes_certames_form[certame_escolhido_id]}** ({duracao} min em {disciplina_selecionada})!{msg_cofre}{msg_gh}")
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
        st.subheader("🔄 Sincronização em Nuvem (GitHub ↔ Obsidian)")
        col_sync_a, col_sync_b = st.columns(2)
        
        with col_sync_a:
            if st.button("📥 Puxar da Nuvem (GitHub) & Descarregar no Obsidian", use_container_width=True):
                ok_pull, msg_pull = pull_from_github_and_merge()
                if ok_pull:
                    st.info(msg_pull)
                else:
                    st.warning(f"Aviso GitHub: {msg_pull}")
                    
                if cofre_conectado:
                    count_obs = 0
                    for s in st.session_state.sessions:
                        ok_s, _ = sync_session_to_obsidian_idempotent(s, cofre_path)
                        if ok_s:
                            count_obs += 1
                    st.success(f"🧠 {count_obs} sessões verificadas/sincronizadas com o Cofre em {cofre_path}!")
                else:
                    st.warning("Pasta do cofre não acessível neste ambiente para gravação direta.")
                    
        with col_sync_b:
            if st.button("📤 Enviar Todo o Histórico Local para a Nuvem (GitHub)", use_container_width=True):
                ok_push, msg_push = push_to_github(f"feat(data): backup completo de {len(st.session_state.sessions)} sessões")
                if ok_push:
                    st.success(f"☁️ {msg_push}")
                else:
                    st.error(f"Falha ao enviar: {msg_push}")
                    
        st.divider()
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_data = df_all.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Histórico Geral (CSV)", data=csv_data, file_name=f"estudos_geral_{date.today()}.csv", mime="text/csv", use_container_width=True)
        with col_exp2:
            json_data = json.dumps(st.session_state.sessions, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("📥 Baixar Backup Geral (JSON)", data=json_data, file_name=f"backup_estudos_{date.today()}.json", mime="application/json", use_container_width=True)

# ------------------------------------------
# TAB 4: GERENCIAR CERTAMES
# ------------------------------------------
with tab_certames:
    st.subheader("🏛️ Meus Certames & Projetos de Concurso")
    st.markdown("Aqui você pode gerenciar todos os concursos que acompanha ou criar novos certames conforme novos editais forem saindo.")
    
    for c in st.session_state.certames:
        with st.expander(f"📌 {c['name']} — Status: **{c.get('status', 'Ativo')}**"):
            st.markdown(f"- **ID:** `{c['id']}`")
            st.markdown(f"- **Cargo:** {c.get('cargo', '-')}")
            st.markdown(f"- **Banca:** {c.get('banca', '-')}")
            st.markdown(f"- **Data da Prova:** {c.get('exam_date', 'Não definida')}")
            st.markdown(f"- **Metas:** {c.get('daily_target_hours', 2.0)}h/dia | {c.get('weekly_target_hours', 10.0)}h/semana")
            st.markdown("**Conteúdo Programático & Disciplinas:**")
            for blk, mats in c.get("subjects", {}).items():
                if isinstance(mats, dict):
                    st.markdown(f"  * **{blk}:** ({len(mats)} disciplinas)")
                    for m_name, t_list in mats.items():
                        n_top = len(t_list) if isinstance(t_list, list) else 0
                        st.markdown(f"    - **{m_name}** ({n_top} tópicos catalogados)")
                elif isinstance(mats, list):
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
                        "Conhecimentos": {m: [f"1. Estudo geral de {m}"] for m in lista_mats}
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
    st.subheader("🧠 Como Funciona a Sincronização Nuvem ↔ GitHub ↔ Obsidian")
    st.markdown("""
    A arquitetura foi projetada para que você tenha total liberdade de registrar seus estudos de qualquer lugar sem risco de perda de dados:
    
    1. **No Celular ou Navegador Externo (Streamlit Cloud):**
       - Você abre o link do app no celular, estuda e registra a sessão.
       - A aplicação executa um **commit automático** com a nova sessão diretamente no seu repositório GitHub (`m-isac14/concursos-study-tracker/data/sessions.json`).
    2. **No seu Computador (com o Google Drive / Obsidian ativo):**
       - Ao abrir o app no computador (ou rodar `iniciar_estudos.bat`), você clica em **"📥 Puxar da Nuvem & Descarregar no Obsidian"**.
       - O app baixa tudo do GitHub e gera/atualiza as notas `.md` em `G:\\Meu Drive\\cofre\\06-Concursos-e-Estudos\\registros-de-estudo\\`.
    3. **No Obsidian:**
       - O plugin **Dataview** lê os metadados e monta relatórios dinâmicos instantâneos.
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
