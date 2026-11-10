
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

    # Captura tabela: cada linha tem posição, nível e XP; nome vem no link.
    for linha in soup.find_all("tr"):
        celulas = linha.find_all(["td", "th"])
        textos = [c.get_text(" ", strip=True) for c in celulas]
        texto_linha = " ".join(textos)
        match_pos = re.search(r"#\s*(\d+)", texto_linha)
        if not match_pos:
            continue
        posicao = int(match_pos.group(1))
        if not 4 <= posicao <= 50:
            continue
        link = linha.find("a")
        nome = limpar_nome(link.get_text(" ", strip=True)) if link else ""

        # Alguns rankings exibem o nome como atributo da imagem/avatar,
        # e não como texto do link.
        if not nome:
            imagem = linha.find("img")
            if imagem:
                nome = limpar_nome(
                    imagem.get("alt") or imagem.get("title") or ""
                )
        if not nome:
            for elemento in linha.find_all(True):
                nome = limpar_nome(
                    elemento.get("data-name") or elemento.get("title") or ""
                )
                if nome and not re.search(r"#?\s*\d+", nome):
                    break

        # Nome pode estar em coluna separada ou em atributos; os números
        # da linha são posição, nível e XP.
        nums = []
        for valor in textos:
            if re.search(r"#\s*\d+", valor):
                continue
            n = numero(valor)
            if n is not None:
                nums.append(n)

        if not nome:
            # Fallback: usa texto integral da linha e remove posição,
            # nível e XP, se o nome estiver presente como texto.
            texto_integral = limpar_nome(linha.get_text(" ", strip=True))
            texto_integral = re.sub(r"#\s*\d+", " ", texto_integral)
            for n in nums:
                texto_integral = re.sub(
                    rf"(?<!\d){n:,}".replace(",", r"[,.]?"),
                    " ",
                    texto_integral,
                    count=1
                )
            nome = limpar_nome(texto_integral)

        if not nome or len(nums) < 2:
            continue
        jogadores[posicao] = {
            "posicao": posicao, "nome": nome,
            "level": nums[-2], "xp": nums[-1]
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
    
