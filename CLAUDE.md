# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Aplicação web Python pura (sem framework), implementando o padrão **WSGI** diretamente com `wsgiref.simple_server`. Renderização server-side com Jinja2 e estilização via Pico CSS + CSS customizado. O objetivo do projeto é implementar autenticação baseada em sessão usando cookies (`sessionId`), conforme descrito no `README.md`.

Não há sistema de build, bundler ou dependências de frontend — tudo é HTML servido por templates Jinja2.

## Comandos

- Rodar o servidor: `python main.py` a partir da raiz do projeto (sobe em `http://localhost:8000`). Não rode de dentro de `app/`, senão o import `from app.server import WebApp` quebra.
- Ambiente virtual já existe em `env/` (`env/bin/activate`); ative-o antes de instalar/rodar caso novas dependências sejam necessárias.
- Não há testes, lint ou scripts de build configurados no projeto.

## Arquitetura

- `app/server.py` — define a aplicação: a classe `WebApp` é o app WSGI (`__call__` faz o roteamento manual por `PATH_INFO` + método HTTP). Não há framework de rotas; cada rota é um `elif` explícito dentro de `__call__`.
- `templates/` — templates Jinja2 (`index.html`, `login.html`, `register.html`, `dashboard.html`, `admin.html`), renderizados via `self.env` (`Environment(loader=FileSystemLoader("templates"), autoescape=True)`).
- `static/` — assets estáticos (CSS), servidos pela própria `WebApp.static_server` (sem servidor estático dedicado); a rota faz checagem de path traversal comparando `os.path.abspath`.
- `main.py` é o ponto de entrada: importa `WebApp` de `app/server.py` e sobe o servidor com `make_server` (bloco `if __name__ == "__main__":`). `app/__init__.py` está vazio, mas é necessário para marcar `app/` como pacote Python (permite o `from app.server import WebApp`).

### Estado em memória

- `self.users_db` e `self.sessions_db` são dicionários em memória dentro da instância de `WebApp` — não há banco de dados, e o estado é perdido a cada reinício do processo.
- Senhas: hash com `hashlib.pbkdf2_hmac("sha512", ...)` + `salt` aleatório (`os.urandom(16)`), comparação com `hmac.compare_digest` (resistente a timing attack). Nunca armazenar senha em texto puro.

### Requisitos funcionais (ver `README.md` para o contrato completo)

O `README.md` é a especificação de comportamento esperado das rotas — consulte-o antes de alterar qualquer rota, pois define códigos de status HTTP esperados (`401`, `409`, `302`, `404`) e regras de cookie (`HttpOnly`, `Path=/`, `SameSite=Strict`, expiração de sessão em 30 minutos).

Estado atual da implementação em `app/server.py` (ainda incompleto em relação ao README):
- Login bem-sucedido **cria** a sessão (`_create_session`: gera `sessionId` com `secrets.token_hex`, registra `email`/`createdAt`/`views` em `self.sessions_db`) e emite o cookie `sessionId` (`HttpOnly`, `Path=/`, `SameSite=Strict`) no redirect `302` para `/dashboard`.
- O cookie de sessão ainda **não é lido** em nenhuma rota — nada consome `HTTP_COOKIE` para recuperar a sessão atual.
- `/dashboard` e `/admin` renderizam seus templates, mas ainda **não verificam autenticação** nem usam `self.sessions_db` (qualquer um acessa, sem checar o cookie).
- Ainda não há verificação de expiração de sessão (30 minutos).
- `handle_logout_post` é um stub (`pass`) — ainda não invalida sessão nem expira o cookie.
- Ao implementar essas partes, siga o padrão já usado nos outros handlers (helpers `_send_reply`, `_redirect` (aceita `extra_headers`), `_render_template`, `_parse_form`, `_create_session`).
