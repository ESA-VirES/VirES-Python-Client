import json
from os.path import dirname, join

_DIRNAME = dirname(__file__)

with open(join(_DIRNAME, "config_swarm.json"), encoding="utf-8") as f:
    CONFIG_SWARM = json.load(f)

with open(join(_DIRNAME, "config_aeolus.json"), encoding="utf-8") as f:
    CONFIG_AEOLUS = json.load(f)
