"""
Painel Legislativo · Raoni Mendes
Transforma o cache bruto do SAPL (coletar.py) no arquivo que o painel lê: ../dados/materias.json

Uso:  python3 processar.py
Regras do painel (aprovadas pelo gabinete):
  - autor x coautor separados (primeiro_autor da autoria)
  - situação = status da tramitação mais recente, agrupado em 5 situações
  - tema = classificação por palavras-chave da ementa/indexação (o SAPL não tem assunto cadastrado)
"""
import glob
import html
import json
import os
import re
import unicodedata
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "cache")
SAIDA = os.path.join(AQUI, "..", "dados", "materias.json")
SAPL = "https://sapl.joaopessoa.pb.leg.br"
AUTOR_ID = 102


def carregar(nome):
    itens = []
    for arq in sorted(glob.glob(os.path.join(CACHE, f"{nome}_p*.json"))):
        with open(arq, encoding="utf-8") as f:
            itens.extend(json.load(f)["results"])
    return itens


def por_id(nome):
    return {x["id"]: x for x in carregar(nome)}


def sem_acento(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def limpar(t):
    return re.sub(r"\s+", " ", html.unescape(t or "").replace("\ufffd", "")).strip()


def url(caminho):
    if not caminho:
        return None
    return caminho if caminho.startswith("http") else SAPL + caminho


# ---------------------------------------------------------------- situação
# 4 situações, nesta ordem no painel: Em tramitação > Atendida/Encaminhada > Arquivada > Aprovada
SITUACOES = ["Em tramitação", "Atendida/Encaminhada", "Arquivada", "Aprovada"]
NORMA = {9, 44, 18, 19, 31, 42}                  # Lei, LC, Decreto Leg., Resolução, Emenda LO, Veto rejeitado
APROVACAO_FINAL = {4, 16, 26, 11} | NORMA        # aprovado em plenário, redação final, sanção, ou virou lei/decreto…
ARQUIVO = {5, 17, 93, 62, 85, 32, 22, 67, 41, 91}  # arquivado, retirado, rejeitado, veto mantido
ENCAMINHAMENTO = {66, 55, 38}                    # encaminhado ao órgão, ofício enviado, indicação ao Executivo
TIPOS_PEDIDO = {"REQ", "IND", "R-OSM", "R-PDI", "R-VOT", "R-LPC", "R-SES", "R-JFA", "R-URG", "R-ENC", "R-CCO", "OFC"}
RX_ENCAMINHADO = re.compile(r"encaminhad|enviad[oa] (ao|a|para)|oficio")


def situacao(tram, sigla_tipo, em_tramitacao):
    """tram: andamentos do mais recente para o mais antigo."""
    ids = [t.get("status") for t in tram if t.get("status")]
    if ids and ids[0] in ARQUIVO:
        return "Arquivada"
    if not ids and not em_tramitacao:
        return "Arquivada"
    pedido = sigla_tipo in TIPOS_PEDIDO
    if pedido:
        enc = set(ids) & (ENCAMINHAMENTO | {65})
        if enc or any(RX_ENCAMINHADO.search(sem_acento(t.get("texto"))) for t in tram):
            return "Atendida/Encaminhada"
    elif set(ids) & ENCAMINHAMENTO:
        return "Atendida/Encaminhada"
    if set(ids) & APROVACAO_FINAL:
        return "Aprovada"
    return "Em tramitação"


# ---------------------------------------------------------------- temas
# A ordem importa: a primeira regra que casar define o tema principal.
HOMENAGEM = re.compile(r"\b(voto|votos) de\b|\btitulo de cidad|\bcidadao pessoense|\bcomenda|\bmedalha|\bhonra ao merito|\bsessao (especial|solene)|\bhomenage|\bdenomina|\bpesar\b|\bfalecimento|\butilidade publica|\bcalendario oficial|\bdia (municipal|estadual|do|da)\b.*\binstitui|\binstitui\b.*\b(dia|semana) (municipal|do|da)\b")
PEDIDO_INFO = re.compile(r"\bpedido de informac|\bacesso a informac|\bsolicita (informac|explicac)|\bexplicacoes\b|\btransparencia|\bprestacao de contas|\blicitac|\bcpi\b|\bcomissao (especial|de estudo|processante)|\btribunal de contas|\bfiscaliza")

# Órgão destinatário citado na ementa: é o sinal mais confiável do tema nos requerimentos.
ORGAOS = [
    ("Educação", r"\bsedec\b|\bseduc\b|\bsecretaria (municipal )?de educacao"),
    ("Mobilidade e Trânsito", r"\bsemob\b|\bsttrans\b|\bsttu\b"),
    ("Infraestrutura e Obras", r"\bseinfra\b|\bemurb\b|\bseplan\b|\bsemhab\b|\benergisa\b|\bsedurb\b"),
    ("Meio Ambiente e Limpeza Urbana", r"\bemlur\b|\bsemam\b|\bcagepa\b"),
    ("Saúde", r"\bsms\b|\bsecretaria (municipal )?de saude"),
    ("Assistência Social", r"\bsedes\b|\bsemdh\b|\bsedhuc\b|\bfunad\b"),
    ("Segurança", r"\bsemusb\b|\bguarda (civil )?municipal\b|\bdefesa civil\b"),
    ("Cultura, Esporte e Lazer", r"\bfunjope\b|\bsejel\b|\bsecult\b|\bsetur\b"),
]

TEMAS = [
    ("Saúde", r"\bsaude|\bhospita|\bupa\b|\busf\b|\besf\b|\bpsf\b|\bmedic|\bvacina|\bdengue|\bzika|\bchikungunya|\bsamu\b|\benferm|\bsus\b|\bodontol|\bfarmac|\bdoenca|\bcancer|\bautis|\btea\b|\bsindrome|\bsaude mental|\bcaps\b"),
    ("Educação", r"\bescola|\beduca(cao|cional)|\bensino|\bcreche|\bcrei\b|\bcmei\b|\bprofessor|\baluno|\bestudant|\balfabetiz|\bbibliotec|\buniversid|\bmerenda|\bfardamento|\bdidatic"),
    ("Mobilidade e Trânsito", r"\btransit|\bonibus|\btransporte|\bsemaforo|\bsinaliza|\bfaixa de pedestre|\blombada|\bredutor(es)? de velocidade|\bciclo(via|faixa)|\bestacionamento|\bmototaxi|\btaxi|\bparada de onibus|\bmobilidade|\btarifa"),
    ("Meio Ambiente e Limpeza Urbana", r"\blixo|\blimpeza|\bcoleta|\brecicla|\bresiduo|\bentulho|\bcacamba|\bcapina|\bmeio ambiente|\bambienta|\barvore|\barboriza|\bpoda\b|\banima(l|is)\b|\bcaes\b|\bgatos\b|\bmaus.?tratos|\bmangue|\bpraia|\bpolui|\bsustentav|\besgoto|\bsaneamento|\bagua\b"),
    ("Infraestrutura e Obras", r"\bpavimenta|\bcalcament|\basfalt|\brecapea|\bburaco|\bdrenagem|\bgaleria|\bobras?\b|\bconstruc|\breforma\b|\biluminac|\blampada|\bposte|\bponte|\bviaduto|\bcanal\b|\bpraca|\bcalcada|\burbaniz|\binfraestrutura|\bhabitac|\bmoradia|\bzoneamento|\bplano diretor|\bcodigo de (urbanismo|obras|posturas)"),
    ("Assistência Social", r"\bassistencia social|\bcras\b|\bcreas\b|\bvulnerab|\bsituacao de rua|\bmorador(es)? de rua|\bfome\b|\bseguranca alimentar|\bcesta basica|\bidos|\bterceira idade|\bancia|\bcrianca|\badolescen|\bjuventude|\bjovens\b|\bmaes?\b|\bgestante|\blactante|\batipic|\bcuidador|\bdeficien|\bcadeirante|\bpcd\b"),
    ("Segurança", r"\bseguranca publica|\bpolicia|\bviolencia(?! contra a mulher| domestica)|\bcrime|\bassalto|\bdrogas?\b|\bvideomonitor|\bcameras?\b|\bronda|\bbombeiro"),
    ("Direitos e Cidadania", r"\bmulher|\bfeminic|\bviolencia (contra a mulher|domestica)|\bgenero|\bigualdade|\bracis|\blgbt|\bdireitos|\bcidadania|\bconsumidor|\bprocon|\bacessibilidade|\binclusao|\breligios|\btrabalhador|\bemprego|\bservidor|\bconcurso|\bempreend|\bcomercio|\bfeirante|\bambulante|\bcombustive"),
    ("Cultura, Esporte e Lazer", r"\bcultura|\besporte|\besportiv|\blazer|\bfesta|\bcarnaval|\bsao joao|\bmusica|\bartista|\bteatro|\bcinema|\bquadra|\bginasio|\bfutebol|\batleta|\bturismo|\bturistic|\bpatrimonio"),
    ("Fiscalização e Transparência", r"\baudiencia publica|\bministerio publico|\bdenuncia|\birregular|\bcontrato|\bconvoca|\bldo\b|\bloa\b|\borcamento"),
]
ORGAOS_RE = [(n, re.compile(p)) for n, p in ORGAOS]
TEMAS_RE = [(n, re.compile(p)) for n, p in TEMAS]
SIGLAS_HOMENAGEM = {"R-VOT", "R-LPC", "R-SES"}


def tema(m, sigla_tipo):
    if sigla_tipo in SIGLAS_HOMENAGEM:
        return "Homenagens e Títulos"
    if sigla_tipo in ("R-PDI", "R-CCO"):
        return "Fiscalização e Transparência"
    if sigla_tipo in ("E-MET", "E-ADI"):
        return "Fiscalização e Transparência"
    if sigla_tipo in ("R-JFA", "R-URG", "R-ENC"):
        return "Outros"  # atos de rotina do processo legislativo
    texto = sem_acento(" ".join([m.get("ementa") or "", m.get("indexacao") or "", m.get("objeto") or ""]))
    if HOMENAGEM.search(texto):
        return "Homenagens e Títulos"
    if PEDIDO_INFO.search(texto):
        return "Fiscalização e Transparência"
    for nome, rx in ORGAOS_RE:
        if rx.search(texto):
            return nome
    for nome, rx in TEMAS_RE:
        if rx.search(texto):
            return nome
    return "Outros"


# ---------------------------------------------------------------- trilha (barra de evolução)
# A barra segue os andamentos reais da aba Tramitação, em ordem cronológica.
NEGATIVO = {22, 41, 5, 17, 93, 62, 85, 32, 67, 91}
VETO = {33, 10}
FIM_OK = NORMA | ENCAMINHAMENTO | {47, 48}
APROVACAO = {4, 16, 26, 86, 11, 87}
TIPOS_PROJETO = {"PLO", "PLC", "PDL", "PRE", "PELO", "E-MET", "E-ADI", "RES"}


# Próximo passo esperado, conforme a natureza da matéria
META = {
    "PLO": "Lei", "PLC": "Lei Complementar", "PDL": "Decreto Legislativo", "PRE": "Resolução",
    "RES": "Resolução", "PELO": "Emenda à Lei Orgânica", "E-MET": "Emenda incluída na LDO",
    "E-ADI": "Emenda incluída na LDO", "REQ": "Envio ao órgão", "R-OSM": "Envio ao órgão",
    "R-PDI": "Envio do pedido de informações", "IND": "Indicação enviada ao Executivo",
    "R-VOT": "Voto aprovado", "R-LPC": "Voto de pesar aprovado", "R-SES": "Sessão aprovada",
    "R-JFA": "Justificativa registrada", "R-URG": "Inclusão na Ordem do Dia",
    "R-ENC": "Encerramento da discussão", "R-CCO": "Comissão constituída", "OFC": "Leitura em Plenário",
}


def rotulo_status(txt):
    txt = (txt or "Andamento").strip().rstrip(".")
    if txt.isupper():
        txt = txt.capitalize().replace("adin", "ADIN")
    return txt


def trilha(sigla, tram_cronologica, apresentacao, em_tramitacao, situacao_, status):
    passos = [{"rotulo": "Apresentada", "data": apresentacao, "tom": "neutro"}]
    for t in tram_cronologica:
        sid = t.get("status")
        if not sid:
            continue
        rot = rotulo_status(status.get(sid, {}).get("descricao"))
        if sid == 1 and len(passos) == 1:      # "Apresentado em Plenário" repete o primeiro passo
            passos[0]["rotulo"], passos[0]["data"] = "Apresentada em Plenário", t.get("data_tramitacao") or apresentacao
            continue
        if passos[-1]["rotulo"] == rot:         # andamentos repetidos em sequência viram um só
            passos[-1]["data"] = t.get("data_tramitacao")
            continue
        tom = ("neg" if sid in NEGATIVO else "veto" if sid in VETO else "fim" if sid in FIM_OK
               else "ok" if sid in APROVACAO else "neutro")
        passos.append({"rotulo": rot, "data": t.get("data_tramitacao"), "tom": tom})

    ultimo = passos[-1]["tom"]
    meta = None
    if situacao_ == "Arquivada":
        andamento = "negativa"
        if ultimo != "neg":
            passos.append({"rotulo": "Arquivada", "data": None, "tom": "neg"})
    elif ultimo == "fim" or situacao_ == "Atendida/Encaminhada" or (situacao_ == "Aprovada" and sigla not in TIPOS_PROJETO):
        andamento = "concluida"
    else:
        andamento = "em_curso"
        meta = META.get(sigla, "Conclusão")
    return {"passos": passos, "andamento": andamento, "meta": meta}


# Tipos que entram na soma total mas não aparecem no detalhamento
OCULTAR_SIGLAS = {"R-JFA"}  # justificativas de falta/ausência


# Nome amigável do tipo (o SAPL tem subtipos internos de requerimento)
TIPO_PUBLICO = {
    "REQ": "Requerimento", "R-OSM": "Requerimento", "R-PDI": "Requerimento", "R-URG": "Requerimento",
    "R-ENC": "Requerimento", "R-CCO": "Requerimento", "R-JFA": "Requerimento", "R-SES": "Requerimento",
    "R-VOT": "Voto de aplauso/congratulação", "R-LPC": "Voto de pesar",
    "IND": "Indicação", "PLO": "Projeto de Lei", "PLC": "Projeto de Lei Complementar",
    "PDL": "Projeto de Decreto Legislativo", "PRE": "Projeto de Resolução", "RES": "Resolução",
    "PELO": "Proposta de Emenda à Lei Orgânica", "E-MET": "Emenda à LDO", "E-ADI": "Emenda à LDO", "OFC": "Ofício",
}


# ---------------------------------------------------------------- montagem
def main():
    tipos = por_id("tipos")
    status = por_id("status")
    unidades = por_id("unidades")
    comissoes = por_id("comissoes")
    parlamentares = por_id("parlamentares")
    autores = por_id("autores")
    tipos_doc = por_id("tipos_documento")

    def nome_unidade(uid):
        u = unidades.get(uid)
        return u["__str__"] if u else None

    def nome_parlamentar(pid):
        p = parlamentares.get(pid)
        return re.sub(r"\s+-\s+Suplente$", "", p["nome_parlamentar"]) if p else None

    materias = carregar("materias")
    ids = {m["id"] for m in materias}
    primeiro = {a["materia"]: a["primeiro_autor"] for a in carregar("autorias")}

    relatorias = {}
    for r in carregar("relatorias_todas"):
        if r["materia"] in ids:
            relatorias.setdefault(r["materia"], []).append(r)
    documentos = {}
    for d in carregar("documentos_todos"):
        if d["materia"] in ids:
            documentos.setdefault(d["materia"], []).append(d)
    # a atualização diária (atualizar.py) grava docs_<id> e rel_<id>: esses valem mais que a carga inicial
    for mid in ids:
        for prefixo, destino in (("docs", documentos), ("rel", relatorias)):
            arq = os.path.join(CACHE, f"{prefixo}_{mid}.json")
            if os.path.exists(arq):
                with open(arq, encoding="utf-8") as f:
                    destino[mid] = json.load(f)

    # coautores de cada matéria (todas as autorias da matéria vêm em "autores")
    saida = []
    sem_tram = 0
    for m in materias:
        tp = tipos.get(m["tipo"], {})
        sigla = tp.get("sigla", "")
        arq_tram = os.path.join(CACHE, f"tram_{m['id']}.json")
        tram = json.load(open(arq_tram, encoding="utf-8")) if os.path.exists(arq_tram) else None
        if tram is None:
            sem_tram += 1
            tram = []
        tram.sort(key=lambda t: (t.get("data_tramitacao") or "", t["id"]), reverse=True)
        ultima = tram[0] if tram else None
        st_id = ultima.get("status") if ultima else None

        outros_autores = [autores[a]["nome"] for a in m.get("autores", []) if a != AUTOR_ID and a in autores]

        saida.append({
            "id": m["id"],
            "tipo": TIPO_PUBLICO.get(sigla, tp.get("descricao", "")),
            "tipo_sapl": tp.get("descricao", ""),
            "sigla": sigla,
            "numero": m["numero"],
            "ano": m["ano"],
            "titulo": f"{TIPO_PUBLICO.get(sigla, tp.get('descricao', 'Matéria'))} nº {m['numero']}/{m['ano']}",
            "apresentacao": m.get("data_apresentacao"),
            "protocolo": m.get("numero_protocolo"),
            "ementa": limpar(m.get("ementa")),
            "apelido": m.get("apelido") or "",
            "indexacao": m.get("indexacao") or "",
            "em_tramitacao": m.get("em_tramitacao"),
            "papel": "Autor" if primeiro.get(m["id"], True) else "Coautor",
            "coautores": outros_autores,
            "texto": url(m.get("texto_original")),
            "link": f"{SAPL}/materia/{m['id']}",
            "status": status.get(st_id, {}).get("descricao") if st_id else None,
            "situacao": situacao(tram, sigla, m.get("em_tramitacao")),
            "tema": tema(m, sigla),
            "ultima_mov": ultima.get("data_tramitacao") if ultima else None,
            "local": nome_unidade(ultima.get("unidade_tramitacao_destino")) if ultima else None,
            "trilha": trilha(sigla, list(reversed(tram)), m.get("data_apresentacao"), m.get("em_tramitacao"),
                             situacao(tram, sigla, m.get("em_tramitacao")), status),
            "tramitacao": [{
                "data": t.get("data_tramitacao"),
                "origem": nome_unidade(t.get("unidade_tramitacao_local")),
                "destino": nome_unidade(t.get("unidade_tramitacao_destino")),
                "status": status.get(t.get("status"), {}).get("descricao"),
                "texto": limpar(t.get("texto")),
                "urgente": t.get("urgente", False),
            } for t in tram],
            "documentos": [{
                "nome": d.get("nome") or tipos_doc.get(d.get("tipo"), {}).get("descricao", "Documento"),
                "tipo": tipos_doc.get(d.get("tipo"), {}).get("descricao", ""),
                "data": d.get("data"),
                "autor": d.get("autor") or "",
                "ementa": limpar(d.get("ementa")),
                "arquivo": url(d.get("arquivo")),
            } for d in sorted(documentos.get(m["id"], []), key=lambda d: d.get("data") or "", reverse=True)],
            "relatorias": [{
                "comissao": comissoes.get(r.get("comissao"), {}).get("nome"),
                "sigla_comissao": comissoes.get(r.get("comissao"), {}).get("sigla"),
                "relator": nome_parlamentar(r.get("parlamentar")),
                "designacao": r.get("data_designacao_relator"),
                "destituicao": r.get("data_destituicao_relator"),
            } for r in sorted(relatorias.get(m["id"], []), key=lambda r: r.get("data_designacao_relator") or "")],
        })

    saida.sort(key=lambda x: (x["apresentacao"] or "", x["id"]), reverse=True)

    # Números do topo contam tudo; a lista detalhada não mostra justificativas de falta
    resumo = {
        "total": len(saida),
        "autor": sum(x["papel"] == "Autor" for x in saida),
        "coautor": sum(x["papel"] == "Coautor" for x in saida),
        "em_tramitacao": sum(x["situacao"] == "Em tramitação" for x in saida),
        "aprovada": sum(x["situacao"] == "Aprovada" for x in saida),
        "encaminhada": sum(x["situacao"] == "Atendida/Encaminhada" for x in saida),
    }
    ocultas = [x for x in saida if x["sigla"] in OCULTAR_SIGLAS]
    saida = [x for x in saida if x["sigla"] not in OCULTAR_SIGLAS]
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    datas = [x["ultima_mov"] for x in saida if x["ultima_mov"]]
    pacote = {
        "atualizado_em": __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "parlamentar": "Raoni Mendes",
        "fonte": SAPL,
        "total": resumo["total"],
        "resumo": resumo,
        "materias": saida,
    }
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(pacote, f, ensure_ascii=False, separators=(",", ":"))

    # cópia em .js: permite abrir o painel direto do computador (file://), sem servidor
    with open(SAIDA[:-5] + ".js", "w", encoding="utf-8") as f:
        f.write("window.PAINEL_DADOS=")
        json.dump(pacote, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";")
    print(f"Total geral {resumo['total']} · {len(ocultas)} justificativas de falta fora do detalhamento")
    print(f"{len(saida)} matérias gravadas em dados/materias.json ({os.path.getsize(SAIDA)//1024} KB)")
    if sem_tram:
        print(f"Aviso: {sem_tram} matérias ainda sem tramitação no cache")
    print("\ntrilha:", Counter(x["trilha"]["andamento"] for x in saida).most_common(),
          "| passos (média):", round(sum(len(x["trilha"]["passos"]) for x in saida) / len(saida), 1))
    for campo in ["papel", "situacao", "tema", "sigla", "ano"]:
        print(f"\n{campo}:", Counter(x[campo] for x in saida).most_common())
    print("\nstatus atuais mais comuns:", Counter(x["status"] for x in saida).most_common(25))
    print("Última movimentação:", max(datas) if datas else "—")


if __name__ == "__main__":
    main()
