import os
import streamlit as st
import PyPDF2
import re

st.set_page_config(
    page_title="Babix - Análise de Multas com MBFT",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
    <style>
    .stButton > button { background-color: #0066cc; color: white; font-weight: bold; border-radius: 8px; padding: 12px 24px;}
    .stSuccess, .stError, .stWarning {font-size: 18px !important; margin-bottom: 14px;}
    .main {background-color: #F5F7FA;}
    .block-container {padding-top: 20px;}
    </style>
    """, unsafe_allow_html=True)

def extrair_campo_observacoes(texto_auto):
    texto_upper = texto_auto.upper()
    pos = texto_upper.find("OBSERVAÇÕES")
    if pos == -1:
        return "(Campo 'OBSERVAÇÕES' não encontrado no auto de infração.)"
    texto_sub = texto_auto[pos + len("OBSERVAÇÕES") :]
    padrao = r"(.*?)(?:\n\s*\n|[A-Z\s]{5,}:|\Z)"
    resultado = re.match(padrao, texto_sub, re.DOTALL)
    if resultado:
        conteudo = resultado.group(1).strip()
    else:
        conteudo = texto_sub.strip()
    return conteudo if conteudo else "(Nenhum texto relevante encontrado)"

def ler_ficha_mbft(codigo_infracao):
    pasta_fichas = "fichas_mbft"
    arquivo_encontrado = None
    if not os.path.exists(pasta_fichas):
        st.error(f"Pasta '{pasta_fichas}' não encontrada!")
        return None
    for arquivo in os.listdir(pasta_fichas):
        if arquivo.endswith('.pdf') and codigo_infracao in arquivo:
            arquivo_encontrado = arquivo
            break
    if not arquivo_encontrado:
        st.error(f"Ficha da infração '{codigo_infracao}' não encontrada na pasta MBFT!")
        return None
    caminho_completo = os.path.join(pasta_fichas, arquivo_encontrado)
    st.info(f"✔️ Ficha MBFT utilizada: **{arquivo_encontrado}**")
    try:
        with open(caminho_completo, 'rb') as arquivo_pdf:
            leitor = PyPDF2.PdfReader(arquivo_pdf)
            texto_completo = ""
            for pagina in leitor.pages:
                texto_completo += pagina.extract_text()
            tem_observacao = 'observa' in texto_completo.lower()
            obrigatoria = any(t in texto_completo.lower() for t in ['obrigatório', 'deve constar', 'necessário'])
            obs_blocos = []
            if tem_observacao:
                linhas = texto_completo.split('\n')
                for i, linha in enumerate(linhas):
                    if 'observa' in linha.lower():
                        contexto = '\n'.join(linhas[i:min(i+4, len(linhas))])
                        obs_blocos.append(contexto)
            # Exibe bloco com texto sobre observação extraído da ficha MBFT
            st.markdown("#### Trecho da Ficha MBFT sobre Observação:")
            st.code('\n---\n'.join(obs_blocos) if obs_blocos else "(Nada encontrado sobre observação)", language="markdown")
            return {
                'codigo': codigo_infracao,
                'arquivo': arquivo_encontrado,
                'texto_completo': texto_completo,
                'tem_campo_observacao': tem_observacao,
                'observacao_obrigatoria': obrigatoria,
                'informacoes_observacao': obs_blocos
            }
    except Exception as e:
        st.error(f"Erro ao ler PDF da ficha: {str(e)}")
        return None

def verificar_observacao_auto(texto_auto, codigo_infracao):
    ficha = ler_ficha_mbft(codigo_infracao)
    if not ficha:
        return {'erro': 'Ficha MBFT não encontrada'}
    texto_observacao = extrair_campo_observacoes(texto_auto)
    tem_observacao_preenchida = len(texto_observacao) > 10 and 'não encontrado' not in texto_observacao.lower()
    analise = {
        'codigo_infracao': codigo_infracao,
        'ficha_exige_observacao': ficha['tem_campo_observacao'],
        'observacao_obrigatoria': ficha['observacao_obrigatoria'],
        'auto_tem_observacao': tem_observacao_preenchida,
        'texto_observacao_auto': texto_observacao,
        'conforme': True,
        'problemas': []
    }
    if ficha['observacao_obrigatoria'] and not tem_observacao_preenchida:
        analise['conforme'] = False
        analise['problemas'].append('Campo de observação é obrigatório mas está vazio ou mal preenchido.')
    if ficha['tem_campo_observacao'] and not tem_observacao_preenchida:
        analise['problemas'].append('Ficha MBFT menciona observações mas o auto não tem esse campo preenchido.')
    return analise

st.title("⚖️ Babix - Análise de Multas com Verificação MBFT")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📤 Upload da Autuação (PDF da multa)")
    arquivo = st.file_uploader("Arraste ou clique para enviar o PDF da multa", type=['pdf'])
    texto_pdf = ""
    if arquivo:
        st.success(f"✅ Arquivo recebido: **{arquivo.name}**")
        try:
            pdf = PyPDF2.PdfReader(arquivo)
            for pagina in pdf.pages:
                texto_pdf += pagina.extract_text()
            with st.expander("👁️ Visualizar texto extraído do PDF", expanded=False):
                st.text_area("Texto extraído:", texto_pdf[:1200] + ("\n...[continua]" if len(texto_pdf) > 1200 else ""), height=180)
        except Exception as e:
            st.error(f"❌ Erro ao ler PDF: {str(e)}")

    st.markdown("---")
    st.markdown("### 🔎 Verificação do Campo Observação MBFT")

    codigo_infracao = st.text_input("Digite o código da infração para consultar a ficha MBFT (ex: 527-41)")
    auto_file = st.file_uploader("Envie o PDF do auto para extrair e verificar o campo 'Observações'", key="auto_pdf", type=['pdf'])
    texto_auto = ""
    if auto_file and codigo_infracao:
        try:
            pdf_auto = PyPDF2.PdfReader(auto_file)
            for pagina in pdf_auto.pages:
                texto_auto += pagina.extract_text()
            resultado_analise = verificar_observacao_auto(texto_auto, codigo_infracao)
            if resultado_analise.get("erro"):
                st.error(resultado_analise["erro"])
            else:
                st.markdown("#### Resultado da Verificação do Campo Observação")
                if resultado_analise['conforme']:
                    st.success("O campo de observação está conforme as exigências da ficha MBFT.")
                else:
                    st.error("Campo de observação incorreto ou não preenchido conforme MBFT.")
                if resultado_analise['problemas']:
                    for problema in resultado_analise['problemas']:
                        st.warning(f"⚠️ {problema}")
                st.markdown("#### Texto extraído do campo Observações do Auto de Infração:")
                st.code(resultado_analise['texto_observacao_auto'])
        except Exception as e:
            st.error(f"❌ Erro ao processar PDF do auto: {str(e)}")

with col2:
    st.markdown("### 📚 Como Funciona")
    st.info("""
**1. Upload:** Envie o PDF da autuação.
**2. Análise:** IA identifica nulidades.
**3. Consulta MBFT:** Digite o código da infração e o app lê a ficha MBFT.
**4. Extrai e verifica Observações:** Envie o PDF do auto, compare na tela.
**5. Recurso:** IA gera defesa completa.
**6. Download:** Baixe e utilize o recurso.
    """)
    st.success("100% GRÁTIS")
    st.info("⚡ IA LLaMA 3.3 70B")
    st.warning("⚖️ Sempre revise seus documentos.")
    st.markdown("---")
    st.markdown("<br><center>Babix AI © 2025 | MG Multas</center>", unsafe_allow_html=True)
