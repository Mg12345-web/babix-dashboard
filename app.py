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
st.markdown("### 🚗 Análise Inteligente e Gratuita de Autuações de Trânsito")
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
            
            if st.button("🔍 Analisar com IA", type="primary"):
                
                with st.spinner("🤖 Analisando autuação..."):
                    
                    try:
                        # Chamar Groq via API HTTP direta
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        
                        headers = {
                            "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                            "Content-Type": "application/json"
                        }
                        
                        prompt = f"""Você é um advogado especialista em direito de trânsito brasileiro.

AUTUAÇÃO RECEBIDA:
{texto[:3000]}

Por favor, faça:

1. **RESUMO DA AUTUAÇÃO:**
   - Código da infração
   - Descrição
   - Valor e pontos

2. **ANÁLISE JURÍDICA:**
   - Base legal (CTB/MBFT)
   - Possíveis vícios
   - Chances de defesa

3. **RECURSO DE DEFESA:**
   - Qualificação
   - Dos fatos
   - Do direito
   - Dos pedidos

Seja técnico e profissional."""

                        data = {
                            "model": "llama3-70b-8192",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.3,
                            "max_tokens": 2000
                        }
                        
                        response = requests.post(url, headers=headers, json=data)
                        
                        if response.status_code == 200:
                            resultado = response.json()['choices'][0]['message']['content']
                        else:
                            st.error(f"❌ Erro API: {response.status_code}")
                            st.code(response.text)
                            resultado = None
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                        resultado = None
                
                if resultado:
                    st.success("✅ Análise concluída!")
                    
                    tab1, tab2, tab3 = st.tabs(["📊 Análise", "📝 Recurso", "💾 Download"])
                    
                    with tab1:
                        st.markdown("### 📊 Análise da IA")
                        st.markdown(resultado)
                    
                    with tab2:
                        st.text_area("Recurso:", resultado, height=400)
                    
                    with tab3:
                        st.download_button(
                            "📥 Baixar",
                            data=resultado,
                            file_name=f"analise_{arquivo.name}.txt"
                        )
        
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

with col2:
    st.markdown("### 📚 Como Funciona")
    st.info("""
    **1. Upload** 📤  
    **2. Extração** 📄  
    **3. Análise** 🔍  
    **4. Recurso** 📝  
    **5. Download** 💾
    """)
    
    st.success("✅ 100% GRÁTIS")
    st.info("⚡ IA Groq")
    st.warning("⚖️ Revise com advogado")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><b>Babix AI</b> © 2025 | MG Multas</p>
</div>
""", unsafe_allow_html=True)
