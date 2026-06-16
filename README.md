# Webdev Cookie

Aplicação com autenticação baseada em sessão, renderização server-side e estilização com algum framework CSS.

## Requisitos

### Sessões


- A autenticação usa cookie `sessionId`.
- O cookie de login é enviado com `HttpOnly`, `Path=/` e `SameSite=Strict`.
- As sessões ficam apenas em memória.
- Cada sessão guarda pelo menos:
  - `email`
  - `createdAt`
  - `views` quantidade de acessos
- Sessões expiradas são removidas automaticamente após `30` minutos.

### Usuários

- Os usuários também ficam apenas em memória.
- Senhas não são armazenadas em texto puro.
- O cadastro usa:
  - `salt` aleatório
  - `pbkdf2` com `sha512`
- A validação de senha usa comparação segura com `timingSafeEqual`.

## Rotas

### Públicas

- `GET /`
  - exibe a página inicial
  - mostra links públicos quando não há sessão
  - mostra links privados quando há sessão

- `GET /register`
  - exibe o formulário de cadastro

- `POST /register`
  - cria um usuário
  - retorna página de sucesso quando o cadastro é concluído
  - retorna `409` quando o e-mail já está cadastrado

- `GET /login`
  - exibe o formulário de login

- `POST /login`
  - autentica o usuário
  - retorna `401` se as credenciais forem inválidas
  - retorna `302` redirecionando para `/dashboard` quando o login é válido

### Protegidas

- `GET /dashboard`
  - exige autenticação
  - mostra o e-mail do usuário autenticado

- `GET /admin`
  - exige autenticação
  - lista todos os usuários em memória
  - lista todas as sessões em memória

- `POST /logout`
  - exige autenticação
  - remove a sessão atual
  - envia um cookie expirado para limpar `sessionId`

### Fallback

- qualquer rota não mapeada retorna:
  - status `404`
  - template de mensagem amigável

## Observações

- O estado da aplicação não persiste reinícios do processo.
- A rota `/admin` expõe dados sensíveis de usuários e sessões e hoje serve apenas para estudo, depuração ou demonstração.
