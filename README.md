## DeScan: Censorship-Resistant Indexing and Search for Web3

DeScan is a censorship-resistant indexing and search engine for Web3 transactions.
The projects' aim is to offer a decentralized alternative to storing and searching Web3 transactions.
DeScan achieves this by having users index their local Web3 transactions.
These transactions are organized in a Knowledge Graph.
Elements of the knowledge graph are stored amongst users and this process is coordinated by maintaining a Skip Graph overlay.
The figure below provides the architectural overview of DeScan.

TODO insert figure with architectural overview

DeScan is built using the [IPv8 networking library](https://github.com/tribler/py-ipv8) which should also be installed prior to running DeScan.
Peer-to-peer communication proceeds using the EVA protocol, a binary transfer protocol based on TFTP.
Full technical details can be found in this publicly available technical report.

### Project Status

This repository contains a proof-of-concept implementation of DeScan.
This implementation has been evaluated extensively using simulations and various scenarios.
A key next milestone of the DeScan project would be a deployment.

### Organization

TODO

### Running the Tests

The DeScan repository contains unit tests to help verifying the correctness of the different components.
You can run these tests as follows:

TODO

### Reproducing the Experiments

In our technical report we have evaluated the scalability, robustness and censorship-resistance of DeScan.
All simulations can be found in the `simulations` directory.
The README.md file there provides detailed instructions on the simulation structure and on how to run these simulations.

### Contributing to DeScan

Contributions to DeScan are very much welcomed!
Feel free to create a new issue or open a pull request if you wish to make code contributions.

### Reference

If you found DeScan useful, please cite it as follows:

TODO