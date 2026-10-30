import base64
import json
import os
import urllib.request
import urllib.error
import streamlit as st

DEFAULT_REPO = "m-isac14/concursos-study-tracker"
DEFAULT_BRANCH = "main"

def get_github_config():
    """Recupera as configurações de repositório, branch e token do GitHub."""
    repo = DEFAULT_REPO
    branch = DEFAULT_BRANCH
    token = None

    # 1. Tenta recuperar de st.secrets (Streamlit Cloud ou .streamlit/secrets.toml)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
        if "GITHUB_REPO" in st.secrets:
            repo = st.secrets["GITHUB_REPO"]
        if "GITHUB_BRANCH" in st.secrets:
            branch = st.secrets["GITHUB_BRANCH"]
    except Exception:
        pass

    # 2. Tenta variáveis de ambiente
    if not token and os.environ.get("GITHUB_TOKEN"):
        token = os.environ.get("GITHUB_TOKEN")
    if os.environ.get("GITHUB_REPO"):
        repo = os.environ.get("GITHUB_REPO")
    if os.environ.get("GITHUB_BRANCH"):
        branch = os.environ.get("GITHUB_BRANCH")

    # 3. Tenta input manual salvo no session_state do Streamlit
    if not token and st.session_state.get("custom_github_token"):
        token = st.session_state["custom_github_token"]

    return {
        "repo": repo,
        "branch": branch,
        "token": token
    }

def github_api_request(url, method="GET", token=None, payload=None):
    """Executa requisições HTTP à API do GitHub usando a biblioteca padrão do Python."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Concursos-Study-Tracker/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token.strip()}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"message": err_body}
        return e.code, err_json
    except Exception as e:
        return 500, {"message": str(e)}

def fetch_file_from_github(repo, file_path, branch="main", token=None):
    """Obtém um arquivo do GitHub via API REST decodificando seu base64."""
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    status, data = github_api_request(url, method="GET", token=token)
    
    if status == 200 and "content" in data:
        try:
            raw_content = base64.b64decode(data["content"]).decode("utf-8")
            sha = data.get("sha")
            return json.loads(raw_content), sha, None
        except Exception as e:
            return None, data.get("sha"), f"Falha ao decodificar JSON: {e}"
    elif status == 404:
        return None, None, "Arquivo não encontrado no repositório."
    elif status == 401:
        return None, None, "Token de acesso do GitHub inválido ou expirado."
    elif status == 403:
        return None, None, f"Permissão negada ou limite de requisições da API atingido: {data.get('message', '')}"
    else:
        return None, None, data.get("message", f"Erro HTTP {status}")

def commit_file_to_github(repo, file_path, data_obj, commit_message, branch="main", token=None):
    """Envia alterações em um arquivo JSON diretamente para o repositório GitHub via API REST."""
    if not token:
        return False, "Token do GitHub não configurado. Adicione o GITHUB_TOKEN nas configurações ou Secrets."

    # 1. Busca o SHA atual se o arquivo já existir
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    status, existing = github_api_request(url, method="GET", token=token)
    sha = existing.get("sha") if status == 200 else None

    # 2. Prepara o conteúdo em Base64
    content_str = json.dumps(data_obj, ensure_ascii=False, indent=2)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    # 3. Executa o PUT
    put_status, put_res = github_api_request(url, method="PUT", token=token, payload=payload)
    if put_status in (200, 201):
        commit_sha = put_res.get("commit", {}).get("sha", "")[:7]
        return True, f"Commit realizado com sucesso! (ID: {commit_sha})"
    else:
        err_msg = put_res.get("message", f"Erro HTTP {put_status}")
        return False, f"Falha no commit: {err_msg}"

def sync_session_to_obsidian_idempotent(session, cofre_dir):
    """Grava o registro no Obsidian de forma idempotente (evita duplicatas pelo ID da sessão)."""
    if not os.path.exists(cofre_dir):
        return False, f"Diretório do cofre não encontrado: {cofre_dir}"

    sess_date = session["date"]
    sess_id = str(session.get("id", ""))
    file_path = os.path.join(cofre_dir, f"{sess_date}.md")
    certame_tag = str(session.get("certame_id", "geral")).lower().replace(" ", "-")

    entry = f"""
### ⏱️ [{session.get('certame_id', 'Geral')}] {session['subject']} — {session['duration_min']} min <!-- id:{sess_id} -->
- **Certame:** {session.get('certame_name', session.get('certame_id', 'Geral'))}
- **Bloco:** {session['block']}
- **Tópico:** {session.get('topic', '-')}
- **Duração:** {session['duration_min']} minutos ({session['duration_min']/60:.2f}h)
- **Questões:** {session.get('questions_correct', 0)} / {session.get('questions_total', 0)} acertos ({session.get('accuracy_pct', 0)}%)
"""
    if session.get("notes"):
        entry += f"- **Notas / Pegadinhas:** {session['notes']}\n"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        # Verifica se essa sessão já foi gravada
        if sess_id and f"<!-- id:{sess_id} -->" in current_content:
            return True, "Sessão já registrada anteriormente no arquivo do dia."

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        header = f"""---
tags:
  - registro-estudo
  - concursos
  - {certame_tag}
date: {sess_date}
certame: {session.get('certame_id', 'Geral')}
---

# 📅 Registro de Estudo — {sess_date}

Voltar para: [[06-Concursos-e-Estudos/00-HUB-CONCURSOS|00-HUB-CONCURSOS.md]] | [[06-Concursos-e-Estudos/plano-de-estudo-dpdf-2027|plano-de-estudo-dpdf-2027.md]]
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header + entry)

    return True, "Sincronizado com sucesso no cofre!"
