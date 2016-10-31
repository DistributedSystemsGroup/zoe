import { Injectable } from '@angular/core';
import { SoftwareInfo } from '../entities/software-info';
import { Headers, Http } from '@angular/http';
import { Execution } from '../entities/execution';
import { Service } from '../entities/service';
import { ServiceDiscovery } from '../entities/service-discovery';
import { Statistics } from '../entities/statistics';

import { environment } from '../../environments/environment';

import 'rxjs/add/operator/toPromise';
import { StorageService } from './storage.service';

let AUTH_HEADERS: string = 'AUTH_HEADERS';

@Injectable()
export class ApiService {
  private baseUrl = environment.apiEndpoint;

  private softwareInfoEndpoint = '/info';
  private executionEndpoint = '/execution';
  private deleteExecutionEndpoint = '/execution/delete';
  private serviceEndpoint = '/service';
  private serviceDiscoveryEndpoint = '/discovery/by_group';
  private statisticsEndpoint = '/statistics/scheduler';

  constructor(
    private http: Http,
    private storageService: StorageService
  ) { }

  isUserLoggedIn(): Boolean {
    return (this.storageService.getAuthHeader() != null);
  }

  loginHandler(username: string, headers: Headers, response: any): Boolean {
    this.storageService.removeAuthHeader();
    this.storageService.removeUsername();

    if (!response.ok) {
      return false;
    }

    if (response.status === 401) {
      return false;
    }

    if (response.status === 200) {
      this.storageService.setAuthHeader(headers);
      this.storageService.setUsername(username);
      return true;
    }

    return false;
  }

  login(username: string, password: string): Promise<Boolean> {
    let headers = new Headers();
    headers.append('Authorization', 'Basic ' +
      btoa(username + ':' + password));

    return this.http.get(this.baseUrl + this.executionEndpoint, { headers: headers })
      .toPromise()
      .then(response => this.loginHandler(username, headers, response))
      .catch(this.handleError);
  }

  getSoftwareInfo(): Promise<SoftwareInfo> {
    let endpoint: string = this.baseUrl + this.softwareInfoEndpoint;

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new SoftwareInfo().deserialize(response.json()))
      .catch(this.handleError);
  }

  getExecutionDetails(id: string): Promise<Execution> {
    let endpoint: string = this.baseUrl + this.executionEndpoint + '/' + id;

    return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => new Execution().deserialize(response.json()))
      .catch(this.handleError);
  }

  terminateExecution(id: string): Promise<Boolean> {
    let endpoint: string = this.baseUrl + this.executionEndpoint + '/' + id;

    return this.http.delete(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => Boolean(response.status === 204))
      .catch(this.handleError);
  }

  deleteExecution(id: string): Promise<Boolean> {
    let endpoint: string = this.baseUrl + this.deleteExecutionEndpoint + '/' + id;

    return this.http.delete(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => Boolean(response.status === 204))
      .catch(this.handleError);
  }

  getAllExecutions(): Promise<Execution[]> {
    let endpoint: string = this.baseUrl + this.executionEndpoint;

    return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => {
        let executionsList: Execution[] = [];

        Object.keys(response.json()).forEach(key => {
          executionsList.push(new Execution().deserialize(response.json()[key]));
        });
        return executionsList;
      })
      .catch(this.handleError);
  }

  startExecution(name: string, application: Object): Promise<number> {
    let endpoint: string = this.baseUrl + this.executionEndpoint;

    let jsonData = {
      'name': name,
      'application': application
    };

    return this.http.post(endpoint, JSON.stringify(jsonData), {headers: this.storageService.getAuthHeader()})
      .toPromise()
      .then(response => response.json().execution_id)
      .catch(this.handleError);
  }

  getServiceDetails(id: string): Promise<Service> {
    let endpoint: string = this.baseUrl + this.serviceEndpoint + '/' + id;

    return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => new Service().deserialize(response.json()))
      .catch(this.handleError);
  }

  discoverServices(executionId: string, serviceType: string): Promise<ServiceDiscovery> {
    let endpoint: string = this.baseUrl + this.serviceDiscoveryEndpoint + '/' + executionId + '/' + serviceType;

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new ServiceDiscovery().deserialize(response.json()))
      .catch(this.handleError);
  }

  getStatistics(): Promise<Statistics> {
    let endpoint: string = this.baseUrl + this.statisticsEndpoint;

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new Statistics().deserialize(response.json()))
      .catch(this.handleError);
  }

  private handleError(error: any): Promise<any> {
    if (!environment.production) {
      console.error('An error occurred', error); // for demo purposes only
    }
    return Promise.reject(error.message || error);
  }
}

export class ApiServiceStub extends ApiService {
  private isLoggedIn: Boolean;
  private loginResult: Boolean;
  private softwareInfo: SoftwareInfo;
  private execution: Execution;
  private terminateExecutionResult: Boolean;
  private deleteExecutionResult: Boolean;
  private allExecutions: Execution[];
  private startExecutionResult: number;
  private service: Service;
  private serviceDiscovery: ServiceDiscovery;
  private statistics: Statistics;
  
  constructor(
      isLoggedIn: Boolean,
      loginResult: Boolean,
      softwareInfo: SoftwareInfo,
      execution: Execution,
      terminateExecutionResult: Boolean,
      deleteExecutionResult: Boolean,
      allExecutions: Execution[],
      startExecutionResult: number,
      service: Service,
      serviceDiscovery: ServiceDiscovery,
      statistics: Statistics
  ) {
    super(null, null);

    this.isLoggedIn = isLoggedIn;
    this.loginResult = loginResult;
    this.softwareInfo = softwareInfo;
    this.execution = execution;
    this.terminateExecutionResult = terminateExecutionResult;
    this.deleteExecutionResult = deleteExecutionResult;
    this.allExecutions = allExecutions;
    this.startExecutionResult = startExecutionResult;
    this.service = service;
    this.serviceDiscovery = serviceDiscovery;
    this.statistics = statistics;
  }

  isUserLoggedIn(): Boolean {
    return this.isLoggedIn;
  }

  login(username: string, password: string): Promise<Boolean> {
    return Promise.resolve(this.loginResult);
  }

  getSoftwareInfo(): Promise<SoftwareInfo> {
    return Promise.resolve(this.softwareInfo);
  }

  getExecutionDetails(id: string): Promise<Execution> {
    return Promise.resolve(this.execution);
  }

  terminateExecution(id: string): Promise<Boolean> {
    return Promise.resolve(this.terminateExecutionResult);
  }

  deleteExecution(id: string): Promise<Boolean> {
    return Promise.resolve(this.deleteExecutionResult);
  }

  getAllExecutions(): Promise<Execution[]> {
    return Promise.resolve(this.allExecutions);
  }

  startExecution(name: string, application: Object): Promise<number> {
    return Promise.resolve(this.startExecutionResult);
  }

  getServiceDetails(id: string): Promise<Service> {
    return Promise.resolve(this.service);
  }

  discoverServices(executionId: string, serviceType: string): Promise<ServiceDiscovery> {
    return Promise.resolve(this.serviceDiscovery);
  }

  getStatistics(): Promise<Statistics> {
    return Promise.resolve(this.statistics);
  }
}