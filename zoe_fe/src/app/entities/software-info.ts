import { Serializable } from '../interfaces/serializable';

export class SoftwareInfo implements Serializable<SoftwareInfo> {
    version: string;
    deploymentName: string;
    applicationFormatVersion: number;
    apiVersion: string;

    rawObject: Object;

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('version')) {
            this.version = input.version;
        }

        if (input.hasOwnProperty('deployment_name')) {
            this.deploymentName = input.deployment_name;
        }

        if (input.hasOwnProperty('application_format_version')) {
            this.applicationFormatVersion = input.application_format_version;
        }

        if (input.hasOwnProperty('api_version')) {
            this.apiVersion = input.api_version;
        }

        return this;
    }
}
