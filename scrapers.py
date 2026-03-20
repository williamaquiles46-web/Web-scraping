import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configurar_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1366,768")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Oculta o navigator.webdriver (anti-bot do ML/Amazon)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def buscarMercadoLivre(query):
    driver = configurar_driver()
    url = f'https://lista.mercadolivre.com.br/{query.replace(" ", "-")}'
    results = []
    try:
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        itens = soup.find_all('li', class_='ui-search-layout__item')
        print(f"DEBUG ML: Encontrei {len(itens)} blocos.")

        for item in itens[:5]:
            try:
                # ML agora usa <h3> com <a class="poly-component__title"> dentro
                link_tag = item.find('a', class_='poly-component__title')
                if not link_tag:
                    print("  [ML] Título não encontrado, pulando item.")
                    continue
                nome = link_tag.get_text(strip=True)
                link = link_tag['href']

                # Preço atual fica dentro de .poly-price__current
                preco_atual = item.find('div', class_='poly-price__current')
                if not preco_atual:
                    print(f"  [ML] Preço não encontrado para: {nome[:40]}")
                    continue

                preco_span = preco_atual.find('span', class_='andes-money-amount__fraction')
                if not preco_span:
                    print(f"  [ML] Fração do preço não encontrada para: {nome[:40]}")
                    continue

                centavos_span = preco_atual.find('span', class_='andes-money-amount__cents')
                centavos = centavos_span.text.strip() if centavos_span else "00"

                preco_txt = preco_span.text.strip().replace('.', '').replace(',', '')
                preco = float(f"{preco_txt}.{centavos}")

                results.append({
                    'loja': 'Mercado Livre',
                    'nome': nome,
                    'preco': preco,
                    'link': link
                })
            except Exception as e:
                print(f"  [ML] Erro ao parsear item: {e}")
                continue

    except Exception as e:
        print(f"[ML] Erro geral: {e}")
    finally:
        driver.quit()

    print(f"DEBUG ML: {len(results)} produtos extraídos com sucesso.")
    return results


def buscarAmazon(query):
    driver = configurar_driver()
    url = f'https://www.amazon.com.br/s?k={query.replace(" ", "+")}'
    results = []
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "a-price-whole"))
        )
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        itens = soup.find_all('div', {'data-component-type': 's-search-result'})
        print(f"DEBUG Amazon: Encontrei {len(itens)} blocos.")

        for item in itens[:10]:  # pega mais itens pois alguns não têm preço
            if len(results) >= 5:
                break
            try:
                # Título
                nome_tag = item.find('h2')
                if not nome_tag:
                    continue
                link_tag = nome_tag.find('a', href=True)
                nome = nome_tag.get_text(strip=True)

                # Preço — Amazon às vezes esconde em span aninhado
                preco_whole = item.find('span', class_='a-price-whole')
                if not preco_whole:
                    print(f"  [AMZ] Sem preço para: {nome[:40]}")
                    continue

                # Remove pontos de milhar e vírgula decimal do inteiro
                preco_limpo = preco_whole.text.strip().replace('.', '').replace(',', '').replace('\xa0', '')
                # Remove qualquer caractere não-dígito que sobrar (ex: ".")
                preco_limpo = ''.join(filter(str.isdigit, preco_limpo))

                centavos_tag = item.find('span', class_='a-price-fraction')
                centavos = centavos_tag.text.strip() if centavos_tag else "00"

                preco = float(f"{preco_limpo}.{centavos}")

                link = ("https://www.amazon.com.br" + link_tag['href']) if link_tag else url

                results.append({
                    'loja': 'Amazon',
                    'nome': nome,
                    'preco': preco,
                    'link': link
                })
            except Exception as e:
                print(f"  [AMZ] Erro ao parsear item: {e}")
                continue

    except Exception as e:
        print(f"[AMZ] Erro geral: {e}")
    finally:
        driver.quit()

    print(f"DEBUG Amazon: {len(results)} produtos extraídos com sucesso.")
    return results