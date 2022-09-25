import numpy as np

from pypop7.optimizers.ds.ds import DS


class HJ(DS):
    """Hooke-Jeeves direct (pattern) search method (HJ).

    .. note:: `HJ` is one of the most popular and most cited `DS` methods, originally published in one of
       the top-tier Computer Science journals (i.e., JACM) in 1961. Although sometimes it is still used to optimize
       *low-dimensional* black-box problems, it is **highly recommended** to first attempt other more advanced methods
       for large-scale black-box optimization.

    Parameters
    ----------
    problem : dict
              problem arguments with the following common settings (`keys`):
                * 'fitness_function' - objective function to be **minimized** (`func`),
                * 'ndim_problem'     - number of dimensionality (`int`),
                * 'upper_boundary'   - upper boundary of search range (`array_like`),
                * 'lower_boundary'   - lower boundary of search range (`array_like`).
    options : dict
              optimizer options with the following common settings (`keys`):
                * 'max_function_evaluations' - maximum of function evaluations (`int`, default: `np.Inf`),
                * 'max_runtime'              - maximal runtime (`float`, default: `np.Inf`),
                * 'seed_rng'                 - seed for random number generation needed to be *explicitly* set (`int`);
              and with the following particular settings (`keys`):
                * 'x'     - initial (starting) point (`array_like`),
                * 'sigma' - initial (global) step-size (`float`),
                * 'gamma' - decreasing factor of step-size (`float`, default: `0.5`).

    Examples
    --------
    Use the Pattern Search optimizer `HJ` to minimize the well-known test function
    `Rosenbrock <http://en.wikipedia.org/wiki/Rosenbrock_function>`_:

    .. code-block:: python
       :linenos:

       >>> import numpy
       >>> from pypop7.benchmarks.base_functions import rosenbrock  # function to be minimized
       >>> from pypop7.optimizers.ds.hj import HJ
       >>> problem = {'fitness_function': rosenbrock,  # define problem arguments
       ...            'ndim_problem': 2,
       ...            'lower_boundary': -5 * numpy.ones((2,)),
       ...            'upper_boundary': 5 * numpy.ones((2,))}
       >>> options = {'max_function_evaluations': 5000,  # set optimizer options
       ...            'seed_rng': 2022,
       ...            'x': 3 * numpy.ones((2,)),
       ...            'sigma': 0.1,
       ...            'verbose_frequency': 500}
       >>> hooke_jeeves = HJ(problem, options)  # initialize the optimizer class
       >>> results = hooke_jeeves.optimize()  # run the optimization process
       >>> # return the number of function evaluations and best-so-far fitness
       >>> print(f"HJ: {results['n_function_evaluations']}, {results['best_so_far_y']}")
       Hooke-Jeeves: 5000, 0.22119484961034389

    Furthermore, an interesting visualization of `HJ`'s search trajectory on a 2-dimensional test function is shown in
    `this GitHub link <https://github.com/Evolutionary-Intelligence/pypop/blob/main/docs/demo/demo_hj.gif>`_.

    Attributes
    ----------
    x     : `array_like`
            search point.
    sigma : `float`
            (global) step-size.
    gamma : `float`
            decreasing factor of step-size.

    References
    ----------
    Kochenderfer, M.J. and Wheeler, T.A., 2019.
    Algorithms for optimization.
    MIT Press.
    https://algorithmsbook.com/optimization/files/chapter-7.pdf
    (See Algorithm 7.5 (Page 104) for details.)

    Kaupe Jr, A.F., 1963.
    Algorithm 178: Direct search.
    Communications of the ACM, 6(6), pp.313-314.
    https://dl.acm.org/doi/pdf/10.1145/366604.366632

    Hooke, R. and Jeeves, T.A., 1961.
    “Direct search” solution of numerical and statistical problems.
    Journal of the ACM, 8(2), pp.212-229.
    https://dl.acm.org/doi/10.1145/321062.321069
    """
    def __init__(self, problem, options):
        DS.__init__(self, problem, options)
        self.gamma = options.get('gamma', 0.5)  # decreasing factor of step-size (γ)
        assert self.gamma > 0.0, f'`self.gamma` == {self.gamma}, but should > 0.0.'

    def initialize(self, args=None, is_restart=False):
        x = self._initialize_x(is_restart)  # initial point
        y = self._evaluate_fitness(x, args)  # fitness
        return x, y

    def iterate(self, args=None, x=None, fitness=None):
        improved, best_so_far_x, best_so_far_y = False, self.best_so_far_x, self.best_so_far_y
        for i in range(self.ndim_problem):  # to search along each coordinate
            for sgn in [-1, 1]:  # for two opponent directions
                if self._check_terminations():
                    return None
                xx = np.copy(best_so_far_x)
                xx[i] += sgn*self.sigma
                y = self._evaluate_fitness(xx, args)
                if self.saving_fitness:
                    fitness.append(y)
                if y < best_so_far_y:
                    best_so_far_y, improved = y, True
        if not improved:  # to decrease step-size if no improvement
            self.sigma *= self.gamma  # alpha
        return None

    def restart_initialize(self, args=None, x=None, y=None, fitness=None):
        self._fitness_list.append(self.best_so_far_y)
        is_restart_1, is_restart_2 = self.sigma < self.sigma_threshold, False
        if len(self._fitness_list) >= self.stagnation:
            is_restart_2 = (self._fitness_list[-self.stagnation] - self._fitness_list[-1]) < self.fitness_diff
        is_restart = bool(is_restart_1) or bool(is_restart_2)
        if is_restart:
            self.sigma = np.copy(self._sigma_bak)
            x, y = self.initialize(args, is_restart)
            if self.saving_fitness:
                fitness.append(y)
            self._fitness_list = [self.best_so_far_y]
            self._n_restart += 1
            self._print_verbose_info(y)
        return x, y

    def optimize(self, fitness_function=None, args=None):
        fitness = DS.optimize(self, fitness_function)
        x, y = self.initialize(args)
        if self.saving_fitness:
            fitness.append(y)
        self._print_verbose_info(y)
        while True:
            self.iterate(args, x, fitness)
            if self._check_terminations():
                break
            self._n_generations += 1
            self._print_verbose_info(y)
            if self.is_restart:
                x, y = self.restart_initialize(args, x, y, fitness)
        return self._collect_results(fitness)
