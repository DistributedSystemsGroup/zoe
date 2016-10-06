import { Injectable } from '@angular/core'
import { SoftwareInfo } from '../entities/software-info'
import { Headers, Http } from '@angular/http';
import { Execution } from '../entities/execution'
import { Service } from '../entities/service'
import { ServiceDiscovery } from '../entities/service-discovery'
import { Statistics } from '../entities/statistics'

import { environment } from '../../environments/environment';

import 'rxjs/add/operator/toPromise';
import { StorageService } from './storage.service'

let AUTH_HEADERS: string = 'AUTH_HEADERS'

@Injectable()
export class ApiService {
  private baseUrl = environment.apiEndpoint

  private softwareInfoEndpoint = '/info'
  private executionEndpoint = '/execution'
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
    var endpoint: string = this.baseUrl + this.softwareInfoEndpoint

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new SoftwareInfo().deserialize(response.json()))
      .catch(this.handleError);
  }

  getExecutionDetails(id: string): Promise<Execution> {
    var endpoint: string = this.baseUrl + this.executionEndpoint + '/' + id

    return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => new Execution().deserialize(response.json()))
      .catch(this.handleError);
  }

  terminateExecution(id: string): Promise<boolean> {
    var endpoint: string = this.baseUrl + this.executionEndpoint + '/' + id

    return this.http.delete(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => Boolean(response.status == 204))
      .catch(this.handleError);
  }

  deleteExecution(id: string): Promise<boolean> {
    var endpoint: string = this.baseUrl + this.deleteExecutionEndpoint + '/' + id

    return this.http.delete(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => Boolean(response.status == 204))
      .catch(this.handleError);
  }

  getAllExecutions(): Promise<Execution[]> {
    var endpoint: string = this.baseUrl + this.executionEndpoint

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

    var jsonData = {
      "name": name,
      "application": application
    }

    return this.http.post(endpoint, JSON.stringify(jsonData), {headers: this.storageService.getAuthHeader()})
      .toPromise()
      .then(response => response.json().execution_id)
      .catch(this.handleError);
  }

  getServiceDetails(id: string) : Promise<Service> {
    var endpoint: string = this.baseUrl + this.serviceEndpoint + '/' + id

    return this.http.get(endpoint, { headers: this.storageService.getAuthHeader() })
      .toPromise()
      .then(response => new Service().deserialize(response.json()))
      .catch(this.handleError);
  }

  discoverServices(executionId: string, serviceType: string) : Promise<ServiceDiscovery> {
    var endpoint: string = this.baseUrl + this.serviceDiscoveryEndpoint + '/' + executionId + '/' + serviceType

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new ServiceDiscovery().deserialize(response.json()))
      .catch(this.handleError);
  }

  getStatistics() : Promise<Statistics> {
    var endpoint: string = this.baseUrl + this.statisticsEndpoint

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new Statistics().deserialize(response.json()))
      .catch(this.handleError);
  }

  private handleError(error: any): Promise<any> {
    if (!environment.production)
      console.error('An error occurred', error); // for demo purposes only
    return Promise.reject(error.message || error);
  }
}
