import gym
import numpy as np

from blocks.bricks import Rectifier, MLP, Tanh, Identity
from blocks.initialization import IsotropicGaussian, Constant
from blocks.graph import ComputationGraph
from mujoco_py.mjtypes import POINTER, c_double
# from rllab.algos.trpo import TRPO
# from rllab.baselines.linear_feature_baseline import LinearFeatureBaseline
# from rllab.envs.gym_env import GymEnv
# from rllab.envs.normalized_env import normalize
# from rllab.policies.gaussian_mlp_policy import GaussianMLPPolicy
# from rllab.misc.instrument import run_experiment_lite
import theano.tensor as T

from buffer_ import Buffer, FIFO
from model import GAN

## Definiing the environnement
coeff = 0.85

# env = normalize(GymEnv('Swimmer-v1', force_reset=True))
env = gym.make('HalfCheetah-v1')
env2 = gym.make('HalfCheetah-v1')

# The second environnement models the real world
env2.env.model.opt.gravity = np.array([0, 0, -9.81*coeff]).ctypes.data_as(POINTER(c_double*3)).contents

def match_env(env1, env2):
    # make env1 state match env2 state (simulator matches real world)
    env1.env.set_state(env2.env.model.data.qpos.ravel(), env2.env.model.data.qvel.ravel())

## Defining the buffer
observation_dim = int(env.observation_space.shape[0])
action_dim = int(env.action_space.shape[0])
rng = np.random.RandomState(seed=23)
max_steps = 10000
history = 2

buffer_ = Buffer(observation_dim, action_dim, rng, history, max_steps)
prev_observations = FIFO(history)
actions = FIFO(history+1)  # also taking current action

## Defining the generative model
input_dim = (observation_dim+action_dim)*(history+1)
h = 128
discriminator_step_rule = None
generator_step_rule = None
nb_epoch = None

x = T.matrix('features')
y = T.matrix('transition')

G = MLP(
    activations=[Rectifier(), Rectifier(), Tanh()],
    dims=[input_dim, h, h, observation_dim],
    weights_init=IsotropicGaussian(std=0.05, mean=0),
    biases_init=Constant(0.02)
)
D = MLP(
    activations=[Rectifier(), Rectifier(), Identity()],
    dims=[observation_dim*(history+1), h, h, 1],
    weights_init=IsotropicGaussian(std=0.05, mean=0),
    biases_init=Constant(0.02)
)

generative_model = GAN(G, D)
generative_model.initialize()
obs_sim = env.observation_space.new_tensor_variable(
    'observations_simulator',
    # It should have 1 extra dimension since we want to represent a list of observations
    extra_dims=1
)
actions_var = env.action_space.new_tensor_variable(
    'actions',
    extra_dims=1
)
obs_real = env.observation_space.new_tensor_variable(
    'observations_real',
)
features = T.concatenate([obs_sim.flatten(), actions_var.flatten()])
cg = ComputationGraph(generative_model.compute_losses(features, obs_real))
import ipdb; ipdb.set_trace()
# for i_episode in range(1):
#     observation = env.reset()
#     observation2 = env2.reset()
#     match_env(env, env2)
#     prev_observations.push(observation)
#
#     for t in range(100):
#         env.render()
#         env2.render()
#
#         action = env.action_space.sample()
#         observation, reward, done, info = env.step(action)
#         observation2, reward2, done2, info2 = env2.step(action)
#
#         actions.push(action)
#         buffer_.add_sample(prev_observations.copy(), action.copy(), observation, observation2, reward, reward2)
#         prev_observations.push(observation2)
#         match_env(env, env2)
#
#         if done:
#             print("Episode finished after {} timesteps".format(t+1))
#             prev_observations.clear()
#             actions.clear()
#             break
# buffer_.save('/Tmp/alitaiga/sim-to-real/buffer-test')


# def run_task(*_):
#     policy = GaussianMLPPolicy(
#         env_spec=env.spec,
#         # The neural network policy should have two hidden layers, each with 32 hidden units.
#         hidden_sizes=(50, 50)
#     )
#
#     baseline = LinearFeatureBaseline(env_spec=env.spec)
#
#     algo = TRPO(
#         env=env,
#         policy=policy,
#         baseline=baseline,
#         batch_size=4000,
#         whole_paths=True,
#         max_path_length=100,
#         n_itr=40,
#         discount=0.99,
#         step_size=0.01,
#     )
#     algo.train()
#
# run_experiment_lite(
#     run_task,
#     # Number of parallel workers for sampling
#     n_parallel=1,
#     # Only keep the snapshot parameters for the last iteration
#     snapshot_mode="last",
#     # Specifies the seed for the experiment. If this is not provided, a random seed
#     # will be used
#     seed=1,
#     #plot=True,
# )
