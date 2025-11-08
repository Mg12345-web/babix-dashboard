import streamlit as st
import PyPDF2
from groq import Client as GroqClient

# Configurar página
st.set_page_config(
    page_title="Babix - Análise de Multas",
    page_icon="⚖️",
    layout="wide"
)

# CSS bonito
st.markdown("""
<style>
    .main {
        background-color: #f5f7fa;
    }
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
    
    # Upload do PDF
    arquivo = st.file_uploader(
        "Arraste ou clique para enviar o PDF da multa",
        type=['pdf'],
        help="Envie o PDF da notificação de autuação"
    )
    
    if arquivo:
        st.success(f"✅ Arquivo recebido: **{arquivo.name}**")
        
        # Ler PDF
        try:
            pdf = PyPDF2.PdfReader(arquivo)
            texto = ""
            
            # Extrair texto de todas as páginas
            for pagina in pdf.pages:
                texto += pagina.extract_text()
            
            # Mostrar preview
            with st.expander("👁️ Visualizar texto extraído"):
                st.text(texto[:500] + "...")
            
            # Botão de análise
            if st.button("🔍 Analisar com IA", type="primary"):
                
                # Barra de progresso
                with st.spinner("🤖 Analisando autuação..."):
                    
                    # Conectar com Groq (IA gratuita)
                    client = GroqClient(api_key=st.secrets["GROQ_API_KEY"])
                    
                    # Criar prompt para IA
                    prompt = f"""Você é um advogado especialista em direito de trânsito brasileiro.

AUTUAÇÃO RECEBIDA:
{texto[:3000]}

Por favor, faça:

1. **RESUMO DA AUTUAÇÃO:**
   - Código da infração
   - Descrição da infração
   - Valor da multa
   - Pontos na CNH

2. **ANÁLISE JURÍDICA:**
   - Base legal (CTB/MBFT)
   - Possíveis vícios ou irregularidades
   - Chances de defesa

3. **RECURSO DE DEFESA (modelo):**
   - Qualificação do autuado
   - Dos fatos
   - Do direito
   - Dos pedidos

Seja técnico, profissional e didático."""

                    # Chamar IA
                    resposta = client.chat.completions.create(
                        model="llama3-70b-8192",  # Modelo grátis e potente
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }],
                        temperature=0.3,
                        max_tokens=2000
                    )
                    
                    resultado = resposta.choices[0].message.content
                
                # Mostrar resultado
                st.success("✅ Análise concluída!")
                
                # Tabs organizadas
                tab1, tab2, tab3 = st.tabs(["📊 Análise Completa", "📝 Recurso", "💾 Download"])
                
                with tab1:
                    st.markdown("### 📊 Análise da IA")
                    st.markdown(resultado)
                
                with tab2:
                    st.markdown("### 📝 Texto do Recurso")
                    st.text_area(
                        "Copie o recurso abaixo:",
                        resultado,
                        height=400
                    )
                
                with tab3:
                    st.markdown("### 💾 Download")
                    st.download_button(
                        "📥 Baixar Análise (TXT)",
                        data=resultado,
                        file_name=f"analise_{arquivo.name}.txt",
                        mime="text/plain"
                    )
                    st.info("💡 Cole este texto no Word e salve como PDF")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar PDF: {str(e)}")
            st.info("Tente outro arquivo PDF ou verifique se não está protegido.")

with col2:
    st.markdown("### 📚 Como Funciona")
    
    st.info("""
    **1. Upload** 📤  
    Envie o PDF da autuação
    
    **2. Extração** 📄  
    Sistema lê o texto do PDF
    
    **3. Análise** 🔍  
    IA especializada analisa
    
    **4. Recurso** 📝  
    Gera defesa personalizada
    
    **5. Download** 💾  
    Baixe e use!
    """)
    
    st.success("✅ **100% GRÁTIS**")
    st.info("⚡ IA super rápida (Groq)")
    st.warning("⚖️ Sempre revise com advogado")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><b>Babix AI</b> © 2025 | MG Multas</p>
    <p>Powered by Groq (llama3-70b) | 100% Gratuito</p>
</div>
""", unsafe_allow_html=True)
