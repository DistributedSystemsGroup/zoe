import { Serializable } from '../interfaces/serializable.interface'

export class Resource implements Serializable<Resource> {
    memory: string

    rawObject: Object

    deserialize(input) {
        this.rawObject = input

        if (input.hasOwnProperty('memory'))
            this.memory = input.memory;

        return this;
    }
}