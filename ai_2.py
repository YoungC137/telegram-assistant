import ollama

def ask_ai(question, json_mode=False):
    response = ollama.chat(
        model='qwen3:4b',
        messages=[
            {
                "role": "user",
                "content": question
            }
        ],
        options={
            "num_predict": 200
        },
        think=False,
        format = 'json' if json_mode else None
    )
    return response['message']['content']