# Autenticação e Segurança

## O que é essa área?

A área de autenticação é responsável por controlar o acesso ao sistema.

Ela garante que cada usuário veja apenas suas próprias informações financeiras.

---

## Pra que serve?

Essa funcionalidade serve para:

* Proteger os dados do usuário
* Garantir privacidade
* Controlar quem pode acessar o sistema
* Manter cada conta separada

---

## Como usar?

### Criar uma conta

1. Acesse a página de cadastro
2. Preencha:

   * Nome
   * Sobrenome
   * Telefone
   * E-mail
   * Senha
3. Clique em **Cadastrar**

---

### Fazer login

1. Acesse a página de login
2. Informe:

   * E-mail
   * Senha
3. Clique em **Entrar**

---

### Logout

* Clique na opção de sair
* O sistema encerra sua sessão com segurança

---

## Como funciona a segurança?

### Senhas protegidas

As senhas não são armazenadas diretamente.

O sistema utiliza um processo chamado **hash**, que transforma a senha em um formato seguro.

Isso significa que:

* ninguém consegue ver sua senha original
* mesmo com acesso ao banco, os dados continuam protegidos

---

### Sessão do usuário

Após o login, o sistema cria uma sessão.

Essa sessão guarda informações como:

* ID do usuário
* Nome

Com isso, o sistema sabe quem está utilizando a plataforma.

---

### Proteção de rotas

Algumas páginas só podem ser acessadas por usuários logados.

Se alguém tentar acessar sem login:

* será redirecionado para a tela de login

---

## Como funciona por trás?

O sistema:

1. Verifica se o e-mail existe
2. Compara a senha com o hash armazenado
3. Cria uma sessão se estiver correto
4. Bloqueia acesso caso não esteja autenticado

---

## Boas práticas implementadas

* Uso de hash de senha
* Controle de sessão
* Rotas protegidas
* Separação de dados por usuário

---

## Possíveis melhorias futuras

Essa área pode evoluir com:

* Login com Google / Facebook / Apple
* Verificação por código (e-mail ou SMS)
* “Lembrar de mim”
* Autenticação em duas etapas (2FA)

---

## Por que isso é importante?

Sem autenticação:

* qualquer pessoa poderia acessar os dados
* não haveria privacidade
* o sistema não seria confiável

Essa área garante que o sistema seja seguro e utilizável no mundo real.