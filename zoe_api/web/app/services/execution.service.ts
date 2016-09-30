import { Injectable } from '@angular/core'
import { Execution } from '../entities/execution.entity'
import { Service } from '../entities/service.entity'
import { Headers, Http } from '@angular/http';

import 'rxjs/add/operator/toPromise';

@Injectable()
export class ExecutionService {
    private headers = new Headers({'Content-Type': 'application/json'})

    private executionListUrl = ''
    private executionUrl = ''

    private mockExecution: Execution
    private mockMyExecutions: Execution[] = []
    private mockAllExecutions: Execution[] = []

    constructor(private http: Http) {
    }

    getExecution(id: String): Promise<Execution> {
        return Promise.resolve(this.mockExecution);
        /*
        return this.http.get(this.executionUrl)
            .toPromise()
            .then(response => response.json().data as Execution)
            .catch(this.handleError);
         */
    }

    getExecutionsList(adminMode: Boolean) : Promise<Execution[]> {
        if (adminMode)
            return this.getAllExecutions()
        else
            return this.getMyExecutions()
    }

    getMyExecutions() : Promise<Execution[]> {
        return Promise.resolve(this.mockMyExecutions);
/*
        return this.http.get(this.executionListUrl)
            .toPromise()
            .then(response => response.json().data as Execution[])
            .catch(this.handleError);
 */
    }

    getAllExecutions() : Promise<Execution[]> {
        return Promise.resolve(this.mockAllExecutions);
 /*
        return this.http.get(this.executionListUrl)
            .toPromise()
            .then(response => response.json().data as Execution[])
            .catch(this.handleError);
  */
    }

    private handleError(error: any): Promise<any> {
        console.error('An error occurred', error); // for demo purposes only
        return Promise.reject(error.message || error);
    }
}