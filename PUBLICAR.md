# Publicar em producaolegis.raonimendes.com.br

Passo a passo para fazer uma vez só. Depois disso, a página se atualiza sozinha às 06h e às 18h.

**Como funciona:** o GitHub guarda os arquivos e publica a página (GitHub Pages). O robô do GitHub (Actions) consulta o SAPL duas vezes por dia. A Cloudflare, onde está o DNS de raonimendes.com.br, aponta o subdomínio para o GitHub. Tudo isso é gratuito.

A pasta `painel-legislativo/` já está pronta como repositório Git, com o primeiro commit feito.

---

## 1. Criar a conta no GitHub (5 min)

1. Acesse https://github.com/signup.
2. Crie uma conta do gabinete, por exemplo `gabineteraoni`. Use um e-mail institucional, porque é para ele que vão os avisos de falha.
3. Ative a verificação em duas etapas: **Settings → Password and authentication**.

## 2. Criar o repositório (2 min)

1. Clique em **New repository**.
2. **Nome:** `producaolegis`.
3. Marque **Public**. O GitHub Pages gratuito exige repositório público, e os dados já são públicos no SAPL.
4. **Não** marque "Add a README", ".gitignore" nem "license". O repositório precisa nascer vazio.
5. Clique em **Create repository**.

## 3. Enviar os arquivos (5 min)

O jeito mais fácil é pelo **GitHub Desktop**:

1. Instale o GitHub Desktop (https://desktop.github.com) e entre com a conta do passo 1.
2. Abra **File → Add local repository** e escolha a pasta `raonimendes-site/painel-legislativo`.
3. Clique em **Publish repository**.
4. Desmarque **Keep this code private** e confirme o nome `producaolegis`.

> Pelo terminal, a alternativa é: `git remote add origin https://github.com/gabineteraoni/producaolegis.git` e depois `git push -u origin main`.

## 4. Dar permissão ao robô (1 min)

1. No repositório, abra **Settings → Actions → General**.
2. Em **Workflow permissions**, marque **Read and write permissions**.
3. Clique em **Save**.

Sem isso, o robô consegue consultar o SAPL, mas não consegue salvar os dados novos.

## 5. Ligar o GitHub Pages (2 min)

1. Abra **Settings → Pages**.
2. Em **Source**, escolha **Deploy from a branch**.
3. Em **Branch**, escolha `main` e a pasta `/ (root)`, e clique em **Save**.
4. Em **Custom domain**, confira se aparece `producaolegis.raonimendes.com.br`. Ele já vem do arquivo `CNAME`. Se estiver vazio, digite o endereço e salve.

## 6. Apontar o subdomínio na Cloudflare (3 min)

O DNS de raonimendes.com.br está na Cloudflare (servidores elisa e graham).

1. Entre em https://dash.cloudflare.com, abra **raonimendes.com.br** e vá em **DNS → Records → Add record**.
2. Preencha:

   | Campo | Valor |
   |---|---|
   | Type | `CNAME` |
   | Name | `producaolegis` |
   | Target | `gabineteraoni.github.io` (troque pelo nome da conta do passo 1) |
   | Proxy status | **DNS only** (nuvem cinza) |
   | TTL | Auto |

3. Clique em **Save**.

> Deixe a nuvem **cinza**. Com a nuvem laranja, o GitHub não consegue emitir o certificado de segurança (HTTPS).

## 7. Ativar o HTTPS (10 a 30 min de espera)

1. Volte em **Settings → Pages** no GitHub.
2. Espere aparecer "DNS check successful".
3. Marque **Enforce HTTPS**. A opção pode demorar alguns minutos para liberar, enquanto o certificado é emitido.

## 8. Rodar a primeira atualização (15 min)

1. Abra **Actions → Atualizar painel → Run workflow → Run workflow**.
2. Espere o círculo ficar **verde**.
3. Abra https://producaolegis.raonimendes.com.br e confira o "Atualizado em …" no topo.

## 9. Testar antes de divulgar

- [ ] Abrir no celular: busca, Filtrar, abrir uma matéria e trocar as abas.
- [ ] Abrir no computador.
- [ ] Copiar o link de uma matéria (botão na ficha) e abrir em outra aba.
- [ ] Enviar o link no WhatsApp e ver se aparece a prévia com o logo.
- [ ] Conferir 3 matérias recentes contra o SAPL.

## 10. Divulgar

Coloque o link **Produção Legislativa → https://producaolegis.raonimendes.com.br** no menu e no rodapé de raonimendes.com.br, e na bio das redes.

---

## No dia a dia: nada

A atualização roda sozinha às **06h e 18h**. Se uma execução falhar, por exemplo porque o SAPL ficou fora do ar, o GitHub manda um e-mail para a conta. A execução seguinte tenta de novo.

**Uma vez por semana (1 minuto, opcional):** abra **Actions** e veja se as últimas execuções estão verdes.

**Atenção:**

- **Recesso parlamentar.** O GitHub pausa robôs agendados quando o repositório fica 60 dias sem nenhuma mudança. Isso só acontece se o SAPL passar dois meses sem movimentar nada do vereador. O GitHub avisa por e-mail antes. Para reativar, abra **Actions → Atualizar painel → Enable workflow**.
- **Se o SAPL bloquear o GitHub.** Se as execuções falharem por vários dias seguidos com erro 503, a atualização pode rodar a partir de um computador do gabinete ou do servidor do site. Me chame para configurar.
- **Ajustes de tema e situação.** As regras ficam em `coleta/processar.py`. Depois de editar, publique a mudança (no GitHub Desktop: **Commit → Push**). O robô usa as regras novas na execução seguinte.
