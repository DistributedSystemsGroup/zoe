import { Serializable } from '../interfaces/serializable';

export class ServiceDiscovery implements Serializable<ServiceDiscovery> {
    serviceType: string;
    executionId: string;
    dnsNames: string[];

    rawObject: Object;

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('service_type')) {
            this.serviceType = input.service_type;
        }

        if (input.hasOwnProperty('execution_id')) {
            this.executionId = input.execution_id;
        }

        if (input.hasOwnProperty('dns_names')) {
            this.dnsNames = [];

            for (let name of input.dns_names) {
                this.dnsNames.push(name)
            }
        }

        return this;
    }
}
