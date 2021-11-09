from os.path import join, dirname
import json

_DIRNAME = dirname(__file__)

with open(join(_DIRNAME, "config_swarm.json"), "r") as f:
    CONFIG_SWARM = json.load(f)

with open(join(_DIRNAME, "config_aeolus.json"), "r") as f:
    CONFIG_AEOLUS = json.load(f)
