from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Instancia o cliente OpenAI com a nova API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/perguntar', methods=['POST'])
def perguntar():
    data = request.get_json()
    pergunta = data.get('pergunta')
    historico = data.get('historico', [])  # histórico opcional

    if not pergunta:
        return jsonify({"resposta": "Desculpe, não consegui entender.", "sugestoes": []})

    try:
        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente jurídico especializado em Direito do Consumidor. "
                    "Responda apenas perguntas relacionadas a esse tema, inclua na sua resposta a lei que se encaixa no caso, se houver. "
                    "Se a pergunta estiver fora desse escopo, oriente o usuário a perguntar algo relacionado ao Direito do Consumidor."
                )
            }
        ]

        # Adiciona o histórico anterior à conversa
        for m in historico:
            mensagens.append({
                "role": "user" if m["autor"] == "user" else "assistant",
                "content": m["mensagem"]
            })

        mensagens.append({"role": "user", "content": pergunta})

        # Gera a resposta principal
        resposta = client.chat.completions.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.7,
            max_tokens=500
        ).choices[0].message.content.strip()

        # Gera sugestões com base na conversa
        sugestao_prompt = mensagens + [
            {"role": "user", "content": "Sugira 3 possíveis próximas mensagens que o usuario possa mandar sobre esse assunto."}
        ]

        sugestao_resposta = client.chat.completions.create(
            model="gpt-4",
            messages=sugestao_prompt,
            temperature=0.7,
            max_tokens=150
        ).choices[0].message.content.strip()

        # Extrai sugestões da resposta textual
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
    app.run(debug=True)
