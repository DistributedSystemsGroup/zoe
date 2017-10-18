# Copyright (c) 2017, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Dynamic allocation experimental code
"""

import logging

import GPy
import numpy as np

from zoe_master.backends.interface import get_platform_state

log = logging.getLogger(__name__)

MEMORY_HISTORY_POINT_COUNT_MAX = 400
PREDICTION_MIN_POINTS = 10

BUFFER_SIZE = 0.20


class DynamicReallocator:
    """The Dynamic reallocator with the predictor."""
    def __init__(self, scheduler):
        self.memory_history = {}
        self.state = scheduler.state
        self.scheduler = scheduler

    def do_dynamic_step(self):
        """Drive the entire dynamic allocation algorithm."""

        next_allocation = {}

        running_components = self.state.service_list(backend_status="started")
        platform_stats = get_platform_state(self.state, force_update=True)
        for rc in running_components:
            if rc.id in self.memory_history:
                self.memory_history[rc.id].append(self._get_component_memory_usage(rc, platform_stats))
            else:
                self.memory_history[rc.id] = [self._get_component_memory_usage(rc, platform_stats)]

        for rc in running_components:
            while len(self.memory_history[rc.id]) > MEMORY_HISTORY_POINT_COUNT_MAX:
                self.memory_history[rc.id].pop(0)

            if len(self.memory_history[rc.id]) < PREDICTION_MIN_POINTS:
                continue

            predicted_allocation, variance = self.gp_predict(self.memory_history[rc.id], restarts=5)
            # Next we add the buffer to compensate for the prediction error
            # For now we use a static value and we do not change it depending on the variance
            next_allocation[rc.id] = predicted_allocation + (1 + BUFFER_SIZE)  # + normalized_variance)

        # Before performing the simulation we have to sort the components per host.
        hosts = {}
        # TODO-Daniele: Group the components per host and per execution.
        # TODO-Daniele: The data structure is as follows:
        # TODO-Daniele: hosts = [
        # TODO-Daniele:     {
        # TODO-Daniele:         'execution_id': {
        # TODO-Daniele:             'core' : [list of running core components on the host bf_X],
        # TODO-Daniele:             'elastic' : [list of running elastic components on the host bf_X]
        # TODO-Daniele:          }
        # TODO-Daniele:      }
        # TODO-Daniele: ]
        # TODO-Daniele: In addition the list of running components must be sorted in ascending order by starting time

        executions_to_kill = []
        components_to_kill = []

        components_to_resize = []

        for host in hosts:
            mem_free = platform_stats.current_mem_free  # FIXME: Daniele
            for execution_id in host:
                execution = host[execution_id]

                tmp_mem_free = mem_free
                tmp_ids = []
                for core in execution['core']:
                    tmp_mem_free -= next_allocation[core.id]
                    tmp_ids.append(core.id)
                if tmp_mem_free < 0:
                    executions_to_kill.append(execution_id)
                else:
                    components_to_resize.extend(tmp_ids)
                    mem_free = tmp_mem_free

                    for elastic in execution['elastic']:
                        tmp_mem_free = mem_free - next_allocation[elastic.id]
                        if tmp_mem_free < 0:
                            components_to_kill.append(elastic.id)
                        else:
                            components_to_resize.append(elastic.id)
                            mem_free = tmp_mem_free

            # TODO-Daniele: From this point forward the code can be executed per host, or once all hosts have been processed. Your call.
            for execution_id in executions_to_kill:
                # TODO-Daniele: Kill the execution and put it back in the queue with the same priority.
                # TODO-Daniele: There is no need to cleaning up stuff here. A brute kill is sufficient.
                # TODO-Daniele: The call will be synchronous.
                # TODO-Daniele: I am assuming that killing a components does not take ages.
                pass
            for component_id in components_to_kill:
                # TODO-Daniele: Kill the component.
                # TODO-Daniele: Same argument as before
                pass

            for component_id in components_to_resize:
                new_allocation = next_allocation[component_id]
                # TODO-Daniele: Change the allocation of the component
                pass


            # TODO-Daniele: Trigger scheduler!

    def _get_component_memory_usage(self, component, platform_stats):
        for node in platform_stats.nodes:
            for cont_id, cont_stat in node.cont_stats.items():
                if cont_id == component.backend_id:
                    return cont_stat['memory_stats']['usage']

    def _generate_kernel(self, kernel_name, input_dim):
        if kernel_name == "RBF":
            return GPy.kern.RBF(input_dim=input_dim)
        elif kernel_name == "Matern52":
            return GPy.kern.Matern52(input_dim=input_dim)
        elif kernel_name == "Bias":
            return GPy.kern.Bias(input_dim=input_dim)
        elif kernel_name == "Exponential":
            return GPy.kern.Exponential(input_dim=input_dim)
        elif kernel_name == "Poly-5":
            return GPy.kern.Poly(input_dim=input_dim, order=5)
        elif kernel_name == "Poly-7":
            return GPy.kern.Poly(input_dim=input_dim, order=7)
        else:
            print("## ERROR: Kernel " + kernel_name + " not recognized.")
            return None

    def _pad_after(self, l, size, padding):
        return l + [padding] * abs((len(l) - size))

    def _pad_before(self, l, size, padding):
        return [padding] * abs((len(l) - size)) + l

    def gp_predict(self, timeseries, kernel_name="Exponential", hist_window_size=10, pred_window_size=1, restarts=0):
        """The predictor."""
        kernel = self._generate_kernel(kernel_name, hist_window_size + 1)

        N = len(timeseries)
        X = np.zeros((N, hist_window_size + 1))
        Y = np.array([[v] for v in timeseries])
        for i in range(N):
            X[i, 0] = i
            window_start = max(i - hist_window_size, 0)
            hist_window = timeseries[window_start:i]
            hist_window = self._pad_before(hist_window, hist_window_size, 0)
            X[i, 1:] = np.array([[v] for v in hist_window]).T

        # print(X)
        # NOTE: the most recent history goes at the last columns of X

        input_mean = np.mean(X, axis=0)
        input_stdv = np.std(X, axis=0)
        training_mean = np.mean(Y)
        training_stdv = np.std(Y)

        X = (X - input_mean) / input_stdv
        Y = (Y - training_mean) / training_stdv

        m = GPy.models.GPRegression(X, Y, kernel, mean_function=None, normalizer=False)
        m.Gaussian_noise.constrain_fixed()
        m.Gaussian_noise = 0.0001

        if restarts == 0:
            m.optimize()
        else:
            m.optimize_restarts(num_restarts=restarts, verbose=False)

        # print(m)
        Xtest = np.array([[v] for v in timeseries[i - hist_window_size:i]]).T
        Xtest = np.concatenate((np.array([[i]]), Xtest), axis=1)

        Xtest = np.zeros((pred_window_size, hist_window_size + 1))
        for i in range(N, N + pred_window_size):
            Xtest[i - N, 0] = i
            window_start = max(i - hist_window_size, 0)
            hist_window = timeseries[window_start:i]
            hist_window = self._pad_after(hist_window, hist_window_size, 0)
            Xtest[i - N, 1:] = np.array([[v] for v in hist_window]).T

        # print(Xtest)
        # NOTE: the most recent history goes at the last columns of Xtest

        (pred, var) = m.predict((Xtest - input_mean) / input_stdv)
        pred = pred * training_stdv + training_mean
        var = var * np.power(training_stdv, 2)
        return pred, var
