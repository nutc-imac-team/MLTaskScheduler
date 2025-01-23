import numpy as np

# GA參數
MAX_GENERATIONS = 1000
POPULATION_SIZE = 50
MUTATION_RATE = 0.2
CROSSOVER_RATE = 0.8

def initialize_population(num_pods, num_nodes):
    return [np.random.randint(0, num_nodes, size=num_pods) for _ in range(POPULATION_SIZE)]

def calculate_fitness(solution, pods, nodes):
    node_usage = {node: {"cpu": 0.0, "memory": 0, "pods": []} for node in nodes}
    unassigned_pods = []

    for pod_index, node_index in enumerate(solution):
        node_name = list(nodes.keys())[node_index]
        pod_name = list(pods.keys())[pod_index]

        if (node_usage[node_name]["cpu"] + pods[pod_name]["cpu"] <= nodes[node_name]["cpu"] and
            node_usage[node_name]["memory"] + pods[pod_name]["memory"] <= nodes[node_name]["memory"]):
            node_usage[node_name]["pods"].append(pod_name)
            node_usage[node_name]["cpu"] += pods[pod_name]["cpu"]
            node_usage[node_name]["memory"] += pods[pod_name]["memory"]
        else:
            unassigned_pods.append(pod_name)

    fitness = 0
    assigned_pods = 0
    for node, usage in node_usage.items():
        if usage["cpu"] > nodes[node]["cpu"] or usage["memory"] > nodes[node]["memory"]:
            fitness -= 10000
        else:
            assigned_pods += len(usage["pods"])

    fitness += assigned_pods * 10
    if len(unassigned_pods) > 0:
        fitness -= len(unassigned_pods) * 2

    return fitness, unassigned_pods


def selection(population, fitness_scores):
    fitness_scores = np.array(fitness_scores)
    probabilities = fitness_scores / fitness_scores.sum()
    selected_indices = np.random.choice(range(len(population)), size=2, p=probabilities)
    return [population[i] for i in selected_indices]

def crossover(parent1, parent2):
    if np.random.rand() < CROSSOVER_RATE:
        point = np.random.randint(1, len(parent1))
        child1 = np.concatenate((parent1[:point], parent2[point:]))
        child2 = np.concatenate((parent2[:point], parent1[point:]))
        return child1, child2
    return parent1, parent2

def mutate(solution, num_nodes, nodes, pods):
    if np.random.rand() < MUTATION_RATE:
        index = np.random.randint(len(solution))
        old_node_index = solution[index]
        node_name = list(nodes.keys())[old_node_index]
        pod_name = list(pods.keys())[index]
        
        valid_nodes = [
            i for i in range(num_nodes)
            if (nodes[node_name]["cpu"] + pods[pod_name]["cpu"] <= nodes[list(nodes.keys())[i]]["cpu"] and
                nodes[node_name]["memory"] + pods[pod_name]["memory"] <= nodes[list(nodes.keys())[i]]["memory"])
        ]
        
        if valid_nodes:
            solution[index] = np.random.choice(valid_nodes)

    return solution

def ga_placement(pods, nodes):
    num_pods = len(pods)
    num_nodes = len(nodes)
    population = initialize_population(num_pods, num_nodes)

    for generation in range(MAX_GENERATIONS):
        fitness_scores = []
        unassigned_pods_all_generations = []

        for sol in population:
            fitness, unassigned_pods = calculate_fitness(sol, pods, nodes)
            fitness_scores.append(fitness)
            unassigned_pods_all_generations.append(unassigned_pods)

        new_population = []
        for _ in range(len(population) // 2):
            parent1, parent2 = selection(population, fitness_scores)
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1, num_nodes, nodes, pods)
            child2 = mutate(child2, num_nodes, nodes, pods)
            new_population.extend([child1, child2])
        
        population = new_population

        best_solution_index = np.argmax(fitness_scores)
        best_solution = population[best_solution_index]
        best_fitness = fitness_scores[best_solution_index]
        unassigned_pods = unassigned_pods_all_generations[best_solution_index]

        print(f"Generation {generation+1}: Best Fitness = {best_fitness}, Unassigned Pods = {len(unassigned_pods)}")

        if best_fitness == num_pods * 10 and len(unassigned_pods) == 0:
            print(f"Solution Found in Generation {generation+1}")
            break

    return best_solution, unassigned_pods

if __name__ == "__main__":
    # 當前節點和 Pod 資訊
    nodes = {
        "node1": {"cpu": 8.0, "memory": 16384},  # 節點1，8 CPU核心，16GB記憶體
        "node2": {"cpu": 8.0, "memory": 16384},  # 節點2，8 CPU核心，16GB記憶體
        "node3": {"cpu": 8.0, "memory": 16384},  # 節點3，8 CPU核心，16GB記憶體
    }

    # task 需要的資源請求

    pods = {
        "pod1": {"cpu": 9.0, "memory": 512},
        "pod2": {"cpu": 2.0, "memory": 1024},
        "pod3": {"cpu": 0.5, "memory": 256},
        "pod4": {"cpu": 1.5, "memory": 2048},
        "pod5": {"cpu": 3.0, "memory": 4096},
        "pod6": {"cpu": 1.0, "memory": 1024},
        "pod7": {"cpu": 2.5, "memory": 2048},
        "pod8": {"cpu": 0.7, "memory": 512},
        "pod9": {"cpu": 1.2, "memory": 1536},
        "pod10": {"cpu": 2.2, "memory": 2048},
        "pod11": {"cpu": 0.8, "memory": 768},
        "pod12": {"cpu": 1.5, "memory": 2048},
        "pod13": {"cpu": 2.0, "memory": 1024},
        "pod14": {"cpu": 1.0, "memory": 1024},
        "pod15": {"cpu": 0.6, "memory": 512},
        "pod16": {"cpu": 2.7, "memory": 3072},
        "pod17": {"cpu": 1.8, "memory": 2048},
        "pod18": {"cpu": 1.2, "memory": 1280},
        "pod19": {"cpu": 3.2, "memory": 4096},
        "pod20": {"cpu": 1.3, "memory": 1536},
    }

    # Best Solution 是
    best_solution, unassigned_pods = ga_placement(pods, nodes)  # 執行 GA 分配
    print(f"Best Solution: {best_solution}")
    print(f"Unassigned Pods: {unassigned_pods}")

    node_usage = {node: {"cpu": 0.0, "memory": 0, "pods": []} for node in nodes}  # 初始化節點使用情況

    for pod, node_index in zip(pods.keys(), best_solution):  # 將 Pod 分配到節點
        node_name = list(nodes.keys())[node_index]
        node_usage[node_name]["pods"].append(pod)
        node_usage[node_name]["cpu"] += pods[pod]["cpu"]
        node_usage[node_name]["memory"] += pods[pod]["memory"]

    # 從節點使用情況中移除未分配的pod
    for pod in unassigned_pods:
        for node in node_usage.values():
            if pod in node["pods"]:
                node["pods"].remove(pod)
                node["cpu"] -= pods[pod]["cpu"]
                node["memory"] -= pods[pod]["memory"]

    print("\nNode Usage:\n", node_usage)
    node_deployment_list = [{"node": node, "pod": usage["pods"]} for node, usage in node_usage.items()] # 建立節點部署列表
    print("\nNode Deployment List:")
    for entry in node_deployment_list: # 顯示節點部署列表
        print(entry)

# 節點資源使用率
for node, usage in node_usage.items():
    print(f"{node}:")
    print(f"  Assigned Pods: {', '.join(usage['pods'])}")
    print(f"  CPU Usage: {usage['cpu']} / {nodes[node]['cpu']}")
    print(f"  Memory Usage: {usage['memory']} / {nodes[node]['memory']}")
    print(f"  CPU Usage Percentage: {usage['cpu'] / nodes[node]['cpu'] * 100:.2f}%")
    print(f"  Memory Usage Percentage: {usage['memory'] / nodes[node]['memory'] * 100:.2f}%")

if unassigned_pods:
    print("\nUnassigned Pods:")
    for pod in unassigned_pods:
        print(pod)
else:
    print("\nAll pods have been successfully assigned to nodes.")
