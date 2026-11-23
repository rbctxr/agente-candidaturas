# agente de candidaturas — piloto supervisionado v0.3

três trilhas: `br_internship`, `global_entry`, `global_freelance`. o agente pesquisa e prepara; **não envia candidaturas automaticamente nesta versão**.

a meta é confirmar **10 candidaturas distintas** enviadas manualmente. depois disso, será necessária uma segunda autorização explícita antes de habilitar qualquer conector de envio. mesmo com autorização, a ausência de um adaptador de envio permitido impede o envio.

## arquitetura

`collectors/` (greenhouse, lever, remotive e manual) → normalização (`Opportunity`) → `policy.eligibility` → `matching` → ia (`ai.py`) → sqlite (`storage.py`) → streamlit (`app.py`) → `pilot.py` (auditoria, limites e autorização).

## instalação

```bash
python -m venv .venv
# linux/macos: source .venv/bin/activate
# windows: .venv\Scripts\activate
pip install -e '.[dev]'
cp .env.example .env  # windows: copy .env.example .env
cp profile.example.json data/profile.json
python run.py
pytest -q
```

## piloto e histórico

o painel existente prepara e aprova candidaturas. após realmente enviar manualmente uma candidatura aprovada, registre a confirmação:

```bash
python pilot_cli.py status
python pilot_cli.py confirm-manual --id ID_DA_VAGA
```

após 10 envios distintos confirmados, o modo automático ainda fica desativado até uma nova autorização:

```bash
python pilot_cli.py enable-auto --confirm 'EU AUTORIZO ENVIO AUTOMATICO'
python pilot_cli.py disable-auto
```

**importante:** `enable-auto` apenas altera uma configuração. não existe adaptador de submissão automática nesta versão.

`can_auto_submit` exige, além do piloto e da autorização explícita, permissão da plataforma, elegibilidade confirmada, aprovação prévia, conteúdo fiel, limites e adaptador implementado.

não contornar captcha, mfa ou bloqueios.

## conectores públicos

`jobagent.collectors.multi.greenhouse('slug-da-empresa')` e `lever('slug-da-empresa')` consultam anúncios públicos de empresas conhecidas.

o campo `remote=False` é proposital: os anúncios exigem verificação de modalidade e elegibilidade antes de serem promovidos a candidatos.

a integração não cobre automaticamente todas as empresas.

para eureca, 99jobs e companhia de estágios, utilizar importação manual ou assistida enquanto não houver permissão e interface técnica autorizadas.

não armazenar senhas nem cookies no git.

## limites e segurança

o piloto prevê 10 candidaturas únicas confirmadas manualmente.

após a liberação, os limites padrão são de 5 envios por dia e 20 envios a cada 7 dias, considerando os eventos registrados.

não enviar candidaturas duplicadas.

nunca enviar uma candidatura sem evidência de elegibilidade no brasil, autorização da plataforma, escopo de aprovação e revisão de conteúdo.

nenhum mecanismo de envio automático está incluído nesta versão. a contagem depende de registros verdadeiros do usuário.

o score da ia não deve ser utilizado como prova de elegibilidade.

## perfil e privacidade

`profile.example.json` contém fatos resumidos dos currículos e deve ser revisado antes do uso.

o agente não deve inventar experiências, qualificações ou certificações.

os arquivos `data/profile.json`, `.env` e o banco sqlite devem permanecer fora do repositório público.

as duas graduações devem permanecer no perfil, com foco profissional em dados e ia.

## limitações

as integrações greenhouse e lever ainda não foram testadas ao vivo. algumas empresas utilizam endpoints diferentes.

não há autenticação automática, submissão a plataformas, geração de pdf ou integração oficial com eureca, 99jobs e companhia de estágios.

os controles do piloto constituem uma base auditável local, mas não oferecem proteção contra alterações manuais no sqlite.

para uso em produção, será necessário implementar transações atômicas, armazenamento de evidências, autenticação e limites do lado do servidor.