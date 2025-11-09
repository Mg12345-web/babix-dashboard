# babix_mbft_app.py
# ⚖️ Babix – QQROC + Verificação MBFT (upload único, layout moderno)
# Reqs: streamlit, PyPDF2

import os
import re
from difflib import SequenceMatcher
import streamlit as st
import PyPDF2

# =============================
# CONFIGURAÇÃO DE PÁGINA / ESTILO
# =============================
st.set_page_config(
    page_title="Babix – QQROC + MBFT",
    page_icon="⚖️",
    layout="centered"
)

st.markdown("""
<style>
:root{
  --bg:#F6F8FB; --card:#ffffff; --accent:#0A66C2; --muted:#5b6b7a; --ok:#1b8f3e; --warn:#b88700; --err:#c23b3b;
}
body {background-color: var(--bg);}
.block-container {padding: 2rem 2.2rem 3rem;}
h1,h2,h3,h4 {color:#0b2b4a;}
small, .caption {color:var(--muted);}
.card{
  background:var(--card); border-radius:14px; padding:18px 18px 16px;
  box-shadow:0 10px 26px rgba(16,24,40,.06), 0 2px 4px rgba(16,24,40,.03);
  margin:12px 0;
}
.kpi{
  display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:0.95rem;
  padding:.55rem .8rem; border-radius:10px; background:#f2f6ff; color:#153561;
}
.badge{display:inline-flex;align-items:center;border-radius:999px;padding:.15rem .6rem;font-size:.8rem;font-weight:700}
.badge.ok{background:#e8f6ed;color:var(--ok)}
.badge.warn{background:#fff7e5;color:var(--warn)}
.badge.err{background:#fdecec;color:var(--err)}
.obs{background:#f3f7ff;border-left:4px solid var(--accent);padding:.75rem;border-radius:6px}
.code-pill{font-family:ui-monospace, SFMono-Regular, Menlo, monospace;background:#eef2f8;color:#0b2b4a;border-radius:8px;padding:.2rem .45rem}
hr{border:none;height:1px;background:#e8eef6;margin:14px 0}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Babix – Análise de Multas (QQROC + MBFT)")
st.caption("Upload único • Extração robusta • Comparação inteligente do campo Observações com a ficha do MBFT")

# =============================
# HELPERS
# =============================

def read_pdf_text(file_obj) -> str:
    """Extrai todo o texto de um PDF com PyPDF2. (Sem OCR)"""
    try:
        reader = PyPDF2.PdfReader(file_obj)
        txt = ""
        for p in reader.pages:
            txt += p.extract_text() or ""
        return txt
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return ""

def norm_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def extract_codigo_infracao(texto: str) -> str | None:
    """
    Extrai especificamente o CÓDIGO DA INFRAÇÃO, ignorando 'código do órgão', etc.
    1) tenta achar o rótulo 'CÓDIGO DA INFRAÇÃO <numero>'
    2) fallback: procura num bloco onde 'DESCRIÇÃO DA INFRAÇÃO' aparece.
    """
    # 1) padrão contextual explícito
    m = re.search(r"C[ÓO]DIGO\s+DA\s+INFRA[ÇC][ÃA]O\s*[:\-]?\s*([0-9]{3,4}[ \-–]?[\d]{1,2})",
                  texto, flags=re.IGNORECASE)
    if m:
        return m.group(1).replace("–", "-").replace(" ", "")

    # 2) fallback perto da descrição da infração
    bloco = re.search(r"(C[ÓO]DIGO\s+DA\s+INFRA[ÇC][ÃA]O.*?DESCRI[ÇC][ÃA]O\s+DA\s+INFRA[ÇC][ÃA]O)",
                      texto, flags=re.IGNORECASE | re.DOTALL)
    if bloco:
        m2 = re.search(r"([0-9]{3,4}[ \-–]?[\d]{1,2})", bloco.group(1))
        if m2:
            return m2.group(1).replace("–", "-").replace(" ", "")
    # 3) derradeira tentativa: busca 527-41 em qualquer lugar, mas só se houver palavra 'INFRAÇÃO' a até 40 chars antes
    m3 = re.search(r"INFRA[ÇC][ÃA]O.{0,40}([0-9]{3,4}[ \-–]?[\d]{1,2})", texto, flags=re.IGNORECASE|re.DOTALL)
    if m3:
        return m3.group(1).replace("–", "-").replace(" ", "")
    return None

# rótulos fortes recorrentes no layout SENATRAN para delimitar seções
NA_TITLES = [
    "EMBARCADOR/TRANSPORTADOR",
    "IDENTIFICAÇÃO DO PROPRIETÁRIO",
    "IDENTIFICAÇÃO DO PROPRIETARIO",
    "IDENTIFICAÇÃO DO AGENTE",
    "IDENTIFICAÇÃO DO LOCAL",
    "MENSAGEM SENATRAN",
    "REGISTRO FOTOGRÁFICO",
    "IDENTIFICAÇÃO DO CONDUTOR",
    "IDENTIFICAÇÃO DO VEÍCULO",
    "IDENTIFICAÇÃO DA AUTUAÇÃO",
    "NOTIFICAÇÃO DE AUTUAÇÃO",
    "CÓDIGO DO ÓRGÃO",
    "CÓDIGO DO ÓRGÃO AUTUADOR",
    "CÓDIGO DO MUNICÍPIO",
    "IDENTIFICAÇÃO DA INFRAÇÃO",
]

def extract_observacoes_auto(texto: str) -> str:
    """
    Extrai o conteúdo do campo OBSERVAÇÃO/OBSERVAÇÕES/OBS: da NA (SENATRAN).
    Pega o bloco entre o rótulo 'OBS...' e o próximo título conhecido do layout.
    """
    upper = texto.upper()

    # achar a âncora (OBSERVAÇÃO|OBSERVAÇÕES|OBS:)
    anchor = re.search(r"\bOBS(?:ERVA[ÇC][ÃA]O(?:ES)?)?\b\s*:?", upper)
    if not anchor:
        # também tentamos "EXEMPLOS DO CAMPO DE OBSERVAÇÕES DO AIT" (caso suba a ficha por engano)
        return "(Campo de Observações não encontrado)"

    start = anchor.start()
    tail = texto[start:]

    # construir regex de parada com os títulos conhecidos
    stop_pat = r"|".join([re.escape(t) for t in NA_TITLES])
    stop = re.search(rf"(?:\n|\r|\r\n)\s*(?:{stop_pat})\b", tail, flags=re.IGNORECASE)
    if stop:
        bloco = tail[:stop.start()]
    else:
        bloco = tail

    # remover o cabeçalho 'OBS...' e aparar
    bloco = re.sub(r"^(?is).*?OBS(?:ERVA[ÇC][ÃA]O(?:ES)?)?\s*:?", "", bloco).strip()

    # às vezes vem tudo colado sem espaços — normalizar
    bloco = norm_spaces(bloco)

    # reduzir lixo quando o parser pega a coluna toda
    # heurística: limitar a 600 chars e parar em pontuação forte
    corte = re.search(r"(.{0,600}[\.!?])", bloco)
    if corte:
        bloco = corte.group(1).strip()
    else:
        bloco = bloco[:600].strip()

    return bloco if bloco else "(Campo de Observações vazio)"

def find_mbft_file(codigo: str, pasta="fichas_mbft") -> str | None:
    """
    Procura a ficha no diretório por padrões com e sem hífen.
    Ex: '527-41' casa '527-41*.pdf' e '52741*.pdf'
    """
    if not codigo:
        return None
    if not os.path.exists(pasta):
        return None
    norm1 = codigo
    norm2 = codigo.replace("-", "")
    for f in os.listdir(pasta):
        if not f.lower().endswith(".pdf"): 
            continue
        name = f.lower()
        if norm1.lower() in name or norm2.lower() in name:
            return os.path.join(pasta, f)
    return None

def extract_mbft_observation_context(full_text: str) -> dict:
    """
    Lê a ficha inteira e extrai:
      - trecho principal (seção 'Exemplos do Campo de Observações do AIT')
      - contextos adicionais com menções 'observa'
      - flag de obrigatoriedade (deve constar/obrigatório/necessário)
    """
    t = full_text
    low = t.lower()

    # seção principal: entre o título e o próximo bloco em CAIXA ALTA ou seção conhecida
    principal = ""
    m = re.search(r"(exemplos\s+do\s+campo\s+de\s+observa[çc][ãa]o(?:es)?\s+do\s+ait.*?)(?:\n[A-Z][A-Z \t/()ºª0-9\.\-]{5,}\n|quando\s+autuar|defini[çc][õo]es|$)",
                  low, flags=re.DOTALL|re.IGNORECASE)
    if m:
        principal = m.group(1)

    # contextos menores com 'observa' ao redor
    contextos = re.findall(r".{0,120}observa.{0,220}", low)

    obrigatorio = any(p in low for p in ["deve constar", "obrigat", "necessário", "registrar no campo"])

    # limpar e devolver versão legível
    def clean(s): 
        return norm_spaces(re.sub(r"\s+", " ", s or "")).strip()

    return {
        "trecho_principal": clean(principal),
        "contextos": [clean(c) for c in contextos[:12]],  # limitar ruído
        "obrigatorio": obrigatorio
    }

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

def compare_observations(obs_auto: str, mbft_ctx: dict) -> tuple[str, str, float]:
    """
    Compara Observações do Auto com o contexto da ficha.
    Retorna (status_text, color, best_score)
    """
    if not obs_auto or "não encontrado" in obs_auto.lower():
        return ("❌ Observações não encontradas no Auto", "err", 0.0)

    candidates = []
    if mbft_ctx.get("trecho_principal"):
        candidates.append(mbft_ctx["trecho_principal"])
    candidates.extend(mbft_ctx.get("contextos", []))

    best = 0.0
    for c in candidates:
        best = max(best, similarity(obs_auto, c))

    # heurística: além de similarity, verificar presença de palavras-chave do principal
    bonus = 0.0
    principal = mbft_ctx.get("trecho_principal", "")
    if principal:
        keys = [w for w in re.findall(r"[a-zà-ú\-]{5,}", principal.lower()) if w not in {"observações","observacao","quando","autuar","definições","procedimentos"}]
        hit = sum(1 for k in keys if k in obs_auto.lower())
        if len(keys) > 0:
            bonus = min(0.15, hit / max(10, len(keys)) * 0.15)
    score = min(1.0, best + bonus)

    if score >= 0.72:
        return ("✅ Condizente com a ficha MBFT", "ok", score)
    elif score >= 0.45:
        return ("⚠️ Parcialmente coerente (pode estar incompleto)", "warn", score)
    else:
        return ("❌ Divergente do que a ficha MBFT exige", "err", score)

# =============================
# QQROC – CHECAGENS BÁSICAS
# =============================

def qqroc_quem(texto: str) -> str:
    org = re.search(r"ÓRG[ÃA]O\s+AUTUADOR\s*[:\n]\s*(.+)", texto, re.IGNORECASE)
    return norm_spaces(org.group(1)) if org else "(Órgão/Autoridade não identificado)"

def qqroc_que(texto: str, codigo: str | None) -> str:
    desc = re.search(r"DESCRI[ÇC][ÃA]O\s+DA\s+INFRA[ÇC][ÃA]O\s*[:\n]\s*(.+)", texto, re.IGNORECASE)
    d = norm_spaces(desc.group(1)) if desc else "(Descrição não localizada)"
    return f"Código: {codigo or '—'} • {d}"

def qqroc_requisitos(texto: str) -> list[str]:
    problemas = []
    if not re.search(r"\bLOCAL DA INFRA[ÇC][ÃA]O\b", texto, re.IGNORECASE): problemas.append("Local da infração ausente")
    if not re.search(r"\bDATA\b", texto, re.IGNORECASE): problemas.append("Data ausente")
    if not re.search(r"\bHORA\b", texto, re.IGNORECASE): problemas.append("Hora ausente")
    if not re.search(r"\bPLACA\b", texto, re.IGNORECASE): problemas.append("Placa ausente")
    # instrumento de aferição pode ser "Não disponível" — sinalizar como alerta, não erro
    if re.search(r"INSTRUMENTO DE AFERI[ÇC][ÃA]O", texto, re.IGNORECASE) and re.search(r"n[aã]o dispon[íi]vel", texto, re.IGNORECASE):
        problemas.append("Instrumento de aferição 'Não disponível'")
    return problemas

def qqroc_consequencia(status_obs: str, obrigatorio: bool) -> tuple[str, str]:
    """
    Regra simples:
      - Se a ficha indica obrigatoriedade e Observações está divergente/ausente -> nulidade provável
      - Se parcial -> orientar complementação
      - Se ok -> válido quanto a esse requisito (demais itens ainda contam)
    """
    if "❌" in status_obs and obrigatorio:
        return ("Provável nulidade por descumprimento do requisito descritivo (MBFT).", "err")
    if "⚠️" in status_obs and obrigatorio:
        return ("Aparente omissão descritiva; recomendada impugnação pela insuficiência de relato.", "warn")
    return ("Requisito descritivo atendido quanto ao MBFT (verificar demais vícios formais/materiais).", "ok")

# =============================
# UI – UPLOAD & PIPELINE
# =============================

st.markdown("### 📄 Envie o Auto de Infração (PDF)")
auto_pdf = st.file_uploader("Arraste o PDF aqui (NA/SENATRAN)", type=["pdf"])

with st.expander("ℹ️ Como funciona (resumo)", expanded=False):
    st.write("""
1) Lemos o PDF da autuação; 2) extraímos CÓDIGO DA INFRAÇÃO; 3) achamos a ficha no diretório `fichas_mbft`;
4) comparamos **Observações do Auto** × **Exemplos/Contexto de Observações do MBFT**; 5) exibimos QQROC com diagnóstico.
""")

if auto_pdf:
    # texto do auto
    auto_txt = read_pdf_text(auto_pdf)
    st.markdown("<div class='card kpi'>📎 Arquivo recebido</div>", unsafe_allow_html=True)

    codigo = extract_codigo_infracao(auto_txt)
    st.markdown(
        f"<div class='card'><b>🆔 CÓDIGO DA INFRAÇÃO:</b> "
        f"<span class='code-pill'>{codigo or 'não localizado'}</span></div>",
        unsafe_allow_html=True
    )

    obs_auto = extract_observacoes_auto(auto_txt)
    st.markdown("<div class='card'><b>📝 Campo de Observações (Auto):</b><div class='obs' style='margin-top:.5rem;'>"
                f"{(obs_auto if len(obs_auto)<1200 else obs_auto[:1200]+' …')}"
                "</div></div>", unsafe_allow_html=True)

    # localizar ficha
    ficha_path = find_mbft_file(codigo)
    if not ficha_path:
        st.markdown("<div class='card'><span class='badge err'>Ficha MBFT não encontrada</span><br>"
                    "Coloque o PDF correspondente em <code>./fichas_mbft/</code> (aceita '527-41' ou '52741' no nome do arquivo).</div>",
                    unsafe_allow_html=True)
        st.stop()

    st.markdown(f"<div class='card'>📘 Ficha MBFT: <span class='code-pill'>{os.path.basename(ficha_path)}</span></div>", unsafe_allow_html=True)
    ficha_txt = read_pdf_text(open(ficha_path, "rb"))
    mbft_ctx = extract_mbft_observation_context(ficha_txt)

    # comparação
    status_obs, color_obs, score = compare_observations(obs_auto, mbft_ctx)
    st.markdown(f"<div class='card'><span class='badge {color_obs}'>{status_obs}</span>"
                f"<div style='margin-top:.5rem;font-size:.9rem;color:var(--muted)'>similaridade: {score:.2%}</div></div>",
                unsafe_allow_html=True)

    with st.expander("👁️ Trecho principal – MBFT (observações)"):
        st.write(mbft_ctx.get("trecho_principal") or "(Nada localizado)")
    with st.expander("🔎 Outros contextos com 'observa' na ficha"):
        ctxs = mbft_ctx.get("contextos") or []
        if ctxs:
            for i, c in enumerate(ctxs, 1):
                st.markdown(f"**{i}.** {c}")
        else:
            st.write("(Nenhum contexto adicional)")

    # =============================
    # QQROC – PAINEL
    # =============================
    st.markdown("## 📊 QQROC – Diagnóstico")
    # Q – Quem
    quem = qqroc_quem(auto_txt)
    st.markdown(f"<div class='card'><b>Q – Quem:</b> {quem}</div>", unsafe_allow_html=True)

    # Q – Que
    que = qqroc_que(auto_txt, codigo)
    st.markdown(f"<div class='card'><b>Q – Que:</b> {que}</div>", unsafe_allow_html=True)

    # R – Requisitos
    req = qqroc_requisitos(auto_txt)
    if req:
        itens = "".join([f"<li>{r}</li>" for r in req])
        st.markdown(f"<div class='card'><b>R – Requisitos:</b> <span class='badge warn'>atenção</span><ul>{itens}</ul></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card'><b>R – Requisitos:</b> <span class='badge ok'>ok</span></div>", unsafe_allow_html=True)

    # O – Observações (resultado já calculado)
    st.markdown(f"<div class='card'><b>O – Observações:</b> <span class='badge {color_obs}'>{status_obs}</span></div>", unsafe_allow_html=True)

    # C – Consequências
    cons_txt, cons_color = qqroc_consequencia(status_obs, mbft_ctx.get("obrigatorio", False))
    st.markdown(f"<div class='card'><b>C – Consequências:</b> <span class='badge {cons_color}'>{cons_txt}</span></div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.caption("Babix AI © 2025 • MG Multas — Este diagnóstico é auxiliar e deve ser revisado por profissional habilitado.")
