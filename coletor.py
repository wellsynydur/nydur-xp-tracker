
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


def normalizar(texto):
    texto = texto.lower().strip()
    texto = texto.replace("í", "i")
    texto = texto.replace("á", "a")
    texto = texto.replace("ã", "a")
    texto = texto.replace("ç", "c")
    texto = texto.replace("ê", "e")
    texto = texto.replace("é", "e")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")
    return texto


def numero(texto):
    texto = str(texto).strip()

    texto = re.sub(r"[^\d]", "", texto)

    if not texto:
        return None

    return int(texto)


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

    tabelas = soup.find_all("table")

    for tabela in tabelas:

        cabecalho = tabela.find("thead")

        if cabecalho is None:
            continue

        colunas_header = cabecalho.find_all("th")

        nomes_colunas = [
            normalizar(
                coluna.get_text(" ", strip=True)
            )
            for coluna in colunas_header
        ]

        if not nomes_colunas:
            continue

        indice_posicao = None
        indice_jogador = None
        indice_level = None
        indice_xp = None

        for i, nome in enumerate(nomes_colunas):

            if "posicao" in nome or "posição" in nome:
                indice_posicao = i

            elif "jogador" in nome:
                indice_jogador = i

            elif "nivel" in nome or "level" in nome:
                indice_level = i

            elif "experiencia" in nome or "xp" in nome:
                indice_xp = i

        if (
            indice_posicao is None
            or indice_jogador is None
            or indice_level is None
            or indice_xp is None
        ):
            continue

        linhas = tabela.find_all("tr")

        for linha in linhas:

            colunas = linha.find_all("td")

            if not colunas:
                continue

            if len(colunas) <= max(
                indice_posicao,
                indice_jogador,
                indice_level,
                indice_xp
            ):
                continue

            posicao = numero(
                colunas[indice_posicao].get_text(
                    " ", strip=True
                )
            )

            coluna_jogador = colunas[indice_jogador]

            link = coluna_jogador.find("a")

            if link:
                nome = link.get_text(
                    " ", strip=True
                )
            else:
                nome = coluna_jogador.get_text(
                    " ", strip=True
                )

            level = numero(
                colunas[indice_level].get_text(
                    " ", strip=True
                )
            )

            xp = numero(
                colunas[indice_xp].get_text(
                    " ", strip=True
                )
            )

            if not nome or posicao is None:
                continue

            jogadores.append({
                "posicao": posicao,
                "nome": nome,
                "level": level,
                "xp": xp
            })

        if jogadores:
            break

    jogadores.sort(
        key=lambda jogador: jogador["posicao"]
    )

    return jogadores


def coletar():

    agora = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    )

    resultado = {
        "data": agora.isoformat(),
        "categorias": {}
    }

    for categoria, nome_categoria in CATEGORIAS.items():

        try:

            jogadores = coletar_categoria(
                categoria
            )

            resultado["categorias"][categoria] = {
                "nome": nome_categoria,
                "jogadores": jogadores,
                "top3": jogadores[:3]
            }

            print(
                f"{nome_categoria}: "
                f"{len(jogadores)} jogadores"
            )

            for jogador in jogadores[:3]:

                print(
                    jogador["posicao"],
                    jogador["nome"],
                    jogador["level"],
                    jogador["xp"]
                )

        except Exception as erro:

            print(
                f"Erro em {nome_categoria}: {erro}"
            )

            resultado["categorias"][categoria] = {
                "nome": nome_categoria,
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
    
