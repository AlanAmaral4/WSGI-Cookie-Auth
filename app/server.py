from wsgiref.simple_server import make_server
from jinja2 import Environment, FileSystemLoader


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

    def _send_reply(self, start_response, text_html, status="200 OK"):
        """
        Método auxiliar para preparar e enviar uma resposta HTTP padrão com conteúdo HTML.
        """
        start_response(status, [("Content-Type", "text/html; charset=utf-8")])
        return [text_html.encode("utf-8")]

    def _redirect(self, start_response, location):
        """
        Método auxiliar para realizar um redirecionamento HTTP (Status 302 Found).
        """
        start_response("302 Found", [("Location", location)])
        return [b""]
    
    def _render_template(self, start_response, template_name, context=None):
        """
        Método auxiliar para renderizar um template Jinja2 e enviar a resposta.
        """
        if context is None:
            context = {}
        template = self.env.get_template(template_name)
        html_string = template.render(**context)
        return self._send_reply(start_response, html_string)

    def render_home(self, environ, start_response):
        """
        Renderiza e retorna a página inicial do site.
        """
        return self._render_template(start_response, "index.html")

    def render_login_get(self, environ, start_response):
        """
        Exibe a página com o formulário de login.
        """
        return self._send_reply(start_response, "<h1>Página de Login</h1>")

    def handle_login_post(self, environ, start_response):
        """
        Processa as credenciais de login enviadas pelo usuário via método POST.
        """
        pass

    def render_register_get(self, environ, start_response):
        """
        Exibe a página com o formulário de cadastro de usuário.
        """
        return self._send_reply(start_response, "<h1>Página de registro</h1>")

    def handle_register_post(self, environ, start_response):
        """
        Processa os dados de criação de conta enviados pelo usuário via método POST."""
        pass

    def render_dashboard(self, environ, start_response):
        """
        Exibe a página restrita do painel de controle (dashboard).
        """
        return self._send_reply(start_response, "<h1>Página do Dashboard</h1>")

    def render_admin(self, environ, start_response):
        """
        Exibe a página do painel de administração.
        """
        return self._send_reply(start_response, "<h1>Página de Admin</h1>")

    def handle_logout_post(self, environ, start_response):
        """
        Processa a requisição de saída (logout) do usuário, encerrando a sessão.
        """
        pass

    def render_404(self, environ, start_response):
        """
        Retorna a página de erro padrão para rotas não encontradas (Erro 404).
        """
        return self._send_reply(
            start_response, "<h1>Erro 404 - Não Encontrado</h1>", "404 Not Found"
        )

if __name__ == "__main__":
    app = WebApp()
    server = make_server("localhost", 8000, app)
    print("Servidor rodando em http://localhost:8000 ...")
    server.serve_forever()