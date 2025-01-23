from kubernetes import client, config, watch
import json
from GA.ga_new import ga_placement

config.load_kube_config()
k8sCoreV1api = client.CoreV1Api()
scheduler_name = 'test'


def get_node():
    nodeInstance = []
    nodeInstanceList = k8sCoreV1api.list_node()
    for i in nodeInstanceList.items:
        nodeInstance.append(i.metadata.name)
    return nodeInstance

def get_node_resource():
    nodes = k8sCoreV1api.list_node().items
    nodeInstance= []
    for node in nodes:
        node_name = node.metadata.name
        resources = node.status.allocatable
        cpu = resources.get("cpu")
        memory = resources.get("memory")
        nodeInstance.append({
            "name": node_name,
            "cpu": cpu,
            "mem": memory
        })
    
    return nodeInstance

"""
用什麼部署pod openfaas??

先將pending的pod以及pod的資源的使用量(limit)取出來。
pods = {
        "pod1": {"cpu": 1.0, "memory": 512},
        "pod2": {"cpu": 2.0, "memory": 1024},
        "pod3": {"cpu": 0.5, "memory": 256},
        "pod4": {"cpu": 1.5, "memory": 2048},
        ...   
}
"""
def get_pending_pod():
    pending_pod = []
    w = watch.Watch()
    for event in w.stream(k8sCoreV1api.list_namespaced_pod, "default"):
        # and event['object'].spec.scheduler_name == scheduler_name:
        if event['object'].status.phase == "Pending":
            try:
                print(event['object'].metadata.name)
                # object_now = json.loads(event['object'].metadata.annotations['com.openfaas.function.spec'])
                # type(object_now['limits'])
                print(event['object'].metadata.limits)
                # res = scheduler(event['object'].metadata.name,random.choice(nodes_available()))
            except client.rest.ApiException as e:
                print(json.load(e.body)["message"])

def bind_pod_to_node(pod_name, node_name):
    config.load_kube_config()
    api = client.CoreV1Api()

    body = client.V1Binding(
        metadata=client.V1ObjectMeta(name=pod_name),
        target=client.V1ObjectReference(
            api_version="v1",
            kind="Node",
            name=node_name
        )
    )
    api.create_namespaced_binding(namespace="default", body=body)

"""
先設定固定節點的資源，我們拿8成核心和16GB記憶體的資源來部署，剩下兩成保留用於static pod以及避免滿載(實際看節點規格決定就好)
nodes = {
    "node1": {"cpu": 8.0, "memory": 16384},  # 節點1，8 CPU核心，16GB記憶體
    "node2": {"cpu": 8.0, "memory": 16384},  # 節點2，8 CPU核心，16GB記憶體
    "node3": {"cpu": 8.0, "memory": 16384},  # 節點3，8 CPU核心，16GB記憶體
}
pod的資源
pods = {
        "pod1": {"cpu": 1.0, "memory": 512},
        "pod2": {"cpu": 2.0, "memory": 1024},
    }
"""
def main():
    # api_response = k8sCoreV1api.read_node('kaip-3', pretty=True)
    # print(api_response)
    pod_dict = {}
    w = watch.Watch()
    for event in w.stream(k8sCoreV1api.list_namespaced_pod, "openfaas-fn"):
        """
        event 格式示意如下：
        {
            "object": {
                "apiVersion": "v1",
                "kind": "Pod",            // 這裡僅舉例為 Pod，實際也可能是 Deployment、Service 等其它物件
                "metadata": {
                "name": "my-function-pod",   // Pod 名稱
                "namespace": "openfaas-fn",  // 所在命名空間
                "annotations": {
                    "com.openfaas.function.spec": "{\n  \"limits\": {\n    \"cpu\": \"200m\",\n    \"memory\": \"128Mi\"\n  },\n  \"otherKey\": \"someValue\"\n}"
                },
                "labels": {
                    "faas_function": "my-function"
                }
                // 其它與 metadata 相關的資訊
                },
                "spec": {
                // 這裡可能包含 Containers、Volumes 等 Pod 規格
                },
                "status": {
                // 這裡可能包含 Pod 狀態，如 phase、podIP 等
                }
            }
        }
        """
        # and event['object'].spec.scheduler_name == scheduler_name:
        if event['object'].status.phase == "Pending":
            try:
                # print(event['object'].metadata.name)
                object_now = json.loads(event['object'].metadata.annotations['com.openfaas.function.spec'])
                print(object_now)
                nodes = {
                    "node1": {"cpu": 8.0, "memory": 16384},  # 節點1，8 CPU核心，16GB記憶體
                    "node2": {"cpu": 8.0, "memory": 16384},  # 節點2，8 CPU核心，16GB記憶體
                    "node3": {"cpu": 8.0, "memory": 16384},  # 節點3，8 CPU核心，16GB記憶體
                }
                pod_dict[event['object'].metadata.name] = object_now['limits']
                best_solution, unassigned_pods = ga_placement(pods=pod_dict, nodes=nodes)
                node_usage = {node: {"cpu": 0.0, "memory": 0, "pods": []} for node in nodes}  # 初始化節點使用情況

                for pod, node_index in zip(pod_dict.keys(), best_solution):  # 將 Pod 分配到節點
                    node_name = list(nodes.keys())[node_index]
                    node_usage[node_name]["pods"].append(pod)
                    node_usage[node_name]["cpu"] += pod_dict[pod]["cpu"]
                    node_usage[node_name]["memory"] += pod_dict[pod]["memory"]

                # 從節點使用情況中移除未分配的pod
                for pod in unassigned_pods:
                    for node in node_usage.values():
                        if pod in node["pods"]:
                            node["pods"].remove(pod)
                            node["cpu"] -= pod_dict[pod]["cpu"]
                            node["memory"] -= pod_dict[pod]["memory"]

                for node, usage in node_usage.items():
                    bind_pod_to_node(pod_name=usage["pods"], node_name=node)

                # type(object_now['limits'])
                # print(event['object'].metadata.limits)
                # res = scheduler(event['object'].metadata.name,random.choice(nodes_available()))
            except client.rest.ApiException as e:
                print('1111111')
                print(json.load(e.body)["message"])

def test():
    pod_dict = {}
    w = watch.Watch()
    for event in w.stream(k8sCoreV1api.list_namespaced_pod, "openfaas-fn"):
        # and event['object'].spec.scheduler_name == scheduler_name:
        if event['object'].status.phase == "Pending":
            try:
                # object_now = json.loads(event['object'].metadata.annotations['com.openfaas.function.spec'])
                nodes = {
                    "node1": {"cpu": 8.0, "memory": 16384},  # 節點1，8 CPU核心，16GB記憶體
                    "node2": {"cpu": 8.0, "memory": 16384},  # 節點2，8 CPU核心，16GB記憶體
                    "node3": {"cpu": 8.0, "memory": 16384},  # 節點3，8 CPU核心，16GB記憶體
                }
                # pod_dict[event['object'].metadata.name] = object_now['limits']
                pod_dict = {
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
                best_solution, unassigned_pods = ga_placement(pods=pod_dict, nodes=nodes)
                node_usage = {node: {"cpu": 0.0, "memory": 0, "pods": []} for node in nodes}  # 初始化節點使用情況

                for pod, node_index in zip(pod_dict.keys(), best_solution):  # 將 Pod 分配到節點
                    node_name = list(nodes.keys())[node_index]
                    node_usage[node_name]["pods"].append(pod)
                    node_usage[node_name]["cpu"] += pod_dict[pod]["cpu"]
                    node_usage[node_name]["memory"] += pod_dict[pod]["memory"]

                # 從節點使用情況中移除未分配的pod
                for pod in unassigned_pods:
                    for node in node_usage.values():
                        if pod in node["pods"]:
                            node["pods"].remove(pod)
                            node["cpu"] -= pod_dict[pod]["cpu"]
                            node["memory"] -= pod_dict[pod]["memory"]

                for node, usage in node_usage.items():
                    bind_pod_to_node(pod_name=usage["pods"], node_name=node)

            except client.rest.ApiException as e:
                print(json.load(e.body)["message"])


if __name__ == '__main__':
    main()
    # nodeInstance = []
    # nodeInstanceList = k8sCoreV1api.list_node()
    # for i in nodeInstanceList.items:
    #     print(i)
    #     nodeInstance.append(i.metadata.name)
    # print(nodeInstanceList)