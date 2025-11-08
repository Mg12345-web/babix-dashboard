import streamlit as st
import PyPDF2
import requests
import json

# Configurar página
st.set_page_config(
    page_title="Babix - Análise de Multas",
    page_icon="⚖️",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    .stButton>button {
        background-color: #0066cc;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px 24px;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho
st.title("⚖️ Babix - Análise de Multas")
st.markdown("### 🚗 Análise Inteligente com IA Especializada")
st.markdown("---")

# Colunas
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📤 Upload da Autuação")
    
    arquivo = st.file_uploader(
        "Arraste ou clique para enviar o PDF da multa",
        type=['pdf']
    )
    
    if arquivo:
        st.success(f"✅ Arquivo recebido: **{arquivo.name}**")
        
        try:
            pdf = PyPDF2.PdfReader(arquivo)
            texto = ""
            
            for pagina in pdf.pages:
                texto += pagina.extract_text()
            
            with st.expander("👁️ Visualizar texto extraído"):
                st.text(texto[:500] + "...")
            
            # ETAPA 1: Análise Inicial
            if st.button("🔍 Analisar Nulidades", type="primary"):
                
                with st.spinner("🤖 Analisando autuação e buscando nulidades..."):
                    
                    try:
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        
                        headers = {
                            "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                            "Content-Type": "application/json"
                        }
                        
                        # PROMPT ETAPA 1: Lista nulidades
                        prompt_etapa1 = f"""Você é um advogado especialista em direito de trânsito brasileiro.

AUTUAÇÃO RECEBIDA:
{texto[:3000]}

TAREFA:
Analise detalhadamente e identifique TODAS as nulidades encontradas.

Responda EXATAMENTE neste formato:

📊 ANÁLISE DA AUTUAÇÃO

**Dados básicos:**
- Auto de Infração nº: [extrair]
- Código da infração: [extrair]
- Descrição: [extrair]
- Local: [extrair]
- Data/Hora: [extrair]
- Valor: [extrair]
- Pontos: [extrair]

**NULIDADES IDENTIFICADAS:**

✅ 1. [Primeira nulidade encontrada]
   - Fundamentação: [CTB/MBFT]
   - Gravidade: [Alta/Média/Baixa]

✅ 2. [Segunda nulidade]
   - Fundamentação: [CTB/MBFT]
   - Gravidade: [Alta/Média/Baixa]

[Continue listando todas...]

**ANÁLISE TÉCNICA:**
[Explicação detalhada das irregularidades]

---

❓ **IMPORTANTE:**
Você identificou alguma nulidade adicional que não está listada na autuação ou que eu não verifiquei?

**Exemplos:**
• Veículo não estava no local (Álibi)
• Veículo estava vendido/transferido
• Radar sem aferição ou calibração
• Sinalização inadequada ou inexistente
• Outra irregularidade

Se sim, descreva abaixo para complementarmos o recurso."""

                        data = {
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": prompt_etapa1}],
                            "temperature": 0.3,
                            "max_tokens": 2000
                        }
                        
                        response = requests.post(url, headers=headers, json=data)
                        
                        if response.status_code == 200:
                            analise_inicial = response.json()['choices'][0]['message']['content']
                            st.session_state['analise_inicial'] = analise_inicial
                            st.session_state['texto_pdf'] = texto
                        else:
                            st.error(f"❌ Erro: {response.status_code}")
                            analise_inicial = None
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                        analise_inicial = None
            
            # Mostrar análise inicial
            if 'analise_inicial' in st.session_state:
                st.success("✅ Análise de nulidades concluída!")
                
                st.markdown("---")
                st.markdown(st.session_state['analise_inicial'])
                st.markdown("---")
                
                # ETAPA 2: Campo para nulidades adicionais
                st.markdown("### 📝 Informações Adicionais (Opcional)")
                
                nulidades_extras = st.text_area(
                    "💡 Descreva nulidades ou informações adicionais:",
                    placeholder="Ex: O veículo foi vendido em 10/09/2025, antes da infração...\n\nOu deixe em branco se não houver nada a acrescentar.",
                    height=150
                )
                
                # Botão gerar recurso final
                if st.button("📝 Gerar Recurso Completo", type="primary"):
                    
                    with st.spinner("🤖 Gerando recurso personalizado..."):
                        
                        try:
                            # PROMPT ETAPA 2: Gerar recurso
                            prompt_etapa2 = f"""Você é um advogado especialista em direito de trânsito brasileiro.

ANÁLISE INICIAL:
{st.session_state['analise_inicial']}

INFORMAÇÕES ADICIONAIS DO CLIENTE:
{nulidades_extras if nulidades_extras else "Nenhuma informação adicional fornecida."}

AUTUAÇÃO COMPLETA:
{st.session_state['texto_pdf'][:2000]}

TAREFA:
Gere um RECURSO DE DEFESA COMPLETO E PROFISSIONAL no seguinte formato:

---

RECURSO DE DEFESA PRÉVIA
AUTO DE INFRAÇÃO Nº [NÚMERO]

EXMO. SR. PRESIDENTE DA JARI

[Nome do Autuado], CPF nº [XXX], residente e domiciliado na [endereço], vem respeitosamente à presença de Vossa Excelência apresentar DEFESA PRÉVIA contra o Auto de Infração nº [número], pelos fundamentos de fato e de direito a seguir expostos:

I - DA QUALIFICAÇÃO
[Dados completos do autuado extraídos do PDF]

II - DOS FATOS
[Descrição detalhada dos fatos constantes na autuação]

III - DAS NULIDADES IDENTIFICADAS
[Liste TODAS as nulidades encontradas + as informações adicionais do cliente]

3.1. [Primeira nulidade]
[Argumentação jurídica completa com base no CTB/MBFT]

3.2. [Segunda nulidade]
[Argumentação jurídica completa]

[Continue com TODAS...]

IV - DO DIREITO
[Fundamentação legal completa - CTB, MBFT, jurisprudência]

V - DOS PEDIDOS
Ante o exposto, requer:

a) Seja conhecido e provido o presente recurso;
b) Seja declarada a NULIDADE do Auto de Infração;
c) Subsidiariamente, seja concedido o benefício da dúvida;
d) Seja o autuado absolvido de todas as penalidades.

Termos em que,
Pede deferimento.

[Local], [Data]

_________________________________
[Nome do Autuado]
CPF: [XXX]

---

IMPORTANTE: Seja técnico, formal e completo. Use linguagem jurídica apropriada."""

                            data2 = {
                                "model": "llama-3.3-70b-versatile",
                                "messages": [{"role": "user", "content": prompt_etapa2}],
                                "temperature": 0.3,
                                "max_tokens": 3000
                            }
                            
                            response2 = requests.post(url, headers=headers, json=data2)
                            
                            if response2.status_code == 200:
                                recurso_final = response2.json()['choices'][0]['message']['content']
                            else:
                                st.error(f"❌ Erro: {response2.status_code}")
                                recurso_final = None
                                
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                            recurso_final = None
                    
                    # Mostrar recurso
                    if recurso_final:
                        st.success("✅ Recurso completo gerado!")
                        
                        st.markdown("---")
                        st.markdown("### 📄 Recurso de Defesa Completo")
                        
                        tab1, tab2 = st.tabs(["📝 Visualizar", "💾 Download"])
                        
                        with tab1:
                            st.markdown(recurso_final)
                        
                        with tab2:
                            st.download_button(
                                "📥 Baixar Recurso (TXT)",
                                data=recurso_final,
                                file_name=f"recurso_defesa_{arquivo.name}.txt",
                                mime="text/plain"
                            )
                            st.info("💡 Cole no Word, formate e salve como PDF")
        
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

with col2:
    st.markdown("### 📚 Como Funciona")
    st.info("""
    **1. Upload** 📤  
    Envie o PDF da autuação
    
    **2. Análise** 🔍  
    IA identifica nulidades
    
    **3. Complemento** 📝  
    Adicione informações extras
    
    **4. Recurso** ⚖️  
    IA gera defesa completa
    
    **5. Download** 💾  
    Baixe e use!
    """)
    
    st.success("✅ 100% GRÁTIS")
    st.info("⚡ IA LLaMA 3.3 70B")
    st.warning("⚖️ Sempre revise")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'><p><b>Babix AI</b> © 2025 | MG Multas</p></div>", unsafe_allow_html=True)
