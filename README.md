# Chatbot Jurídico - Backend

Este é o backend do projeto **Chatbot Jurídico voltado ao Direito do Consumidor**, responsável por receber perguntas do frontend e retornar respostas geradas com a API da OpenAI (GPT-4).

---

## 🛠 Tecnologias Utilizadas

- **Python 3**
- **Flask**
- **Flask-CORS**
- **OpenAI API**
- **dotenv** (para gerenciar a chave de API com segurança)

---

## 🚀 Como Executar o Backend Localmente

### 1. Clonar o Repositório

```bash
git clone https://github.com/SeuUsuario/Back_ChatBot.git
cd Back_ChatBot
2. Criar Ambiente Virtual (opcional, mas recomendado)
bash
Copiar código
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
3. Instalar Dependências
bash
Copiar código
pip install -r requirements.txt
Se você ainda não tem o requirements.txt, crie um com o seguinte conteúdo:

nginx
Copiar código
flask
flask-cors
openai
python-dotenv
4. Criar Arquivo .env
Crie um arquivo .env na raiz do projeto com sua chave da OpenAI:

ini
Copiar código
OPENAI_API_KEY=sua-chave-aqui
5. Rodar o Servidor
bash
Copiar código
python app.py
A API estará disponível em http://localhost:5000.

