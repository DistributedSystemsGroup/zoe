import { Serializable } from '../interfaces/serializable';
import { Service } from './service';
import { Resource } from './resource';
import { Port } from './port';

export class ServiceDescription implements Serializable<ServiceDescription> {
    environment: string[][];
    requiredResources: Resource;
    startupOrder: number;
    ports: Port[];
    totalCount: number;
    monitor: boolean;
    essentialCount: number;
    dockerImage: string;
    name: string;

    willEnd: boolean;
    size: number;
    version: number;
    services: Service[];

    rawObject: Object;

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('name')) {
            this.name = input.name;
        }

        if (input.hasOwnProperty('startup_order')) {
            this.startupOrder = input.startup_order;
        }

        if (input.hasOwnProperty('will_end')) {
            this.willEnd = input.will_end;
        }

        if (input.hasOwnProperty('size')) {
            this.size = input.size;
        }

        if (input.hasOwnProperty('version')) {
            this.version = input.version;
        }

        if (input.hasOwnProperty('resources')) {
            this.requiredResources = new Resource().deserialize(input.resources);
        }

        if (input.hasOwnProperty('environment')) {
            this.environment = [];

            for (let environments of input.environment) {
                var temp: string[] = [];

                for (let enviroment of environments) {
                    temp.push(enviroment);
                }

                this.environment.push(temp)
            }
        }

        if (input.hasOwnProperty('monitor')) {
            this.monitor = input.monitor;
        }

        if (input.hasOwnProperty('essential_count')) {
            this.essentialCount = input.essential_count;
        }

        if (input.hasOwnProperty('docker_image')) {
            this.dockerImage = input.docker_image;
        }

        if (input.hasOwnProperty('total_count')) {
            this.totalCount = input.total_count;
        }

        if (input.hasOwnProperty('ports')) {
            this.ports = [];

            for (let port of input.ports) {
                this.ports.push(new Port().deserialize(port));
            }
        }

        if (input.hasOwnProperty('services')) {
            this.services = [];

            for (let service of input.services) {
                this.services.push(new Service().deserialize(service));
            }
        }

        return this;
    }
}
