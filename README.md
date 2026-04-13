# Smart Gym - Monitoramento Inteligente de Exercicios

Projeto de monitoramento de exercicios com camera, MediaPipe e Arduino/RFID.

## Sobre

O sistema identifica o aluno por RFID ou permite entrar no modo convidado pelo teclado. Depois disso, a webcam acompanha o movimento, calcula o angulo do braco e conta as repeticoes em tempo real.

## Funcionalidades

- Identificacao por RFID
- Modo convidado com a tecla `S`
- Leitura de pose pela webcam
- Contagem de repeticoes
- Grafico do angulo em tempo real

## Requisitos

- Python 3.10+
- Webcam
- Arduino Uno/Nano ou ESP32
- Leitor RFID MFRC522 ou entrada simulada por teclado

## Instalacao

Siga exatamente estes passos dentro da pasta `python`:

```bash
cd python
py -3.10 -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

Se estiver usando o Prompt de Comando, ative com:

```bat
venv\Scripts\activate
```

## Como executar

Antes de rodar, ajuste a porta serial no arquivo `python/app.py`:

```python
serial.Serial('COMx', 9600, timeout=0.1)
```

Depois, execute:

```bash
cd python
python app.py
```

## Uso

- Aproximar o cartao RFID para iniciar como aluno cadastrado
- Ou pressionar `S` para iniciar como convidado
- Pressionar `Q` para sair

## Estrutura

- `arduino/` - arquivos do Arduino
- `assets/` - modelo de pose do MediaPipe
- `docs/` - documentacao complementar
- `python/` - aplicacao principal em Python

## Integrantes

- Lorenzo Hayashi Mangini - RM 554901
- Milton Cezar Bacanieski - RM 555206
- Vitor Bebiano Mulford - RM 555026
- Victorio Maia Bastelli - RM 554723
tall -r requirements.txt