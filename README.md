# 🏋️ Smart Gym — Monitoramento Inteligente de Exercícios

> Sistema embarcado de monitoramento de exercícios físicos com visão computacional, identificação por RFID e contagem automática de repetições em tempo real.

---

## 📌 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Como Executar](#como-executar)
- [Uso do Sistema](#uso-do-sistema)
- [Fluxo de Estados](#fluxo-de-estados)
- [Configuração de Alunos](#configuração-de-alunos)
- [Integrantes](#integrantes)

---

## 🧠 Sobre o Projeto

O **Smart Gym** é um sistema IoT de monitoramento de atividade física desenvolvido para academias inteligentes. Ele combina um **leitor RFID (via Arduino)** com **visão computacional (MediaPipe)** para identificar o aluno, acompanhar seus movimentos pela webcam, calcular o ângulo do braço em tempo real e contar automaticamente as repetições do exercício *Rosca Direta*.

O sistema exibe um gráfico de ângulo ao vivo, uma barra de status com progresso e emite uma confirmação ao atingir a meta de repetições cadastrada para cada aluno.

---

## ✅ Funcionalidades

- **Identificação por RFID** — o aluno aproxima o cartão e o sistema carrega seu perfil automaticamente
- **Modo Convidado** — acesso rápido sem cartão, pressionando a tecla `S`
- **Detecção de pose em tempo real** — usa MediaPipe Pose Landmarker para rastrear ombro, cotovelo e pulso
- **Cálculo de ângulo do braço** — trigonometria aplicada sobre os marcos anatômicos detectados
- **Contagem automática de repetições** — baseada em limites de ângulo configuráveis (> 160° = descida, < 35° = subida)
- **Gráfico de ângulo ao vivo** — renderizado com Matplotlib e embutido no frame da câmera
- **Barra de status** — exibe nome do aluno, repetições realizadas e meta
- **Conclusão de treino** — mensagem de parabéns ao atingir o objetivo, seguida de reset automático

---

## 🏗️ Arquitetura do Sistema

```
┌──────────────┐     Serial (USB)     ┌─────────────────────┐
│ Arduino +    │ ──── ID do RFID ───► │                     │
│ Leitor RFID  │                      │     app.py          │
└──────────────┘                      │  (Orquestrador)     │
                                      │                     │
┌──────────────┐     Frame BGR        │  ┌───────────────┐  │
│   Webcam     │ ──────────────────► │  │pose_detector  │  │
└──────────────┘                      │  └───────────────┘  │
                                      │  ┌───────────────┐  │
                                      │  │   serial_io   │  │
                                      │  └───────────────┘  │
                                      │  ┌───────────────┐  │
                                      │  │     ui.py     │  │
                                      │  └───────────────┘  │
                                      │  ┌───────────────┐  │
                                      │  │   config.py   │  │
                                      │  └───────────────┘  │
                                      └─────────────────────┘
```

### Módulos Python

| Módulo | Responsabilidade |
|---|---|
| `app.py` | Orquestrador principal — loop de captura, máquina de estados |
| `config.py` | Constantes globais, perfis de alunos e caminho do modelo |
| `serial_io.py` | Comunicação serial com Arduino/RFID (inicialização e leitura) |
| `pose_detector.py` | Carregamento do modelo MediaPipe e cálculo de ângulo articular |
| `ui.py` | Gráfico de ângulo em tempo real e barra de status sobreposta |

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|---|---|---|
| Python | 3.10+ | Linguagem principal |
| OpenCV | 4.9.0.80 | Captura de vídeo e renderização |
| MediaPipe | 0.10.33 | Detecção de pose (Pose Landmarker) |
| NumPy | 1.26.4 | Cálculo de ângulos e manipulação de arrays |
| PySerial | 3.5 | Comunicação serial com Arduino |
| Matplotlib | 3.8.2 | Gráfico de ângulo em tempo real |
| Arduino | — | Leitura do cartão RFID via MFRC522 |

---

## 📁 Estrutura do Repositório

```
smart-gym/
├── arduino/                  # Sketch Arduino para leitura RFID
├── assets/
│   └── pose_landmarker_full.task  # Modelo MediaPipe (download necessário)
├── docs/                     # Documentação complementar e diagramas
├── python/
│   ├── app.py                # Ponto de entrada da aplicação
│   ├── config.py             # Configurações e perfis de alunos
│   ├── pose_detector.py      # Detecção de pose e cálculo de ângulo
│   ├── serial_io.py          # Comunicação serial com Arduino
│   ├── ui.py                 # Interface visual (gráfico e status)
│   └── requirements.txt      # Dependências Python
└── README.md
```

---

## 📋 Pré-requisitos

- **Python 3.10** (versão específica exigida pelo MediaPipe)
- **Webcam** conectada ao computador
- **Arduino Uno/Nano ou ESP32** com leitor **RFID MFRC522** *(opcional — modo convidado disponível sem Arduino)*
- **Modelo MediaPipe** — baixe o arquivo `pose_landmarker_full.task` em:
  [https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)
  e coloque-o em `assets/pose_landmarker_full.task`

---

## ⚙️ Instalação

Execute os comandos abaixo **dentro da pasta `python`**:

```bash
# 1. Acesse o diretório
cd python

# 2. Crie o ambiente virtual com Python 3.10
py -3.10 -m venv venv

# 3. Ative o ambiente virtual
# No Git Bash / macOS / Linux:
source venv/Scripts/activate

# No Prompt de Comando (Windows):
venv\Scripts\activate

# 4. Instale as dependências
pip install -r requirements.txt
```

---

## ▶️ Como Executar

> **Importante:** antes de executar, configure a porta serial correta no arquivo `python/app.py`:

```python
# Linha em app.py — substitua 'COMx' pela porta real do seu Arduino
ser = serial_io.init_serial('COM3', 9600, timeout=0.1)
```

Dicas para identificar a porta:
- **Windows:** Gerenciador de Dispositivos → Portas (COM e LPT)
- **Linux/macOS:** `ls /dev/tty*` (ex: `/dev/ttyUSB0` ou `/dev/ttyACM0`)

Depois, execute:

```bash
cd python
python app.py
```

> Se o Arduino não estiver conectado, o sistema iniciará automaticamente em **modo somente convidado** (tecla `S`).

---

## 🎮 Uso do Sistema

| Ação | Como fazer |
|---|---|
| Identificar-se como aluno cadastrado | Aproximar o cartão RFID ao leitor |
| Entrar como convidado | Pressionar a tecla `S` |
| Sair do sistema | Pressionar a tecla `Q` |

Após a identificação:
1. Posicione-se em frente à webcam com o braço visível
2. O sistema detectará automaticamente ombro, cotovelo e pulso
3. Realize a *Rosca Direta* — o ângulo será calculado e as repetições contadas
4. Ao atingir a meta, uma mensagem de conclusão será exibida por 3 segundos
5. O sistema retorna automaticamente à tela de identificação

---

## 🔄 Fluxo de Estados

```
        ┌─────────────────────┐
        │   AGUARDANDO_ID     │ ◄─────────────────────┐
        │  (Tela inicial)     │                       │
        └────────┬────────────┘                       │
                 │ RFID lido ou tecla 'S'             │
                 ▼                                    │
        ┌─────────────────────┐              3s e reset
        │  TREINO_EM_CURSO    │                       │
        │  (Detecção + conta) │                       │
        └────────┬────────────┘                       │
                 │ reps >= objetivo                   │
                 ▼                                    │
        ┌─────────────────────┐                       │
        │  TREINO_CONCLUÍDO   │ ──────────────────────┘
        │  (Mensagem final)   │
        └─────────────────────┘
```

---

## 👤 Configuração de Alunos

Edite o arquivo `python/config.py` para cadastrar alunos com seus cartões RFID:

```python
ALUNOS_REGISTRADOS = {
    "4A B9 3B 1B": {"nome": "Lucas", "exercicio": "Rosca Direta", "objetivo": 5},
    "B3 22 A1 0C": {"nome": "Maria", "exercicio": "Rosca Direta", "objetivo": 8},
    # Adicione novos alunos no formato:
    # "ID_RFID": {"nome": "Nome", "exercicio": "Exercicio", "objetivo": N_REPS},
}

# Perfil padrão para o modo convidado
PERFIL_CONVIDADO = {"nome": "Convidado", "exercicio": "Rosca Direta", "objetivo": 3}
```

O **ID RFID** pode ser obtido pela saída serial do Arduino após aproximar o cartão.

---

## 👥 Integrantes

| Nome | RM |
|---|---|
| Lorenzo Hayashi Mangini | RM 554901 |
| Milton Cezar Bacanieski | RM 555206 |
| Vitor Bebiano Mulford | RM 555026 |
| Victorio Maia Bastelli | RM 554723 |

---

> Projeto desenvolvido para a disciplina de **IoT & IoB** — FIAP.
