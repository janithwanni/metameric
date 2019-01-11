cimport cython
cimport numpy as np
import numpy as np


@cython.wraparound(False)
@cython.boundscheck(False)
def strength_new(np.ndarray[np.float64_t, ndim=1] activations,
                 np.ndarray[np.float64_t, ndim=1] resting,
                 list conn,
                 list mtrs,
                 np.float64_t minimum,
                 np.float64_t decay,
                 np.float64_t step_size):
    """Fast function for calculating association strength."""
    cdef int i
    cdef int n_neurons = activations.shape[0]
    cdef np.ndarray[np.float64_t, ndim=1] net = np.zeros([n_neurons],
                                                         dtype=np.float64)
    net += calc_net(activations, net, conn, mtrs)
    for i in range(n_neurons):
        if net[i] > 0:
            net[i] *= 1.0 - activations[i]
        else:
            net[i] *= activations[i] - minimum
        net[i] -= decay * (activations[i] - resting[i])

    return net * step_size



@cython.wraparound(False)
@cython.boundscheck(False)
def calc_net(np.ndarray[np.float64_t, ndim=1] activations,
             np.ndarray[np.float64_t, ndim=1] net,
             list conn,
             list mtrs):
    """Fast function for calculating association strength."""
    cdef int i, j, z
    cdef int n_neurons = activations.shape[0]

    cdef np.ndarray[np.float64_t, ndim=1] c
    cdef np.ndarray[np.float64_t, ndim=2] mtr
    # There are as many conn as mtr.
    for z in range(len(conn)):
        c = conn[z]
        mtr = mtrs[z]
        for i in range(c.shape[0]):
            if c[i] > 0:
                for j in range(n_neurons):
                    net[j] += c[i] * mtr[i, j]

    return net
