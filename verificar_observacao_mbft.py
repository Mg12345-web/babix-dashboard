import os
import PyPDF2
from pathlib import Path

def ler_ficha_mbft(codigo_infracao):
    """
    Lê a ficha MBFT específica da infração e extrai informações do campo observação.
    
    Args:
        codigo_infracao: Código da infração (ex: "574-10", "195", etc)
    
    Returns:
        dict com informações da ficha ou None se não encontrar
    """
    
    # Pasta onde estão as fichas
    pasta_fichas = "fichas_mbft"
    
    # Procura arquivo que contenha o código da infração no nome
    # Exemplo: "574-10.pdf", "ficha_574-10.pdf", etc
    arquivo_encontrado = None
    
    if not os.path.exists(pasta_fichas):
        print(f"❌ Pasta '{pasta_fichas}' não encontrada!")
        return None
    
    # Lista todos os arquivos PDF na pasta
    for arquivo in os.listdir(pasta_fichas):
        if arquivo.endswith('.pdf') and codigo_infracao in arquivo:
            arquivo_encontrado = arquivo
            break
    
    if not arquivo_encontrado:
        print(f"❌ Ficha da infração {codigo_infracao} não encontrada!")
        return None
    
    # Caminho completo do arquivo
    caminho_completo = os.path.join(pasta_fichas, arquivo_encontrado)
    print(f"📄 Lendo ficha: {arquivo_encontrado}")
    
    try:
        # Abre e lê o PDF
        with open(caminho_completo, 'rb') as arquivo_pdf:
            leitor = PyPDF2.PdfReader(arquivo_pdf)
            
            # Extrai texto de todas as páginas
            texto_completo = ""
            for pagina in leitor.pages:
                texto_completo += pagina.extract_text()
            
            # Busca informações sobre campo de observação
            resultado = {
                'codigo': codigo_infracao,
                'arquivo': arquivo_encontrado,
                'texto_completo': texto_completo,
                'tem_campo_observacao': False,
                'observacao_obrigatoria': False,
                'informacoes_observacao': []
            }
            
            # Verifica se menciona campo de observação
            if 'observa' in texto_completo.lower():
                resultado['tem_campo_observacao'] = True
                
                # Extrai linhas que mencionam observação
                linhas = texto_completo.split('\n')
                for i, linha in enumerate(linhas):
                    if 'observa' in linha.lower():
                        # Pega a linha e as próximas 2 para contexto
                        contexto = '\n'.join(linhas[i:min(i+3, len(linhas))])
                        resultado['informacoes_observacao'].append(contexto)
                
                # Verifica se é obrigatório
                texto_lower = texto_completo.lower()
                if any(palavra in texto_lower for palavra in ['obrigatório', 'obrigatoria', 'deve constar', 'necessário']):
                    resultado['observacao_obrigatoria'] = True
            
            return resultado
            
    except Exception as e:
        print(f"❌ Erro ao ler PDF: {str(e)}")
        return None


def verificar_observacao_auto(texto_auto, codigo_infracao):
    """
    Verifica se o campo de observação do auto de infração está bem preenchido
    comparando com as exigências da ficha MBFT.
    
    Args:
        texto_auto: Texto extraído do auto de infração
        codigo_infracao: Código da infração
    
    Returns:
        dict com análise da conformidade
    """
    
    # Lê a ficha MBFT
    ficha = ler_ficha_mbft(codigo_infracao)
    
    if not ficha:
        return {'erro': 'Ficha não encontrada'}
    
    # Procura campo observação no auto
    tem_observacao_preenchida = False
    texto_observacao = ""
    
    # Busca padrões comuns de campo observação
    linhas = texto_auto.split('\n')
    for i, linha in enumerate(linhas):
        if 'observa' in linha.lower():
            # Pega as próximas linhas após "Observação:"
            texto_observacao = '\n'.join(linhas[i:min(i+5, len(linhas))])
            
            # Verifica se tem conteúdo além do título
            if len(texto_observacao.strip()) > 20:
                tem_observacao_preenchida = True
            break
    
    # Análise
    analise = {
        'codigo_infracao': codigo_infracao,
        'ficha_exige_observacao': ficha['tem_campo_observacao'],
        'observacao_obrigatoria': ficha['observacao_obrigatoria'],
        'auto_tem_observacao': tem_observacao_preenchida,
        'texto_observacao_auto': texto_observacao,
        'conforme': True,
        'problemas': []
    }
    
    # Verifica conformidade
    if ficha['observacao_obrigatoria'] and not tem_observacao_preenchida:
        analise['conforme'] = False
        analise['problemas'].append('Campo de observação é OBRIGATÓRIO mas está vazio ou mal preenchido')
    
    if ficha['tem_campo_observacao'] and not tem_observacao_preenchida:
        analise['problemas'].append('Ficha MBFT menciona observações mas o auto não tem o campo preenchido')
    
    return analise


# EXEMPLO DE USO
if __name__ == "__main__":
    
    print("="*60)
    print("🔍 VERIFICADOR DE CAMPO OBSERVAÇÃO - MBFT")
    print("="*60)
    
    # Exemplo 1: Apenas ler uma ficha
    print("\n📋 TESTE 1: Lendo ficha MBFT")
    codigo = "574-10"  # Substitua pelo código real
    ficha = ler_ficha_mbft(codigo)
    
    if ficha:
        print(f"\n✅ Ficha encontrada: {ficha['arquivo']}")
        print(f"📌 Campo observação mencionado: {'SIM' if ficha['tem_campo_observacao'] else 'NÃO'}")
        print(f"⚠️  Observação obrigatória: {'SIM' if ficha['observacao_obrigatoria'] else 'NÃO'}")
        
        if ficha['informacoes_observacao']:
            print(f"\n📝 Informações sobre observação encontradas:")
            for info in ficha['informacoes_observacao'][:3]:  # Mostra até 3
                print(f"   → {info[:200]}...")
    
    # Exemplo 2: Verificar auto de infração
    print("\n" + "="*60)
    print("📋 TESTE 2: Verificando auto de infração")
    
    # Simula texto de um auto (substitua com seu PDF real)
    texto_auto_exemplo = """
    AUTO DE INFRAÇÃO Nº 12345
    Infração: 574-10
    ...
    Observações: Condutor transitava sem cinto de segurança.
    Constatado visualmente pelo agente.
    """
    
    analise = verificar_observacao_auto(texto_auto_exemplo, codigo)
    
    if 'erro' not in analise:
        print(f"\n{'✅' if analise['conforme'] else '❌'} STATUS: {'CONFORME' if analise['conforme'] else 'NÃO CONFORME'}")
        print(f"📌 Observação obrigatória: {'SIM' if analise['observacao_obrigatoria'] else 'NÃO'}")
        print(f"📝 Auto tem observação: {'SIM' if analise['auto_tem_observacao'] else 'NÃO'}")
        
        if analise['problemas']:
            print(f"\n⚠️  PROBLEMAS ENCONTRADOS:")
            for problema in analise['problemas']:
                print(f"   • {problema}")
    
    print("\n" + "="*60)
