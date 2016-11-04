import { Serializable } from '../interfaces/serializable';
import { ServiceDescription } from './service-description';

export class Execution implements Serializable<Execution> {
    id: string;
    name: string;
    owner: string;
    status: string;
    errorMessage: string;
    submitted: number;
    started: number;

    //application: string;
    //scheduled: number;
    //finished: number;

    ended: number;
    description: ServiceDescription;
    services: number[];

    rawObject: Object;

    canBeRestarted() : boolean {
        return this.status && this.status == 'terminated';
    }

    canBeDeleted() : boolean {
        return this.status && this.status == 'terminated';
    }

    canBeTerminated() : boolean {
        return this.status && this.status == 'running';
    }

    applicationName() : string {
        if (this.description && this.description.name)
            return this.description.name;
        return '';
    }

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('id')) {
            this.id = input.id;
        }

        if (input.hasOwnProperty('execution_id')) {
            this.id = input.execution_id;
        }

        if (input.hasOwnProperty('name')) {
            this.name = input.name;
        }

        if (input.hasOwnProperty('error_message')) {
            this.errorMessage = input.error_message;
        }

        if (input.hasOwnProperty('user_id')) {
            this.owner = input.user_id;
        }

        if (input.hasOwnProperty('status')) {
            this.status = input.status;
        }

        if (input.hasOwnProperty('time_submit')) {
            this.submitted = input.time_submit;
        }

        if (input.hasOwnProperty('time_start')) {
            this.started = input.time_start;
        }
/*
        if (input.hasOwnProperty('application')) {
            this.application = input.application;
        }

        if (input.hasOwnProperty('time_schedul')) {
            this.scheduled = moment.unix(input.time_schedul).toDate();
        }

        if (input.hasOwnProperty('time_finish')) {
            this.finished = moment.unix(input.time_finish).toDate();
        }
*/
        if (input.hasOwnProperty('description')) {
            this.description = new ServiceDescription().deserialize(input.description);
        }

        if (input.hasOwnProperty('time_end')) {
            this.ended = input.time_end;
        }

        if (input.hasOwnProperty('services')) {
            this.services = [];

            for (let service of input.services) {
                this.services.push(service);
            }
        }

        return this;
    }
}
