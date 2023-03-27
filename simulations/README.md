## DeScan Simulations

We have evaluated DeScan using a set of simulations.
These discrete-event simulations rely on the simulation primitive provided by IPv8, more information on this can be found [here](https://py-ipv8.readthedocs.io/en/latest/simulation/simulation_tutorial.html).
We provide simulation both for the Skip Graph (SG) structure and the full DeScan mechanism, that uses both the SG as well as maintains a decentralized knowledge graph.

### Running the Simulations

After ensuring all DeScan dependencies have been installed, you can run the simulations in this directory using the following commands:

```bash
export PYTHONPATH=$PWD  # Makes sure the simulations can find the DeScan modules
python simulations/skipgraph/search_simulation.py
```

The above commands will execute the `search_simulation.py` file which in turns starts an experiment with many peers that first construct and join the Skip Graph, and then conduct searches in it.
Your output should look something like this:

```
martijndevos@iMac-van-Martijn DeScan % python3 simulations/skipgraph/search_simulation.py
Created 100 peers...
Created 200 peers...
Created 300 peers...
Created 400 peers...
Created 500 peers...
Created 600 peers...
Created 700 peers...
Created 800 peers...
Created 900 peers...
Created 1000 peers...
Created 1100 peers...
Created 1200 peers...
Created 1300 peers...
Created 1400 peers...
Created 1500 peers...
Created 1600 peers...
Read latency matrix with 227 sites!
Latencies applied!
0 nodes joined the Skip Graphs!
100 nodes joined the Skip Graphs!
200 nodes joined the Skip Graphs!
300 nodes joined the Skip Graphs!
400 nodes joined the Skip Graphs!
500 nodes joined the Skip Graphs!
600 nodes joined the Skip Graphs!
700 nodes joined the Skip Graphs!
800 nodes joined the Skip Graphs!
900 nodes joined the Skip Graphs!
1000 nodes joined the Skip Graphs!
1100 nodes joined the Skip Graphs!
1200 nodes joined the Skip Graphs!
1300 nodes joined the Skip Graphs!
1400 nodes joined the Skip Graphs!
1500 nodes joined the Skip Graphs!
Skip Graph valid!
Extending Skip Graph neighbourhood size to 2
Completed 100 searches...
Completed 200 searches...
Completed 300 searches...
Completed 400 searches...
Completed 500 searches...
Completed 600 searches...
Completed 700 searches...
Completed 800 searches...
Completed 900 searches...
Completed 1000 searches...
Searches with incorrect result: 0
Simulation setup took 36.765254 seconds
Starting simulation with 1600 peers...
Simulation took 0.232867 seconds
Average search hops: 6.717000
```

You might see some warnings or errors related to `asyncio`.
These can usually be ignored as we are overwriting the default `asyncio` event loop with a custom one.

For convenience, we have also provided two bash files that can be executed to run the DeScan simulations with malicious and offline nodes enabled.

_The simulations are mainly CPU and memory bound and each simulation runs within a single process.
We have observed significant memory usage when experimenting with over 6'400 peers.
To ensure acceptable experiment durations, we suggest to run these experiments on a server with multiple CPU cores and at least 64 GB of memory._

### Customizing an Experiment

The settings of each experiment is prescribed by the variables in either the `SkipGraphSimulationSettings` or `DKGSimulationSettings` class, which both have `SimulationSettings` as base class.
We refer the interested reader to the documentation the files implementing these classes.

### Adding new Datasets

The experiments currently support two different datasets:
- Ethereum, where the simulations will read a file containing Ethereum blocks. The `blocks.json` file we used during the experiment consists of real Ethereum blocks and can be downloaded from [here](http://gofile.me/5flbT/1Masmx98t).
- Tribler, in which we parse torrent names using the [PTN library](https://pypi.org/project/parse-torrent-title/#description) and inject them into the network. A `torrents_100000.txt` file that can be used to play with this dataset can be downloaded from [here](http://gofile.me/5flbT/4733ZnZt4).

You can easily add your own datasets by modifying the `Dataset` enumerator (see `dkg/settings.py`).
Then you need to set the `data_file_name` property of your experiment to point to the file containing your data.
Then you need to write some logic to parse your data and setup the experiment correctly, see for example the following code in `simulations/dkg/dkg_simulation.py`:

```python3
...
        if self.settings.dataset == Dataset.TRIBLER:
            await self.setup_tribler_experiment()
        elif self.settings.dataset == Dataset.ETHEREUM:
            await self.setup_ethereum_experiment()
        else:
            raise RuntimeError("Unknown dataset %s" % self.settings.dataset)
...
```

Note that you need to write a custom rule to process each content item accordingly.
We refer to the implementation of the `setup_ethereum_experiment` function for more details on how to correctly setup your experiment with a custom dataset.

### Using Realistic Network Latencies

We have executed our experiments and simulations using a trace with realistic network latencies.
This becomes particularly important when one wants to evaluate the query durations of DeScan in realistic settings.
The `latencies.txt` file, included in the root of this repository, contains the average ping latencies in milliseconds between 227 different cities spread across the world.
This file has been constructed using the [network latencies observed by WonderNetwork](https://wondernetwork.com/pings).
You can run the experiments with these traces enabled by setting the `latencies_file` property in your simulation settings, for example:

```python
settings = DKGSimulationSettings()
settings.latencies_file = "latencies.txt"
```

To verify that this latency file is being used, you should see the following lines in your experiment output:

```
...
Read latency matrix with 227 sites!
Latencies applied!
...
```