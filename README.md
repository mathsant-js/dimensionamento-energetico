# Dimensionamento Energético

![GitHub](https://img.shields.io/github/license/mathsant-js/dimensionamento-energetico)
![GitHub top language](https://img.shields.io/github/languages/top/mathsant-js/dimensionamento-energetico)
![GitHub repo size](https://img.shields.io/github/repo-size/mathsant-js/dimensionamento-energetico)
![GitHub last commit](https://img.shields.io/github/last-commit/mathsant-js/dimensionamento-energetico)

## Índice

- [Dimensionamento Energético](#dimensionamento-energético)
  - [Índice](#índice)
  - [Título](#título)
  - [Descrição do Projeto](#descrição-do-projeto)
  - [Status do Projeto](#status-do-projeto)
  - [Funcionalidades e Demonstração da Aplicação](#funcionalidades-e-demonstração-da-aplicação)
    - [Funcionalidades do Usuário](#funcionalidades-do-usuário)
    - [Funcionalidades do Sistema](#funcionalidades-do-sistema)
    - [Funcionalidades Avançadas de Dimensionamento Fotovoltaico (Futuras)](#funcionalidades-avançadas-de-dimensionamento-fotovoltaico-futuras)
  - [Acesso ao Projeto](#acesso-ao-projeto)
  - [Como rodar o projeto](#como-rodar-o-projeto)
    - [Pré-requisitos](#pré-requisitos)
    - [Passo a passo para execução local](#passo-a-passo-para-execução-local)
    - [Credenciais de acesso padrão](#credenciais-de-acesso-padrão)
  - [Tecnologias utilizadas](#tecnologias-utilizadas)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Ferramentas de Desenvolvimento](#ferramentas-de-desenvolvimento)
  - [Pessoas Contribuidoras](#pessoas-contribuidoras)
  - [Pessoas Desenvolvedoras do Projeto](#pessoas-desenvolvedoras-do-projeto)
  - [Licença](#licença)

## Título

Dimensionamento Energético - Sistema de Estimativa de Consumo Residencial e Dimensionamento de Sistemas Fotovoltaicos

## Descrição do Projeto

O **Dimensionamento Energético** é um sistema completo para estimativa de consumo energético residencial e dimensionamento de sistemas fotovoltaicos. O projeto permite que usuários cadastrem suas propriedades, informem os eletrodomésticos presentes, definam padrões de utilização e obtenham estimativas detalhadas de consumo mensal. Além disso, o sistema inclui funcionalidades para dimensionamento automático de sistemas solares fotovoltaicos, incluindo cálculo de painéis necessários, seleção de inversores, opcional inclusão de sistemas de armazenamento em baterias e geração de proposta financeira preliminar.

Este sistema foi desenvolvido como parte de um projeto acadêmico da FIAP, atendendo às necessidades de profissionais de energia solar, consumidores residenciais interessados em energia renovável e estudantes da área de engenharia e sustentabilidade.

## Status do Projeto

**Em andamento** - Projeto em desenvolvimento

## Funcionalidades e Demonstração da Aplicação

### Funcionalidades do Usuário

- ✅ Cadastro de usuário com autenticação segura
- ✅ Login com JWT tokens
- ✅ Cadastro de propriedades residenciais com identificação, tipo e localização
- ✅ Visualização de catálogo de equipamentos elétricos com potência (W)
- ✅ Associação de eletrodomésticos a propriedades específicas
- ✅ Definição de tempo médio diário de utilização para cada equipamento (0-24h)
- ✅ Cálculo individual de consumo mensal de cada equipamento
- ✅ Agregação do consumo total mensal do imóvel
- ✅ Edição de dados de propriedades cadastradas
- ✅ Exclusão de propriedades com confirmação modal
- ✅ Visualização de todas as propriedades cadastradas pelo usuário

### Funcionalidades do Sistema

- ✅ Base de dados predefinida com nome, categoria e potência de equipamentos elétricos
- ✅ Cálculo automático do consumo mensal de cada equipamento: `(Potência × Quantidade × Horas/dia × 30) / 1000`
- ✅ Cálculo do consumo total mensal do imóvel
- ✅ Validação de dados de entrada (campos obrigatórios, faixas de valores)
- ✅ Isolamento de dados por usuário (cada usuário vê apenas suas propriedades)
- ✅ Persistência de dados em banco de dados SQLite
- ✅ API RESTful com documentação automática Swagger
- ✅ Interface web responsiva construída com React e TypeScript

### Funcionalidades Avançadas de Dimensionamento Fotovoltaico (Futuras)

- ✅ Cálculo automático da geração necessária com base no consumo e taxa de compensação desejada
- ✅ Dimensionamento da potência necessária do sistema PV considerando HSP local
- ✅ Seleção automática de módulos fotovoltaicos compatíveis
- ✅ Seleção de inversores com validação técnica (tensão, corrente, potência máxima)
- ✅ Cálculo opcional de sistema de armazenamento em baterias (BESS)
- ✅ Geração de proposta financeira com custos estimados

## Acesso ao Projeto

O projeto está disponível em: https://github.com/mathsant/dimensionamento-energetico

Para acessar diretamente:
- **Frontend**: http://localhost:3000 (quando em execução local)
- **Backend API**: http://localhost:8000 (quando em execução local)
- **Documentação da API**: http://localhost:8000/docs (interface Swagger)

## Como rodar o projeto

### Pré-requisitos

- Node.js (versão 16 ou superior)
- Python (versão 3.10 ou superior)
- npm ou yarn
- Git

### Passo a passo para execução local

1. **Clone o repositório**
   ```bash
   git clone https://github.com/mathsant/dimensionamento-energetico.git
   cd dimensionamento-energetico
   ```

2. **Configure e execute o backend**
   ```bash
   cd backend
   
   # Instale as dependências
   pip install -r requirements.txt
   
   # Execute o servidor API
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   O backend estará disponível em http://localhost:8000
   A documentação automática da API em http://localhost:8000/docs

3. **Configure e execute o frontend**
   ```bash
   # Em outro terminal, na raiz do projeto:
   cd frontend
   
   # Instale as dependências
   npm install
   
   # Execute o aplicativo
   npm start
   ```
   
   O frontend estará disponível em http://localhost:3000

### Credenciais de acesso padrão

Para testes iniciais, use:
- **Email**: test@example.com
- **Senha**: testpassword123

Estas credenciais criam automaticamente um usuário de teste com uma propriedade de exemplo cadastrada.

## Tecnologias utilizadas

### Backend
- **Python 3.10+** - Linguagem de programação principal
- **FastAPI** - Framework web moderno e rápido para construção de APIs
- **SQLAlchemy** - ORM para interação com banco de dados
- **Pydantic** - Validação de dados e configurações
- **JWT (PyJWT)** - Autenticação baseada em tokens
- **Passlib** - Hash seguro de senhas
- **Uvicorn** - Servidor ASGI para produção
- **SQLite** - Banco de dados embutido para desenvolvimento

### Frontend
- **React 18** - Biblioteca JavaScript para construção de interfaces
- **TypeScript** - Superset tipado do JavaScript
- **Axios** - Cliente HTTP para comunicação com a API
- **React-scripts** - Ferramentas de build e desenvolvimento do Create React App

### Ferramentas de Desenvolvimento
- **Git** - Controle de versão
- **GitHub** - Hospedagem do código-fonte
- **VS Code** - Editor de código recomendado

## Pessoas Contribuidoras

- [mathsant-js](https://github.com/mathsant-js) - Scrum Master e Desenvolvedor

## Pessoas Desenvolvedoras do Projeto

- **mathsant-js** - Concepção, desenvolvimento backend e frontend, testes e documentação

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
