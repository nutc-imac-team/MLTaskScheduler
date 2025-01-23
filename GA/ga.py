import numpy as np
import datetime

def __init__(self, resource_dict, number_of_node, limit_W, nodes):
    req_list, resource_list = self.convert_resource_format(resource_dict)
    self.req_list = req_list
    self.resource_list = resource_list
    self.item = pd.DataFrame(data=resource_list, columns=['cpu', 'mem', 'images'])
    self.number_of_node = number_of_node

    node_list, node_resource_list = self.convert_node_resource_format(nodes)
    self.node_list = node_list
    self.node_resource_list = node_resource_list

    self.node_state = list(map(self.gen_node_state, node_list))
    self.actions = list()
    for place in range(self.number_of_node):
        self.actions = self.actions + [(place, item) for item in list(range(len(self.item)))]
    
    self.q_table = pd.DataFrame(columns=self.actions)
    self.limit_W = limit_W

def convert_resource_format(resource_dict):
    req_list = list()
    resource_list = list()
    for key, value in resource_dict.items():
        req_list.append((key, value['node_name']))
        try:
            cpu = float(value['cpu'])
        except ValueError:
            cpu = float(value['cpu'].split('m')[0]) / 1000
        resource_list = [cpu, float(value['memory'][:-2]), float(value['images'])]
        resource_list.append(resource_list)
    return req_list, resource_list

def convert_node_resource_format(nodes):
    node_list = list(nodes.keys())
    node_resource_list = list(nodes.values())
    return node_list, node_resource_list

def gen_node_state(self, node_name):
    node_state = list()
    for index, value in enumerate(self.req_list):
        isinside = value[-1]
        if isinside == node_name:
            node_state.append(index)
    return node_state

def get_score(self, placement):
    score = 0
    count = 0
    for index, node_stat in enumerate(placement):
        count += len(node_stat)
        cpu_usage = np.sum([self.item['cpu'][i] for i in node_stat]) / self.limit_W['cpu']
        memory_usage = np.sum([self.item['mem'][i] for i in node_stat]) / self.limit_W['mem']
        images = np.sum([self.item['images'][i] for i in node_stat]) / self.nodeimage['images']
        if cpu_usage > 1 or memory_usage > 1 or images >= 1:
            score = -99
            done = "oom"
            return done, score
        node_score = int(cpu_usage * 10) + int(memory_usage * 10) + int(images * 10)
        score += node_score

    if count >= len(self.item):
        score = score + 30
        done = "finish"
        return done, score

    done = "continue"
    return done, score

def create_gen(panjang_target):
    random_number = np.random.randint(32, 126, size=panjang_target)
    gen = ''.join([chr(i) for i in random_number])
    return gen

def calculate_fitness(gen, target, panjang_target):
    fitness = 0
    for i in range (panjang_target):
        if gen[i:i+1] == target[i:i+1]:
            fitness += 1
    fitness = fitness / panjang_target * 100
    return fitness

def create_population(target, max_population, panjang_target):
    populasi = {}
    for i in range(max_population):
        gen = create_gen(panjang_target)
        genfitness = calculate_fitness(gen, target, panjang_target)
        populasi[gen] =  genfitness
    return populasi

def selection(populasi):
    pop = dict(populasi)
    parent = {}
    for i in range(2):
        gen = max(pop, key=pop.get)
        genfitness = pop[gen]
        parent[gen] = genfitness
        if i == 0:
            del pop[gen]
    return parent

def crossover(parent, target, panjang_target):
    child = {}
    cp = round(len(list(parent)[0])/2)
    for i in range(2):
        gen = list(parent)[i][:cp] + list(parent)[1-i][cp:]
        genfitness = calculate_fitness(gen, target, panjang_target)
        child[gen] = genfitness
    return child

def mutation(child, target, mutation_rate, panjang_target):
    mutant = {}
    for i in range(len(child)):     
        data = list(list(child)[i])
        for j in range(len(data)):
            if np.random.rand(1) <= mutation_rate:
                ch = chr(np.random.randint(32, 126))
                data[j] = ch
        gen = ''.join(data)
        genfitness = calculate_fitness(gen, target, panjang_target)
        mutant[gen] = genfitness
    return mutant

def regeneration(mutant, populasi):
    for i in range(len(mutant)):
        bad_gen = min(populasi, key=populasi.get)
        del populasi[bad_gen]
    populasi.update(mutant)
    return populasi

def bestgen(parent):
    gen = max(parent, key=parent.get)
    return gen

def bestfitness(parent):
    fitness = parent[max(parent, key=parent.get)]
    return fitness

def display(parent):
    timeDiff=datetime.datetime.now()-startTime
    print('{}\t{}%\t{}'.format(bestgen(parent), round(bestfitness(parent), 2), timeDiff))

if __name__ == "__main__":
    max_population = 10
    mutation_rate = 0.2

    panjang_target = len(target)
    populasi = create_population(target, int(max_population), panjang_target)
    parent = selection(populasi)

    while 1:
        child = crossover(parent, target, panjang_target)
        mutant = mutation(child, target, float(mutation_rate), panjang_target)
        if bestfitness(parent) >= bestfitness(mutant):
            continue
        populasi = regeneration(mutant, populasi)
        parent = selection(populasi)
        display(parent)
        if bestfitness(mutant) >= 100:
            break