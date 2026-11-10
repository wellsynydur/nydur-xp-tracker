
import requests
from bs4 import BeautifulSoup
import json
import re
import os
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

def numero(texto):
    texto = texto.replace(".", "").replace(",", "")
    resultado = re.search(r"\d+", texto)
    return int(resultado.group()) if resultado else 0

def coletar_categoria(categoria):
    url = f"{BASE_URL}?lang=pt&category={categoria}"

    resposta = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(resposta.text, "html.parser")
    jogadores = []

    for linha in soup.select("tr"):
        colunas = linha.find_all("td")

        if len(colunas) < 3:
            continue

        textos = [
            coluna.get_text(" ", strip=True)
            for coluna in colunas
        ]

        posicao = numero(textos[0])

        if posicao <= 0:
            continue

        nome = textos[1]

        if not nome:
            continue

        level = None
        xp = None

        for texto in textos[2:]:
            valor = numero(texto)

            if valor > 0:
                if level is None:
                    level = valor
                else:
                    xp = valor

        jogadores.append({
            "posicao": posicao,
            "nome": nome,
            "level": level,
            "xp": xp
        })

    jogadores.sort(key=lambda x: x["posicao"])

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
            jogadores = coletar_categoria(categoria)

            resultado["categorias"][categoria] = {
                "nome": nome,
                "jogadores": jogadores,
                "top3": jogadores[:3]
            }

            print(f"{nome}: {len(jogadores)} jogadores")

            for jogador in jogadores[:3]:
                print(
                    jogador["posicao"],
                    jogador["nome"],
                    jogador["level"],
                    jogador["xp"]
                )

        except Exception as erro:
            print(f"Erro em {nome}: {erro}")

            resultado["categorias"][categoria] = {
                "nome": nome,
                "jogadores": [],
                "top3": [],
                "erro": str(erro)
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
    
