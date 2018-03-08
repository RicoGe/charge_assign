import networkx as nx
import pytest

from charge.bond_type import BondType

# Fixtures for testing loading and saving to and from various
# formats.

@pytest.fixture
def ref_graph_attributes():
    return {
        'group_charges': {0: 0.0}
        }


@pytest.fixture
def ref_graph_nodes():
    return [(1, {'atom_type': 'C', 'label': 'C1', 'charge_group': 0}),
            (2, {'atom_type': 'HC', 'label': 'H1', 'charge_group': 0}),
            (3, {'atom_type': 'HC', 'label': 'H2', 'charge_group': 0}),
            (4, {'atom_type': 'HC', 'label': 'H3', 'charge_group': 0}),
            (5, {'atom_type': 'HC', 'label': 'H4', 'charge_group': 0})]


@pytest.fixture
def ref_graph_edges():
    return [(1, 2, {'bond_type': BondType.UNKNOWN}),
            (1, 3, {'bond_type': BondType.UNKNOWN}),
            (1, 4, {'bond_type': BondType.UNKNOWN}),
            (1, 5, {'bond_type': BondType.UNKNOWN})]


@pytest.fixture
def ref_graph(ref_graph_attributes, ref_graph_nodes, ref_graph_edges):
    graph = nx.Graph(**ref_graph_attributes)
    graph.add_nodes_from(ref_graph_nodes)
    graph.add_edges_from(ref_graph_edges)
    return graph


@pytest.fixture
def ref_graph_lgf():
    return ('@nodes\n'
            'label\tlabel2\tatomType\tinitColor\t\n'
            '1\tC1\t12\t0\t\n'
            '2\tH1\t20\t0\t\n'
            '3\tH2\t20\t0\t\n'
            '4\tH3\t20\t0\t\n'
            '5\tH4\t20\t0\t\n'
            '@edges\n'
            '\t\tlabel\t\n'
            '1\t2\t0\t\n'
            '1\t3\t1\t\n'
            '1\t4\t2\t\n'
            '1\t5\t3\t\n')


@pytest.fixture
def ref_graph_gml():
    return (
            'graph [\n'
            '  groupcharge0 0.0\n'
            '  node [\n'
            '    id 0\n'
            '    label "C1"\n'
            '    atomtype "C"\n'
            '    chargegroup 0\n'
            '  ]\n'
            '  node [\n'
            '    id 1\n'
            '    label "H1"\n'
            '    atomtype "HC"\n'
            '    chargegroup 0\n'
            '  ]\n'
            '  node [\n'
            '    id 2\n'
            '    label "H2"\n'
            '    atomtype "HC"\n'
            '    chargegroup 0\n'
            '  ]\n'
            '  node [\n'
            '    id 3\n'
            '    label "H3"\n'
            '    atomtype "HC"\n'
            '    chargegroup 0\n'
            '  ]\n'
            '  node [\n'
            '    id 4\n'
            '    label "H4"\n'
            '    atomtype "HC"\n'
            '    chargegroup 0\n'
            '  ]\n'
            '  edge [\n'
            '    source 0\n'
            '    target 1\n'
            '    bondtype "UNKNOWN"\n'
            '  ]\n'
            '  edge [\n'
            '    source 0\n'
            '    target 2\n'
            '    bondtype "UNKNOWN"\n'
            '  ]\n'
            '  edge [\n'
            '    source 0\n'
            '    target 3\n'
            '    bondtype "UNKNOWN"\n'
            '  ]\n'
            '  edge [\n'
            '    source 0\n'
            '    target 4\n'
            '    bondtype "UNKNOWN"\n'
            '  ]\n'
            ']')


@pytest.fixture
def ref_graph_itp():
    return (
            '[ atoms ]\n'
            ';  nr  type  atom total_charge\n'
            '    1     C    C1\n'
            '    2    HC    H1\n'
            '    3    HC    H2\n'
            '    4    HC    H3\n'
            '    5    HC    H4  ;  0.000\n'
            '[ pairs ]\n'
            ';  ai   aj\n'
            '    1    2\n'
            '    1    3\n'
            '    1    4\n'
            '    1    5\n')


@pytest.fixture
def ref_graph_rdkit(ref_graph_nodes, ref_graph_edges):
    from rdkit import Chem
    rdmol = Chem.RWMol()

    rdmol.SetDoubleProp('group_charge_0', 0.0)

    c = Chem.Atom('C')
    h1 = Chem.Atom('H')
    h2 = Chem.Atom('H')
    h3 = Chem.Atom('H')
    h4 = Chem.Atom('H')

    h1.SetProp('label', 'H1')
    h2.SetProp('label', 'H2')
    h3.SetProp('label', 'H3')
    h4.SetProp('label', 'H4')

    h1.SetProp('atom_type', 'HC')
    h2.SetProp('atom_type', 'HC')
    h3.SetProp('atom_type', 'HC')
    h4.SetProp('atom_type', 'HC')

    idx = dict()
    idx[c] = rdmol.AddAtom(c)
    idx[h1] = rdmol.AddAtom(h1)
    idx[h2] = rdmol.AddAtom(h2)
    idx[h3] = rdmol.AddAtom(h3)
    idx[h4] = rdmol.AddAtom(h4)

    rdmol.AddBond(idx[c], idx[h1])
    rdmol.AddBond(idx[c], idx[h2])
    rdmol.AddBond(idx[c], idx[h3])
    rdmol.AddBond(idx[c], idx[h4])

    return rdmol


@pytest.fixture
def ref_graph_nodes_shifted(ref_graph_nodes):
    from rdkit import Chem
    return [(v-1, data) for v, data in ref_graph_nodes]


@pytest.fixture
def ref_graph_edges_shifted(ref_graph_edges):
    from rdkit import Chem
    return [(u - 1, v - 1, {**{'rdkit_bond_type': Chem.BondType.UNSPECIFIED}, **data})
                for u, v, data in ref_graph_edges]


@pytest.fixture
def ref_graph_shifted(ref_graph_attributes, ref_graph_nodes_shifted, ref_graph_edges_shifted):
    graph = nx.Graph(**ref_graph_attributes)
    graph.add_nodes_from(ref_graph_nodes_shifted)
    graph.add_edges_from(ref_graph_edges_shifted)
    return graph