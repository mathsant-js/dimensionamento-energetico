# Dimensionamento Energético

![GitHub](https://img.shields.io/github/license/mathsant-js/dimensionamento-energetico)
![GitHub top language](https://img.shields.io/github/languages/top/mathsant-js/dimensionamento-energetico)
![GitHub repo size](https://img.shields.io/github/repo-size/mathsant-js/dimensionamento-energetico)
![GitHub last commit](https://img.shields.io/github/last-commit/mathsant-js/dimensionamento-energetico)

Sistema web para estimar o consumo mensal de energia de residências. O usuário cadastra seus imóveis, vincula equipamentos de um catálogo predefinido e acompanha o consumo total, a participação de cada equipamento e o maior consumidor estimado.

Desenvolvido como projeto acadêmico da FIAP.

## Sumário

- [Funcionalidades implementadas](#funcionalidades-implementadas)
- [Escopo futuro](#escopo-futuro)
- [Arquitetura](#arquitetura)
- [Execução local](#execução-local)
- [Pré-requisitos](#pré-requisitos)
- [Backend](#backend)
- [Frontend](#frontend)
- [Configuração opcional](#configuração-opcional)
- [Primeiro acesso](#primeiro-acesso)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Validação](#validação)
- [Licença](#licença)

## Funcionalidades implementadas

- Cadastro e autenticação de usuários com JWT.
- Cadastro, edição, listagem e exclusão de residências.
- Catálogo predefinido de 20 equipamentos com potência nominal em watts.
- Vínculo de equipamentos a uma residência com quantidade e horas de uso diário.
- Validações para campos obrigatórios, quantidade maior que zero e uso entre 0 e 24 horas.
- Cálculo do consumo mensal por equipamento: `(potencia_watts x quantidade x horas_dia x 30) / 1000`.
- Total mensal calculado pelo backend.
- Relatório com tabela detalhada, maior consumidor, percentuais e gráficos de pizza e barras.
- Isolamento dos dados por usuário autenticado.
- Persistência em SQLite via SQLAlchemy.

## Escopo futuro

O projeto também possui especificações para evolução de dimensionamento fotovoltaico, incluindo seleção de módulos e inversores, armazenamento em baterias e orçamento. Esses recursos ainda não estão implementados no aplicativo atual. Consulte `AGENTS.md` e `SPEC.md` para o escopo planejado.

## Arquitetura

- **Frontend:** React 19, TypeScript, Axios, Recharts e Create React App.
- **Backend:** Python 3.10+, FastAPI, Pydantic, SQLAlchemy, python-jose e Passlib.
- **Banco de dados:** SQLite por padrão.
- **API:** REST com documentação Swagger em `/docs`.

## Execução local

### Pré-requisitos

- Node.js 18 ou superior.
- Python 3.10 ou superior.
- npm.

### Backend

Em um terminal, a partir da raiz do repositório:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O backend inicia em `http://localhost:8000`, e a documentação interativa fica em `http://localhost:8000/docs`.

### Frontend

Em outro terminal, a partir da raiz do repositório:

```bash
cd frontend
npm install
npm start
```

O aplicativo inicia em `http://localhost:3000`. O frontend utiliza o proxy configurado para encaminhar requisições ao backend em `http://localhost:8000`.

### Configuração opcional

Por padrão, o backend usa o banco `backend/sqlite.db`, token JWT válido por 30 minutos e uma chave de desenvolvimento. Para personalizar a autenticação, crie `backend/.env`:

```dotenv
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Para usar outro banco, defina `DATABASE_URL` no ambiente antes de iniciar o backend:

```bash
export DATABASE_URL='sqlite:///./sqlite.db'
```

## Primeiro acesso

Ao iniciar o backend, o catálogo de equipamentos é preenchido automaticamente caso esteja vazio. Não há credenciais padrão: crie uma conta na tela de cadastro e, em seguida, cadastre uma residência para iniciar a estimativa de consumo.

## Estrutura do projeto

```text
backend/
  app/                 API FastAPI, modelos, schemas e regras de negócio
  requirements.txt     Dependências Python
frontend/
  src/                 Aplicação React e TypeScript
  package.json         Dependências e scripts npm
docs/                  Documentação complementar
```

## Validação

Para gerar o build de produção do frontend:

```bash
cd frontend
npm run build
```

O projeto também inclui scripts de verificação manual no diretório `backend`, incluindo o teste de isolamento de dados entre usuários.

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte [LICENSE](LICENSE).
