import threading
import time
import random

class Recurso:
    def __init__(self, nome, identificador, quantidade, atualizar_log):
        self.nome = nome
        self.identificador = identificador
        self.quantidade_total = quantidade
        self.quantidade_disponivel = quantidade
        self.alocados = {}  # Dicionário para rastrear quais processos possuem este recurso
        self.lock = threading.Lock()  # Lock para sincronização
        self.condition = threading.Condition(self.lock)  # Condição para notificar processos bloqueados
        self.atualizar_log = atualizar_log  # Referência ao método de log

    def solicitar(self, processo_id):
        with self.lock:
            while self.quantidade_disponivel == 0:
                self.atualizar_log(f"[Processo {processo_id}] Aguardando recurso {self.nome}...")
                self.condition.wait()  # Aguarda até que o recurso seja liberado
            self.atualizar_log(f"[Processo {processo_id}] Solicitando recurso {self.nome}")
            self.quantidade_disponivel -= 1
            self.alocados[processo_id] = self.alocados.get(processo_id, 0) + 1

    def liberar(self, processo_id):
        with self.lock:
            if processo_id in self.alocados:
                self.alocados[processo_id] -= 1
                if self.alocados[processo_id] == 0:
                    del self.alocados[processo_id]
                self.quantidade_disponivel += 1
                self.atualizar_log(f"[Processo {processo_id}] Liberando recurso {self.nome}")
                self.condition.notify_all()  # Notifica processos bloqueados

class Processo(threading.Thread):
    def __init__(self, id, delta_ts, delta_tu, recursos, atualizar_log):
        super().__init__()
        self.id = id
        self.delta_ts = delta_ts  # Intervalo de tempo para solicitar recursos
        self.delta_tu = delta_tu  # Tempo de utilização do recurso
        self.recursos = recursos  # Lista de recursos disponíveis no sistema
        self.status = "rodando"  # Status pode ser "rodando" ou "bloqueado"
        self.recursos_alocados = []  # Recursos atualmente alocados ao processo
        self.lock = threading.Lock()
        self.running = True
        self.atualizar_log = atualizar_log  # Referência ao método de log

    def run(self):
        while self.running:
            time.sleep(self.delta_ts)
            if not self.running:
                break

            # Libera recursos que já foram utilizados pelo tempo necessário
            with self.lock:
                for recurso, tempo_alocacao in list(self.recursos_alocados):
                    if time.time() - tempo_alocacao >= self.delta_tu:
                        recurso.liberar(self.id)
                        self.recursos_alocados.remove((recurso, tempo_alocacao))
                        self.atualizar_log(f"[Processo {self.id}] Liberou recurso {recurso.nome}")

            # Solicita um novo recurso aleatório
            try:
                recurso = random.choice(self.recursos)
                recurso.solicitar(self.id)
                self.recursos_alocados.append((recurso, time.time()))  # Armazena o recurso e o tempo de alocação
                self.atualizar_log(f"[Processo {self.id}] Solicitou recurso {recurso.nome}")
            except Exception as e:
                self.atualizar_log(f"[Processo {self.id}] Erro ao manipular recurso: {e}")

    def finalizar(self):
        with self.lock:
            self.running = False

class SistemaOperacional(threading.Thread):
    def __init__(self, recursos, intervalo_verificacao, atualizar_log):
        super().__init__()
        self.recursos = recursos
        self.intervalo_verificacao = intervalo_verificacao
        self.processos = []
        self.lock = threading.Lock()
        self.running = True
        self.atualizar_log = atualizar_log  # Referência ao método de log

    def adicionar_processo(self, processo):
        with self.lock:
            self.processos.append(processo)

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
            work = available_vector.copy()
            finish = {p.id: False for p in self.processos}
            safe_sequence = []
            while True:
                found = False
                for processo in self.processos:
                    if not finish[processo.id]:
                        if all(allocation_matrix[processo.id][r.identificador] + work[r.identificador] >= request_matrix[processo.id][r.identificador] for r in self.recursos):
                            for r in self.recursos:
                                work[r.identificador] += allocation_matrix[processo.id][r.identificador]
                            finish[processo.id] = True
                            safe_sequence.append(processo.id)
                            found = True
                            break
                if not found:
                    break
            # Se houver processos que não foram finalizados, há deadlock
            processos_bloqueados = [p.id for p in self.processos if not finish[p.id]]
            if processos_bloqueados:
                self.atualizar_log(f"[SO] Deadlock detectado envolvendo os processos: {processos_bloqueados}")
            else:
                self.atualizar_log("[SO] Nenhum deadlock detectado.")

    def run(self):
        while self.running:
            time.sleep(self.intervalo_verificacao)
            self.atualizar_log("[SO] Verificando deadlocks...")
            self.verificar_deadlock()

    def parar(self):
        self.running = False