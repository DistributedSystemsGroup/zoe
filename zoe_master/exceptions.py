# Copyright (c) 2016, Daniele Venzano
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

"""Exceptions that can be raised by the Zoe Master"""


class ZoeException(Exception):
    """
    A generic exception.
    """
    def __init__(self, message='Something happened'):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class ZoeStartExecutionRetryException(ZoeException):
    """Execution emitted in case the Execution failed to start for a transient error."""
    pass


class ZoeStartExecutionFatalException(ZoeException):
    """Execution emitted in case the Execution failed to start for a fatal error."""
    pass


class UnsupportedSchedulerPolicyError(ZoeException):
    """The configuration asks for a combination of scheduler and policy that is unsupported."""
    pass


class ZoeNotEnoughResourcesException(ZoeException):
    """Service failed to start due to not enough available resources."""
    pass
