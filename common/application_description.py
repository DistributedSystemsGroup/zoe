import logging

from common.exceptions import InvalidApplicationDescription

log = logging.getLogger(__name__)


class ZoeApplication:
    def __init__(self):
        self.name = ''
        self.version = 0
        self.will_end = True
        self.priority = 512
        self.requires_binary = False
        self.processes = []

    @classmethod
    def from_dict(cls, data):
        ret = cls()

        try:
            ret.version = int(data["version"])
        except ValueError:
            raise InvalidApplicationDescription(msg="version field should be an int")
        except KeyError:
            raise InvalidApplicationDescription(msg="Missing required key: version")

        required_keys = ['name', 'will_end', 'priority', 'requires_binary']
        for k in required_keys:
            try:
                setattr(ret, k, data[k])
            except KeyError:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            ret.will_end = bool(ret.will_end)
        except ValueError:
            raise InvalidApplicationDescription(msg="will_end field must be a boolean")

        try:
            ret.requires_binary = bool(ret.requires_binary)
        except ValueError:
            raise InvalidApplicationDescription(msg="requires_binary field must be a boolean")

        try:
            ret.priority = int(ret.priority)
        except ValueError:
            raise InvalidApplicationDescription(msg="priority field must be an int")
        if ret.priority < 0 or ret.priority > 1024:
            raise InvalidApplicationDescription(msg="priority must be between 0 and 1024")

        for p in data['processes']:
            ret.processes.append(ZoeApplicationProcess.from_dict(p))
        return ret

    def to_dict(self) -> dict:
        ret = {
            'name': self.name,
            'version': self.version,
            'will_end': self.will_end,
            'priority': self.priority,
            'processes': []
        }
        for p in self.processes:
            ret['processes'].append(p.to_dict())
        return ret

    def total_memory(self) -> int:
        memory = 0
        for p in self.processes:
            memory += p.required_resources['memory']
        return memory


class ZoeApplicationProcess:
    def __init__(self):
        self.name = ''
        self.version = 0
        self.docker_image = ''
        self.monitor = False  # if this process dies, the whole application is considered as complete and the execution is terminated
        self.ports = []
        self.required_resources = {}
        self.environment = []  # Environment variables to pass to Docker
        self.command = None  # Commandline to pass to the Docker container

    def to_dict(self) -> dict:
        ret = {
            'name': self.name,
            'version': self.version,
            'docker_image': self.docker_image,
            'monitor': self.monitor,
            'ports': self.ports.copy(),
            'required_resources': self.required_resources.copy(),
            'environment': self.environment.copy()
        }
        return ret

    @classmethod
    def from_dict(cls, data):
        ret = cls()
        try:
            ret.version = int(data["version"])
        except ValueError:
            raise InvalidApplicationDescription(msg="version field should be an int")
        except KeyError:
            raise InvalidApplicationDescription(msg="Missing required key: version")

        required_keys = ['name', 'docker_image', 'monitor']
        for k in required_keys:
            try:
                setattr(ret, k, data[k])
            except KeyError:
                raise InvalidApplicationDescription(msg="Missing required key: %s" % k)

        try:
            ret.monitor = bool(ret.monitor)
        except ValueError:
            raise InvalidApplicationDescription(msg="monitor field should be a boolean")

        if 'ports' not in data:
            raise InvalidApplicationDescription(msg="Missing required key: ports")
        if not hasattr(data['ports'], '__iter__'):
            raise InvalidApplicationDescription(msg='ports should be an iterable')
        for pp in data['ports']:
            if len(pp) != 3:
                raise InvalidApplicationDescription(msg="ports entries must contain exactly three elements (port_number, name, is_main_port)")
        ret.ports = data['ports'].copy()

        if 'required_resources' not in data:
            raise InvalidApplicationDescription(msg="Missing required key: required_resources")
        if not isinstance(data['required_resources'], dict):
            raise InvalidApplicationDescription(msg="required_resources should be a dictionary")
        if 'memory' not in data['required_resources']:
            raise InvalidApplicationDescription(msg="Missing required key: required_resources -> memory")

        ret.required_resources = data['required_resources'].copy()
        try:
            ret.required_resources['memory'] = int(ret.required_resources['memory'])
        except ValueError:
            raise InvalidApplicationDescription(msg="required_resources -> memory field should be an int")

        if 'environment' in data:
            if not hasattr(data['environment'], '__iter__'):
                raise InvalidApplicationDescription(msg='environment should be an iterable')
            ret.environment = data['environment'].copy()
            for n, v in ret.environment:
                if not isinstance(n, str):
                    raise InvalidApplicationDescription(msg='environment variable names must be strings: {}'.format(n))
                if not isinstance(v, str):
                    raise InvalidApplicationDescription(msg='environment variable values must be strings: {}'.format(v))

        if 'command' in data:
            ret.command = data['command']
        return ret
