import { Injectable } from '@angular/core'
import { SoftwareInfo } from '../entities/software-info.entity'
import { Headers, Http } from '@angular/http';

import 'rxjs/add/operator/toPromise';

@Injectable()
export class InfoService {
    private headers = new Headers({'Content-Type': 'application/json'})

    private infoUrl = ''

    constructor(private http: Http) { }

    get(): Promise<SoftwareInfo> {
         return this.http.get(this.infoUrl)
             .toPromise()
             .then(response => new SoftwareInfo().deserialize(response.json().data))
//             .then(response => response.json().data as SoftwareInfo)
             .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error('An error occurred', error); // for demo purposes only
        return Promise.reject(error.message || error);
    }
}