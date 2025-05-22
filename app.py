from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__)

# Configura CORS para aceitar requisições apenas do seu frontend
CORS(app, resources={r"/perguntar": {"origins": "https://luiz-gustavo-d-lacerda.github.io"}})

# Instancia o cliente OpenAI com a nova API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def home():
    return '''
    <html>
      <head><title>Chatbot API</title></head>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>Chatbot API está rodando!</h1>
        <p>Para usar o frontend, acesse:</p>
        <a href="https://luiz-gustavo-d-lacerda.github.io/Front_chatbot/" target="_blank">
          https://luiz-gustavo-d-lacerda.github.io/Front_chatbot/
        </a>
      </body>
    </html>
    '''

@app.route('/perguntar', methods=['POST'])
def perguntar():
    data = request.get_json()
    pergunta = data.get('pergunta')
    historico = data.get('historico', [])

    if not pergunta:
        return jsonify({"resposta": "Desculpe, não consegui entender.", "sugestoes": []})

    try:
        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente jurídico especializado exclusivamente em Direito do Consumidor, com base na legislação brasileira.\n\n"
                    "Seu papel é responder perguntas com linguagem técnico-jurídica clara, objetiva e acessível, mantendo um tom sério, respeitoso e com estilo acadêmico.\n\n"
                    "Sempre que possível:\n"
                    "- Cite a norma legal relevante (com nome, número e artigo).\n"
                    "- Indique se a resposta depende de análise do caso concreto.\n"
                    "- Finalize com uma orientação prática, como: 'Recomenda-se buscar orientação jurídica especializada.'\n\n"
                    "Se a pergunta estiver fora do escopo do Direito do Consumidor, responda de forma educada: \n"
                    "'Desculpe, só posso responder perguntas relacionadas ao Direito do Consumidor.'\n\n"
                    "Nunca responda perguntas fora desse tema."
                )
            }
        ]

        for m in historico:
            mensagens.append({
                "role": "user" if m["autor"] == "user" else "assistant",
                "content": m["mensagem"]
            })

        mensagens.append({"role": "user", "content": pergunta})

        resposta = client.chat.completions.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()

        sugestao_prompt = mensagens + [
            {"role": "user", "content": "Sugira 3 possíveis próximas mensagens que o usuário possa mandar sobre esse assunto."}
        ]

        sugestao_resposta = client.chat.completions.create(
            model="gpt-4",
            messages=sugestao_prompt,
            temperature=0.7,
            max_tokens=150
        ).choices[0].message.content.strip()

        sugestoes = [s.strip("-• \n") for s in sugestao_resposta.split("\n") if s.strip()]
        sugestoes = sugestoes[:3]

        return jsonify({
            "resposta": resposta,
            "sugestoes": sugestoes
        })

    except Exception as e:
        print("Erro real:", e)
        return jsonify({
            "resposta": "Erro ao processar a pergunta.",
            "sugestoes": []
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
