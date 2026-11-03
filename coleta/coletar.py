"""
Painel Legislativo · Raoni Mendes
Carga inicial: baixa da API pública do SAPL da CMJP tudo o que o painel precisa
e grava em cache/ (uma resposta por arquivo, para poder retomar se parar no meio).

Uso:  python3 coletar.py
O SAPL bloqueia consultas rápidas (erro 503), por isso cada chamada espera PAUSA segundos
e, se for recusada, tenta de novo com espera crescente.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = "https://sapl.joaopessoa.pb.leg.br/api/"
AUTOR_ID = 102  # Raoni Mendes
PAUSA = 2.5
PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(PASTA, exist_ok=True)


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def get(caminho):
    """GET com pausa e novas tentativas. Devolve o JSON."""
    url = BASE + caminho
    espera = 10
    for tentativa in range(8):
        time.sleep(PAUSA)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PainelLegislativoRaoni/1.0 (gabinete)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            log(f"  recusado ({e}); nova tentativa em {espera}s")
            time.sleep(espera)
            espera = min(espera * 2, 180)
    raise RuntimeError("Falhou depois de várias tentativas: " + url)


def com_cache(nome, func):
    arq = os.path.join(PASTA, nome + ".json")
    if os.path.exists(arq):
        with open(arq, encoding="utf-8") as f:
            return json.load(f)
    dados = func()
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    return dados


def todas_as_paginas(caminho, nome):
    """Percorre a paginação (100 por página) guardando cada página no cache."""
    sep = "&" if "?" in caminho else "?"
    primeira = com_cache(f"{nome}_p1", lambda: get(f"{caminho}{sep}page_size=100&page=1"))
    total = primeira["pagination"]["total_pages"]
    itens = list(primeira["results"])
    for p in range(2, total + 1):
        pag = com_cache(f"{nome}_p{p}", lambda p=p: get(f"{caminho}{sep}page_size=100&page={p}"))
        itens.extend(pag["results"])
        if p % 10 == 0:
            log(f"  {nome}: página {p}/{total}")
    log(f"{nome}: {len(itens)} registros")
    return itens


def main():
    log("Tabelas de apoio")
    for caminho, nome in [
        ("materia/tipomaterialegislativa/", "tipos"),
        ("materia/statustramitacao/", "status"),
        ("materia/unidadetramitacao/", "unidades"),
        ("materia/tipodocumento/", "tipos_documento"),
        ("comissoes/comissao/", "comissoes"),
        ("parlamentares/parlamentar/", "parlamentares"),
        ("base/autor/", "autores"),
    ]:
        try:
            todas_as_paginas(caminho, nome)
        except Exception as e:  # uma tabela de apoio que falhe não impede o resto
            log(f"  aviso: {nome} não coletado ({e})")

    log("Matérias e autorias do vereador")
    materias = todas_as_paginas(f"materia/materialegislativa/?autores={AUTOR_ID}", "materias")
    todas_as_paginas(f"materia/autoria/?autor={AUTOR_ID}", "autorias")
    ids = {m["id"] for m in materias}

    log("Relatorias e documentos acessórios (base inteira, filtrada depois)")
    todas_as_paginas("materia/relatoria/", "relatorias_todas")
    todas_as_paginas("materia/documentoacessorio/", "documentos_todos")

    log(f"Tramitação de cada matéria ({len(ids)})")
    for n, mid in enumerate(sorted(ids), 1):
        com_cache(f"tram_{mid}", lambda mid=mid: todas_as_paginas_simples(f"materia/tramitacao/?materia={mid}"))
        if n % 25 == 0:
            log(f"  tramitação {n}/{len(ids)}")
    log("Carga inicial concluída")


def todas_as_paginas_simples(caminho):
    pag = get(caminho + "&page_size=100&page=1")
    itens = list(pag["results"])
    for p in range(2, pag["pagination"]["total_pages"] + 1):
        itens.extend(get(caminho + f"&page_size=100&page={p}")["results"])
    return itens


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrompido. Rode de novo para continuar de onde parou.")
