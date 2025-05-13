from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# Configure sua chave API da OpenAI
openai.api_key = "sua-chave-api-da-openai"

@app.route('/perguntar', methods=['POST'])
def perguntar():
    data = request.get_json()
    pergunta = data.get('pergunta')
    
    if not pergunta:
        return jsonify({"resposta": "Desculpe, não consegui entender."})

    try:
        # Enviar a pergunta para o modelo GPT da OpenAI
        resposta = openai.Completion.create(
            model="gpt-4",  # Ou o modelo que você preferir
            prompt=pergunta,
            max_tokens=150
        )
        return jsonify({"resposta": resposta.choices[0].text.strip()})
    except Exception as e:
        return jsonify({"resposta": "Erro ao processar a pergunta."})

if __name__ == '__main__':
    app.run(debug=True)
