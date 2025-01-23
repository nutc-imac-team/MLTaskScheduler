import numpy as np
import pandas as pd
import time

N_STATES = 6   # The width of the 1D world
ACTIONS = ['left', 'right']     # Available actions for the explorer
EPSILON = 0.9   # Greedy rate
ALPHA = 0.1     # Learning rate
GAMMA = 0.9     # Reward discount factor
MAX_EPISODES = 13   # Maximum number of episodes
FRESH_TIME = 0.3    # Time interval for each step

def build_q_table(n_states, actions):
    table = pd.DataFrame(
        np.zeros((n_states, len(actions))),     # Initialize q_table with all zeros
        columns=actions,    # Columns correspond to action names
    )
    return table

# Select an action in a given state
def choose_action(state, q_table):
    state_actions = q_table.iloc[state, :]  # Get all action values for the current state
    if (np.random.uniform() > EPSILON) or (state_actions.all() == 0):  # Non-greedy or this state hasn't been explored
        action_name = np.random.choice(ACTIONS)
    else:
        action_name = state_actions.argmax()    # Greedy mode
    return action_name

def get_env_feedback(S, A):
    # This is how the agent interacts with the environment
    if A == 'right':    # Move right
        if S == N_STATES - 2:   # Reaching the terminal
            S_ = 'terminal'
            R = 1
        else:
            S_ = S + 1
            R = 0
    else:   # Move left
        R = 0
        if S == 0:
            S_ = S  # Hit the wall
        else:
            S_ = S - 1
    return S_, R

def update_env(S, episode, step_counter):
    # This is how the environment is updated
    env_list = ['-']*(N_STATES-1) + ['T']   # '---------T' represents the environment
    if S == 'terminal':
        interaction = 'Episode %s: total_steps = %s' % (episode+1, step_counter)
        print('\r{}'.format(interaction), end='')
        time.sleep(2)
        print('\r                                ', end='')
    else:
        env_list[S] = 'o'
        interaction = ''.join(env_list)
        print('\r{}'.format(interaction), end='')
        time.sleep(FRESH_TIME)

def rl():
    q_table = build_q_table(N_STATES, ACTIONS)  # Initialize q_table
    for episode in range(MAX_EPISODES):     # Iterate through episodes
        step_counter = 0
        S = 0   # Initial state in each episode
        is_terminated = False   # Whether the episode ends
        update_env(S, episode, step_counter)    # Update the environment
        while not is_terminated:
            A = choose_action(S, q_table)   # Choose an action
            S_, R = get_env_feedback(S, A)  # Take action and receive feedback from the environment
            q_predict = q_table.loc[S, A]    # Predicted Q value for (state, action)
            if S_ != 'terminal':
                q_target = R + GAMMA * q_table.iloc[S_, :].max()   # Actual Q value (if episode is not over)
            else:
                q_target = R     # Actual Q value (if episode ends)
                is_terminated = True    # Terminate the episode

            q_table.loc[S, A] += ALPHA * (q_target - q_predict)  # Update q_table
            S = S_  # Move explorer to the next state
            update_env(S, episode, step_counter+1)  # Update the environment
            step_counter += 1
    return q_table

if __name__ == "__main__":
    print(build_q_table(N_STATES, ACTIONS))
