# Smart Gym - Monitoramento Inteligente de Exercicios

Sistema IoT de monitoramento de exercicios fisicos com webcam, MediaPipe,
Arduino/RFID e contagem automatica de repeticoes em tempo real.

## Indice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura do Repositorio](#estrutura-do-repositorio)
- [Pre-requisitos](#pre-requisitos)
- [Instalacao](#instalacao)
- [Como Executar](#como-executar)
- [Teste do RFID](#teste-do-rfid)
- [Uso do Sistema](#uso-do-sistema)
- [Fluxo de Estados](#fluxo-de-estados)
- [Configuracao de Alunos](#configuracao-de-alunos)
- [Integrantes](#integrantes)

## Sobre o Projeto

O Smart Gym identifica o aluno por RFID usando um Arduino com leitor MFRC522.
Depois da identificacao, a aplicacao usa a webcam e o MediaPipe Pose Landmarker
para acompanhar o movimento do corpo, calcular o angulo do joelho e contar
repeticoes de agachamento.

O sistema tambem possui modo convidado pela tecla `S`, grafico de angulo em
tempo real, barra de status com nome do aluno e meta de repeticoes, e tela de
conclusao ao atingir o objetivo cadastrado.

## Funcionalidades

- Identificacao por RFID via Arduino.
- Modo convidado pela tecla `S`.
- Deteccao de pose em tempo real com MediaPipe.
- Calculo do angulo do joelho usando quadril, joelho e tornozelo.
- Contagem automatica de agachamentos.
- Grafico de angulo ao vivo com Matplotlib.
- Barra de status com aluno ativo, repeticoes e objetivo.
- Reset automatico apos concluir o treino.
- Teste isolado de RFID em `python/test_rfid.py`.

## Arquitetura do Sistema

```text
Arduino + MFRC522 -- Serial USB / UID --> python/serial_io.py
Webcam ------------ Frame BGR ---------> python/app.py

python/app.py
  |-- config.py        -> porta serial, alunos, objetivo e limites de angulo
  |-- serial_io.py     -> deteccao da porta COM e leitura do UID
  |-- pose_detector.py -> MediaPipe e calculo do angulo do joelho
  |-- ui.py            -> grafico e barra de status
```

### Modulos Python

| Modulo | Responsabilidade |
|---|---|
| `app.py` | Orquestrador principal, loop de camera e maquina de estados |
| `config.py` | Configuracoes, alunos cadastrados, caminho do modelo e limites de angulo |
| `serial_io.py` | Comunicacao serial com Arduino/RFID e normalizacao do UID |
| `pose_detector.py` | Carregamento do MediaPipe e calculo do angulo do joelho |
| `ui.py` | Grafico de angulo e barra de status |
| `test_rfid.py` | Teste isolado da leitura RFID sem webcam |

## Tecnologias Utilizadas

| Tecnologia | Versao | Finalidade |
|---|---|---|
| Python | 3.10+ | Linguagem principal |
| OpenCV | 4.9.0.80 | Captura de video e renderizacao |
| MediaPipe | 0.10.33 | Deteccao de pose |
| NumPy | 1.26.4 | Calculo de angulos e manipulacao de arrays |
| PySerial | 3.5 | Comunicacao serial com Arduino |
| Matplotlib | 3.8.2 | Grafico de angulo em tempo real |
| Arduino | - | Leitura do cartao RFID via MFRC522 |

## Estrutura do Repositorio

```text
smart-gym/
|-- arduino/
|   `-- rfid_reader/
|       `-- rfid_reader.ino
|-- assets/
|   `-- pose_landmarker_full.task
|-- docs/
|-- python/
|   |-- app.py
|   |-- config.py
|   |-- pose_detector.py
|   |-- requirements.txt
|   |-- serial_io.py
|   |-- test_rfid.py
|   `-- ui.py
`-- README.md
```

## Pre-requisitos

- Python 3.10+.
- Webcam conectada ao computador.
- Arduino Uno/Nano ou ESP32 com leitor RFID MFRC522.
- Modelo `pose_landmarker_full.task` em `assets/pose_landmarker_full.task`.

O modelo pode ser baixado pela pagina oficial do MediaPipe Pose Landmarker:

```text
https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
```

## Instalacao

Execute os comandos dentro da pasta `python`:

```powershell
cd python
py -3.10 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

No Git Bash, use:

```bash
source venv/Scripts/activate
```

## Como Executar

O Arduino deve enviar o UID pela serial neste formato:

```text
UID:00:A9:39:26
```

No sketch Arduino, a saida principal fica assim:

```cpp
Serial.print("UID:");
Serial.println(strID);
```

Antes de rodar o Python, feche o Monitor Serial da Arduino IDE. No Windows, a
porta COM fica presa a um unico programa por vez. Se o Monitor Serial estiver
aberto, o Python nao consegue abrir a `COM5`.

Por padrao, o Python tenta detectar a porta automaticamente em `config.py`:

```python
SERIAL_PORT = None
SERIAL_BAUD = 9600
```

Se precisar fixar a porta manualmente, altere para:

```python
SERIAL_PORT = "COM5"
SERIAL_BAUD = 9600
```

Depois execute:

```powershell
cd python
.\venv\Scripts\python.exe app.py
```

O terminal deve mostrar algo parecido com:

```text
Portas seriais encontradas: COM1 (...), COM5 (Arduino Uno (COM5))
Arduino ON em COM5 - Sistema de Identificacao Pronto!
```

## Teste do RFID

Antes de testar com a webcam, e recomendado validar apenas a leitura RFID:

```powershell
cd python
.\venv\Scripts\python.exe test_rfid.py
```

Aproxime o cartao. O esperado e:

```text
[DEBUG serial] recebido: 'UID:00:A9:39:26'
[DEBUG serial] UID extraido: 00:A9:39:26
OK: 00:A9:39:26 -> Lucas
```

Se aparecer `porta ocupada`, feche o Monitor Serial da Arduino IDE e qualquer
outra execucao antiga do Python que possa estar usando a COM do Arduino.

## Uso do Sistema

| Acao | Como fazer |
|---|---|
| Identificar aluno cadastrado | Aproximar o cartao RFID ao leitor |
| Entrar como convidado | Pressionar a tecla `S` |
| Sair do sistema | Pressionar a tecla `Q` |

Depois da identificacao:

1. Posicione-se em frente a webcam com o corpo visivel.
2. O sistema detecta quadril, joelho e tornozelo.
3. Realize o agachamento.
4. O angulo do joelho aparece na tela e no grafico.
5. Ao atingir a meta, a mensagem de treino concluido aparece por 3 segundos.
6. O sistema volta para a tela de identificacao.

## Fluxo de Estados

```text
AGUARDANDO_ID
  |-- RFID cadastrado ou tecla S
  v
TREINO_EM_CURSO
  |-- contador_reps >= objetivo
  v
TREINO_CONCLUIDO
  |-- espera 3 segundos
  v
AGUARDANDO_ID
```

## Configuracao de Alunos

Edite `python/config.py` para cadastrar alunos:

```python
ALUNOS_REGISTRADOS = {
    "00:A9:39:26": {"nome": "Lucas", "exercicio": "Agachamento", "objetivo": 5},
    "B3 22 A1 0C": {"nome": "Maria", "exercicio": "Agachamento", "objetivo": 8},
}

PERFIL_CONVIDADO = {"nome": "Convidado", "exercicio": "Agachamento", "objetivo": 3}
```

O UID pode vir com `:` ou espacos. O Python normaliza os formatos abaixo para o
mesmo valor:

```text
UID:00:A9:39:26
00:A9:39:26
00 A9 39 26
```

## Integrantes

| Nome | RM |
|---|---|
| Lorenzo Hayashi Mangini | RM 554901 |
| Milton Cezar Bacanieski | RM 555206 |
| Vitor Bebiano Mulford | RM 555026 |
| Victorio Maia Bastelli | RM 554723 |

Projeto desenvolvido para a disciplina de IoT & IoB - FIAP.
