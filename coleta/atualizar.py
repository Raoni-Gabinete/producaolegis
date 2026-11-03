"""
Painel Legislativo · Raoni Mendes
Atualização incremental (roda todo dia, sozinha, pelo GitHub Actions).

O que faz, em poucos minutos:
  1. Baixa de novo a lista de matérias e autorias do vereador (cerca de 24 consultas).
  2. Refaz a tramitação, os documentos acessórios e a relatoria só das matérias que podem ter mudado:
     - matérias novas;
     - matérias cuja ficha foi alterada no SAPL (data_ultima_atualizacao);
     - matérias ainda em andamento que se moveram nos últimos 2 anos;
     - matérias apresentadas nos últimos 120 dias.
  3. Aos domingos (ou com --tudo), revisa todas as que não foram concluídas, mesmo paradas há anos.

Uso:  python3 atualizar.py   (depois: python3 processar.py)
"""
import datetime as dt
import json
import os
import sys

from coletar import AUTOR_ID, PASTA, get, log, com_cache, todas_as_paginas_simples

ESTADO = os.path.join(PASTA, "_estado.json")
CONCLUSIVOS = {9, 44, 18, 19, 31, 42, 66, 55, 38, 47, 48, 5, 17, 93, 62, 85, 32, 22, 67, 41, 91}
# matérias paradas nesses status não precisam ser consultadas todo dia (concluídas ou aprovadas)
PARADOS = CONCLUSIVOS | {4, 16, 26}


def baixar_lista(caminho, nome):
    """Baixa todas as páginas de novo (sem cache) e regrava o cache por página."""
    sep = "&" if "?" in caminho else "?"
    itens, p, total = [], 1, 1
    while p <= total:
        pag = get(f"{caminho}{sep}page_size=100&page={p}")
        total = pag["pagination"]["total_pages"]
        with open(os.path.join(PASTA, f"{nome}_p{p}.json"), "w", encoding="utf-8") as f:
            json.dump(pag, f, ensure_ascii=False)
        itens.extend(pag["results"])
        p += 1
    # remove páginas que deixaram de existir
    q = total + 1
    while os.path.exists(os.path.join(PASTA, f"{nome}_p{q}.json")):
        os.remove(os.path.join(PASTA, f"{nome}_p{q}.json"))
        q += 1
    log(f"{nome}: {len(itens)} registros")
    return itens


def gravar(nome, dados):
    with open(os.path.join(PASTA, nome + ".json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)


def ler(nome):
    arq = os.path.join(PASTA, nome + ".json")
    if os.path.exists(arq):
        with open(arq, encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    hoje = dt.date.today()
    estado = ler("_estado") or {"versoes": {}}
    versoes = estado["versoes"]  # id da matéria -> data_ultima_atualizacao já processada

    log("Lista de matérias e autorias")
    materias = baixar_lista(f"materia/materialegislativa/?autores={AUTOR_ID}", "materias")
    baixar_lista(f"materia/autoria/?autor={AUTOR_ID}", "autorias")

    revisao_semanal = hoje.weekday() == 6 or "--tudo" in sys.argv
    limite = (hoje - dt.timedelta(days=120)).isoformat()
    dois_anos = (hoje - dt.timedelta(days=730)).isoformat()
    alvo = []
    for m in materias:
        mid = str(m["id"])
        tram = ler(f"tram_{mid}")
        ultimo, ultima_mov = None, ""
        if tram:
            tram_ord = sorted(tram, key=lambda t: (t.get("data_tramitacao") or "", t["id"]), reverse=True)
            ultimo = tram_ord[0].get("status")
            ultima_mov = tram_ord[0].get("data_tramitacao") or ""
        else:
            ultima_mov = ""
        motivo = None
        if tram is None:
            motivo = "nova"
        elif versoes.get(mid) != m.get("data_ultima_atualizacao"):
            motivo = "alterada no SAPL"
        elif (m.get("data_apresentacao") or "") >= limite:
            motivo = "recente"
        elif ultimo not in PARADOS and (revisao_semanal or ultima_mov >= dois_anos):
            motivo = "em andamento" if not revisao_semanal else "revisão semanal"
        if motivo:
            alvo.append((m, motivo))

    log(f"{len(alvo)} matérias para atualizar")
    for n, (m, motivo) in enumerate(alvo, 1):
        mid = m["id"]
        gravar(f"tram_{mid}", todas_as_paginas_simples(f"materia/tramitacao/?materia={mid}"))
        gravar(f"docs_{mid}", todas_as_paginas_simples(f"materia/documentoacessorio/?materia={mid}"))
        gravar(f"rel_{mid}", todas_as_paginas_simples(f"materia/relatoria/?materia={mid}"))
        versoes[str(mid)] = m.get("data_ultima_atualizacao")
        if n % 10 == 0 or n == len(alvo):
            log(f"  {n}/{len(alvo)} ({motivo})")

    estado["versoes"] = versoes
    estado["ultima_execucao"] = dt.datetime.now().isoformat(timespec="minutes")
    gravar("_estado", estado)
    log("Atualização concluída")


if __name__ == "__main__":
    main()
