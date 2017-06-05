# MaxCount 1.0.0
An approximate Max#SAT solver by Daniel Fremont, Markus Rabe, and Sanjit Seshia.
For descriptions of the Max#SAT problem and our algorithm, see our AAAI 2017 paper [here](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2016/EECS-2016-169.html).

## Solver files and prerequisites

The solver consists of two Python scripts, which should be placed in the same folder.

* _maxcount.py_: main solver script
* _selfcomposition.py_: utility script to construct self-compositions


### CryptoMiniSat Python bindings

Your system must have an installation of the CryptoMiniSat Python bindings, available [here](https://github.com/msoos/cryptominisat/).


### SCALMC binaries

The solver expects a binary _scalmc_ present in the same directory implementing the UniGen2 algorithm of Chakraborty, Fremont, Meel, Seshia, and Vardi and the ApproxMC2 algorithm of Chakraborty, Meel, and Vardi.
The particular implementation used in our experiments is based on a prototype by Mate Soos and Kuldeep Meel which is pending publication.
In the mean time we provide binaries for several platforms in the _scalmc-binaries_ folder (if you cannot use any of the available binaries, please contact us).

The binaries are dynamically linked against the _Boost.ProgramOptions_ library.
To install that, on Linux systems try

    sudo apt-get install libboost-program-options-dev

On OS X systems try

    brew install boost

Please let us know if you experience problems when using the provided binaries. 

Alternatively, older implementations of UniGen2 and ApproxMC2 are available [here](https://bitbucket.org/kuldeepmeel/unigen) and [here](https://bitbucket.org/kuldeepmeel/approxmc) (although not integrated into a single binary). 

## Example problems
The _benchmarks_ folder contains benchmarks from our AAAI 2017 paper.
To test that MaxCount is set up correctly, you can try for example:

    python maxcount.py benchmarks/SyGuS/IssueServiceImpl.dimacs 2

This particular benchmark should take around 30 seconds and return an estimate of `1.964 x 2^28` (for reproducibility, MaxCount is deterministic; you can change the random seed with the option `--seed`).

## Input format

MaxCount accepts Max#SAT problems in a simple extension of the standard DIMACS CNF format.

	c max 1 2 3 4 5 0
	c ind 6 7 12 0
	p cnf 17 18
	3 1 0
	4 -1 0

Lines beginning `c max` specify a list of maximization variables, terminated with a `0`.
Lines beginning `c ind` likewise specify a set of counting/summation variables.
All variables not mentioned in such lines are existentially quantified.

## Using MaxCount

Running MaxCount is straightforward. The basic command is

	python maxcount.py formula.cnf k

where `formula.cnf` is a Max#SAT problem (in the format described above) and `k` is the number of copies of the formula to use in the self-composition (see our paper; in general, as `k` increases from 0 runtime increases and better results are obtained).

The solver outputs the estimated max-count, the corresponding witness (assignment to the maximization variables), and probabilistic bounds on the max-count.

	v -1 2 3 4 -5 0
	c Estimated max-count: 1.875 x 2^8
	c Max-count is <= 1.72649 x 2^12 with probability >= 0.6
	c Max-count is >= 1.875 x 2^7 with probability >= 0.9801

MaxCount accepts a variety of options, which can be viewed using the option `-h`. Many are primarily used for tuning the performance of the solver (see below), but three are used for specifying the desired tolerance and confidence of the solver's output:

* `--countingTolerance` controls how accurately each witness' count is estimated; assuming `k` is large enough that good witnesses are being sampled, further improvements in accuracy require decreasing this parameter
* `--upperBoundConfidence` specifies the confidence desired for the max-count upper bound; increasing this does not affect the runtime, but weakens the bound (i.e. the bound MaxCount returns is the strongest one true with at least the desired confidence given the outcome of the sampling and counting)
* `--lowerBoundConfidence` likewise specifies the confidence desired for the max-count lower bound; increasing this _can_ increase the runtime

MaxCount may return bounds with higher confidences than those specified by the options above, for example when a count can be computed exactly.

## Tuning MaxCount

MaxCount exposes many parameters useful in optimizing solver performance on particular types of problems.
Adjusting these parameters is always safe: the probabilistic bounds output by MaxCount are computed in such a way that they are correct for any values of the parameters.
Thus you are free to experiment with the settings to find which values give you the strongest bounds or the best performance.

### Sampling

Sampling is done using UniGen2, unless `k` is zero (in which case we sample uniformly at random from all assignments to the maximization variables).
The number of samples to generate is specified by the option `--samples`.
Increasing the number of samples may yield better results when `k` is small; conversely, if `k` is large enough then good results may be obtained with only a few samples.

The sampling tolerance may be adjusted with the option `--samplingKappa` (see the UniGen2 paper for the definition of _kappa_).
Using a looser tolerance (larger _kappa_) may improve sampling performance at the cost of decreased accuracy (unless the number of samples is correspondingly increased).

### Counting

A variety of techniques are used for projected counting:

* _brute force_: testing every possible assignment to the counting variables for satisfiability
* _Monte Carlo sampling_: testing many random assignments
* _enumeration_: enumerating satisfying assignments up to a threshold
* _hashing_: ApproxMC2

The first three techniques are simpler and faster than hashing, and brute force and enumeration can yield exact counts.
Thus MaxCount attempts them when possible, as this can often improve performance and accuracy while typically adding little overhead.
The precise procedure for deciding which techniques to use is as follows:

1. We check if the formula is UNSAT, returning immediately if so.
2. If the number of samples that would be used for Monte Carlo sampling is larger than the total number of assignments to the counting variables, we instead brute force test every assignment for satisfiability, obtaining an exact count.
3. Otherwise we do Monte Carlo sampling, obtaining an estimate of the solution density.
4. If the density is low enough that the count might be below the enumeration threshold, we try enumeration (thereby possibly obtaining an exact count).
5. If the density is high enough that it yields a count estimate accurate to within the required multiplicative error, we return that estimate.
6. Otherwise we count using hashing.

The number of Monte Carlo samples and the enumeration threshold to use can be specified by the options `--monteCarloSamples` and `--enumerationThreshold`.
These techniques can be disabled entirely by setting the corresponding options to zero (if both are disabled, MaxCount will always use hashing).