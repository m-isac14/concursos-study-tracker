import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os
import pathlib

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="DPDF Study Tracker | Isac",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
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
    .metric-val {
        font-size: 1.8rem;
        font-weight: bold;
        color: #ECEFF1;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #78909C;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTES DO CONCURSO DPDF 2026/2027
# ==========================================
PROVA_DATA = datetime(2027, 2, 21, 8, 0, 0)
META_DIARIA_HORAS = 2.0
META_SEMANAL_HORAS = 10.0

COFRE_DIR_DEFAULT = r"G:\Meu Drive\cofre\06-Concursos-e-Estudos\registros-de-estudo"
COFRE_MATRIZ_DEFAULT = r"G:\Meu Drive\cofre\06-Concursos-e-Estudos\matriz-de-desempenho-e-materias.md"
LOCAL_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "sessions.json")

DISCIPLINAS_CONFIG = {
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

# ==========================================
# FUNÇÕES DE PERSISTÊNCIA E DADOS
# ==========================================
def ensure_data_dir():
    data_dir = os.path.dirname(LOCAL_DATA_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

def load_sessions():
    ensure_data_dir()
    if os.path.exists(LOCAL_DATA_FILE):
        try:
            with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_sessions(sessions):
    ensure_data_dir()
    with open(LOCAL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def sync_session_to_obsidian(session, cofre_dir):
    """Grava o registro no Cofre Obsidian como nota markdown estruturada para Dataview."""
    if not os.path.exists(cofre_dir):
        return False, f"Diretório do cofre não encontrado: {cofre_dir}"
    
    sess_date = session["date"]
    file_path = os.path.join(cofre_dir, f"{sess_date}.md")
    
    # Se o arquivo do dia já existir, adiciona a sessão; senão cria com cabeçalho
    if os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n### ⏱️ Sessão: {session['subject']} — {session['duration_min']} min\n")
            f.write(f"- **Bloco:** {session['block']}\n")
            f.write(f"- **Tópico:** {session.get('topic', '-')}\n")
            f.write(f"- **Duração:** {session['duration_min']} minutos ({session['duration_min']/60:.2f}h)\n")
            f.write(f"- **Questões:** {session.get('questions_correct', 0)} / {session.get('questions_total', 0)} acertos ({session.get('accuracy_pct', 0)}%)\n")
            if session.get("notes"):
                f.write(f"- **Notas / Pegadinhas:** {session['notes']}\n")
    else:
        content = f"""---
tags:
  - registro-estudo
  - concursos
  - dpdf
date: {sess_date}
---

# 📅 Registro de Estudo — {sess_date}

Voltar para: [[06-Concursos-e-Estudos/00-HUB-CONCURSOS|00-HUB-CONCURSOS.md]] | [[06-Concursos-e-Estudos/plano-de-estudo-dpdf-2027|plano-de-estudo-dpdf-2027.md]]

### ⏱️ Sessão: {session['subject']} — {session['duration_min']} min
- **Bloco:** {session['block']}
- **Tópico:** {session.get('topic', '-')}
- **Duração:** {session['duration_min']} minutos ({session['duration_min']/60:.2f}h)
- **Questões:** {session.get('questions_correct', 0)} / {session.get('questions_total', 0)} acertos ({session.get('accuracy_pct', 0)}%)
"""
        if session.get("notes"):
            content += f"- **Notas / Pegadinhas:** {session['notes']}\n"
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    return True, "Sincronizado com sucesso!"

# Inicializa sessões no session_state
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions()

# Inicializa estado do cronômetro
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

# ==========================================
# SIDEBAR: RADAR DPDF & CRONÔMETRO
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("DPDF 2026/2027")
    st.caption("Cargo 5: Analista de TI — Redes | Banca: ACCESS")
    
    # Contagem Regressiva
    agora = datetime.now()
    delta = PROVA_DATA - agora
    if delta.total_seconds() > 0:
        dias = delta.days
        horas = delta.seconds // 3600
        st.info(f"⏳ **Faltam {dias} dias e {horas}h** para a prova (21/02/2027)")
    else:
        st.success("🎉 Chegou a data da prova!")
        
    st.divider()
    
    # Seção do Cronômetro Ativo
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
    
    # Configuração do Cofre
    st.subheader("⚙️ Conexão com Obsidian")
    cofre_path = st.text_input("Caminho do Cofre:", value=COFRE_DIR_DEFAULT)
    cofre_conectado = os.path.exists(cofre_path)
    if cofre_conectado:
        st.success("🟢 Cofre conectado!")
    else:
        st.warning("🟡 Cofre local não detectado (modo nuvem)")

# ==========================================
# CORPO PRINCIPAL
# ==========================================
st.markdown('<p class="main-title">🛡️ Painel de Estudos — DPDF 2026/2027</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Gestão inteligente de horas líquidas, desempenho por banca e integração viva com o Second Brain</p>', unsafe_allow_html=True)

# Processa DataFrame de sessões
df = pd.DataFrame(st.session_state.sessions)
if not df.empty:
    df["date"] = pd.to_datetime(df["date"])
    df["hours"] = df["duration_min"] / 60.0
    
    hoje = pd.to_datetime(date.today())
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    
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
# ABAS DE NAVEGAÇÃO
# ==========================================
tab_dash, tab_reg, tab_hist, tab_obsidian = st.tabs([
    "📊 Dashboard & Insights",
    "⏱️ Registrar Nova Sessão",
    "📋 Histórico & Gestão",
    "🧠 Integração com o Cofre & Dataview"
])

# ------------------------------------------
# TAB 1: DASHBOARD & INSIGHTS
# ------------------------------------------
with tab_dash:
    # Cards de Métricas Principais
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="📅 Horas Hoje", 
            value=f"{horas_hoje:.1f}h", 
            delta=f"{(horas_hoje - META_DIARIA_HORAS):.1f}h da meta (2h)"
        )
        prog_dia = min(horas_hoje / META_DIARIA_HORAS, 1.0)
        st.progress(prog_dia, text=f"{prog_dia*100:.0f}% da meta diária")
        
    with c2:
        st.metric(
            label="🗓️ Horas na Semana", 
            value=f"{horas_semana:.1f}h", 
            delta=f"{(horas_semana - META_SEMANAL_HORAS):.1f}h da meta (10h)"
        )
        prog_sem = min(horas_semana / META_SEMANAL_HORAS, 1.0)
        st.progress(prog_sem, text=f"{prog_sem*100:.0f}% da meta semanal")
        
    with c3:
        st.metric(label="📆 Horas no Mês", value=f"{horas_mes:.1f}h")
        st.caption(f"Acumulado total: **{horas_total:.1f}h**")
        
    with c4:
        st.metric(
            label="🎯 Questões Resolvidas", 
            value=f"{total_q_feitas}", 
            delta=f"{taxa_geral:.1f}% de acertos"
        )
        st.caption(f"{total_q_acertos} acertos no total")
        
    st.divider()
    
    if df.empty:
        st.info("💡 Nenhuma sessão registrada ainda. Vá na aba **⏱️ Registrar Nova Sessão** para registrar seu primeiro estudo!")
    else:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("⚖️ Regra 70 / 30 (Alocação de Tempo)")
            st.caption("Meta do edital: 70% em Específicos de TI e 30% em Básicos")
            
            bloco_horas = df.groupby("block")["hours"].sum().reset_index()
            fig_bloco = px.pie(
                bloco_horas, 
                values="hours", 
                names="block",
                hole=0.45,
                color="block",
                color_discrete_map={
                    "Conhecimentos Específicos (Peso 2)": "#1E88E5",
                    "Conhecimentos Básicos (Peso 1)": "#FFB300",
                    "Discursivas": "#43A047"
                }
            )
            fig_bloco.update_traces(textinfo="percent+label")
            fig_bloco.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_bloco, use_container_width=True)
            
        with col_g2:
            st.subheader("📚 Horas por Disciplina")
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
                
                # Cores baseadas nas metas: 🟢 >80%, 🟡 65-80%, 🔴 <65%
                cores = ["#EF5350" if t < 65 else "#FFCA28" if t < 80 else "#66BB6A" for t in mat_q["taxa"]]
                
                fig_taxa = go.Figure(go.Bar(
                    x=mat_q["taxa"],
                    y=mat_q["subject"],
                    orientation="h",
                    marker_color=cores,
                    text=[f"{t}% ({c}/{tot})" for t, c, tot in zip(mat_q["taxa"], mat_q["questions_correct"], mat_q["questions_total"])],
                    textposition="auto"
                ))
                fig_taxa.update_layout(
                    xaxis=dict(title="Taxa de Acertos (%)", range=[0, 100]),
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig_taxa, use_container_width=True)
            else:
                st.caption("Nenhuma questão com acertos registrada ainda.")
                
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
            fig_consist.add_hline(y=2.0, line_dash="dash", line_color="#FFB300", annotation_text="Meta (2h)")
            fig_consist.update_layout(margin=dict(t=10, b=10, l=10, r=10), coloraxis_showscale=False)
            st.plotly_chart(fig_consist, use_container_width=True)

# ------------------------------------------
# TAB 2: REGISTRAR NOVA SESSÃO
# ------------------------------------------
with tab_reg:
    st.subheader("📝 Registrar Sessão de Estudo")
    
    with st.form("form_nova_sessao", clear_on_submit=False):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            data_sessao = st.date_input("Data do Estudo:", value=date.today())
            bloco_selecionado = st.selectbox("Bloco do Edital:", list(DISCIPLINAS_CONFIG.keys()))
            materia_opcoes = DISCIPLINAS_CONFIG[bloco_selecionado]
            disciplina_selecionada = st.selectbox("Disciplina:", materia_opcoes)
            topico = st.text_input("Tópico Específico (ex: 'Arts. 22 a 29 - Posse e Exercício' ou 'Sub-redes e CIDR'):")
            
        with c_f2:
            # Sugere o valor do cronômetro se houver
            tempo_sugerido = minutos_cronometro if minutos_cronometro > 0 else 60
            duracao = st.number_input("Duração em Minutos:", min_value=1, max_value=600, value=int(tempo_sugerido), step=5)
            
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                q_total = st.number_input("Questões Feitas:", min_value=0, max_value=200, value=0, step=1)
            with col_q2:
                q_corretas = st.number_input("Questões Acertadas:", min_value=0, max_value=200, value=0, step=1)
                
            if q_total > 0 and q_corretas > q_total:
                st.error("O número de acertos não pode ser maior que o total de questões!")
                
            sync_cofre = st.checkbox("Sincronizar automaticamente com o Cofre Obsidian", value=True)
            
        notas = st.text_area("Anotações, Pegadinhas ou Dificuldades (será enviado ao cofre):", placeholder="Ex: Cuidado com o prazo de 30 dias da posse na LC 840...")
        
        submitted = st.form_submit_button("💾 Salvar Sessão de Estudo", use_container_width=True)
        
        if submitted:
            if q_total > 0 and q_corretas > q_total:
                st.error("Corrija a quantidade de acertos antes de salvar.")
            else:
                acc = round((q_corretas / q_total * 100), 1) if q_total > 0 else 0.0
                nova_sessao = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
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
                
                # Zera cronômetro se foi usado
                if minutos_cronometro > 0:
                    st.session_state.timer_running = False
                    st.session_state.elapsed_seconds = 0
                    st.session_state.timer_start = None
                    
                msg_cofre = ""
                if sync_cofre and cofre_conectado:
                    ok, res = sync_session_to_obsidian(nova_sessao, cofre_path)
                    msg_cofre = f" e {res}" if ok else f" (Aviso Cofre: {res})"
                    
                st.success(f"✅ Sessão salva com sucesso ({duracao} min em {disciplina_selecionada}){msg_cofre}!")
                st.rerun()

# ------------------------------------------
# TAB 3: HISTÓRICO & GESTÃO
# ------------------------------------------
with tab_hist:
    st.subheader("📋 Todas as Sessões Registradas")
    
    if df.empty:
        st.info("Nenhuma sessão registrada até o momento.")
    else:
        # Filtros rápidos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_mat = st.multiselect("Filtrar por Disciplina:", options=sorted(df["subject"].unique()))
        with col_f2:
            filtro_bloco = st.multiselect("Filtrar por Bloco:", options=sorted(df["block"].unique()))
            
        df_view = df.copy()
        if filtro_mat:
            df_view = df_view[df_view["subject"].isin(filtro_mat)]
        if filtro_bloco:
            df_view = df_view[df_view["block"].isin(filtro_bloco)]
            
        st.dataframe(
            df_view[["date", "block", "subject", "topic", "duration_min", "hours", "questions_total", "questions_correct", "accuracy_pct", "notes"]],
            column_config={
                "date": st.column_config.DateColumn("Data"),
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
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Histórico em CSV", data=csv_data, file_name=f"estudos_dpdf_{date.today()}.csv", mime="text/csv", use_container_width=True)
        with col_exp2:
            json_data = json.dumps(st.session_state.sessions, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("📥 Baixar Backup em JSON", data=json_data, file_name=f"estudos_dpdf_{date.today()}.json", mime="application/json", use_container_width=True)
        with col_exp3:
            if st.button("🔄 Sincronizar Tudo c/ Cofre", use_container_width=True):
                if cofre_conectado:
                    count = 0
                    for s in st.session_state.sessions:
                        sync_session_to_obsidian(s, cofre_path)
                        count += 1
                    st.success(f"✅ {count} sessões sincronizadas com {cofre_path}!")
                else:
                    st.error("Cofre não encontrado no caminho especificado.")

# ------------------------------------------
# TAB 4: INTEGRAÇÃO OBSIDIAN & DATAVIEW
# ------------------------------------------
with tab_obsidian:
    st.subheader("🧠 Como seus Dados Integram com o Second Brain")
    st.markdown(f"""
    Cada sessão salva no Study Tracker é automaticamente gravada em:
    `{COFRE_DIR_DEFAULT}\\<DATA>.md`
    
    Isso significa que você tem o melhor dos dois mundos:
    1. **Visualização Gráfica Interativa** aqui no aplicativo web;
    2. **Propriedade Completa dos Dados** em notas puras Markdown no Obsidian com links bidirecionais.
    """)
    
    st.divider()
    st.subheader("📋 Códigos Prontos do Dataview para Colar no Obsidian")
    st.caption("Copie qualquer um dos blocos abaixo e cole em qualquer nota do seu cofre para gerar relatórios dinâmicos automáticos:")
    
    st.markdown("**1. Tabela com as Últimas Sessões de Estudo Registradas:**")
    st.code("""```dataview
TABLE file.mtime AS "Registrado em", date AS "Data do Estudo"
FROM "06-Concursos-e-Estudos/registros-de-estudo"
SORT file.mtime DESC
LIMIT 10
```""", language="markdown")

    st.markdown("**2. Lista com Resumo Diário de Estudos:**")
    st.code("""```dataview
LIST
FROM "06-Concursos-e-Estudos/registros-de-estudo"
SORT file.name DESC
LIMIT 7
```""", language="markdown")
