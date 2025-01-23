import pandas as pd
import numpy as np
from time import time
import itertools
import copy

# item = pd.DataFrame(data=[['A1', 2, 4, True], ['A2', 4, 4, False], ['A3', 6, 8, False], ['A4', 8, 10, False], ['A5', 10, 12, False]], columns=['Pod', 'CPU', 'Memory', 'Pending'])
# item2 = pd.DataFrame(data=[['B1', 2, 4, True], ['B2', 4, 4, False], ['B3', 6, 8, False], ['B4', 8, 10, False], ['B5', 10, 12, False]], columns=['Pod', 'CPU', 'Memory', 'Pending'])

# all_task = pd.concat([item,item2]).reset_index(drop=True)

# node_list = ['N1','N2','N3','N4']
# node_usage = ['N1','N2','N3','N4']
# limit_CPU = 8
# limit_MEM = 16
# gamma = 0.9
# knapsack = []

# def getQueue():
#     queue_list = pd.DataFrame()
#     queue_list = all_task[all_task['Pending'] == True]
#     return queue_list

class Placement():

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

    @staticmethod
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

    @staticmethod
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

    def check_state(self, q_table, placement, actions):

        if str(placement) not in q_table.index:
            q_table_new_row = pd.Series([np.NAN] * len(actions),
                                        index=q_table.columns,
                                        name=str(placement))
            already_placement = []
            for value in placement:
                for i in value:
                    already_placement = already_placement + [(x, i) for x in range(self.number_of_node)]
            for i in list(set(actions).difference(set(already_placement))):
                q_table_new_row[i] = 0
            return q_table.append(q_table_new_row)
        else:
            return q_table

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

    def env_reward(self, action, placement):

        node = action // len(self.item)
        req = action % len(self.item)
        placement_ = copy.deepcopy(placement)
        placement_[node] += [req]
        placement_[node].sort()
        done, reward = self.getscore(placement_)

        return reward, placement_, done

    def mu_policy(self, q_table, epsilon, nA, observation, actions):
        already_placement = []
        for value in observation:
            for i in value:
                already_placement = already_placement + [(x, i) for x in range(self.number_of_node)]
        actions_list = list(set(actions).difference(set(already_placement)))
        action_values = q_table.loc[str(observation), :]
        greedy_action = action_values.idxmax()
        probabilities = np.zeros(nA)
        for i in actions_list:
            node, req = i
            j = (node * len(self.item)) + req
            probabilities[j] = 1 / len(actions_list) * epsilon
        (node, req) = greedy_action
        greedy_action = (node * len(self.item)) + req
        probabilities[greedy_action] = probabilities[greedy_action] + (1 - epsilon)
        return probabilities

    def q_learning(self, num_episodes, discount_factor=1.0, alpha=0.7, epsilon=0.2):
        number_of_actions = len(self.actions)

        for i_episode in range(1, num_episodes + 1):
            placement = [[] for _ in range(self.number_of_node)]
            self.q_table = self.check_state(self.q_table, placement, self.actions)

            action = np.random.choice(number_of_actions,
                                      p=self.mu_policy(self.q_table,
                                                       epsilon,
                                                       number_of_actions,
                                                       placement,
                                                       self.actions))
            for t in itertools.count():
                node = action // len(self.item)
                req = action % len(self.item)
                action_index_name = (node, req)
                reward, next_placement, done = self.env_reward(action, placement)
                if done != "continue":
                    self.q_table.loc[str(placement)][action_index_name] = \
                        self.q_table.loc[str(placement)][action_index_name] + \
                        alpha * (reward +
                                 discount_factor * 100 -
                                 self.q_table.loc[str(placement)][action_index_name])
                    break
                self.q_table = self.check_state(self.q_table, next_placement, self.actions)
                self.q_table.loc[str(placement)][action_index_name] = \
                    self.q_table.loc[str(placement)][action_index_name] + \
                    alpha * (reward +
                             discount_factor * self.q_table.loc[str(next_placement), :].max() -
                             self.q_table.loc[str(placement)][action_index_name])
                placement = next_placement
                next_action = np.random.choice(number_of_actions,
                                               p=self.mu_policy(self.q_table,
                                                                epsilon,
                                                                number_of_actions,
                                                                next_placement,
                                                                self.actions))
                action = next_action
            if i_episode % 50 == 0:
                print("\rEpisode {}/{}. | ".format(i_episode, num_episodes), end="")
        print("\n")
        return self.q_table

    def pi_policy(self, observation):

        try:
            action_values = self.q_table.loc[str(observation), :]
            best_action = action_values.idxmax()
            node, req = best_action
            action = (node * len(self.item)) + req
            return np.eye(len(action_values))[action]
        except KeyError:
            return []

    def get_cur_placement(self):

        knapsack = [[] for _ in range(self.number_of_node)]
        number_of_actions = len(self.actions)
        actions_list = []

        action = np.random.choice(number_of_actions,
                                  p=self.pi_policy(knapsack))

        for t in itertools.count():
            actions_list.append(action)
            reward, next_knapsack, done = self.env_reward(action, knapsack)

            if done == "continue":
                p = self.pi_policy(next_knapsack)
                try:
                    next_action = np.random.choice(number_of_actions,
                                                   p=p)
                except:
                    print(number_of_actions)
                    print(p)

                action = next_action
                knapsack = next_knapsack
            elif done == "oom":
                print(done)
                break
            else:
                knapsack = next_knapsack
                break

        return knapsack, self.req_list, self.node_state, self.node_list


if __name__ == "__main__":

    req_placement = Placement(item=item_list, number_of_node=4, limit_W=node_resource)
    Q = req_placement.q_learning(num_episodes=1000, discount_factor=0.9, alpha=0.3, epsilon=0.25)
    placement_result = req_placement.get_cur_placement()
