import os
import streamlit as st
import PyPDF2
import requests
import json

# Suas funções existentes de ler_ficha_mbft e verificar_observacao_auto (copie exatamente o código que passei antes)

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
        st.error(f"Ficha da infração {codigo_infracao} não encontrada!")
        return None
    caminho_completo = os.path.join(pasta_fichas, arquivo_encontrado)
    try:
        with open(caminho_completo, 'rb') as arquivo_pdf:
            leitor = PyPDF2.PdfReader(arquivo_pdf)
            texto_completo = ""
            for pagina in leitor.pages:
                texto_completo += pagina.extract_text()
            resultado = {
                'codigo': codigo_infracao,
                'arquivo': arquivo_encontrado,
                'texto_completo': texto_completo,
                'tem_campo_observacao': False,
                'observacao_obrigatoria': False,
                'informacoes_observacao': []
            }
            if 'observa' in texto_completo.lower():
                resultado['tem_campo_observacao'] = True
                linhas = texto_completo.split('\n')
                for i, linha in enumerate(linhas):
                    if 'observa' in linha.lower():
                        contexto = '\n'.join(linhas[i:min(i+3, len(linhas))])
                        resultado['informacoes_observacao'].append(contexto)
                texto_lower = texto_completo.lower()
                if any(palavra in texto_lower for palavra in ['obrigatório', 'obrigatoria', 'deve constar', 'necessário']):
                    resultado['observacao_obrigatoria'] = True
            return resultado
    except Exception as e:
        st.error(f"Erro ao ler PDF da ficha: {str(e)}")
        return None


def verificar_observacao_auto(texto_auto, codigo_infracao):
    ficha = ler_ficha_mbft(codigo_infracao)
    if not ficha:
        return {'erro': 'Ficha não encontrada'}
    tem_observacao_preenchida = False
    texto_observacao = ""
    linhas = texto_auto.split('\n')
    for i, linha in enumerate(linhas):
        if 'observa' in linha.lower():
            texto_observacao = '\n'.join(linhas[i:min(i+5, len(linhas))])
            if len(texto_observacao.strip()) > 20:
                tem_observacao_preenchida = True
            break
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
        analise['problemas'].append('Campo de observação é OBRIGATÓRIO mas está vazio ou mal preenchido')
    if ficha['tem_campo_observacao'] and not tem_observacao_preenchida:
        analise['problemas'].append('Ficha MBFT menciona observações mas o auto não tem o campo preenchido')
    return analise


# ===================== INÍCIO INTEGRAÇÃO STREAMLIT =====================

st.title("⚖️ Babix - Análise de Multas com Verificação MBFT")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📤 Upload da Autuação")
    arquivo = st.file_uploader("Arraste ou clique para enviar o PDF da multa", type=['pdf'])

    # Seu código existente de análise inicial continua aqui...

    # NOVA SEÇÃO para verificação campo observação MBFT
    st.markdown("---")
    st.markdown("### 🔍 Verificação do Campo Observação MBFT")

    codigo_infracao = st.text_input("Digite o código da infração para verificar observação na ficha MBFT")

    auto_file = st.file_uploader("Envie o PDF do auto de infração para verificar campo observação", key="auto_pdf", type=['pdf'])

    if auto_file and codigo_infracao:
        pdf_auto = PyPDF2.PdfReader(auto_file)
        texto_auto = ""
        for pagina in pdf_auto.pages:
            texto_auto += pagina.extract_text()

        resultado_analise = verificar_observacao_auto(texto_auto, codigo_infracao)

        if resultado_analise.get("erro"):
            st.error(resultado_analise["erro"])
        else:
            st.write("### Resultado da Verificação do Campo Observação")
            if resultado_analise['conforme']:
                st.success("✅ O campo de observação está conforme as exigências da ficha MBFT.")
            else:
                st.error("❌ O campo de observação está incorreto ou não preenchido conforme a ficha MBFT.")

            if resultado_analise['problemas']:
                for problema in resultado_analise['problemas']:
                    st.warning(f"⚠️ {problema}")

            if resultado_analise['texto_observacao_auto']:
                st.markdown("#### Texto extraído do campo Observação:")
                st.code(resultado_analise['texto_observacao_auto'])

with col2:
    st.markdown("### 📚 Como Funciona")
    st.info(""" 
    **1. Upload** 📤 Envie o PDF da autuação  
    **2. Análise** 🔍 IA identifica nulidades  
    **3. Verificação Observação** 🔎 Insira o código e envie PDF do auto para verificar  
    **4. Complemento** 📝 Adicione informações extras se necessário  
    **5. Recurso** ⚖️ IA gera recurso completo  
    **6. Download** 💾 Baixe e use!  
    """)
    st.success("✅ 100% GRÁTIS")
    st.info("⚡ IA LLaMA 3.3 70B")
    st.warning("⚖️ Sempre revise seus documentos")
    st.markdown("---")

# ===================== FIM DA INTEGRAÇÃO =====================
