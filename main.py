from wsgiref.simple_server import make_server
from app.server import WebApp

if __name__ == "__main__":
    app = WebApp()
    server = make_server("localhost", 8000, app)
    print("Servidor rodando em http://localhost:8000 ...")
    server.serve_forever()
    