import { Injectable } from '@angular/core'
import { SoftwareInfo } from '../entities/software-info.entity'
import { Headers, RequestOptions, Http } from '@angular/http';
import { Execution } from '../entities/execution.entity'
import { Service } from '../entities/service.entity'
import { ServiceDiscovery } from '../entities/service-discovery.entity'
import { Statistics } from '../entities/statistics.entity'

import 'rxjs/add/operator/toPromise';
import { StorageService } from './storage.service'

let AUTH_HEADERS: string = 'AUTH_HEADERS'

@Injectable()
export class ApiService {
    private realEndpoint = true

    private baseUrl = 'http://localhost:5001/zoe/api/0.6'
    private softwareInfoEndpoint = '/info'
    private executionEndpoint = '/execution'
    private terminateExecutionEndpoint = '/execution'
    private deleteExecutionEndpoint = '/execution/delete'
    private serviceEndpoint = '/service'
    private serviceDiscoveryEndpoint = '/discovery/by_group'
    private statisticsEndpoint = '/statistics/scheduler'

    constructor(
        private http: Http,
        private storageService: StorageService
    ) { }

    isUserLoggedIn(): Boolean {
        return (this.storageService.getAuthHeader() != null)
    }

    loginHandler(username: string, headers: Headers, response: any): Boolean {
        this.storageService.removeAuthHeader()
        this.storageService.removeUsername()

        if (!response.ok)
            return false

        if (response.status == 401)
            return false

        if (response.status == 200) {
            this.storageService.setAuthHeader(headers)
            this.storageService.setUsername(username)
            return true
        }

        return false
    }

    login(username: string, password: string): Promise<boolean> {
        var headers = new Headers();
        headers.append('Authorization', 'Basic ' +
            btoa(username + ':' + password));

        return this.http.get(this.baseUrl + this.executionEndpoint, { headers: headers })
            .toPromise()
            .then(response => this.loginHandler(username, headers, response))
            .catch(this.handleError);
    }

    getSoftwareInfo(): Promise<SoftwareInfo> {
        var endpoint: string
        if (this.realEndpoint)
            endpoint = this.baseUrl + this.softwareInfoEndpoint
        else
            endpoint = "app/examples/software_info.json"

        return this.http.get(endpoint)
            .toPromise()
            .then(response => new SoftwareInfo().deserialize(response.json()))
            .catch(this.handleError);
    }

    getExecutionDetails(id: string): Promise<Execution> {
        var endpoint: string
        if (this.realEndpoint)
            endpoint = this.baseUrl + this.executionEndpoint + '/' + id
        else
            endpoint = "app/examples/execution_details_" + id +".json"

        return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
            .toPromise()
            .then(response => new Execution().deserialize(response.json()))
            .catch(this.handleError);
    }

    terminateExecution(id: string): Promise<boolean> {
        var endpoint: string = this.baseUrl + this.terminateExecutionEndpoint + '/' + id

        if (this.realEndpoint) {
            return this.http.delete(endpoint, { headers: this.storageService.getAuthHeader() })
                .toPromise()
                .then(response => Boolean(response.status == 204))
                .catch(this.handleError);
        }
        else
            return Promise.resolve(true)
    }

    deleteExecution(id: string): Promise<boolean> {
        var endpoint: string = this.baseUrl + this.deleteExecutionEndpoint + '/' + id

        if (this.realEndpoint) {
            return this.http.delete(endpoint, { headers: this.storageService.getAuthHeader() })
                .toPromise()
                .then(response => Boolean(response.status == 204))
                .catch(this.handleError);
        }
        else
            return Promise.resolve(true)
    }

    getAllExecutions(): Promise<Execution[]> {
        var endpoint: string
        if (this.realEndpoint)
            endpoint = this.baseUrl + this.executionEndpoint
        else
            endpoint = "app/examples/executions_list.json"

        return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
            .toPromise()
            .then(response => {
                var executionsList: Execution[] = []

                Object.keys(response.json()).forEach(key => {
                    executionsList.push(new Execution().deserialize(response.json()[key]))
                });
                return executionsList
            })
            .catch(this.handleError);
    }

    startExecution(name: string, application: Object): Promise<number> {
        var endpoint: string = this.baseUrl + this.executionEndpoint

        if (this.realEndpoint) {
            var jsonData = {}
            jsonData['name'] = name
            jsonData['application'] = application

            return this.http.post(endpoint, JSON.stringify(jsonData), {headers: this.storageService.getAuthHeader()})
                .toPromise()
                .then(response => response.json().execution_id)
                .catch(this.handleError);
        }
        else
            return Promise.resolve(23453)
/*
        if (this.realEndpoint) {
            return Observable.create(observer => {
                let formData: FormData = new FormData(),
                    xhr: XMLHttpRequest = new XMLHttpRequest();

                formData.append("file", file, file.name);
                formData.append("exec_name", name)

                let authHeader = this.storageService.getAuthHeader()
                xhr.setRequestHeader("Authorization", authHeader.get("authorization"))

                xhr.onreadystatechange = () => {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            observer.next(JSON.parse(xhr.response).execution_id);
                            observer.complete();
                        } else {
                            observer.error(xhr.response);
                        }
                    }
                };

                xhr.open('POST', endpoint, true);
                xhr.send(formData);
            });

        }
        else
            return Promise.resolve(23453)
            */
    }

    getServiceDetails(id: string) : Promise<Service> {
        var endpoint: string
        if (this.realEndpoint)
            endpoint = this.baseUrl + this.serviceEndpoint + '/' + id
        else
            endpoint = "app/examples/service_details_" + id +".json"

        return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
            .toPromise()
            .then(response => new Service().deserialize(response.json()))
            .catch(this.handleError);
    }

    discoverServices(executionId: string, serviceType: string) : Promise<ServiceDiscovery> {
        var endpoint: string
        if (this.realEndpoint)
            endpoint = this.baseUrl + this.serviceDiscoveryEndpoint + '/' + executionId + '/' + serviceType
        else
            endpoint = "app/examples/service_discovery.json"

        return this.http.get(endpoint)
            .toPromise()
            .then(response => new ServiceDiscovery().deserialize(response.json()))
            .catch(this.handleError);
    }

    getStatistics() : Promise<Statistics> {
        var endpoint: string
        if (this.realEndpoint)
            endpoint = this.baseUrl + this.statisticsEndpoint
        else
            endpoint = "app/examples/statistics.json"

        return this.http.get(endpoint)
            .toPromise()
            .then(response => new Statistics().deserialize(response.json()))
            .catch(this.handleError);
    }

    private handleError(error: any): Promise<any> {
        console.error('An error occurred', error); // for demo purposes only
        return Promise.reject(error.message || error);
    }
}
