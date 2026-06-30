from jinja2 import Environment, FileSystemLoader
import urllib.parse
import hashlib
import os
import hmac
import re
import secrets
from datetime import datetime, timedelta
from http.cookies import SimpleCookie


class WebApp:
    """
    Aplicação Web baseada no padrão WSGI (Web Server Gateway Interface).
    """

    def __init__(self):
        """
        Inicializa a aplicação web configurando os bancos de dados na memória
        (usuários e sessões) e o ambiente de templates do Jinja2.
        """
        self.users_db = {}
        self.sessions_db = {}

        self.env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

    def __call__(self, environ, start_response):
        """
        Ponto de entrada da aplicação WSGI. Atua como o roteador (router) principal,
        direcionando a requisição para o método apropriado com base na URL e no método HTTP.
        """
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")

        if path == "/" and method == "GET":
            return self.render_home(environ, start_response)

        # Static
        elif path.startswith("/static") and method == "GET":
            return self.static_server(environ, start_response)

        # Favicon
        elif path == "/favicon.ico" and method == "GET":
            environ["PATH_INFO"] = "/static/img/biscoito.png"
            return self.static_server(environ, start_response)

        # Login
        elif path == "/login" and method == "GET":
            return self.render_login_get(environ, start_response)
        elif path == "/login" and method == "POST":
            return self.handle_login_post(environ, start_response)

        # Cadastro
        elif path == "/register" and method == "GET":
            return self.render_register_get(environ, start_response)
        elif path == "/register" and method == "POST":
            return self.handle_register_post(environ, start_response)

        # Dashboard
        elif path == "/dashboard" and method == "GET":
            return self.render_dashboard(environ, start_response)

        # Admin
        elif path == "/admin" and method == "GET":
            return self.render_admin(environ, start_response)

        elif path == "/logout" and method == "POST":
            return self.handle_logout_post(environ, start_response)

        else:
            return self.render_404(environ, start_response)

    def _open_file(self, path):
        try:
            with open(path, "rb") as file:
                return file.read()

        except Exception as error:
            print(f"Erro ao tentar abrir o arquivo {path}: {error}")
            return b""

    def static_server(self, environ, start_response):
        import mimetypes

        path = environ.get("PATH_INFO", "")
        relative_path = path.lstrip("/")

        base_dir = os.path.abspath("static")
        full_path = os.path.abspath(relative_path)

        if not full_path.startswith(base_dir) or not os.path.isfile(full_path):
            return self.render_404(environ, start_response)

        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        body_bytes = self._open_file(full_path)

        start_response(
            "200 OK",
            [("Content-Type", mime_type), ("Content-Length", str(len(body_bytes)))],
        )
        return [body_bytes]

    def _send_reply(self, start_response, text_html, status="200 OK"):
        """
        Método auxiliar para preparar e enviar uma resposta HTTP padrão com conteúdo HTML.
        """
        start_response(status, [("Content-Type", "text/html; charset=utf-8")])
        return [text_html.encode("utf-8")]

    def _redirect(self, start_response, location, extra_headers=None):
        """
        Método auxiliar para realizar um redirecionamento HTTP (Status 302 Found).
        Aceita cabeçalhos extras (ex.: Set-Cookie) que serão enviados junto.
        """
        headers = [("Location", location)]
        if extra_headers:
            headers.extend(extra_headers)
        start_response("302 Found", headers)
        return [b""]

    def _create_session(self, email):
        """
        Cria uma nova sessão em memória para o usuário e devolve o cabeçalho
        Set-Cookie pronto para ser enviado na resposta.
        """
        session_id = secrets.token_hex(32)
        self.sessions_db[session_id] = {
            "email": email,
            "createdAt": datetime.now(),
            "views": 0,
        }
        cookie = f"sessionId={session_id}; HttpOnly; Path=/; SameSite=Strict"
        return ("Set-Cookie", cookie)

    def _get_session(self, environ):
        """
        Recupera a sessão ativa a partir do cookie 'sessionId' da requisição.
        """
        cookie_header = environ.get("HTTP_COOKIE", "")
        cookies = SimpleCookie(cookie_header)
        if "sessionId" not in cookies:
            return None, None

        session_id = cookies["sessionId"].value
        session = self.sessions_db.get(session_id)
        if session is None:
            return None, None

        if (datetime.now() - session["createdAt"]) > timedelta(minutes=30):
            del self.sessions_db[session_id]
            return None, None

        return session_id, session

    def _render_template(
        self, start_response, template_name, context=None, status="200 OK"
    ):
        """
        Método auxiliar para renderizar um template Jinja2 e enviar a resposta.
        """
        if context is None:
            context = {}

        template = self.env.get_template(template_name)
        html_string = template.render(**context)
        return self._send_reply(start_response, html_string, status=status)

    def _parse_form(self, environ):
        """
        Método auxiliar para ler e decodificar dados de formulários POST.
        """
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
        except ValueError:
            content_length = 0

        request_body = environ["wsgi.input"].read(content_length).decode("utf-8")
        return urllib.parse.parse_qs(request_body)

    def render_home(self, environ, start_response):
        """
        Renderiza e retorna a página inicial do site.
        """
        _, session = self._get_session(environ)
        context = {}
        if session:
            context = {"email": session["email"]}

        return self._render_template(start_response, "index.html", context)

    def render_login_get(self, environ, start_response):
        """
        Exibe a página com o formulário de login.
        """
        return self._render_template(start_response, "login.html")

    def handle_login_post(self, environ, start_response):
        """
        Processa as credenciais de login enviadas pelo usuário via método POST.
        """
        form_data = self._parse_form(environ)
        email = form_data.get("email", [""])[0].strip()
        password = form_data.get("password", [""])[0]

        user = self.users_db.get(email)
        if user:
            computed_hash = hashlib.pbkdf2_hmac(
                "sha512", password.encode("utf-8"), user["salt"], 100000
            )
            # função segura que previne time attacks
            if hmac.compare_digest(computed_hash, user["hash"]):
                cookie_header = self._create_session(email)
                return self._redirect(
                    start_response, "/dashboard", extra_headers=[cookie_header]
                )

        context = {"error": "E-mail ou senha inválidos.", "email": email}
        return self._render_template(
            start_response, "login.html", context, status="401 Unauthorized"
        )

    def render_register_get(self, environ, start_response):
        """
        Exibe a página com o formulário de cadastro de usuário.
        """
        return self._render_template(start_response, "register.html")

    def handle_register_post(self, environ, start_response):
        """
        Processa os dados de criação de conta enviados pelo usuário via método POST.
        """
        form_data = self._parse_form(environ)

        email = form_data.get("email", [""])[0].strip()
        password = form_data.get("password", [""])[0]

        if email in self.users_db:
            context = {"error": "Este e-mail já está cadastrado.", "email": email}
            return self._render_template(
                start_response, "register.html", context, status="409 Conflict"
            )

        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha512", password.encode("utf-8"), salt, 100000
        )

        self.users_db[email] = {"salt": salt, "hash": password_hash}

        context = {"success": "Conta criada com sucesso! Você já pode fazer login."}
        return self._render_template(
            start_response, "login.html", context, status="201 Created"
        )

    def render_dashboard(self, environ, start_response):
        """
        Exibe a página restrita do painel de controle (dashboard).
        """
        _, session = self._get_session(environ)
        if session is None:
            return self._redirect(start_response, "/login")

        session["views"] += 1

        context = {
            "email": session["email"],
            "views": session["views"],
            "createdAt": session["createdAt"],
        }
        return self._render_template(start_response, "dashboard.html", context)

    def render_admin(self, environ, start_response):
        """
        Exibe a página do painel de administração.
        """
        _, session = self._get_session(environ)
        if session is None:
            return self._redirect(start_response, "/login")

        context = {"users": list(self.users_db.keys()), "sessions": self.sessions_db}
        return self._render_template(start_response, "admin.html", context)

    def handle_logout_post(self, environ, start_response):
        """
        Processa a requisição de saída (logout) do usuário, encerrando a sessão.
        """
        session_id, _ = self._get_session(environ)
        if session_id:
            del self.sessions_db[session_id]

        expired_cookie = (
            "Set-Cookie",
            "sessionId=; HttpOnly; Path=/; SameSite=Strict; Max-Age=0",
        )
        return self._redirect(start_response, "/", extra_headers=[expired_cookie])

    def render_404(self, environ, start_response):
        """
        Retorna a página de erro padrão para rotas não encontradas (Erro 404).
        """
        return self._send_reply(
            start_response, "<h1>Erro 404 - Não Encontrado</h1>", "404 Not Found"
        )
