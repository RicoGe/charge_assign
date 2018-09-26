from abc import ABC
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np

from charge.util import AssignmentError
from charge.settings import MAX_BINS
from charge.nauty import Nauty
from charge.repository import ChargeSet, Repository

Atom = Any  # TODO: define this for the whole library
ChargeList = List[float]
WeightList = List[float]


class Collector(ABC):
    """Base class for collectors.

    Collectors query the repository for possible charges for each atom \
    in a molecule graph, and return a histogram describing the \
    distribution of the obtained charges for each atom.
    """
    def collect_values(
            self,
            graph: nx.Graph,
            iacm_data_only: bool,
            shells: List[int],
            **kwargs: Any
            ) -> Dict[Atom, Tuple[ChargeList, WeightList]]:
        """Collect charges for a graph's atoms.

        For each atom in the graph, return a list of possible \
        charges.

        Args:
            graph: The graph to collect charges for
            iacm_data_only: If true, do not fall back to plain elements
            shells: A list of shell sizes to try, in order, until a \
                    match is found.

        Raises:
            AssignmentError: If no charges could be found for at least \
                    one of the atoms in the molecule.

        Returns:
            A dictionary mapping atoms (nodes) in graph to a tuple of \
                    lists, the first with charges, the second with \
                    weights.
        """
        raise NotImplemented()


class MeanCollector(Collector):
    """A collector that returns the mean of all charges found.

    For each atom, this collector collects possible charges, then it \
    returns their mean.

    Args:
        repo: The Repository to collect charges from.
        rounding_digits: The number of decimals to round charges to.
    """
    def __init__(
            self,
            repository: Repository,
            rounding_digits: int,
            nauty: Optional[Nauty]=None
            ) -> None:
        """Create a MeanCollector.

        Args:
            repository: The repository to collect charges from
            rounding_digits: Number of digits to round charges to
            nauty: An external Nauty instance to use
        """
        self.__repository = repository
        self.__rounding_digits = rounding_digits
        self.__nauty = nauty if nauty is not None else Nauty()

    def collect_values(
            self,
            graph: nx.Graph,
            iacm_data_only: bool,
            shells: List[int],
            **kwargs: Any
            ) -> Dict[Atom, Tuple[ChargeList, WeightList]]:
        """Collect charges for a graph's atoms from a Repository.

        For each atom in the graph, this function will determine its \
        neighborhood, then collect all charges for such an atom with \
        such a neighborhood from the given repository. It does this \
        starting with the first shell size in shells, and continues \
        trying with subsequent shell sizes until at least one charge \
        is found (so you probably want to sort shells in descending \
        order). Finally, it calculates the mean of the collected \
        charges and rounds to the given precision.

        The nodes (atoms) in the graph are assumed to have an \
        'atom_type' data attribute associated with them containing the \
        elemental atom type and may have an 'iacm' attribute as well \
        with the IACM atom type.

        Args:
            graph: The graph to collect charges for
            iacm_data_only: If true, only use IACM data in the \
                    repository, and do not fall back to plain element \
                    data.
            shells: A list of shell sizes to try, in order, until a \
                    match is found.

        Raises:
            AssignmentError: If no charges could be found for at least \
                    one of the atoms in the molecule.

        Returns:
            A dictionary mapping atoms (nodes) in graph to a tuple of \
                    lists, the first with charges, the second with \
                    weights.
        """
        charges = dict()
        no_vals = list()

        for atom in graph.nodes():
            for shell_size in shells:
                atom_has_iacm = 'iacm' in graph.node[atom]
                attribute = 'iacm' if atom_has_iacm else 'atom_type'
                charges[atom] = self.__collect(
                        graph, atom, shell_size, attribute,
                        self.__repository.charges_iacm)

                if charges[atom] == [] and not iacm_data_only:
                    charges[atom] = self.__collect(
                            graph, atom, shell_size, 'atom_type',
                            self.__repository.charges_elem)

                if charges[atom] != []:
                    break
            else:
                no_vals.append(atom)

        if len(no_vals) > 0:
            err = 'Could not find charges for atoms {0}.'.format(', '.join(map(str, no_vals)))
            if not 0 in shells:
                err += ' Please retry with a smaller "shell" parameter.'
            raise AssignmentError(err)
        return charges

    def __collect(
            self,
            graph: nx.Graph,
            atom: Atom,
            shell_size: int,
            attribute: str,
            charges: ChargeSet
            ) -> Tuple[float, float]:
        """Collect charges for a particular atom."""
        if shell_size in charges:
            key = self.__nauty.canonize_neighborhood(graph, atom, shell_size, attribute)
            if key in charges[shell_size]:
                values = charges[shell_size][key]
                mean_charge = round(float(np.mean(values)), self.__rounding_digits)
                return [mean_charge], [1.0]
        return []


class HistogramCollector(Collector):
    """A collector that returns a histogram of all charges found.

    For each atom, this collector collects possible charges, then it \
    creates a histogram, with each bin becoming a kind of meta-charge \
    in a coarse-grained version of the original list. It returns these \
    meta-charges.

    Args:
        repository: The Repository to collect charges from.
        rounding_digits: The number of decimals to round charges to.
    """
    def __init__(
            self,
            repository: Repository,
            rounding_digits: int,
            nauty: Optional[Nauty]=None
            ) -> None:
        self.__repository = repository
        self.__rounding_digits = rounding_digits
        self.__nauty = nauty if nauty is not None else Nauty()

    def collect_values(
            self,
            graph: nx.Graph,
            iacm_data_only: bool,
            shells: List[int],
            **kwargs: Any
            ) -> Dict[Atom, Tuple[ChargeList, WeightList]]:
        """Collect charges for a graph's atoms from a Repository.

        For each atom in the graph, this function will determine its \
        neighborhood, then collect all charges for such an atom with \
        such a neighborhood from the given repository. It does this \
        starting with the first shell size in shells, and continues \
        trying with subsequent shell sizes until at least one charge \
        is found (so you probably want to sort shells in descending \
        order). Finally, it summarizes the found charges using a \
        histogram, and returns the course-grained surrogate charges.

        The nodes (atoms) in the graph are assumed to have an \
        'atom_type' data attribute associated with them containing the \
        elemental atom type and may have an 'iacm' attribute as well \
        with the IACM atom type.

        Args:
            graph: The graph to collect charges for
            iacm_data_only: If true, only use IACM data in the \
                    repository, and do not fall back to plain element \
                    data.
            shells: A list of shell sizes to try, in order, until a \
                    match is found.

        Raises:
            AssignmentError: If no charges could be found for at least \
                    one of the atoms in the molecule.

        Returns:
            A dictionary mapping atoms (nodes) in graph to lists of \
                    charges and their weights. The list will be empty \
                    if no charge is found.
        """
        histograms = dict()
        no_vals = list()

        max_bins = max(int(kwargs['max_bins']), 1) if 'max_bins' in kwargs else MAX_BINS

        for atom in graph.nodes():
            for shell in shells:
                if shell in self.__repository.charges_iacm:
                    key = self.__nauty.canonize_neighborhood(
                            graph, atom, shell,
                            color_key='iacm' if 'iacm' in graph.node[atom] else 'atom_type')
                    if key in self.__repository.charges_iacm[shell]:
                        charges = self.__repository.charges_iacm[shell][key]
                        histograms[atom] = self.__calculate_histogram(
                                charges, max_bins)
                        break
                elif not iacm_data_only:
                    if shell in self.__repository.charges_elem:
                        key = self.__nauty.canonize_neighborhood(graph, atom, shell)
                        if key in self.__repository.charges_elem[shell]:
                            charges = self.__repository.charges_elem[shell][key]
                            histograms[atom] = self.__calculate_histogram(
                                    charges, max_bins)
                            break
            else:
                no_vals.append(atom)
        # collect charges from first shell size that gives a match, iacm if possible, elem otherwise unless disabled
        # if no matches at any shell size, add to no_vals

        if len(no_vals) > 0:
            err = 'Could not find charges for atoms {0}.'.format(', '.join(map(str, no_vals)))
            if not 0 in shells:
                err += (' Please retry with a smaller "shell" parameter'
                        ' or a SimpleCharger.')
            else:
                err += ' Please retry with a SimpleCharger.'
            raise AssignmentError(err)

        return histograms

    def __calculate_histogram(
            self,
            charges: ChargeList,
            max_bins: int
            ) -> Tuple[ChargeList, WeightList]:
        """Create a histogram from a raw list of charges.

        Histogram bins will be chosen so that:
            - They are all equally wide
            - Their centers fall on n-significant-digit numbers,
                according to self.__rounding_digits
            - Their widths are n-significant-digit numbers,
                according to self.__rounding_digits
            - There are at most max_bins non-zero bins

        Only non-empty bins will be returned.

        Args:
            charges: A list of charges to process into a histogram
            max_bins: The maximum number of bins the histogram should have
        """
        def round_to(x, grain, up):
            # rounds to nearest int, with 0.5 rounded down
            return ceil((x / grain) - 0.5) * grain

        grain = 10**(-self.__rounding_digits)
        print(charges, max_bins, grain)
        spacing = 0
        num_bins = max_bins + 1
        while num_bins > max_bins:
            spacing += 1
            step = grain * spacing

            min_charge_bin = round_to(min(charges), step, False)
            max_charge_bin = round_to(max(charges), step, True)
            # add half a step to include the last value
            bin_centers = np.arange(min_charge_bin, max_charge_bin + 0.5*step, step)
            print(bin_centers)

            min_bin_edge = min_charge_bin - 0.5*step
            max_bin_edge = max_charge_bin + 0.5*step
            # add half a step to include the last value
            bin_edges = np.arange(min_bin_edge, max_bin_edge + 0.5*step, step)
            # extend a bit to compensate for round-off error
            bin_edges[-1] += 1e-15
            print(bin_edges)

            counts, _ = np.histogram(charges, bins=bin_edges)
            num_bins = np.count_nonzero(counts)
            print(counts)
            print(num_bins)

        nonzero_bins = np.nonzero(counts)
        counts = list(counts[nonzero_bins])
        bin_centers = list(bin_centers[nonzero_bins])
        print(bin_centers, counts)
        print()

        return bin_centers, counts