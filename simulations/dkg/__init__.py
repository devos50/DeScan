"""
Contains simulations for the Decentralized Knowledge Graph.
"""
import os


def create_aggregate_result_files(exp_name):
    with open(os.path.join("data", "edge_searches_exp_%s.csv" % exp_name), "w") as out_file:
        out_file.write("peers,nb_size,offline_fraction,malicious_fraction,skip_graphs,replication_factor,total_searches,failed_searches\n")
    with open(os.path.join("data", "edge_search_latencies_exp_%s.csv" % exp_name), "w") as out_file:
        out_file.write("peers,nb_size,offline_fraction,malicious_fraction,skip_graphs,replication_factor,part,time\n")
    with open(os.path.join("data", "kg_stats_exp_%s.csv" % exp_name), "w") as out_file:
        out_file.write("peers,nb_size,offline_fraction,malicious_fraction,skip_graphs,replication_factor,peer,key,num_edges,storage_costs\n")
    with open(os.path.join("data", "search_hops_exp_%s.csv" % exp_name), "w") as out_file:
        out_file.write("peers,nb_size,hops,freq\n")
