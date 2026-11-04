# Painel Legislativo · Vereador Raoni Mendes

Painel público com toda a produção legislativa do vereador. Os dados vêm do SAPL da CMJP (autor ID 102).

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `index.html` | O painel em si. É uma página só e não precisa de banco de dados. |
| `dados/materias.js` | Os dados que o painel lê. Funciona mesmo abrindo o arquivo direto do computador. |
| `logo-raoni.png` | Logo em versão negativa (branca), reduzido para 720px a partir de `../logo-raoni-negativo.png`. |
| `dados/materias.json` | Os mesmos dados, em JSON (reserva). |
| `coleta/coletar.py` | Carga completa do SAPL para `coleta/cache/`, só na primeira vez. Se parar no meio, retoma de onde parou. |
| `coleta/atualizar.py` | Atualização diária incremental: só o que pode ter mudado. |
| `.github/workflows/atualizar.yml` | O robô que roda a atualização às 06h e 14h, de segunda a sexta e publica. |
| `CNAME` | Diz ao GitHub Pages que o endereço é `producaolegis.raonimendes.com.br`. |
| `compartilhar.png`, `favicon.svg` | Imagem de prévia para WhatsApp e redes sociais, e o ícone da aba do navegador. |
| `coleta/processar.py` | Transforma o cache nos arquivos de `dados/`: situação, tema, autor ou coautor e barra de evolução. |

## Endereço oficial

**https://producaolegis.raonimendes.com.br**

A página fica hospedada no **GitHub Pages**, que é gratuito. O **GitHub Actions** atualiza os dados sozinho, às **06h e 14h, de segunda a sexta** (horário de Brasília). Ninguém precisa fazer nada no dia a dia.

## Publicar pela primeira vez (uma vez só)

O passo a passo completo está em `PUBLICAR.md`.

## Como a atualização automática funciona

1. `coleta/atualizar.py` baixa de novo a lista de matérias do vereador e busca a tramitação, os documentos e a relatoria das matérias que podem ter mudado: as novas, as alteradas no SAPL, as recentes e as ainda em andamento. São cerca de 45 por dia, e leva de 10 a 15 minutos.
   - Na segunda-feira às 06h, ele revisa também as paradas há muito tempo.
2. `coleta/processar.py` monta `dados/materias.js` e `dados/materias.json`.
3. O robô salva as mudanças no repositório, e o GitHub Pages publica sozinho.

Para rodar na hora: no GitHub, abra **Actions → Atualizar painel → Run workflow**. Marque "Revisar todas" se quiser uma revisão completa.

Para rodar no computador:

```
cd coleta
python3 atualizar.py     # incremental, de 10 a 15 min
python3 processar.py
```

Para refazer tudo do zero, apague `coleta/cache/` e rode `python3 coletar.py`. Leva cerca de 3 horas.

## Regras do painel

- **Barra de evolução.** Mostra os andamentos reais da aba Tramitação, em ordem cronológica.
  - Andamentos repetidos em sequência viram um só.
  - Cores do último passo:
    - dourado pulsando: em curso;
    - verde: concluída (virou lei, decreto, resolução… ou foi encaminhada);
    - vermelho: arquivada, rejeitada ou retirada;
    - laranja: vetada.
  - Se a matéria ainda corre, aparece em tracejado o próximo passo conforme a natureza: Projeto de Lei → "Lei", PLC → "Lei Complementar", PDL → "Decreto Legislativo", Projeto de Resolução → "Resolução", PELO → "Emenda à Lei Orgânica", Emenda à LDO → "Emenda incluída na LDO", Requerimento → "Envio ao órgão", Indicação → "Indicação enviada ao Executivo", votos → "Voto aprovado" (lista `META` em `processar.py`).
  - No cartão aparecem no máximo 5 passos. Na ficha aparecem todos.
- **Situação.** São 4 grupos, nesta ordem, definidos pela tramitação:
  1. **Em tramitação:** todas as que não se encaixam nos outros grupos.
  2. **Atendida/Encaminhada:** requerimentos, indicações e afins cuja tramitação informa encaminhamento (encaminhado ao órgão, ofício enviado, indicação ao Executivo, enviado ao Executivo).
  3. **Arquivada:** o último andamento é de arquivamento, retirada, rejeição ou veto mantido.
  4. **Aprovada:** aprovada em plenário, redação final, sanção, ou virou lei, lei complementar, decreto legislativo, resolução ou emenda à Lei Orgânica.
- **Justificativas de falta (tipo R-JFA).** Entram nos números do topo (total 1.166), mas não aparecem na lista, nos filtros nem nas fichas (`OCULTAR_SIGLAS` em `processar.py`).
- **Tema.** Classificado pelo gabinete a partir da ementa, porque o SAPL não tem assunto cadastrado.
  - Primeiro pelo órgão citado (SEDEC, SEMOB, SEINFRA, EMLUR…).
  - Depois por palavras-chave.
  - Para ajustar, edite as listas `ORGAOS` e `TEMAS` em `processar.py`.

## Layout (mobile first)

- **Base: celular.**
  - Os números do topo ficam numa faixa com rolagem lateral.
  - A busca e o botão Filtrar ficam fixos no alto ao rolar a página.
  - Os filtros abrem como uma gaveta, com o botão "Ver N resultados".
  - No cartão, a barra de evolução mostra só os pontos e uma linha "Agora: … · data · próximo passo".
  - A ficha da matéria ocupa a tela inteira, com a evolução em linha do tempo vertical.
- **A partir de 640px (tablet):** a barra mostra o nome e a data de cada etapa, e a ficha abre como uma janela.
- **A partir de 960px (computador):** os filtros aparecem dentro da página, logo abaixo da busca.
- **Cores e fontes:** azul `#0064FF`, títulos em Geist e textos em Inter.
