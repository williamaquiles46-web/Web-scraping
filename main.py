import pandas as pd
import os
from scrapers import buscarMercadoLivre, buscarAmazon

def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return f"R$ {valor}"

def executar_comparador():
    print("\n" + "="*50)
    print("      🔍 COMPARADOR ML vs AMAZON")
    print("="*50)
    
    produto_busca = input("\nO que você deseja buscar hoje? ")
    
    
    print(f"\n[1/2] Buscando no Mercado Livre...")
    res_ml = buscarMercadoLivre(produto_busca)
    print(f"   -> Recebi {len(res_ml)} produtos do ML") 
    
    print(f"[2/2] Buscando na Amazon...")
    res_amz = buscarAmazon(produto_busca)
    print(f"   -> Recebi {len(res_amz)} produtos da Amazon") 
    
    # 2. Une os resultados
    todos_resultados = res_ml + res_amz

    # VERIFICAÇÃO CRÍTICA
    if not todos_resultados:
        print("\n❌ Erro: As listas voltaram vazias para o programa principal.")
        return

    
    print("\n📊 Gerando comparativo... Por favor, aguarde.")
    df = pd.DataFrame(todos_resultados)
    
    
    df['preco'] = pd.to_numeric(df['preco'], errors='coerce')
    df = df.dropna(subset=['preco']) 
    
    df = df.sort_values(by='preco', ascending=True).reset_index(drop=True)

    
    if not df.empty:
        campeao = df.iloc[0]
        print("\n" + "🏆" * 20)
        print("    MELHOR OFERTA ENCONTRADA!")
        print(f"    Loja: {campeao['loja']}")
        print(f"    Produto: {campeao['nome']}")
        print(f"    Preço: {formatar_moeda(campeao['preco'])}")
        print(f"    Link: {campeao['link']}")
        print("🏆" * 20 + "\n")

        
        if not os.path.exists('relatorios'):
            os.makedirs('relatorios')
            
        nome_arquivo = f"relatorios/comparativo_{produto_busca.replace(' ', '_')}.xlsx"
        df.to_excel(nome_arquivo, index=False)
        print(f"✅ Relatório salvo com sucesso em: {nome_arquivo}")
    else:
        print("❌ Ocorreu um erro ao processar os preços.")

if __name__ == "__main__":
    executar_comparador()