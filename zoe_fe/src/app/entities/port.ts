import { Serializable } from '../interfaces/serializable';

export class Port implements Serializable<Port> {
    protocol: string;
    name: string;
    path: string;
    isMainEndpoint: boolean;
    portNumber: number;

    rawObject: Object;

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('protocol')) {
            this.protocol = input.protocol;
        }

        if (input.hasOwnProperty('name')) {
            this.name = input.name;
        }

        if (input.hasOwnProperty('path')) {
            this.path = input.path;
        }

        if (input.hasOwnProperty('port_number')) {
            this.portNumber = input.port_number;
        }

        if (input.hasOwnProperty('is_main_endpoint')) {
            this.isMainEndpoint = input.is_main_endpoint;
        }

        return this;
    }
}
