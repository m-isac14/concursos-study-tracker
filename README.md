# 🎯 Central de Estudos — Plataforma Unificada de Concursos Públicos

Plataforma inteligente desenvolvida em **Python + Streamlit** para gerenciar a **trajetória completa de estudos para concursos públicos** do Isac, com suporte nativo a múltiplos certames (DPDF, CGU, DATAPREV, Ciclo Base TI) e integração contínua ao **Second Brain no Obsidian (`G:\Meu Drive\cofre`)**.

---

## 🏛️ Funcionalidades Centrais

1. **🌐 Visão Consolidada da Trajetória:**
   - Acompanhamento do total histórico de horas estudadas ao longo dos meses e anos.
   - Gráfico de distribuição de tempo entre diferentes concursos.
   - Rendimento unificado em questões por disciplina (ex.: histórico de acertos em Banco de Dados, Redes, Português, etc. independentemente do certame).
2. **🎯 Modo Foco por Certame:**
   - Selecione um certame específico (ex.: **DPDF 2026/2027**) para ver:
     - Contagem regressiva da data da prova (21/02/2027);
     - Meta diária (2h) e semanal (10h);
     - Regra 70/30 (Específicos vs Básicos);
     - Grade de matérias exatas do edital.
3. **➕ Gestão Dinâmica de Certames:**
   - Adicione novos concursos com poucos cliques (nome, cargo, banca, data da prova e matérias) conforme novos editais forem publicados.
4. **🧠 Sincronização com o Obsidian (Dataview):**
   - Salva automaticamente as sessões em `G:\Meu Drive\cofre\06-Concursos-e-Estudos\registros-de-estudo\<DATA>.md` com metadados do certame e tags `#dpdf`, `#cgu`, etc.

---

## 🚀 Como Rodar Localmente

1. Dê dois cliques em **`iniciar_estudos.bat`** ou execute:
   ```powershell
   cd "C:\Users\isacm\OneDrive\Desktop\Isac\Concursos\concursos-study-tracker"
   .\venv\Scripts\activate
   streamlit run app.py
   ```
2. O navegador abrirá automaticamente em `http://localhost:8501`.

---

## ☁️ Como Hospedar na Nuvem (Streamlit Community Cloud)

1. Crie um repositório no seu GitHub: `https://github.com/m-isac14/concursos-study-tracker`.
2. Execute no terminal:
   ```powershell
   git add .
   git commit -m "feat: central study platform with multi-certame support"
   git branch -M main
   git remote add origin https://github.com/m-isac14/concursos-study-tracker.git
   git push -u origin main
   ```
3. No [share.streamlit.io](https://share.streamlit.io/), selecione o repositório `concursos-study-tracker` e dê **Deploy**.
