import os
import re
from difflib import SequenceMatcher
import streamlit as st
import PyPDF2

# =============================
# CONFIGURAÇÃO DO LAYOUT
# =============================
st.set_page_config(
    page_title="Babix – Análise MBFT Inteligente",
    page_icon="⚖️",
    layout="centered"
)

st.markdown("""
<style>
body {background-color: #F7F8FA;}
.block-container {padding: 2rem 3rem;}
h1, h2, h3, h4, h5 {color: #003366;}
.stButton > button {
    background-color: #004AAD;
    color: white;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 600;
}
.result-card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.07);
    padding: 20px;
    margin-top: 15px;
}
.obs-box {
    background: #f0f4ff;
    padding: 10px;
    border-left: 4px solid #004AAD;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Babix – Análise de Multas com Verificação MBFT")
st.caption("Sistema automatizado de auditoria de autos de infração conforme o Manual Brasileiro de Fiscalização de Trânsito (MBFT).")

# =============================
# FUNÇÕES AUXILIARES
# =============================

def extrair_texto_pdf(arquivo):
    """Extrai todo o texto de um PDF."""
    try:
        leitor = PyPDF2.PdfReader(arquivo)
        texto = ""
        for pagina in leitor.pages:
            texto += pagina.extract_text() or ""
        return texto
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return ""

def extrair_codigo_infracao(texto):
    """Tenta localizar o código da infração no texto do auto."""
    padrao = r"(\d{3,4}[-–]?\d{1,2})"
    match = re.search(padrao, texto)
    return match.group(1).replace("–", "-") if match else None

def extrair_campo_observacoes(texto):
    """Extrai o conteúdo do campo Observações / Observação / Obs: do Auto."""
    padrao = r"(?:OBSERVAÇÕES?|OBSERVAÇÃO|OBS:)\s*(.*)"
    match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
    if not match:
        return "(Campo 'Observações' não encontrado)"
    conteudo = match.group(1).strip()
    # Para limitar até a próxima seção (ex: IDENTIFICAÇÃO, LOCAL, etc)
    conteudo = re.split(r"[A-Z\s]{4,}[:\n]", conteudo)[0].strip()
    return conteudo[:400] if conteudo else "(Campo vazio)"

def analisar_ficha_mbft(texto_ficha):
    """Lê a ficha completa e retorna trechos relevantes ao campo de observações."""
    texto_lower = texto_ficha.lower()
    padrao_principal = r"exemplos do campo de observações.*?(?:quando|definições|$)"
    trecho_principal = re.search(padrao_principal, texto_lower, re.DOTALL)
    trecho_principal = trecho_principal.group(0).strip() if trecho_principal else ""

    blocos_obs = re.findall(r".{0,100}observa.{0,200}", texto_lower)
    obrigatorio = any(palavra in texto_lower for palavra in [
        "deve constar", "obrigatório", "necessário", "registrar no campo"
    ])
    return {
        "trecho_principal": trecho_principal,
        "contextos": blocos_obs,
        "obrigatorio": obrigatorio
    }

def similaridade(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def comparar_observacoes(auto_obs, ficha_info):
    """Compara as observações do auto com a ficha MBFT."""
    melhores_sim = 0
    for contexto in ficha_info["contextos"]:
        sim = similaridade(auto_obs, contexto)
        melhores_sim = max(melhores_sim, sim)

    if melhores_sim > 0.7:
        status = "✅ Condizente com o MBFT"
        cor = "green"
    elif 0.4 < melhores_sim <= 0.7:
        status = "⚠️ Parcialmente coerente — pode haver omissão"
        cor = "orange"
    else:
        status = "❌ Divergente — provável nulidade"
        cor = "red"

    return status, cor, melhores_sim

# =============================
# UPLOAD E ANÁLISE
# =============================

st.markdown("### 📄 Envie o Auto de Infração (PDF)")
arquivo_auto = st.file_uploader("Envie o PDF do Auto", type=['pdf'])

if arquivo_auto:
    texto_auto = extrair_texto_pdf(arquivo_auto)
    codigo = extrair_codigo_infracao(texto_auto)
    obs_auto = extrair_campo_observacoes(texto_auto)

    st.markdown(f"#### 🆔 Código da Infração Detectado: `{codigo or 'não encontrado'}`")
    st.markdown("#### 📋 Campo de Observações do Auto:")
    st.markdown(f"<div class='obs-box'>{obs_auto}</div>", unsafe_allow_html=True)

    # Buscar ficha correspondente
    if codigo:
        pasta_fichas = "fichas_mbft"
        ficha_encontrada = None
        for arq in os.listdir(pasta_fichas):
            if codigo in arq:
                ficha_encontrada = os.path.join(pasta_fichas, arq)
                break

        if ficha_encontrada:
            st.markdown(f"#### 📘 Ficha MBFT Encontrada: `{os.path.basename(ficha_encontrada)}`")
            texto_ficha = extrair_texto_pdf(ficha_encontrada)
            ficha_info = analisar_ficha_mbft(texto_ficha)

            status, cor, sim = comparar_observacoes(obs_auto, ficha_info)

            st.markdown(f"<div class='result-card'><h3 style='color:{cor}'>{status}</h3>", unsafe_allow_html=True)
            st.progress(sim)
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("👁️ Ver trecho principal da ficha MBFT"):
                st.write(ficha_info['trecho_principal'] or "(Nada encontrado)")
        else:
            st.error("Ficha MBFT correspondente não encontrada na pasta.")
    else:
        st.error("Não foi possível detectar o código da infração automaticamente.")
