
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


def limpar_nome(texto):
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def coletar_categoria(categoria):

    url = f"{BASE_URL}?lang=pt&category={categoria}"

    resposta = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(
        resposta.text,
        "html.parser"
    )

    jogadores = {}

    # Captura os jogadores da tabela
    for linha in soup.find_all("tr"):

        colunas = linha.find_all("td")
        if colunas:
            print("CELULAS:", [
                c.get_text(" ", strip=True)
                for c in colunas
            ])
        if len(colunas) < 4:
            continue

        textos = [
            coluna.get_text(" ", strip=True)
            for coluna in colunas
        ]

        # Posição
        match_pos = re.search(
            r"#?\s*(\d+)",
            textos[0]
        )

        if not match_pos:
            continue

        posicao = int(match_pos.group(1))

        # Nome do jogador
        link = colunas[1].find("a")

        if link:
            nome = limpar_nome(
                link.get_text(" ", strip=True)
            )
        else:
            nome = limpar_nome(textos[1])

        # Nível da categoria
        level = numero(textos[2])

        # Experiência da categoria
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

        # Somente cards com posição 1, 2 ou 3
        match_pos = re.search(
            r"#\s*([123])\b",
            texto
        )

        if not match_pos:
            continue

        posicao = int(match_pos.group(1))

        # Evita containers que englobam a página inteira
        if len(texto) > 500:
            continue

        nome_tag = card.find(
            ["h2", "h3", "h4"]
        )

        if not nome_tag:
            continue

        nome = limpar_nome(
            nome_tag.get_text(" ", strip=True)
        )

        # Identifica nível e XP
        match_level = re.search(
            r"(?:Nível|Magia|Força|Paladino|Defesa)"
            r"\s*(\d+)",
            texto,
            re.IGNORECASE
        )

        match_xp = re.search(
            r"([\d.]+)\s*XP",
            texto,
            re.IGNORECASE
        )

        if not match_level:
            continue

        level = numero(match_level.group(1))

        xp = (
            numero(match_xp.group(1))
            if match_xp
            else None
        )

        jogadores[posicao] = {
            "posicao": posicao,
            "nome": nome,
            "level": level,
            "xp": xp
        }

    # Ordena pela posição real do ranking
    lista = sorted(
        jogadores.values(),
        key=lambda jogador: jogador["posicao"]
    )

    return lista


def coletar():

    agora = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    )

    resultado = {
        "data": agora.isoformat(),
        "categorias": {}
    }

    total_jogadores = 0

    for categoria, nome_categoria in CATEGORIAS.items():

        jogadores = coletar_categoria(categoria)

        print(
            f"{nome_categoria}: "
            f"{len(jogadores)} jogadores"
        )

        # Exige pelo menos os 50 jogadores
        if len(jogadores) != 50:

            raise RuntimeError(
                f"{nome_categoria}: esperado 50 jogadores, "
                f"encontrados {len(jogadores)}. "
                "JSON anterior preservado."
            )

        # Verifica posições
        posicoes = [
            jogador["posicao"]
            for jogador in jogadores
        ]

        if posicoes != list(range(1, 51)):

            raise RuntimeError(
                f"{nome_categoria}: posições incorretas. "
                "JSON anterior preservado."
            )

        resultado["categorias"][categoria] = {
            "nome": nome_categoria,
            "jogadores": jogadores,
            "top3": jogadores[:3]
        }

        total_jogadores += len(jogadores)

    # Só salva se todas as categorias estiverem completas
    if total_jogadores != 250:

        raise RuntimeError(
            "Coleta incompleta. JSON anterior preservado."
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

    print("Coleta finalizada: 250 jogadores.")
    print("5 categorias completas.")
    print("Top 3 incluído em cada categoria.")


if __name__ == "__main__":
    coletar()
    
