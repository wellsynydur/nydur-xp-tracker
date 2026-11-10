
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_URL = "https://nyduronline.com/ranking.php"

CATEGORIAS = {
    "level": "XP Level",
    "magic": "Magia",
    "strength": "Força",
    "pally": "Paladino",
    "defense": "Defesa"
}

JOGADORES = ["Wellsy", "Kann"]

def coletar_categoria(categoria):
    url = f"{BASE_URL}?lang=pt&category={categoria}"

    resposta = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(
        resposta.text,
        "html.parser"
    )

    jogadores = []

    for linha in soup.select("tr"):
        colunas = linha.find_all("td")

        if len(colunas) < 2:
            continue

        texto = " ".join(
            coluna.get_text(" ", strip=True)
            for coluna in colunas
        )

        jogadores.append(texto)

    return jogadores


def coletar():
    agora = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    )

    resultado = {
        "data": agora.isoformat(),
        "categorias": {}
    }

    for categoria, nome in CATEGORIAS.items():
        try:
            dados = coletar_categoria(categoria)

            resultado["categorias"][categoria] = {
                "nome": nome,
                "jogadores": dados
            }

            print(
                f"{nome}: {len(dados)} registros"
            )

        except Exception as erro:
            print(
                f"Erro em {nome}: {erro}"
            )

            resultado["categorias"][categoria] = {
                "nome": nome,
                "erro": str(erro),
                "jogadores": []
            }

    with open(
        "ranking_atual.json",
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            resultado,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    print("Coleta finalizada.")


if __name__ == "__main__":
    coletar()
          
