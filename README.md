# 🛡️ DPDF Study Tracker — Painel Inteligente de Estudos

Aplicação web desenvolvida em **Streamlit (Python)** para gerenciar horas líquidas, desempenho por banca, cumprimento da meta diária de 2h e alocação de tempo (Regra 70/30) para o concurso da **Defensoria Pública do Distrito Federal (DPDF 2026/2027)** — Cargo 5: Analista de TI (Redes).

---

## 🚀 Como Rodar Localmente

1. Abra a pasta do projeto:
   ```cmd
   cd "C:\Users\isacm\OneDrive\Desktop\Isac\Concursos\dpdf-study-tracker"
   ```
2. Dê dois cliques no arquivo `iniciar_estudos.bat` ou execute no terminal:
   ```bash
   venv\Scripts\activate
   streamlit run app.py
   ```
3. O painel abrirá automaticamente no navegador em `http://localhost:8501`.

---

## ☁️ Como Hospedar Gratuitamente na Nuvem (Streamlit Community Cloud)

1. Crie um repositório no seu GitHub (`https://github.com/m-isac14/dpdf-study-tracker`).
2. Faça o commit e push dos arquivos:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit DPDF study tracker"
   git branch -M main
   git remote add origin https://github.com/m-isac14/dpdf-study-tracker.git
   git push -u origin main
   ```
3. Acesse [share.streamlit.io](https://share.streamlit.io/) e faça login com seu GitHub (`m-isac14`).
4. Clique em **"New app"**, selecione o repositório `dpdf-study-tracker`, a branch `main` e o arquivo `app.py`.
5. Clique em **"Deploy"**! Sua aplicação estará no ar 24/7 com URL pública acessível do celular ou de qualquer computador.

---

## 🧠 Integração com o Cofre Obsidian

Cada sessão salva grava automaticamente notas em:
`G:\Meu Drive\cofre\06-Concursos-e-Estudos\registros-de-estudo\<DATA>.md`

Compatível com o plugin **Dataview** do Obsidian para consultas dinâmicas.
