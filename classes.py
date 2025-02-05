import threading
import time
import random

class Recurso:
    def __init__(self, nome, identificador, quantidade):
        self.nome = nome
        self.identificador = identificador
        self.quantidade_total = quantidade
        self.quantidade_disponivel = quantidade
        self.alocados = {}  # Dicionário para rastrear quais processos possuem este recurso
        self.lock = threading.Lock()  # Lock para sincronização
        self.condition = threading.Condition(self.lock)  # Condição para notificar processos bloqueados

    def solicitar(self, processo_id):
        with self.lock:
            while self.quantidade_disponivel == 0:
                print(f"[Processo {processo_id}] Aguardando recurso {self.nome}...")
                self.condition.wait()  # Aguarda até que o recurso seja liberado
            print(f"[Processo {processo_id}] Solicitando recurso {self.nome}")
            self.quantidade_disponivel -= 1
            self.alocados[processo_id] = self.alocados.get(processo_id, 0) + 1

    def liberar(self, processo_id):
        with self.lock:
            if processo_id in self.alocados:
                self.alocados[processo_id] -= 1
                if self.alocados[processo_id] == 0:
                    del self.alocados[processo_id]
                self.quantidade_disponivel += 1
                print(f"[Processo {processo_id}] Liberando recurso {self.nome}")
                self.condition.notify_all()  # Notifica processos bloqueados


class Processo(threading.Thread):
    def __init__(self, id, delta_ts, delta_tu, recursos):
        super().__init__()
        self.id = id
        self.delta_ts = delta_ts  # Intervalo de tempo para solicitar recursos
        self.delta_tu = delta_tu  # Tempo de utilização do recurso
        self.recursos = recursos  # Lista de recursos disponíveis no sistema
        self.status = "rodando"  # Status pode ser "rodando" ou "bloqueado"
        self.recursos_alocados = []  # Recursos atualmente alocados ao processo
        self.lock = threading.Lock()

    def run(self):
        while True:
            time.sleep(self.delta_ts)
            if self.status == "finalizado":
                break

            # Libera recursos que já foram utilizados pelo tempo necessário
            with self.lock:
                for recurso, tempo_alocacao in list(self.recursos_alocados):
                    if time.time() - tempo_alocacao >= self.delta_tu:
                        recurso.liberar(self.id)
                        self.recursos_alocados.remove((recurso, tempo_alocacao))
                        print(f"[Processo {self.id}] Liberou recurso {recurso.nome}")

            # Solicita um novo recurso aleatório
            try:
                recurso = random.choice(self.recursos)
                recurso.solicitar(self.id)
                self.recursos_alocados.append((recurso, time.time()))  # Armazena o recurso e o tempo de alocação
                print(f"[Processo {self.id}] Solicitou recurso {recurso.nome}")
            except Exception as e:
                print(f"[Processo {self.id}] Erro ao manipular recurso: {e}")

    def finalizar(self):
        with self.lock:
            self.status = "finalizado"


class SistemaOperacional(threading.Thread):
    def __init__(self, recursos, intervalo_verificacao):
        super().__init__()
        self.recursos = recursos
        self.intervalo_verificacao = intervalo_verificacao
        self.processos = []
        self.lock = threading.Lock()

    def adicionar_processo(self, processo):
        with self.lock:
            self.processos.append(processo)

    def remover_processo(self, id):
        with self.lock:
            for processo in self.processos:
                if processo.id == id:
                    processo.finalizar()
                    print(f"[SO] Processo {id} eliminado")
                    self.processos.remove(processo)
                    return
            print(f"[SO] Processo {id} não encontrado")

    def verificar_deadlock(self):
        with self.lock:
            # Construir matriz de alocação (Allocation Matrix)
            allocation_matrix = {}
            for processo in self.processos:
                allocation_matrix[processo.id] = {
                    r.identificador: r.alocados.get(processo.id, 0) for r in self.recursos
                }

            # Construir matriz de requisição (Request Matrix)
            request_matrix = {}
            for processo in self.processos:
                request_matrix[processo.id] = {
                    r.identificador: 1 if processo.status == "bloqueado" and r.quantidade_disponivel == 0 else 0
                    for r in self.recursos
                }

            # Vetor de recursos disponíveis (Available Vector)
            available_vector = {r.identificador: r.quantidade_disponivel for r in self.recursos}

            # Detectar deadlock usando o algoritmo de detecção de ciclos
            processos_finalizados = set()
            while True:
                processo_encontrado = False
                for processo in self.processos:
                    if processo.id in processos_finalizados:
                        continue

                    # Verificar se o processo pode ser concluído
                    pode_concluir = True
                    for recurso in self.recursos:
                        if request_matrix[processo.id][recurso.identificador] > available_vector[recurso.identificador]:
                            pode_concluir = False
                            break

                    if pode_concluir:
                        # Liberar recursos do processo
                        for recurso in self.recursos:
                            available_vector[recurso.identificador] += allocation_matrix[processo.id][recurso.identificador]
                        processos_finalizados.add(processo.id)
                        processo_encontrado = True

                if not processo_encontrado:
                    break

            # Se houver processos que não foram finalizados, há deadlock
            processos_bloqueados = [p.id for p in self.processos if p.id not in processos_finalizados]
            if processos_bloqueados:
                print(f"[SO] Deadlock detectado envolvendo os processos: {processos_bloqueados}")
            else:
                print("[SO] Nenhum deadlock detectado.")

    def run(self):
        while True:
            time.sleep(self.intervalo_verificacao)
            print("[SO] Verificando deadlocks...")
            self.verificar_deadlock()


# Configuração inicial
recursos = [
    Recurso(nome="Impressora", identificador=1, quantidade=1),
    Recurso(nome="Scanner", identificador=2, quantidade=1),
]

so = SistemaOperacional(recursos=recursos, intervalo_verificacao=7)
so.start()

# Criação de processos
processos = []
for i in range(1, 3):  # Exemplo com 4 processos
    processo = Processo(id=i, delta_ts=5, delta_tu=10, recursos=recursos)
    so.adicionar_processo(processo)
    processos.append(processo)
    processo.start()

# Simulação contínua
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Encerrando simulação...")
    for processo in processos:
        processo.finalizar()