import { Serializable } from '../interfaces/serializable';

export class Credentials implements Serializable<Credentials> {
    username: string;
    role: string;

    isAdmin(): boolean {
        return (this.role == 'admin');
    }

    rawObject: Object;

    deserialize(input) {
        this.rawObject = input;

        if (input.hasOwnProperty('uid')) {
            this.username = input.uid;
        }

        if (input.hasOwnProperty('role')) {
            this.role = input.role;
        }

        return this;
    }
}
