
import requests
from bs4 import BeautifulSoup
import json
import re
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
    texto = str(texto)
    texto = re.sub(r"[^\d]", "", texto)
    return int(texto) if texto else None


def coletar_categoria(categoria):

    url = f"{BASE_URL}?lang=pt&category={categoria}"

    resposta = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(resposta.text, "html.parser")

    print("\n===== DIAGNOSTICO =====")
    print("Categoria:", categoria)
    print("Status HTTP:", resposta.status_code)
    print("Tamanho HTML:", len(resposta.text))
    print("Tabelas encontradas:", len(soup.find_all("table")))
    print("Linhas encontradas:", len(soup.find_all("tr")))
    print("Cards encontrados:", len(soup.find_all(["div", "article"])))
    print("===== INICIO DO HTML =====")
    print(soup.get_text(" ", strip=True)[:2500])
    print("===== FIM DO DIAGNOSTICO =====\n")
    
    jogadores = {}

    # Lê os jogadores da tabela
    for linha in soup.find_all("tr"):

        colunas = linha.find_all("td")

        if len(colunas) < 4:
            continue

        textos = [
            coluna.get_text(" ", strip=True)
            for coluna in colunas
        ]

        posicao_match = re.search(
            r"#?\s*(\d+)",
            textos[0]
        )

        if not posicao_match:
            continue

        posicao = int(posicao_match.group(1))

        coluna_nome = colunas[1]

        link = coluna_nome.find("a")

        if link:
            nome = link.get_text(" ", strip=True)
        else:
            nome = coluna_nome.get_text(" ", strip=True)

        level = numero(textos[2])
        xp = numero(textos[3])

        if not nome:
            continue

        jogadores[posicao] = {
            "posicao": posicao,
            "nome": nome,
            "level": level,
            "xp": xp
        }

    # Captura os cards do Top 1, 2 e 3
    for card in soup.find_all(["div", "article"]):

        texto = card.get_text(" ", strip=True)

        posicao_match = re.search(
            r"#\s*([123])\b",
            texto
        )

        if not posicao_match:
            continue

        posicao = int(posicao_match.group(1))

        # Evita considerar containers grandes
        if len(texto) > 500:
            continue

        nome_tag = card.find(["h2", "h3", "h4"])

        if not nome_tag:
            continue

        nome = nome_tag.get_text(" ", strip=True)

        level_match = re.search(
            r"Nível\s*([\d.]+)",
            texto,
            re.IGNORECASE
        )

        xp_match = re.search(
            r"([\d.]+)\s*XP",
            texto,
            re.IGNORECASE
        )

        if not level_match:
            continue

        level = numero(level_match.group(1))

        xp = numero(xp_match.group(1)) if xp_match else None

        jogadores[posicao] = {
            "posicao": posicao,
            "nome": nome,
            "level": level,
            "xp": xp
        }

    return sorted(
        jogadores.values(),
        key=lambda jogador: jogador["posicao"]
    )


def coletar():

    resultado = {
        "data": datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).isoformat(),
        "categorias": {}
    }

    for categoria, nome in CATEGORIAS.items():

        jogadores = coletar_categoria(categoria)

        resultado["categorias"][categoria] = {
            "nome": nome,
            "jogadores": jogadores,
            "top3": jogadores[:3]
        }

        print(
            f"{nome}: {len(jogadores)} jogadores"
        )

    # Não sobrescreve o ranking com dados vazios
    total = sum(
        len(item["jogadores"])
        for item in resultado["categorias"].values()
    )

    if total == 0:
        raise RuntimeError(
            "Nenhum jogador encontrado. "
            "Ranking anterior preservado."
        )

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
    
