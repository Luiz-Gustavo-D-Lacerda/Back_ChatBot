from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis do arquivo .env

app = Flask(__name__)
CORS(app)

# Instancia o cliente OpenAI com a chave da API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/perguntar', methods=['POST'])
def perguntar():
    data = request.get_json()
    pergunta = data.get('pergunta')

    if not pergunta:
        return jsonify({"resposta": "Desculpe, não consegui entender."})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente jurídico especializado em Direito do Consumidor. Responda apenas perguntas relacionadas a esse tema. Se a pergunta estiver fora desse escopo, oriente o usuário a perguntar algo relacionado ao Direito do Consumidor."
                },
                {
                    "role": "user",
                    "content": pergunta
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        return jsonify({"resposta": response.choices[0].message.content.strip()})

    except Exception as e:
        print("Erro real:", e)
        return jsonify({"resposta": "Erro ao processar a pergunta."})

if __name__ == '__main__':
    app.run(debug=True)
