import { Serializable } from '../interfaces/serializable';
import { ServiceDescription } from './service-description';
import { Port } from './port';
import { Resource } from './resource';

export class Service implements Serializable<Service> {
    dockerId: string;
    dockerStatus: string;
    errorMessage: string;
    executionId: number;
    id: number;
    ipAddress: string;
    status: string;
    name: string;
    serviceGroup: string;

    dockerImage: string;
    environment: string[][];
    essentialCount: number;
    monitor: boolean;
    //networks: string[];
    ports: Port[];
    requiredResources: Resource;
    startupOrder: number;
    totalCount: number;
    proxyAddress: string;

    description: ServiceDescription;

    rawObject: Object;

    link(): Link {
        if (this.ipAddress && this.description && this.proxyAddress) {
            if (this.description.ports && this.description.ports.length > 0) {
                let port = this.description.ports[0];

                var link = new Link();
                link.name = port.name;
                link.url = this.proxyAddress;

                return link;
            }
        }

        return null;
    }

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('name')) {
            this.name = input.name;
        }

        if (input.hasOwnProperty('service_group')) {
            this.serviceGroup = input.service_group;
        }

        if (input.hasOwnProperty('docker_status')) {
            this.dockerStatus = input.docker_status;
        }

        if (input.hasOwnProperty('docker_image')) {
            this.dockerImage = input.docker_image;
        }

        if (input.hasOwnProperty('environment')) {
            this.environment = [];

            for (let environments of input.environment) {
                var temp: string[] = [];

                for (let enviroment of environments) {
                    temp.push(enviroment);
                }

                this.environment.push(temp);
            }
        }

        if (input.hasOwnProperty('status')) {
            this.status = input.status;
        }

        if (input.hasOwnProperty('error_message')) {
            this.errorMessage = input.error_message;
        }

        if (input.hasOwnProperty('execution_id')) {
            this.executionId = input.execution_id;
        }

        if (input.hasOwnProperty('ip_address')) {
            this.ipAddress = input.ip_address;
        }

        if (input.hasOwnProperty('id')) {
            this.id = input.id;
        }

        if (input.hasOwnProperty('docker_id')) {
            this.dockerId = input.docker_id;
        }

        if (input.hasOwnProperty('description')) {
            this.description = new ServiceDescription().deserialize(input.description);
        }

        if (input.hasOwnProperty('essential_count')) {
            this.essentialCount = input.essential_count;
        }

        if (input.hasOwnProperty('monitor')) {
            this.monitor = input.monitor;
        }

        if (input.hasOwnProperty('ports')) {
            this.ports = [];

            for (let port of input.ports) {
                this.ports.push(new Port().deserialize(port));
            }
        }

        if (input.hasOwnProperty('required_resources')) {
            this.requiredResources = new Resource().deserialize(input.required_resources);
        }

        if (input.hasOwnProperty('startup_order')) {
            this.startupOrder = input.startup_order;
        }

        if (input.hasOwnProperty('total_count')) {
            this.totalCount = input.total_count;
        }

        if (input.hasOwnProperty('proxy_address')) {
            this.proxyAddress = input.proxy_address;
        }

        return this;
    }
}

export class Link {
    name: string;
    url: string;
}
