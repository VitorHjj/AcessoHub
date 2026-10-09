# AcessoHub

[Português (Brasil)](README.md) · [English](README.en.md)

Aplicação web para gerenciar usuários, planos de assinatura e permissões de acesso. Desenvolvida como projeto de estudo e portfólio com Python, Flask e SQLite.

O administrador pode cadastrar usuários, selecionar um plano, renovar a validade e consultar o histórico de acessos e contratações em uma interface web com menu lateral.

## Funcionalidades

- Configuração do primeiro administrador, login e logout.
- Dashboard com totais de usuários, situação dos cadastros e valores registrados.
- Cadastro, edição, exclusão e busca por nome, CPF ou ID.
- Validação de CPF, telefone e data de nascimento, com verificação básica de e-mail.
- Filtros por usuários ativos, vencidos e suspensos.
- Planos mensal, trimestral, semestral e anual no cadastro e na renovação.
- Renovação que preserva a validade ainda disponível.
- Suspensão e reativação de usuários.
- Verificação de acesso e registro de data, horário e resultado.
- Histórico de contratações e relatórios mensais.
- Interface adaptável para diferentes tamanhos de tela.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python e Flask |
| Banco de dados | SQLite |
| Interface | HTML, CSS e JavaScript |
| Templates | Jinja2 |
| Senhas | Hash com Werkzeug |

## Executar localmente

Requisito: Python 3.10 ou superior, com pip. Abra o terminal dentro da pasta do projeto.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Os comandos usam o Python do ambiente virtual diretamente, sem precisar alterar a política de execução do PowerShell.

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000). No primeiro acesso, escolha um usuário com pelo menos três caracteres e uma senha com pelo menos dez caracteres. A criação do administrador inicia a sessão e abre o dashboard.

O arquivo `acesso.db` e a chave local `.session_key` são criados automaticamente. Eles são ignorados pelo Git. Para encerrar o servidor, pressione `Ctrl + C` no terminal.

## Fluxo de demonstração

1. Crie o administrador.
2. Cadastre um usuário com dados fictícios e CPF válido, selecionando um plano.
3. Localize o cadastro pela busca e confira a validade.
4. Renove com outro plano e consulte o histórico em Mensalidades.
5. Suspenda o usuário e use a ação de verificar acesso para registrar o bloqueio.
6. Reative o cadastro e confira o histórico de acessos e os relatórios.

Use apenas dados fictícios nas demonstrações e nas capturas de tela.

## Planos de demonstração

| Plano | Duração | Preço fictício |
|---|---|---:|
| Mensal | 1 mês | R$ 100,00 |
| Trimestral | 3 meses | R$ 270,00 |
| Semestral | 6 meses | R$ 510,00 |
| Anual | 12 meses | R$ 960,00 |

Os pacotes ficam no dicionário `PLANOS`, em `app.py`. O backend determina o preço a partir do plano selecionado. Cadastro e renovação registram a contratação; não há integração com cartão, Pix ou outro serviço de pagamento. Os indicadores representam valores registrados, não confirmação bancária de recebimento.

A validade usa meses de calendário. Quando o dia não existe no mês de destino, é usado o último dia desse mês. Por exemplo, 31/01/2026 + 1 mês resulta em 28/02/2026. Se a assinatura estiver ativa, a renovação começa na validade atual; se estiver vencida, começa na data de hoje. O acesso é permitido até a data de vencimento, inclusive, desde que o cadastro não esteja suspenso.

## Organização do código

| Arquivo / pasta | Responsabilidade |
|---|---|
| `app.py` | Rotas, autenticação, validação, planos e regras de acesso |
| `database.py` | Conexão SQLite, criação e atualização das tabelas |
| `templates/` | Páginas HTML renderizadas com Jinja2 |
| `static/style.css` | Estilos da interface |
| `static/app.js` | Interação do formulário de renovação |
| `requirements.txt` | Dependências Python |
| `.gitignore` | Exclusão de dados, segredos e arquivos locais |
| `GITHUB.md` | Passo a passo para publicar o repositório |

## Banco existente

Antes de atualizar uma instalação, pare o servidor e faça uma cópia de segurança do `acesso.db`. Preserve também `.session_key` para manter a chave local. As tabelas e colunas necessárias são criadas na inicialização.

Cadastros anteriores sem plano aparecem como “Cadastro antigo” até uma renovação. Históricos anteriores são preservados. Se o banco antigo tiver CPFs duplicados, a migração mantém os registros e não cria o índice único até que as duplicatas sejam corrigidas.

Excluir um usuário também exclui seus históricos de contratações e acessos.

## Validação realizada

Foram verificados com o cliente de testes do Flask: criação do administrador e redirecionamento ao dashboard, renderização das páginas principais, cadastro com plano, preço definido pelo servidor, renovação sem perder validade, rejeição de plano inválido, cálculo de meses e migração de banco antigo.

Essas verificações não substituem testes de interação no navegador. Os scripts de verificação usados durante o desenvolvimento não fazem parte deste pacote.

## Escopo e limitações

Esta versão é uma demonstração local. Usa hash de senha, proteção CSRF em formulários, consultas SQL parametrizadas e cookies de sessão HTTP-only. Ainda não possui controle de tentativas de login, recuperação de senha, múltiplos perfis administrativos ou processamento de pagamentos.

Para uso público, é necessário revisar a segurança e o tratamento de dados pessoais, configurar HTTPS, servidor WSGI, backups e uma `SECRET_KEY` adequada no ambiente. Os valores monetários são armazenados em `REAL` para simplificar o projeto; uma aplicação financeira deve usar centavos inteiros ou outra representação exata.

## Publicação no GitHub

Veja [GITHUB.md](GITHUB.md). O pacote não inclui banco de dados, credenciais, ambiente virtual ou chave de sessão.
