# ML Pipeline Deployment and Scheduling

This project demonstrates how to deploy and schedule Pods in a machine learning pipeline using Kubernetes and a GA algorithm.

## Table of Contentss

- Deploy ML Pipeline
- GA Algorithm Scheduling
- Code Explanation
- Test the Scheduler

## Deploy ML Pipeline

First, use the following CRD file to deploy the ML Pipeline

## GA Algorithm Scheduling

When a Pod is in the Pending state, the following code will execute the GA algorithm to perform scheduling:

```python
def main():
    pod_dict = {}
    w = watch.Watch()
    for event in w.stream(k8sCoreV1api.list_namespaced_pod, "openfaas-fn"):
        if event['object'].status.phase == "Pending":
            try:
                object_now = json.loads(event['object'].metadata.annotations['com.openfaas.function.spec'])
                nodes = {
                    "node1": {"cpu": 8.0, "memory": 16384},
                    "node2": {"cpu": 8.0, "memory": 16384},
                    "node3": {"cpu": 8.0, "memory": 16384},
                }
                pod_dict[event['object'].metadata.name] = object_now['limits']
                best_solution, unassigned_pods = ga_placement(pods=pod_dict, nodes=nodes)
                
                node_usage = {node: {"cpu": 0.0, "memory": 0, "pods": []} for node in nodes}

                for pod, node_index in zip(pod_dict.keys(), best_solution):
                    node_name = list(nodes.keys())[node_index]
                    node_usage[node_name]["pods"].append(pod)
                    node_usage[node_name]["cpu"] += pod_dict[pod]["cpu"]
                    node_usage[node_name]["memory"] += pod_dict[pod]["memory"]

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
```

## Code Explanation

1. **Monitor Pending Pods**:
   - Use `watch.Watch()` to monitor the status of Pods in the `openfaas-fn` namespace.
   - When a Pod is in the Pending state, extract its resource requirements.

2. **Define Node Resources**:
   - Define three nodes, each with 8 CPU cores and 16GB of memory.

3. **GA Algorithm Scheduling**:
   - Use the GA algorithm to calculate the most suitable node for each Pod.
   - Initialize node usage and assign Pods to the corresponding nodes.

4. **Remove Unassigned Pods**:
   - Remove unassigned Pods from the node usage.

5. **Bind Pods to Nodes**:
   - Use the `bind_pod_to_node` function to bind Pods to the calculated nodes.

## Test the Scheduler

To run the scheduler, follow these steps:

1. Create a virtual environment:

    ```sh
    python3 -m venv .venv
    ```

2. Activate the virtual environment:

    ```sh
    source ./.venv/bin/activate
    ```

3. Run the GA scheduler script:

    ```sh
    python3 ./MLTaskScheduler/GA/ga_new.py
    ```
