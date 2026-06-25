# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Aplicação web Python pura (sem framework), implementando o padrão **WSGI** diretamente com `wsgiref.simple_server`. Renderização server-side com Jinja2 e estilização via Pico CSS + CSS customizado. O objetivo do projeto é implementar autenticação baseada em sessão usando cookies (`sessionId`), conforme descrito no `README.md`.

Não há sistema de build, bundler ou dependências de frontend — tudo é HTML servido por templates Jinja2.

## Comandos

- Rodar o servidor: `python app/server.py` (sobe em `http://localhost:8000`)
- Ambiente virtual já existe em `env/` (`env/bin/activate`); ative-o antes de instalar/rodar caso novas dependências sejam necessárias.
- Não há testes, lint ou scripts de build configurados no projeto.

## Arquitetura

- `app/server.py` — contém toda a aplicação: a classe `WebApp` é o app WSGI (`__call__` faz o roteamento manual por `PATH_INFO` + método HTTP). Não há framework de rotas; cada rota é um `elif` explícito dentro de `__call__`.
- `templates/` — templates Jinja2 (`index.html`, `login.html`, `register.html`, `dashboard.html`, `admin.html`), renderizados via `self.env` (`Environment(loader=FileSystemLoader("templates"), autoescape=True)`).
- `static/` — assets estáticos (CSS), servidos pela própria `WebApp.static_server` (sem servidor estático dedicado); a rota faz checagem de path traversal comparando `os.path.abspath`.
- `main.py` e `app/__init__.py` estão vazios — o ponto de entrada real é `app/server.py` (bloco `if __name__ == "__main__":`).

### Estado em memória

- `self.users_db` e `self.sessions_db` são dicionários em memória dentro da instância de `WebApp` — não há banco de dados, e o estado é perdido a cada reinício do processo.
- Senhas: hash com `hashlib.pbkdf2_hmac("sha512", ...)` + `salt` aleatório (`os.urandom(16)`), comparação com `hmac.compare_digest` (resistente a timing attack). Nunca armazenar senha em texto puro.

### Requisitos funcionais (ver `README.md` para o contrato completo)

O `README.md` é a especificação de comportamento esperado das rotas — consulte-o antes de alterar qualquer rota, pois define códigos de status HTTP esperados (`401`, `409`, `302`, `404`) e regras de cookie (`HttpOnly`, `Path=/`, `SameSite=Strict`, expiração de sessão em 30 minutos).

Estado atual da implementação em `app/server.py` (ainda incompleto em relação ao README):
- O cookie de sessão (`sessionId`) ainda não é criado/lido em nenhuma rota — login bem-sucedido apenas redireciona para `/dashboard` sem estabelecer sessão.
- `/dashboard` e `/admin` ainda não verificam autenticação nem usam `self.sessions_db`.
- `handle_logout_post` é um stub (`pass`) — ainda não invalida sessão nem expira o cookie.
- Ao implementar essas partes, siga o padrão já usado nos outros handlers (helpers `_send_reply`, `_redirect`, `_render_template`, `_parse_form`).
