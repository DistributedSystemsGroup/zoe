import { Serializable } from '../interfaces/serializable';

export class Statistics implements Serializable<Statistics> {
    terminationThreadsCount: number;
    queueLenght: number;

    rawObject: Object;

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('termination_threads_count')) {
            this.terminationThreadsCount = input.termination_threads_count;
        }

        if (input.hasOwnProperty('queue_lenght')) {
            this.queueLenght = input.queue_lenght;
        }

        return this;
    }
}
