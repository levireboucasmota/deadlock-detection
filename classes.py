import threading
import time
import random

# Classe para representar o Sistema Operacional
class SistemaOperacional(threading.Thread):
    def __init__(self, recursos, processos, intervalo_verificacao):
        super().__init__()
        self.recursos = recursos  # Dicionário: {ID_recurso: {'nome': nome, 'total': total, 'disponivel': disponivel}}
        self.processos = processos  # Lista de instâncias da classe Processo
        self.intervalo_verificacao = intervalo_verificacao
        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.intervalo_verificacao)
            self.detectar_deadlock()

    def detectar_deadlock(self):
        self.atualizar_log("\n[DETECTOR DE DEADLOCK] Verificando...")
        n_processos = len(self.processos)
        n_recursos = len(self.recursos)

        # Se houver menos de dois processos, não há deadlock possível
        if n_processos < 2:
            self.atualizar_log("[SEM DEADLOCK] Menos de dois processos.")
            return

        # Criar um mapeamento de ID de recurso para índice
        recursos_ids = [r.id for r in self.recursos]
        recurso_para_indice = {recurso_id: idx for idx, recurso_id in enumerate(recursos_ids)}

        # Inicializar matrizes
        A = [[0 for _ in range(n_recursos)] for _ in range(n_processos)]  # Matriz de Alocação
        R = [[0 for _ in range(n_recursos)] for _ in range(n_processos)]  # Matriz de Requisição
        D = [r.disponivel for r in self.recursos]  # Vetor de Recursos Disponíveis

        # Preencher matrizes
        for i, processo in enumerate(self.processos):
            for recurso_id, quantidade in processo.recursos_alocados.items():
                idx = recurso_para_indice[recurso_id]
                A[i][idx] = quantidade
            for recurso_id, quantidade in processo.recursos_requisitados.items():
                idx = recurso_para_indice[recurso_id]
                R[i][idx] = quantidade

        # Construir o grafo de dependências
        grafo = {i: [] for i in range(n_processos)}  # Grafo de dependências entre processos
        for i in range(n_processos):
            for j in range(n_recursos):
                if R[i][j] > 0 and A[i][j] == 0:  # Processo i precisa do recurso j
                    for k in range(n_processos):
                        if A[k][j] > 0:  # Processo k está segurando o recurso j
                            grafo[i].append(k)

        # Detectar ciclos no grafo (usando DFS)
        visitados = [False] * n_processos
        pilha_recursao = [False] * n_processos

        def tem_ciclo(processo):
            if not visitados[processo]:
                visitados[processo] = True
                pilha_recursao[processo] = True
                for vizinho in grafo[processo]:
                    if not visitados[vizinho]:
                        if tem_ciclo(vizinho):
                            return True
                    elif pilha_recursao[vizinho]:
                        return True
                pilha_recursao[processo] = False
            return False

        # Verificar se há ciclos
        deadlocked = []
        for i in range(n_processos):
            if tem_ciclo(i):
                deadlocked.append(i)

        if deadlocked:
            self.atualizar_log("[DEADLOCK DETECTADO] Processos envolvidos: " + str([self.processos[i].id for i in deadlocked]))
        else:
            self.atualizar_log("[SEM DEADLOCK] Todos os processos estão finalizáveis.")

    def parar(self):
        self.running = False

# Classe para representar um Processo
class Processo(threading.Thread):
    id_counter = 1

    def __init__(self, recursos, delta_ts, delta_tu):
        super().__init__()
        self.id = Processo.id_counter
        Processo.id_counter += 1
        self.recursos = recursos
        self.delta_ts = delta_ts
        self.delta_tu = delta_tu
        self.recursos_alocados = {}  # {ID_recurso: quantidade}
        self.recursos_requisitados = {}  # {ID_recurso: quantidade}
        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.delta_ts)
            if not self.running:
                break
            recurso_id = random.choice(list(self.recursos.keys()))
            self.solicitar_recurso(recurso_id)

    def solicitar_recurso(self, recurso_id):
        print(f"[PROCESSO {self.id}] Solicitando recurso {recurso_id}")
        with threading.Lock():
            if self.recursos[recurso_id]['disponivel'] > 0:
                self.recursos[recurso_id]['disponivel'] -= 1
                self.recursos_alocados[recurso_id] = self.recursos_alocados.get(recurso_id, 0) + 1
                print(f"[PROCESSO {self.id}] Recebeu recurso {recurso_id}")
                threading.Thread(target=self.utilizar_recurso, args=(recurso_id,)).start()
            else:
                self.recursos_requisitados[recurso_id] = self.recursos_requisitados.get(recurso_id, 0) + 1
                print(f"[PROCESSO {self.id}] Bloqueado aguardando recurso {recurso_id}")

    def utilizar_recurso(self, recurso_id):
        print(f"[PROCESSO {self.id}] Utilizando recurso {recurso_id} por {self.delta_tu}s")
        time.sleep(self.delta_tu)
        self.liberar_recurso(recurso_id)

    def liberar_recurso(self, recurso_id):
        print(f"[PROCESSO {self.id}] Liberando recurso {recurso_id}")
        with threading.Lock():
            self.recursos[recurso_id]['disponivel'] += 1
            self.recursos_alocados[recurso_id] -= 1
            if self.recursos_alocados[recurso_id] == 0:
                del self.recursos_alocados[recurso_id]
            if recurso_id in self.recursos_requisitados:
                self.recursos_requisitados[recurso_id] -= 1
                if self.recursos_requisitados[recurso_id] == 0:
                    del self.recursos_requisitados[recurso_id]

    def parar(self):
        self.running = False

# Função principal
def main():
    # Configuração inicial
    recursos = {
        1: {'nome': 'Impressora', 'total': 2, 'disponivel': 2},
        2: {'nome': 'Scanner', 'total': 1, 'disponivel': 1},
        3: {'nome': 'Modem', 'total': 1, 'disponivel': 1},
    }

    # Criar processos
    processos = [
        Processo(recursos, delta_ts=3, delta_tu=6),
        Processo(recursos, delta_ts=4, delta_tu=5),
        Processo(recursos, delta_ts=5, delta_tu=7),
    ]

    # Criar e iniciar o Sistema Operacional
    intervalo_verificacao = 5
    so = SistemaOperacional(recursos, processos, intervalo_verificacao)
    so.start()

    # Iniciar os processos
    for processo in processos:
        processo.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando simulação...")
        for processo in processos:
            processo.parar()
            processo.join()
        so.parar()
        so.join()

if __name__ == "__main__":
    main()